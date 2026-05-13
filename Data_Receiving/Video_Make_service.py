# 영상 생성
from fastapi import UploadFile


class VideoMakeService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> None:
        del file
        del payload