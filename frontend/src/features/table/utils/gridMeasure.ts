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

/** 线段像素长度 → 按整格取整的 ft 标签（线段本身不吸附） */
export function measureLineLabelFt(
  pxDistance: number,
  gridCellPx: number,
  gridCellFt: number,
) {
  if (!gridCellPx || !gridCellFt || pxDistance < 1) return 0;
  const gridCells = Math.round(pxDistance / gridCellPx);
  if (gridCells < 1) return 0;
  return gridCells * gridCellFt;
}
