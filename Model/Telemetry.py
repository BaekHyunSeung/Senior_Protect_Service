from time import monotonic

from pydantic import BaseModel, Field


class TelemetryKeypoint(BaseModel):
    x: float
    y: float
    score: float = 0.0


class TelemetryMessage(BaseModel):
    label: str
    confidence: float = 0.0
    keypoints: list[TelemetryKeypoint] = Field(default_factory=list, max_length=17)
    source_ip: str | None = None
    source_port: int | None = None
    received_at_monotonic: float = Field(default_factory=monotonic)
    dedupe_key: str = ""
