import type { DrawingKind, RoomDrawing } from "@/infra/api/rooms.api";
import { DRAWING_PICK_HIT_RADIUS } from "@/features/table/constants";
import { snapSideToFt } from "@/features/table/utils/gridMeasure";

export type DrawSubTool = "brush" | "line" | "rect" | "ellipse" | "text" | "eraser" | "boxSelect";
export type ShapeDrawMode = "outline" | "mask";

export type DrawingStyle = {
  color?: string;
  width?: number;
  fontSize?: number;
  fill?: string;
  fillOpacity?: number;
  shapeMode?: ShapeDrawMode;
};

export type DrawingBounds = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export const DEFAULT_STROKE_COLOR = "#e11d48";
export const DEFAULT_STROKE_WIDTH = 3;
export const DEFAULT_FONT_SIZE = 16;

export function nextDrawingZIndex(drawings: RoomDrawing[]) {
  if (!drawings.length) return 0;
  return Math.max(...drawings.map((d) => d.z_index)) + 1;
}

export function findTopDrawingAt(
  drawings: RoomDrawing[],
  x: number,
  y: number,
  pad = DRAWING_PICK_HIT_RADIUS,
): RoomDrawing | null {
  const sorted = [...drawings].sort((a, b) => b.z_index - a.z_index || b.id - a.id);
  return sorted.find((d) => hitTestDrawing(d, x, y, pad)) ?? null;
}

export function getDrawingBounds(drawing: RoomDrawing): DrawingBounds | null {
  const g = drawing.geometry;
  switch (drawing.kind) {
    case "brush": {
      const points = g.points as number[][] | undefined;
      if (!points?.length) return null;
      let minX = Infinity;
      let minY = Infinity;
      let maxX = -Infinity;
      let maxY = -Infinity;
      for (const pt of points) {
        const px = pt[0] ?? 0;
        const py = pt[1] ?? 0;
        minX = Math.min(minX, px);
        minY = Math.min(minY, py);
        maxX = Math.max(maxX, px);
        maxY = Math.max(maxY, py);
      }
      const padW = (drawing.style.width as number) ?? DEFAULT_STROKE_WIDTH;
      return {
        x: minX - padW,
        y: minY - padW,
        width: maxX - minX + padW * 2,
        height: maxY - minY + padW * 2,
      };
    }
    case "line": {
      const x1 = Number(g.x1);
      const y1 = Number(g.y1);
      const x2 = Number(g.x2);
      const y2 = Number(g.y2);
      const padW = (drawing.style.width as number) ?? DEFAULT_STROKE_WIDTH;
      return {
        x: Math.min(x1, x2) - padW,
        y: Math.min(y1, y2) - padW,
        width: Math.abs(x2 - x1) + padW * 2,
        height: Math.abs(y2 - y1) + padW * 2,
      };
    }
    case "rect": {
      const x = Number(g.x);
      const y = Number(g.y);
      const w = Number(g.width);
      const h = Number(g.height);
      return {
        x: w < 0 ? x + w : x,
        y: h < 0 ? y + h : y,
        width: Math.abs(w),
        height: Math.abs(h),
      };
    }
    case "ellipse": {
      const cx = Number(g.cx);
      const cy = Number(g.cy);
      const rx = Number(g.rx);
      const ry = Number(g.ry);
      return { x: cx - rx, y: cy - ry, width: rx * 2, height: ry * 2 };
    }
    case "text": {
      const x = Number(g.x);
      const y = Number(g.y);
      const w = Number(g.width);
      const h = Number(g.height);
      if (w > 0 && h > 0) {
        return { x, y, width: w, height: h };
      }
      const fontSize = (drawing.style.fontSize as number) ?? DEFAULT_FONT_SIZE;
      const text = String(g.text ?? "");
      return {
        x,
        y: y - fontSize,
        width: Math.max(40, text.length * fontSize * 0.55),
        height: fontSize * 1.4,
      };
    }
    default:
      return null;
  }
}

