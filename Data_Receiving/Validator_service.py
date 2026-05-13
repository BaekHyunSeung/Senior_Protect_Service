#메타 데이터 형식 검증
from fastapi import UploadFile


class ValidatorService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> None:
        del file
        del payload