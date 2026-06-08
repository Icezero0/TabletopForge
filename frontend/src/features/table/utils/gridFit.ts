export type GridSampleRect = { x: number; y: number; width: number; height: number };
export type GridSampleLegacy = { x: number; y: number; size: number };

function circularMeanFromValues(values: number[], cellSize: number): number {
  let sinSum = 0;
  let cosSum = 0;
  for (const v of values) {
    const raw = ((v % cellSize) + cellSize) % cellSize;
    sinSum += Math.sin((2 * Math.PI * raw) / cellSize);
    cosSum += Math.cos((2 * Math.PI * raw) / cellSize);
  }
  const n = values.length;
  return ((Math.atan2(sinSum / n, cosSum / n) / (2 * Math.PI)) * cellSize + cellSize) % cellSize;
}

// Least-squares fit: given edge positions that should land on grid lines,
// find cellSize and phase that minimize Σ(p_j - phase - k_j * cellSize)².
// k_j are inferred by rounding to the nearest grid line and refined each iteration.
function fitGridAxis(
  edges: number[],
  initialCellSize: number,
): { cellSize: number; phase: number } {
  if (edges.length < 2 || initialCellSize <= 0) return { cellSize: initialCellSize, phase: 0 };
  let cellSize = initialCellSize;
  let phase = circularMeanFromValues(edges, cellSize);
  for (let iter = 0; iter < 8; iter++) {
    const ks = edges.map((p) => Math.round((p - phase) / cellSize));
    const n = edges.length;
    const sumK = ks.reduce((a, b) => a + b, 0);
    const sumP = edges.reduce((a, b) => a + b, 0);
    const sumKP = edges.reduce((s, p, i) => s + ks[i]! * p, 0);
    const sumK2 = ks.reduce((s, k) => s + k * k, 0);
    const denom = n * sumK2 - sumK * sumK;
    if (Math.abs(denom) < 1e-6) break;
    const newCellSize = (n * sumKP - sumK * sumP) / denom;
    const newPhase = (sumP - newCellSize * sumK) / n;
    if (newCellSize <= 0) break;
    const prevCellSize = cellSize;
    cellSize = newCellSize;
    const normPhase = ((newPhase % cellSize) + cellSize) % cellSize;
    const converged = Math.abs(cellSize - prevCellSize) < 0.001 && Math.abs(normPhase - phase) < 0.001;
    phase = normPhase;
    if (converged) break;
  }
  return { cellSize, phase };
}

export function fitGridFromSamples(samples: GridSampleRect[]): {
  cellWidth: number; phaseX: number;
  cellHeight: number; phaseY: number;
} {
  const xEdges = samples.flatMap((s) => [s.x, s.x + s.width]);
  const yEdges = samples.flatMap((s) => [s.y, s.y + s.height]);
  const initW = samples.reduce((a, s) => a + s.width, 0) / samples.length;
  const initH = samples.reduce((a, s) => a + s.height, 0) / samples.length;
  const { cellSize: cellWidth, phase: phaseX } = fitGridAxis(xEdges, initW);
  const { cellSize: cellHeight, phase: phaseY } = fitGridAxis(yEdges, initH);
  return { cellWidth, phaseX, cellHeight, phaseY };
}

// Legacy: circular mean for old-format calibration {x, y, size}
export function circularMeanPhase(
  samples: Array<{ x: number; y: number }>,
  axis: "x" | "y",
  scale: number,
  cellPx: number,
): number {
  return circularMeanFromValues(samples.map((s) => s[axis] * scale), cellPx);
}