export function translateDrawingGeometry(
  drawing: RoomDrawing,
  dx: number,
  dy: number,
): Record<string, unknown> {
  const g = drawing.geometry;
  switch (drawing.kind) {
    case "brush": {
      const points = (g.points as number[][]) ?? [];
      return {
        points: points.map(([x, y]) => [(x ?? 0) + dx, (y ?? 0) + dy]),
      };
    }
    case "line":
      return {
        x1: Number(g.x1) + dx,
        y1: Number(g.y1) + dy,
        x2: Number(g.x2) + dx,
        y2: Number(g.y2) + dy,
      };
    case "rect":
      return {
        x: Number(g.x) + dx,
        y: Number(g.y) + dy,
        width: Number(g.width),
        height: Number(g.height),
      };
    case "ellipse":
      return {
        cx: Number(g.cx) + dx,
        cy: Number(g.cy) + dy,
        rx: Number(g.rx),
        ry: Number(g.ry),
      };
    case "text":
      return {
        x: Number(g.x) + dx,
        y: Number(g.y) + dy,
        width: Number(g.width),
        height: Number(g.height),
        text: g.text,
      };
    default:
      return { ...g };
  }
}

export type DrawingResizeOrigin = {
  bounds: DrawingBounds;
  fontSize?: number;
};

export function resizeTextGeometry(
  drawing: RoomDrawing,
  _corner: "tl" | "tr" | "bl" | "br",
  nextBounds: DrawingBounds,
  origin?: DrawingResizeOrigin,
): { geometry: Record<string, unknown>; style: Record<string, unknown> } {
  const g = drawing.geometry;
  const originBounds = origin?.bounds ?? getDrawingBounds(drawing);
  const baseFont =
    origin?.fontSize ?? ((drawing.style.fontSize as number) || DEFAULT_FONT_SIZE);
  let fontSize = baseFont;
  if (originBounds && originBounds.width > 0 && originBounds.height > 0) {
    const sx = nextBounds.width / originBounds.width;
    const sy = nextBounds.height / originBounds.height;
    const scale = Math.sqrt(sx * sy);
    fontSize = Math.max(1, Math.round(baseFont * scale));
  }
  return {
    geometry: {
      x: nextBounds.x,
      y: nextBounds.y,
      width: nextBounds.width,
      height: nextBounds.height,
      text: g.text,
    },
    style: { ...drawing.style, fontSize },
  };
}

export function resizeDrawingGeometry(
  drawing: RoomDrawing,
  _corner: "tl" | "tr" | "bl" | "br",
  nextBounds: DrawingBounds,
  origin?: DrawingResizeOrigin,
): { geometry: Record<string, unknown>; style: Record<string, unknown> } {
  const g = drawing.geometry;
  switch (drawing.kind) {
    case "rect":
      return {
        geometry: {
          x: nextBounds.x,
          y: nextBounds.y,
          width: nextBounds.width,
          height: nextBounds.height,
        },
        style: { ...drawing.style },
      };
    case "ellipse":
      return {
        geometry: {
          cx: nextBounds.x + nextBounds.width / 2,
          cy: nextBounds.y + nextBounds.height / 2,
          rx: nextBounds.width / 2,
          ry: nextBounds.height / 2,
        },
        style: { ...drawing.style },
      };
    case "line": {
      const old = getDrawingBounds(drawing);
      if (!old || old.width <= 0 || old.height <= 0) {
        return { geometry: { ...g }, style: { ...drawing.style } };
      }
      const sx = nextBounds.width / old.width;
      const sy = nextBounds.height / old.height;
      const x1 = nextBounds.x + (Number(g.x1) - old.x) * sx;
      const y1 = nextBounds.y + (Number(g.y1) - old.y) * sy;
      const x2 = nextBounds.x + (Number(g.x2) - old.x) * sx;
      const y2 = nextBounds.y + (Number(g.y2) - old.y) * sy;
      return {
        geometry: { x1, y1, x2, y2 },
        style: { ...drawing.style },
      };
    }
    case "brush": {
      const old = getDrawingBounds(drawing);
      const points = (g.points as number[][] | undefined) ?? [];
      if (!old || old.width <= 0 || old.height <= 0 || !points.length) {
        return { geometry: { points }, style: { ...drawing.style } };
      }
      const sx = nextBounds.width / old.width;
      const sy = nextBounds.height / old.height;
      return {
        geometry: {
          points: points.map(([px, py]) => [
            nextBounds.x + ((px ?? 0) - old.x) * sx,
            nextBounds.y + ((py ?? 0) - old.y) * sy,
          ]),
        },
        style: { ...drawing.style },
      };
    }
    case "text":
      return resizeTextGeometry(drawing, _corner, nextBounds, origin);
    default:
      return { geometry: { ...g }, style: { ...drawing.style } };
  }
}

export function cloneDrawingGeometry(drawing: RoomDrawing): Record<string, unknown> {
  const g = drawing.geometry;
  if (drawing.kind === "brush") {
    const points = g.points as number[][] | undefined;
    return { points: points?.map((p) => [p[0] ?? 0, p[1] ?? 0]) ?? [] };
  }
  return { ...g };
}

