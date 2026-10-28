"""Upload checks for event flyers and leader photos."""
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from PIL import Image

ALLOWED_IMAGE_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def validate_image_upload(file):
    """Accept only real JPEG, PNG or WebP images up to the configured size."""
    max_bytes = settings.FLYER_MAX_UPLOAD_BYTES
    if file.size > max_bytes:
        raise ValidationError(
            f"The image is too large ({file.size / 1024 / 1024:.1f} MB). The limit is {max_bytes / 1024 / 1024:.0f} MB."
        )
    # Check the actual file content, not just its name
    try:
        pos = file.tell() if hasattr(file, "tell") else 0
        with Image.open(file) as img:
            fmt = img.format
            img.verify()
        file.seek(pos)
    except Exception as exc:
        raise ValidationError("The file is not a valid image.") from exc
    if fmt not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Only JPEG, PNG and WebP images are allowed.")


@deconstructible
class UniqueUploadPath:
    """Store uploads as <folder>/<year>/<month>/<random>.<ext> so names never clash
    and a replaced flyer always gets a new URL (no stale browser caches)."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        from django.utils import timezone

        ext = Path(filename).suffix.lower().lstrip(".")
        ext = "jpg" if ext == "jpeg" else ext
        now = timezone.now()
        return f"{self.folder}/{now:%Y}/{now:%m}/{uuid.uuid4().hex}.{ext}"

    def __eq__(self, other):
        return isinstance(other, UniqueUploadPath) and other.folder == self.folder
