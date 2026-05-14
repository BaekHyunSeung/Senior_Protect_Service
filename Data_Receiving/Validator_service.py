#메타 데이터 형식 검증
from datetime import datetime

from fastapi import UploadFile
from pydantic import ValidationError

from Model.Request import ReceivePayload


class ValidatorService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> None:
        self._validate_file(file)
        self._validate_payload(payload)

    def _validate_file(self, file: UploadFile) -> None:
        if not file.filename:
            raise ValueError("이미지 파일명이 필요합니다.")

        if not file.content_type or not file.content_type.startswith("image/"):
            raise ValueError("이미지 파일만 업로드할 수 있습니다.")

    def _validate_payload(self, payload: str) -> None:
        try:
            request_payload = ReceivePayload.model_validate_json(payload)
        except ValidationError as exc:
            raise ValueError("payload 형식이 올바르지 않습니다.") from exc

        self._validate_timestamp(request_payload.header.TimeStamp)
        self._validate_skeleton_points(request_payload.analysis.Skeleton_point)

    def _validate_timestamp(self, timestamp: str) -> None:
        try:
            datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        except ValueError as exc:
            raise ValueError("TimeStamp 형식은 YYYYMMDD_HHMMSS 여야 합니다.") from exc

    def _validate_skeleton_points(self, skeleton_points: list[object]) -> None:
        seen_indexes: set[int] = set()

        for point in skeleton_points:
            point_index = point.index
            if not 0 <= point_index <= 16:
                raise ValueError("Skeleton_point index는 0~16 범위여야 합니다.")

            if point_index in seen_indexes:
                raise ValueError("Skeleton_point index가 중복되었습니다.")

            seen_indexes.add(point_index)