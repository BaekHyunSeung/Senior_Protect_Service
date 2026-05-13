# 분석 데이터 DB 업데이트
from fastapi import UploadFile


class DataSaveService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> None:
        del file
        del payload
