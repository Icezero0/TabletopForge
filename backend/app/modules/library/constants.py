from dataclasses import dataclass
from enum import StrEnum


class ResourceType(StrEnum):
    MAP_BACKGROUND = "map_background"
    # Reserved: TOKEN_IMAGE = "token_image"
    # Reserved: AUDIO_TRACK = "audio_track"


@dataclass
class ResourceTypeSpec:
    required_image: bool = False
    required_audio: bool = False
    # future: meta_fields: list[MetaFieldSpec] = field(default_factory=list)


RESOURCE_TYPE_SPECS: dict[ResourceType, ResourceTypeSpec] = {
    ResourceType.MAP_BACKGROUND: ResourceTypeSpec(required_image=True),
}
