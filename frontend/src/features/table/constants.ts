export const GRID_CELL_FT = 5;
/** @deprecated use DEFAULT_GRID_CELL_PX */
export const GRID_CELL_PX = 40;
export const DEFAULT_GRID_CELL_PX = 72;
export const MIN_GRID_CELL_PX = 28;
export const MAX_GRID_CELL_PX = 120;
export const GRID_CELL_PX_STEP = 4;

/** Scene-space half-size of the repeating grid (total span = 2 × half). */
export const SCENE_GRID_HALF_EXTENT = 32000;
/** Scene-space origin (top-left) for full-scene SVG layers. */
export const SCENE_ORIGIN = -SCENE_GRID_HALF_EXTENT;
/** Scene-space width/height for full-scene SVG layers. */
export const SCENE_SPAN = SCENE_GRID_HALF_EXTENT * 2;

export const TOKEN_BAND_BASE = 100;
/** 绘制 band 基准（effectiveZ = base + z_index，见 tabletop_scene.md §3.2） */
export const DRAWING_BAND_BASE = 200;
/** 测距叠层：高于绘制，低于网格 */
export const MEASURE_LAYER_Z = DRAWING_BAND_BASE + 5;
/** 战争迷雾：高于指示物，低于绘制、Pointer、测距 */
export const FOG_LAYER_Z = DRAWING_BAND_BASE - 1;
/** 网格叠层：SceneCanvas 内最上（不拦截指针） */
export const GRID_LAYER_Z = DRAWING_BAND_BASE + 10;

export function sceneBandZ(zIndex: number, base = TOKEN_BAND_BASE) {
  return base + zIndex;
}

export const MAP_SCALE_MIN = 0.01;
export const MAP_SCALE_STEP = 0.001;

export const ERASER_RADIUS = 14;

/** Scene-space radius for logical hit tests (select / hover). */
export const DRAWING_PICK_HIT_RADIUS = 20;
/** Minimum invisible stroke width for pick-mode SVG hit targets. */
export const DRAWING_PICK_STROKE_HIT = 18;

/** Default scene width when placing a new text box (before typing). */
export const TEXT_INITIAL_WIDTH = 30;
