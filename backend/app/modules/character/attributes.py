from typing import Any


def derived_int(attributes: dict[str, Any] | None, key: str) -> int | None:
    if not attributes:
        return None
    derived = attributes.get("derived")
    if not isinstance(derived, dict):
        return None
    entry = derived.get(key)
    if not isinstance(entry, dict):
        return None
    value = entry.get("value")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None
