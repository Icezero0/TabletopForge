PLAYER_COLOR_PRESETS: tuple[str, ...] = (
    "#e11d48",
    "#2563eb",
    "#16a34a",
    "#ca8a04",
    "#9333ea",
    "#0891b2",
    "#ea580c",
    "#4b5563",
)


def is_valid_player_color(color: str) -> bool:
    return color in PLAYER_COLOR_PRESETS


def pick_player_color(used_colors: set[str], user_id: int) -> str:
    for color in PLAYER_COLOR_PRESETS:
        if color not in used_colors:
            return color
    return PLAYER_COLOR_PRESETS[user_id % len(PLAYER_COLOR_PRESETS)]
