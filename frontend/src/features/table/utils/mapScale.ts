import { MAP_SCALE_MIN, MAP_SCALE_STEP } from "@/features/table/constants";

function roundMapScale(raw: number) {
  return Math.max(MAP_SCALE_MIN, Math.round(raw / MAP_SCALE_STEP) * MAP_SCALE_STEP);
}

export function computeMapScaleForGrid(
  naturalWidth: number,
  naturalHeight: number,
  gridCellPx: number,
  targetCellsAlongShortSide = 20,
) {
  if (!naturalWidth || !naturalHeight || !gridCellPx) return 1;
  const shortSide = Math.min(naturalWidth, naturalHeight);
  const raw = (targetCellsAlongShortSide * gridCellPx) / shortSide;
  return roundMapScale(raw);
}

export function computeMapScaleForViewport(
  naturalWidth: number,
  viewportWidthPx: number,
  fraction = 0.4,
) {
  if (!naturalWidth || !viewportWidthPx) return 1;
  const raw = (viewportWidthPx * fraction) / naturalWidth;
  return roundMapScale(raw);
}
