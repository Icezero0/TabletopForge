from enum import StrEnum


class AssetType(StrEnum):
    AVATAR = "avatar"
    FEEDBACK_IMAGE = "feedback_image"


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
