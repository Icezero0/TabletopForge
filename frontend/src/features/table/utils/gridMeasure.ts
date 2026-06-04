export function scenePxToFt(px: number, gridCellPx: number, gridCellFt: number) {
  if (!gridCellPx || !gridCellFt) return 0;
  return Math.round(((px / gridCellPx) * gridCellFt) * 10) / 10;
}

export function pxPerFt(gridCellPx: number, gridCellFt: number) {
  if (!gridCellFt) return gridCellPx;
  return gridCellPx / gridCellFt;
}

export function snapSideToFt(
  px: number,
  gridCellPx: number,
  gridCellFt: number,
  minFt = 1,
) {
  const p = pxPerFt(gridCellPx, gridCellFt);
  if (!p) return px;
  return Math.max(minFt, Math.round(px / p)) * p;
}
