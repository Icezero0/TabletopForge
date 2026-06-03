from enum import StrEnum


class SiteRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class SitePermission(StrEnum):
    MANAGE_SITE_ROLES = "manage_site_roles"
    CREATE_FEEDBACK = "create_feedback"
    VIEW_OWN_FEEDBACK = "view_own_feedback"
    VIEW_ALL_FEEDBACK = "view_all_feedback"
    UPDATE_FEEDBACK = "update_feedback"
    DELETE_FEEDBACK = "delete_feedback"

