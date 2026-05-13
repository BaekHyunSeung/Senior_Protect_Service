# 복호화 단계
from fastapi import UploadFile


class SecurityService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> tuple[UploadFile, str]:
        return file, payload