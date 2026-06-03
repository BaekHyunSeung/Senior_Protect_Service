# 복호화 단계
from fastapi import UploadFile


class SecurityService:
    async def run(
        self,
        file: UploadFile | None,
        payload: str,
    ) -> tuple[UploadFile | None, str]:
        return file, payload