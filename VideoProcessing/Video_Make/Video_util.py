from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from Model.Video import VideoSessionState


def image_bytes_to_bgr_frame(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValueError("영상 생성을 위한 이미지 데이터가 비어 있습니다.")

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("영상 생성을 위한 이미지 형식이 올바르지 않습니다.") from exc

    return cv2.cvtColor(np.array(image, dtype=np.uint8), cv2.COLOR_RGB2BGR)


def build_video_output_paths(output_root: Path, device_id: int) -> tuple[Path, Path]:
    device_dir = output_root / str(device_id)
    device_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = device_dir / f"{timestamp}.mp4"
    temp_path = device_dir / f"{timestamp}.writing.mp4"
    return temp_path, output_path


def create_video_writer(
    temp_path: Path,
    fps: int,
    width: int,
    height: int,
) -> Any:
    writer = cv2.VideoWriter(
        str(temp_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise ValueError("mp4 영상을 생성할 수 없습니다.")

    return writer


def write_frame_to_session(
    session: VideoSessionState,
    frame: np.ndarray,
) -> None:
    session.writer.write(frame)
    session.frames_written += 1


def release_writer_safely(session: VideoSessionState) -> None:
    try:
        if session.writer is not None:
            session.writer.release()
    finally:
        session.writer = None


def finalize_video_file(session: VideoSessionState) -> None:
    try:
        release_writer_safely(session)
        session.temp_path.replace(session.output_path)
    finally:
        delete_file_if_exists(session.temp_path)


def delete_file_if_exists(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except FileNotFoundError:
        pass
