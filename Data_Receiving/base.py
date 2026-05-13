#데이터 수신 파이프 라인
import os

from dotenv import load_dotenv
from fastapi import UploadFile

from .Data_Save_service import DataSaveService
from .Notifier_service import NotifierService
from .Security_service import SecurityService
from .Skeleton_service import SkeletonService
from .Transform_service import TransformService
from .Validator_service import ValidatorService
from .Video_Make_service import VideoMakeService

load_dotenv()
TRANSFORM_ON = os.getenv("TRANSFORM_ON", "0") == "1"
SKELETON_ON = os.getenv("SKELETON_ON", "0") == "1"


class DataPipeline:
    def __init__(self) -> None:
        self.security_service = SecurityService()
        self.validator_service = ValidatorService()
        self.transform_service = TransformService()
        self.skeleton_service = SkeletonService()
        self.data_save_service = DataSaveService()
        self.notifier_service = NotifierService()
        self.video_make_service = VideoMakeService()

    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> None:
        file, payload = await self.security_service.run(file=file, payload=payload)
        await self.validator_service.run(file=file, payload=payload)

        if TRANSFORM_ON:
            file, payload = await self.transform_service.run(file=file, payload=payload)

        if SKELETON_ON:
            file, payload = await self.skeleton_service.run(file=file, payload=payload)

        await self.data_save_service.run(file=file, payload=payload)
        await self.notifier_service.run(file=file, payload=payload)
        await self.video_make_service.run(file=file, payload=payload)