export function boundsIntersect(a: DrawingBounds, b: DrawingBounds) {
  return (
    a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y
  );
}

export function pointInBounds(x: number, y: number, b: DrawingBounds, pad = 4) {
  return (
    x >= b.x - pad &&
    x <= b.x + b.width + pad &&
    y >= b.y - pad &&
    y <= b.y + b.height + pad
  );
}

function strokeHitTolerance(drawing: RoomDrawing, hitRadius: number) {
  const w = (drawing.style.width as number) ?? DEFAULT_STROKE_WIDTH;
  return hitRadius + w / 2;
}

function hitTestBrushPoints(
  points: number[][],
  x: number,
  y: number,
  tolerance: number,
): boolean {
  const tolSq = tolerance * tolerance;
  for (let i = 0; i < points.length; i++) {
    const px = points[i]?.[0] ?? 0;
    const py = points[i]?.[1] ?? 0;
    const dx = px - x;
    const dy = py - y;
    if (dx * dx + dy * dy <= tolSq) return true;
    if (i > 0) {
      const prev = points[i - 1]!;
      const dist = distanceToSegment(x, y, prev[0] ?? 0, prev[1] ?? 0, px, py);
      if (dist <= tolerance) return true;
    }
  }
  return false;
}

export function hitTestDrawing(
  drawing: RoomDrawing,
  x: number,
  y: number,
  hitRadius = DRAWING_PICK_HIT_RADIUS,
): boolean {
  const bounds = getDrawingBounds(drawing);
  if (!bounds) return false;
  if (!pointInBounds(x, y, bounds, hitRadius)) return false;

  const g = drawing.geometry;
  switch (drawing.kind) {
    case "brush": {
      const points = g.points as number[][] | undefined;
      if (!points?.length) return false;
      return hitTestBrushPoints(points, x, y, strokeHitTolerance(drawing, hitRadius));
    }
    case "line": {
      const x1 = Number(g.x1);
      const y1 = Number(g.y1);
      const x2 = Number(g.x2);
      const y2 = Number(g.y2);
      const dist = distanceToSegment(x, y, x1, y1, x2, y2);
      return dist <= strokeHitTolerance(drawing, hitRadius);
    }
    default:
      return true;
  }
}

function distanceToSegment(px: number, py: number, x1: number, y1: number, x2: number, y2: number) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return Math.hypot(px - x1, py - y1);
  let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  const projX = x1 + t * dx;
  const projY = y1 + t * dy;
  return Math.hypot(px - projX, py - projY);
}

export function brushPathFromPoints(points: number[][]) {
  if (points.length < 2) return "";
  return points
    .map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x} ${y}`)
    .join(" ");
}

export function kindFromSubTool(subTool: DrawSubTool): DrawingKind | null {
  if (subTool === "eraser" || subTool === "boxSelect") return null;
  return subTool;
}

export type GridSnap = { gridCellPx: number; gridCellFt: number };

export function constrainRectGeometry(
  startX: number,
  startY: number,
  x: number,
  y: number,
  square: boolean,
  snap?: GridSnap,
) {
  const dx = x - startX;
  const dy = y - startY;
  if (!square) {
    return { x: startX, y: startY, width: dx, height: dy };
  }
  let side = Math.max(Math.abs(dx), Math.abs(dy));
  if (snap) {
    side = snapSideToFt(side, snap.gridCellPx, snap.gridCellFt);
  }
  const sx = dx < 0 ? -1 : 1;
  const sy = dy < 0 ? -1 : 1;
  return { x: startX, y: startY, width: side * sx, height: side * sy };
}

export function constrainEllipseGeometry(
  startX: number,
  startY: number,
  x: number,
  y: number,
  circle: boolean,
  snap?: GridSnap,
) {
  if (!circle) {
    return {
      cx: (startX + x) / 2,
      cy: (startY + y) / 2,
      rx: Math.abs(x - startX) / 2,
      ry: Math.abs(y - startY) / 2,
    };
  }
  let side = Math.max(Math.abs(x - startX), Math.abs(y - startY));
  if (snap) {
    side = snapSideToFt(side, snap.gridCellPx, snap.gridCellFt);
  }
  const cx = (startX + x) / 2;
  const cy = (startY + y) / 2;
  const r = side / 2;
  return { cx, cy, rx: r, ry: r };
}
