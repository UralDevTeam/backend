from io import BytesIO
from typing import TYPE_CHECKING, Tuple
from uuid import UUID

if TYPE_CHECKING:  # pragma: no cover - only for type checkers
    from PIL import Image as PILImage
    from PIL import UnidentifiedImageError

from src.domain.models import Avatar
from src.infrastructure.repositories import AvatarRepository


class AvatarService:
    def __init__(self, avatar_repository: AvatarRepository):
        self.avatar_repository = avatar_repository

    async def save_avatar(self, employee_id: UUID, content: bytes) -> Avatar:
        if not content:
            raise ValueError("Empty image content provided")

        Image, UnidentifiedImageError = self._load_image_library()

        try:
            with Image.open(BytesIO(content)) as image:
                image.load()
                prepared_image = self._prepare_image(image)
        except UnidentifiedImageError as exc:
            raise ValueError("Uploaded file is not a valid image") from exc

        small_image, large_image = self._render_sizes(prepared_image)

        avatar = Avatar(
            employee_id=employee_id,
            mime_type="image/png",
            image_small=small_image,
            image_large=large_image,
        )

        return await self.avatar_repository.upsert(avatar)

    async def get_avatar(self, employee_id: UUID) -> Avatar | None:
        return await self.avatar_repository.get_by_employee_id(employee_id)

    async def delete_avatar(self, employee_id: UUID) -> None:
        avatar_exists = await self.avatar_repository.delete_by_employee_id(employee_id)
        if not avatar_exists:
            raise ValueError(f"No avatar found for user '{employee_id}'")

    def _load_image_library(self) -> Tuple["PILImage", "UnidentifiedImageError"]:
        try:
            from PIL import Image, UnidentifiedImageError  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Pillow is required for avatar processing. Please install the 'pillow' package."
            ) from exc

        return Image, UnidentifiedImageError

    def _prepare_image(self, image: "PILImage") -> "PILImage":
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        width, height = image.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        right = left + side
        bottom = top + side

        return image.crop((left, top, right, bottom))

    def _render_sizes(self, image: "PILImage") -> Tuple[bytes, bytes]:
        large = self._resize_to_png(image, 128)
        small = self._resize_to_png(image, 32)
        return small, large

    def _resize_to_png(self, image: "PILImage", size: int) -> bytes:
        Image, _ = self._load_image_library()
        resized = image.resize((size, size), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        resized.save(buffer, format="PNG")
        return buffer.getvalue()
