# 스켈레톤 기능
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, ImageDraw, UnidentifiedImageError

from Config.Server_Options import load_server_options
from Model.Request import ReceivePayload, SkeletonPointPayload


class SkeletonService:
    async def run(
        self,
        file: UploadFile,
        payload: str,
    ) -> tuple[UploadFile, str]:
        skeleton_settings = load_server_options()["skeleton"]
        skeleton_connections = skeleton_settings["connections"]
        skeleton_line_color = tuple(skeleton_settings["line_color"])
        skeleton_point_color = tuple(skeleton_settings["point_color"])
        skeleton_point_radius = skeleton_settings["point_radius"]

        request_payload = ReceivePayload.model_validate_json(payload)
        skeleton_points = self._normalize_points(request_payload.analysis.Skeleton_point)
        image_bytes = await file.read()

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
        except UnidentifiedImageError as exc:
            raise ValueError("스켈레톤을 그릴 수 없는 이미지 형식입니다.") from exc

        draw = ImageDraw.Draw(image)
        for start_index, end_index in self._parse_connections(skeleton_connections):
            start_point = skeleton_points[start_index]
            end_point = skeleton_points[end_index]
            if start_point is None or end_point is None:
                continue

            draw.line([start_point, end_point], fill=skeleton_line_color, width=3)

        for point in skeleton_points:
            if point is None:
                continue

            x, y = point
            draw.ellipse(
                [
                    (x - skeleton_point_radius, y - skeleton_point_radius),
                    (x + skeleton_point_radius, y + skeleton_point_radius),
                ],
                fill=skeleton_point_color,
            )

        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)

        return (
            UploadFile(
                file=output,
                filename=file.filename,
                headers=file.headers,
            ),
            payload,
        )

    def _normalize_points(
        self,
        skeleton_points: list[SkeletonPointPayload],
    ) -> list[tuple[float, float] | None]:
        normalized_points: list[tuple[float, float] | None] = [None] * 17

        for point in skeleton_points:
            normalized_points[point.index] = (point.x, point.y)

        return normalized_points

    def _parse_connections(self, raw_connections: str) -> list[tuple[int, int]]:
        connections: list[tuple[int, int]] = []

        for raw_connection in raw_connections.split(","):
            connection = raw_connection.strip()
            if not connection:
                continue

            try:
                start, end = connection.split("-", maxsplit=1)
                start_index = int(start.strip())
                end_index = int(end.strip())
            except ValueError as exc:
                raise ValueError("SKELETON_CONNECTIONS 형식이 올바르지 않습니다.") from exc

            if not (0 <= start_index <= 16 and 0 <= end_index <= 16):
                raise ValueError("SKELETON_CONNECTIONS 인덱스는 0~16 범위여야 합니다.")

            connections.append((start_index, end_index))

        return connections