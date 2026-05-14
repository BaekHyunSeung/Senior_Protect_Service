#데이터 수신 파이프 라인
from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from Config.Server_Options import load_server_options
from .Data_Save_service import DataSaveService
from .Notifier_service import NotifierService
from .Security_service import SecurityService
from .Skeleton_service import SkeletonService
from .Transform_service import TransformService
from .Validator_service import ValidatorService
from .Video_Make_service import VideoMakeService

SERVER_OPTIONS = load_server_options()
FEATURE_SETTINGS = SERVER_OPTIONS["features"]


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
        session: AsyncSession,
        file: UploadFile,
        payload: str,
    ) -> None:
        file, payload = await self.security_service.run(file=file, payload=payload)
        await self.validator_service.run(file=file, payload=payload)

        if FEATURE_SETTINGS.get("transform_on", False):
            file, payload = await self.transform_service.run(file=file, payload=payload)

        if FEATURE_SETTINGS.get("skeleton_on", False):
            file, payload = await self.skeleton_service.run(file=file, payload=payload)

        await self.data_save_service.run(session=session, file=file, payload=payload)
        await self.notifier_service.run(file=file, payload=payload)
        await self.video_make_service.run(file=file, payload=payload)