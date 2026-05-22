# 분석 데이터 DB 업데이트
from dataclasses import dataclass
from datetime import datetime
from time import monotonic

from fastapi import UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from Config.Server_Options import load_server_options
from DB.Entity import Accident, AccidentDetail, Device
from Model.Request import ReceivePayload

SERVER_OPTIONS = load_server_options()
ACCIDENT_FILTER_SETTINGS = SERVER_OPTIONS["accident_filter"]
ACCIDENT_SESSION_TIMEOUT_SEC = max(
    1.0,
    float(ACCIDENT_FILTER_SETTINGS["session_timeout_sec"]),
)


@dataclass
class AccidentSessionState:
    started_at: float
    last_seen_at: float
    saved: bool = False


class DataSaveService:
    def __init__(self) -> None:
        self._active_accident_sessions: dict[tuple[int, str], AccidentSessionState] = {}

    async def run(
        self,
        session: AsyncSession,
        file: UploadFile,
        payload: str,
    ) -> None:
        del file

        try:
            request_payload = ReceivePayload.model_validate_json(payload)
            accident_key = (
                request_payload.header.Device_ID,
                request_payload.analysis.Type,
            )
            if self._is_accident_in_progress(accident_key):
                return

            device = await self._get_device(
                session=session,
                device_id=request_payload.header.Device_ID,
            )
            accident_timestamp = datetime.fromisoformat(
                request_payload.header.TimeStamp
            )

            bbox = request_payload.analysis.bbox
            accident_detail = AccidentDetail(
                bbox_x1=float(bbox[0]),
                bbox_y1=float(bbox[1]),
                bbox_x2=float(bbox[2]),
                bbox_y2=float(bbox[3]),
            )
            session.add(accident_detail)
            await session.flush()

            accident = Accident(
                User_id=device.Target,
                Device_id=device.Device_id,
                Type=request_payload.analysis.Type,
                Time=accident_timestamp,
                Detail_id=accident_detail.Detail_id,
            )
            session.add(accident)
            await session.commit()
            self._mark_accident_started(accident_key)
        except Exception:
            await session.rollback()
            raise

    def _is_accident_in_progress(self, accident_key: tuple[int, str]) -> bool:
        self._cleanup_expired_sessions()
        accident_session = self._active_accident_sessions.get(accident_key)
        if accident_session is None:
            return False

        accident_session.last_seen_at = monotonic()
        return accident_session.saved

    def _mark_accident_started(self, accident_key: tuple[int, str]) -> None:
        self._cleanup_expired_sessions()
        now = monotonic()
        self._active_accident_sessions[accident_key] = AccidentSessionState(
            started_at=now,
            last_seen_at=now,
            saved=True,
        )

    def _cleanup_expired_sessions(self) -> None:
        now = monotonic()
        expired_keys = [
            accident_key
            for accident_key, accident_session in self._active_accident_sessions.items()
            if now - accident_session.last_seen_at >= ACCIDENT_SESSION_TIMEOUT_SEC
        ]
        for accident_key in expired_keys:
            del self._active_accident_sessions[accident_key]

    async def _get_device(
        self,
        session: AsyncSession,
        device_id: int,
    ) -> Device:
        result = await session.exec(
            select(Device).where(Device.Device_id == device_id)
        )
        device = result.first()
        if device is None:
            raise ValueError("등록되지 않은 Device_ID 입니다.")

        return device
