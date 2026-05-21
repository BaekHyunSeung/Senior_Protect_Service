from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class VideoSessionState:
    writer: Any
    temp_path: Path
    output_path: Path
    width: int
    height: int
    started_at: float
    last_received_at: float
    frames_written: int = 0
