# 분석 데이터 DB 업데이트
from datetime import datetime

from fastapi import UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from DB.Entity import Accident, AccidentDetail, Device
from Model.Request import ReceivePayload


class DataSaveService:
    async def run(
        self,
        session: AsyncSession,
        file: UploadFile,
        payload: str,
    ) -> None:
        del file

        try:
            request_payload = ReceivePayload.model_validate_json(payload)

            device = await self._get_device(
                session=session,
                device_id=request_payload.header.Device_ID,
            )
            accident_time = datetime.strptime(
                request_payload.header.TimeStamp,
                "%Y%m%d_%H%M%S",
            ).time()

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
                Time=accident_time,
                Detail_id=accident_detail.Detail_id,
            )
            session.add(accident)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

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
