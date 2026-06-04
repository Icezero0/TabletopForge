from enum import StrEnum


class AssetType(StrEnum):
    AVATAR = "avatar"
    FEEDBACK_IMAGE = "feedback_image"
    MAP_BACKGROUND = "map_background"
    IMAGE = "image"
    AUDIO = "audio"


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
}


USER_LIBRARY_ASSET_TYPES = {AssetType.IMAGE, AssetType.AUDIO}
DEDUPED_ASSET_TYPES = {AssetType.AVATAR, AssetType.IMAGE, AssetType.AUDIO}
