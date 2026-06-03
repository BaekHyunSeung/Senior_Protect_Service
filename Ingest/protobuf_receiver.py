import asyncio
import json
import logging
import socket
from collections import deque
from contextlib import suppress
from datetime import datetime
from time import monotonic

from google.protobuf.message import DecodeError

from DB.DB import async_session_factory
from Pipeline.base import DataPipeline
from Model.Telemetry import TelemetryKeypoint, TelemetryMessage
from protobuf_server.d import pose_telemetry_pb2 as pb

logger = logging.getLogger(__name__)


class ProtobufIngestReceiver:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 50052,
        max_buffer_size: int = 256,
        message_ttl_sec: float = 2.0,
    ) -> None:
        self.host = host
        self.port = port
        self.max_buffer_size = max_buffer_size
        self.message_ttl_sec = message_ttl_sec
        self._udp_socket: socket.socket | None = None
        self._receiver_task: asyncio.Task[None] | None = None
        self._pipeline = DataPipeline()
        self._buffer: deque[TelemetryMessage] = deque()
        self._dedupe_keys: set[str] = set()

    async def start(self) -> None:
        if self._receiver_task is not None and not self._receiver_task.done():
            return

        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind((self.host, self.port))
        udp_sock.setblocking(False)

        self._udp_socket = udp_sock
        self._receiver_task = asyncio.create_task(self._udp_receiver_loop())
        logger.info("Protobuf ingest receiver ready on %s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self._receiver_task is not None:
            self._receiver_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._receiver_task
            self._receiver_task = None

        if self._udp_socket is not None:
            self._udp_socket.close()
            self._udp_socket = None

    async def _udp_receiver_loop(self) -> None:
        if self._udp_socket is None:
            raise RuntimeError("UDP socket is not initialized.")

        loop = asyncio.get_running_loop()

        while True:
            try:
                data, addr = await loop.sock_recvfrom(self._udp_socket, 4096)
                logger.info("Telemetry protobuf received: %s bytes from %s", len(data), addr)

                packet = pb.PosePacket()
                packet.ParseFromString(data)

                telemetry_message = self._to_telemetry_message(packet=packet, addr=addr)
                if not self._store_message(telemetry_message):
                    continue

                payload = self._convert_telemetry_to_payload(telemetry_message)
                await self._dispatch_payload(payload)
            except DecodeError as exc:
                logger.warning("Telemetry protobuf parse error: %s", exc)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Protobuf ingest receiver failed")
                await asyncio.sleep(0.01)

    async def _dispatch_payload(self, payload: str) -> None:
        async with async_session_factory() as session:
            await self._pipeline.run(session=session, file=None, payload=payload)

    def _to_telemetry_message(
        self,
        packet: pb.PosePacket,
        addr: tuple[str, int],
    ) -> TelemetryMessage:
        keypoints = [
            TelemetryKeypoint(x=keypoint.x, y=keypoint.y, score=keypoint.score)
            for keypoint in packet.keypoints[:17]
        ]
        dedupe_key = self._build_dedupe_key(packet=packet, addr=addr)
        return TelemetryMessage(
            label=packet.label or "unknown",
            confidence=packet.confidence,
            keypoints=keypoints,
            source_ip=addr[0],
            source_port=addr[1],
            dedupe_key=dedupe_key,
        )

    def _store_message(self, message: TelemetryMessage) -> bool:
        self._evict_expired_messages()

        if message.dedupe_key in self._dedupe_keys:
            logger.info("Telemetry duplicate skipped: %s", message.dedupe_key)
            return False

        if len(self._buffer) >= self.max_buffer_size:
            oldest = self._buffer.popleft()
            self._dedupe_keys.discard(oldest.dedupe_key)
            logger.warning("Telemetry buffer full. Oldest message evicted.")

        self._buffer.append(message)
        self._dedupe_keys.add(message.dedupe_key)
        logger.info("Telemetry buffered. Current buffer size=%s", len(self._buffer))
        return True

    def _evict_expired_messages(self) -> None:
        now = monotonic()
        while self._buffer:
            oldest = self._buffer[0]
            if oldest.received_at_monotonic + self.message_ttl_sec > now:
                break

            expired = self._buffer.popleft()
            self._dedupe_keys.discard(expired.dedupe_key)
            logger.info("Telemetry expired and evicted: %s", expired.dedupe_key)

    def _build_dedupe_key(
        self,
        packet: pb.PosePacket,
        addr: tuple[str, int],
    ) -> str:
        rounded_points = [
            f"{keypoint.x:.4f}:{keypoint.y:.4f}:{keypoint.score:.4f}"
            for keypoint in packet.keypoints[:17]
        ]
        return "|".join(
            [
                addr[0],
                str(addr[1]),
                packet.label or "unknown",
                f"{packet.confidence:.4f}",
                ",".join(rounded_points),
            ]
        )

    def _convert_telemetry_to_payload(self, message: TelemetryMessage) -> str:
        payload = {
            "header": {
                "Device_ID": 1,
                "TimeStamp": datetime.now().isoformat(timespec="seconds"),
            },
            "analysis": {
                "Type": message.label,
                "bbox": [0, 0, 0, 0],
                "Masking_box": [0, 0, 0, 0],
                "Skeleton_point": [
                    {
                        "index": index,
                        "x": keypoint.x,
                        "y": keypoint.y,
                    }
                    for index, keypoint in enumerate(message.keypoints)
                ],
            },
        }
        return json.dumps(payload)


protobuf_ingest_receiver = ProtobufIngestReceiver()
