from enum import StrEnum

DEFAULT_GRID_CELL_FT = 5.0
DEFAULT_GRID_CELL_PX = 52

TOKEN_BAND_BASE = 100

# 绘制 band 基准（类内 z_index；前端 effectiveZ = base + z_index，见 tabletop_scene.md §3.2）
DRAWING_BAND_BASE = 200


class TokenType(StrEnum):
    CHARACTER = "character"
    MONSTER = "monster"
    OBJECT = "object"


class DrawingKind(StrEnum):
    BRUSH = "brush"
    LINE = "line"
    RECT = "rect"
    ELLIPSE = "ellipse"
    TEXT = "text"
