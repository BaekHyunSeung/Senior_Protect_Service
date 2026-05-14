#요청 데이터 구조 정의
from typing import Any

from pydantic import BaseModel, Field

#----------------------------------
#데이터 수신 형식 검증 정의
#----------------------------------
class HeaderPayload(BaseModel):
    Device_ID: int
    TimeStamp: str


class SkeletonPointPayload(BaseModel):
    index: int
    x: float
    y: float


class AnalysisPayload(BaseModel):
    Type: str
    bbox: list[Any] = Field(min_length=4, max_length=4)
    Masking_box: list[Any] = Field(min_length=4, max_length=4)
    Skeleton_point: list[SkeletonPointPayload] = Field(default_factory=list, max_length=17)

class ReceivePayload(BaseModel):
    header: HeaderPayload
    analysis: AnalysisPayload
#----------------------------------