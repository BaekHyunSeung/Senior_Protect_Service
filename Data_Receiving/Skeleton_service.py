# 스켈레톤 기능
from fastapi import UploadFile


class SkeletonService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> tuple[UploadFile, str]:
        return file, payload