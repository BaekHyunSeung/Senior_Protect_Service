# 마스킹 복원
from fastapi import UploadFile


class TransformService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> tuple[UploadFile, str]:
        return file, payload