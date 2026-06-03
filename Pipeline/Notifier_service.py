# 사고 알림 발송 -> 관리자 웹, 보호자 앱
from fastapi import UploadFile


class NotifierService:
    async def run(
        self,
        file: UploadFile | None,
        payload: str,
    ) -> None:
        del file
        del payload