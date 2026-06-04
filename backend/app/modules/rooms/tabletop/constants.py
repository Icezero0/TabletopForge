from enum import StrEnum

DEFAULT_GRID_CELL_FT = 5.0
DEFAULT_GRID_CELL_PX = 40


class DrawingKind(StrEnum):
    BRUSH = "brush"
    LINE = "line"
    RECT = "rect"
    ELLIPSE = "ellipse"
    TEXT = "text"
