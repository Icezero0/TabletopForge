from dataclasses import dataclass
from enum import StrEnum


class ResourceType(StrEnum):
    MAP_BACKGROUND = "map_background"
    TOKEN = "token"
    SOUND = "sound"


@dataclass
class ResourceTypeSpec:
    required_image: bool = False
    required_audio: bool = False
    has_tags: bool = False
    has_comment: bool = False


RESOURCE_TYPE_SPECS: dict[ResourceType, ResourceTypeSpec] = {
    ResourceType.MAP_BACKGROUND: ResourceTypeSpec(required_image=True, has_comment=True),
    ResourceType.TOKEN: ResourceTypeSpec(required_image=True, has_tags=True, has_comment=True),
    ResourceType.SOUND: ResourceTypeSpec(required_audio=True, has_tags=True, has_comment=True),
}
