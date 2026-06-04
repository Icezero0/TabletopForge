from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
)

from app.core.validators import (
    normalize_email,
    normalize_optional_non_empty_str,
    normalize_required_str,
)
from app.modules.site.constants import SitePermission, SiteRole
from app.modules.site.permissions import get_permissions_by_role


class UserCreate(BaseModel):
    email: EmailStr
    username: str | None = None
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        return normalize_optional_non_empty_str(value, field_name="Username")

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return normalize_required_str(value, field_name="Password")


class UserPatch(BaseModel):
    username: str | None = None
    password: str | None = None

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        return normalize_optional_non_empty_str(value, field_name="Username")

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        return normalize_optional_non_empty_str(value, field_name="Password")


class UserSiteRolePatch(BaseModel):
    site_role: SiteRole


class UserBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str | None
    avatar_asset_id: int | None = None
    site_role: SiteRole

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        if self.avatar_asset_id is None:
            return None
        return f"/api/v1/assets/{self.avatar_asset_id}/content"


class UserResponse(UserBriefResponse):
    pass


class UserSiteRoleResponse(UserResponse):
    site_role: SiteRole


class UserMeResponse(UserResponse):
    site_role: SiteRole

    @computed_field
    @property
    def site_permissions(self) -> list[SitePermission]:
        return sorted(get_permissions_by_role(self.site_role), key=lambda item: item.value)


class UserListResponse(BaseModel):
    items: list[UserResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int
