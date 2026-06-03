import asyncio
from pathlib import Path
from time import monotonic

import numpy as np
from fastapi import UploadFile

from Config.Server_Options import load_server_options
from Model.Request import ReceivePayload
from Model.Video import VideoSessionState
from .Video_util import (
    build_video_output_paths,
    create_video_writer,
    delete_file_if_exists,
    finalize_video_file,
    image_bytes_to_bgr_frame,
    release_writer_safely,
    write_frame_to_session,
)

SERVER_OPTIONS = load_server_options()
VIDEO_SETTINGS = SERVER_OPTIONS["video"]


class VideoMakeService:
    def __init__(self) -> None:
        self.output_root = Path(VIDEO_SETTINGS["output_dir"])
        self.default_fps = max(1, int(VIDEO_SETTINGS["fps"]))
        self.segment_timeout_sec = max(
            0.5,
            float(VIDEO_SETTINGS["session_end_timeout_sec"]),
        )
        self.monitor_interval_sec = max(
            0.1,
            float(VIDEO_SETTINGS["monitor_interval_sec"]),
        )
        self._sessions: dict[int, VideoSessionState] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        self._monitor_task: asyncio.Task[None] | None = None
        self.output_root.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        file: UploadFile | None,
        payload: str,
    ) -> None:
        if file is None:
            return

        request_payload = ReceivePayload.model_validate_json(payload)
        frame = await self._read_frame(file=file)
        device_id = request_payload.header.Device_ID
        await self._ensure_monitor_task()

        lock = self._locks.setdefault(device_id, asyncio.Lock())
        async with lock:
            session = self._sessions.get(device_id)
            if session is None:
                session = self._create_session(
                    device_id=device_id,
                    width=int(frame.shape[1]),
                    height=int(frame.shape[0]),
                )
                self._sessions[device_id] = session

            if session.width != int(frame.shape[1]) or session.height != int(frame.shape[0]):
                await self._finalize_session(device_id=device_id, session=session)
                session = self._create_session(
                    device_id=device_id,
                    width=int(frame.shape[1]),
                    height=int(frame.shape[0]),
                )
                self._sessions[device_id] = session
            self._write_frame(session=session, frame=frame)
            session.last_received_at = monotonic()

    async def _ensure_monitor_task(self) -> None:
        if self._monitor_task is not None and not self._monitor_task.done():
            return

        self._monitor_task = asyncio.create_task(self._monitor_sessions())

    async def _monitor_sessions(self) -> None:
        while True:
            await asyncio.sleep(self.monitor_interval_sec)
            now = monotonic()

            for device_id in list(self._sessions):
                lock = self._locks.setdefault(device_id, asyncio.Lock())
                async with lock:
                    session = self._sessions.get(device_id)
                    if session is None:
                        continue

                    if now - session.last_received_at < self.segment_timeout_sec:
                        continue

                    await self._finalize_session(device_id=device_id, session=session)

    async def _read_frame(self, file: UploadFile) -> np.ndarray:
        image_bytes = await file.read()
        return image_bytes_to_bgr_frame(image_bytes)

    def _create_session(
        self,
        device_id: int,
        width: int,
        height: int,
    ) -> VideoSessionState:
        temp_path, output_path = build_video_output_paths(
            output_root=self.output_root,
            device_id=device_id,
        )
        writer = create_video_writer(
            temp_path=temp_path,
            fps=self.default_fps,
            width=width,
            height=height,
        )
        now = monotonic()
        return VideoSessionState(
            writer=writer,
            temp_path=temp_path,
            output_path=output_path,
            width=width,
            height=height,
            started_at=now,
            last_received_at=now,
        )

    def _write_frame(
        self,
        session: VideoSessionState,
        frame: np.ndarray,
    ) -> None:
        write_frame_to_session(session, frame)

    async def _finalize_session(
        self,
        device_id: int,
        session: VideoSessionState,
    ) -> None:
        if session.frames_written <= 0:
            release_writer_safely(session)
            self._sessions.pop(device_id, None)
            delete_file_if_exists(session.temp_path)
            return

        await asyncio.to_thread(self._finalize_session_file, session)
        self._sessions.pop(device_id, None)

    def _finalize_session_file(
        self,
        session: VideoSessionState,
    ) -> None:
        finalize_video_file(session)
