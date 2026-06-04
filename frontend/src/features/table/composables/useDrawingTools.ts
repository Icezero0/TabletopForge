import { ref, watch, type Ref } from "vue";
import type { DrawingKind, RoomDrawing } from "@/infra/api/rooms.api";
import {
  boundsIntersect,
  constrainEllipseGeometry,
  constrainRectGeometry,
  DEFAULT_FONT_SIZE,
  DEFAULT_STROKE_COLOR,
  DEFAULT_STROKE_WIDTH,
  getDrawingBounds,
  kindFromSubTool,
  type DrawSubTool,
  type GridSnap,
} from "@/features/table/drawingTypes";
import { TEXT_INITIAL_WIDTH } from "@/features/table/constants";
import { scenePxToFt } from "@/features/table/utils/gridMeasure";
import { lineHeightForFont, measureTextBoxSize } from "@/features/table/utils/textMeasure";

export type DrawPreview = {
  kind: DrawingKind | "marquee";
  geometry: Record<string, unknown>;
  style: Record<string, unknown>;
  measureLabel?: string;
} | null;

export type TextPlacementRequest = {
  x: number;
  y: number;
  width: number;
  height: number;
} | null;

const TEXT_MIN_WIDTH = 10;

type UseDrawingToolsOptions = {
  drawings: Ref<RoomDrawing[]>;
  gridCellPx: Ref<number>;
  gridCellFt: Ref<number>;
  onCommit: (payload: {
    kind: DrawingKind;
    geometry: Record<string, unknown>;
    style: Record<string, unknown>;
  }) => void | Promise<void>;
  onDeleteIds: (ids: number[]) => void | Promise<void>;
};

export function useDrawingTools(options: UseDrawingToolsOptions) {
  const subTool = ref<DrawSubTool>("brush");
  const strokeColor = ref(DEFAULT_STROKE_COLOR);
  const strokeWidth = ref(DEFAULT_STROKE_WIDTH);
  const fontSize = ref(DEFAULT_FONT_SIZE);
  const preview = ref<DrawPreview>(null);
  const textPlacement = ref<TextPlacementRequest>(null);

  let pointerId: number | null = null;
  let startX = 0;
  let startY = 0;
  let brushPoints: number[][] = [];

  function gridSnap(): GridSnap {
    return { gridCellPx: options.gridCellPx.value, gridCellFt: options.gridCellFt.value };
  }

  function currentStyle() {
    return {
      color: strokeColor.value,
      width: strokeWidth.value,
      fontSize: fontSize.value,
    };
  }

  function resetPointer() {
    pointerId = null;
    brushPoints = [];
    preview.value = null;
  }

  watch(subTool, (tool) => {
    if (tool === "eraser") {
      subTool.value = "boxSelect";
    }
  });

  function measureRectLabel(geometry: Record<string, unknown>) {
    const w = Math.abs(Number(geometry.width));
    const h = Math.abs(Number(geometry.height));
    const side = Math.max(w, h);
    const ft = scenePxToFt(side, options.gridCellPx.value, options.gridCellFt.value);
    return `边长：${ft} ft`;
  }

  function measureEllipseLabel(geometry: Record<string, unknown>) {
    const r = Math.max(Number(geometry.rx), Number(geometry.ry));
    const ft = scenePxToFt(r, options.gridCellPx.value, options.gridCellFt.value);
    return `半径：${ft} ft`;
  }

  function pointerDown(x: number, y: number, event: PointerEvent) {
    const activeSubTool = subTool.value === "eraser" ? "boxSelect" : subTool.value;

    if (subTool.value === "text") {
      const h = lineHeightForFont(fontSize.value);
      textPlacement.value = {
        x,
        y,
        width: TEXT_INITIAL_WIDTH,
        height: h,
      };
      return;
    }

    pointerId = event.pointerId;
    startX = x;
    startY = y;
    brushPoints = [[x, y]];

    if (activeSubTool === "boxSelect") {
      preview.value = {
        kind: "marquee",
        geometry: { x, y, width: 0, height: 0 },
        style: { color: strokeColor.value, width: 1 },
      };
      return;
    }

    const kind = kindFromSubTool(activeSubTool);
    if (!kind) return;

    if (kind === "brush") {
      preview.value = {
        kind: "brush",
        geometry: { points: brushPoints },
        style: currentStyle(),
      };
      return;
    }

    preview.value = {
      kind,
      geometry: startGeometry(kind, x, y),
      style: currentStyle(),
    };
  }

  function startGeometry(kind: DrawingKind, x: number, y: number) {
    switch (kind) {
      case "line":
        return { x1: x, y1: y, x2: x, y2: y };
      case "rect":
        return { x, y, width: 0, height: 0 };
      case "ellipse":
        return { cx: x, cy: y, rx: 0, ry: 0 };
      default:
        return { points: [[x, y]] };
    }
  }

  function pointerMove(x: number, y: number, event: PointerEvent) {
    const activeSubTool = subTool.value === "eraser" ? "boxSelect" : subTool.value;

    if (pointerId !== event.pointerId) return;

    if (activeSubTool === "boxSelect" && preview.value?.kind === "marquee") {
      preview.value = {
        kind: "marquee",
        geometry: {
          x: Math.min(startX, x),
          y: Math.min(startY, y),
          width: Math.abs(x - startX),
          height: Math.abs(y - startY),
        },
        style: { color: strokeColor.value, width: 1 },
      };
      return;
    }

    const kind = kindFromSubTool(activeSubTool);
    if (!kind || !preview.value) return;

    if (kind === "brush") {
      brushPoints.push([x, y]);
      preview.value = {
        kind: "brush",
        geometry: { points: [...brushPoints] },
        style: currentStyle(),
      };
      return;
    }

    if (kind === "line") {
      preview.value = {
        kind: "line",
        geometry: { x1: startX, y1: startY, x2: x, y2: y },
        style: currentStyle(),
      };
      return;
    }

    const constrain = !(event.ctrlKey || event.metaKey);
    const snap = constrain ? gridSnap() : undefined;

    if (kind === "rect") {
      const geometry = constrainRectGeometry(startX, startY, x, y, constrain, snap);
      preview.value = {
        kind: "rect",
        geometry,
        style: currentStyle(),
        measureLabel: constrain ? measureRectLabel(geometry) : undefined,
      };
      return;
    }

    if (kind === "ellipse") {
      const geometry = constrainEllipseGeometry(startX, startY, x, y, constrain, snap);
      preview.value = {
        kind: "ellipse",
        geometry,
        style: currentStyle(),
        measureLabel: constrain ? measureEllipseLabel(geometry) : undefined,
      };
    }
  }

  async function pointerUp(_x: number, _y: number, event: PointerEvent) {
    const activeSubTool = subTool.value === "eraser" ? "boxSelect" : subTool.value;
    if (activeSubTool === "text") return;

    if (pointerId !== event.pointerId) return;

    if (activeSubTool === "boxSelect") {
      const marquee = preview.value?.geometry;
      resetPointer();
      if (!marquee) return;
      const box = {
        x: Number(marquee.x),
        y: Number(marquee.y),
        width: Number(marquee.width),
        height: Number(marquee.height),
      };
      if (box.width < 4 && box.height < 4) return;
      const ids = options.drawings.value
        .filter((d) => {
          const b = getDrawingBounds(d);
          return b && boundsIntersect(b, box);
        })
        .map((d) => d.id);
      if (ids.length) await options.onDeleteIds(ids);
      return;
    }

    const kind = kindFromSubTool(activeSubTool);
    const p = preview.value;
    const points = [...brushPoints];
    resetPointer();
    if (!kind || !p || p.kind !== kind) return;

    if (kind === "brush") {
      if (points.length < 2) return;
      await options.onCommit({
        kind: "brush",
        geometry: { points },
        style: p.style,
      });
      return;
    }

    if (kind === "line") {
      const g = p.geometry;
      const len = Math.hypot(Number(g.x2) - Number(g.x1), Number(g.y2) - Number(g.y1));
      if (len < 2) return;
    }
    if (kind === "rect") {
      const w = Math.abs(Number(p.geometry.width));
      const h = Math.abs(Number(p.geometry.height));
      if (w < 2 && h < 2) return;
    }
    if (kind === "ellipse") {
      const rx = Number(p.geometry.rx);
      const ry = Number(p.geometry.ry);
      if (rx < 2 && ry < 2) return;
    }

    await options.onCommit({
      kind,
      geometry: p.geometry,
      style: p.style,
    });
  }

  function confirmText(payload: { text: string; width: number; height: number }) {
    const place = textPlacement.value;
    textPlacement.value = null;
    const trimmed = payload.text.trim();
    if (!place || !trimmed) return;
    const measured = measureTextBoxSize(trimmed, fontSize.value);
    const width = Math.max(measured.width, payload.width, place.width, TEXT_MIN_WIDTH);
    const height = Math.max(measured.height, payload.height, place.height);
    void options.onCommit({
      kind: "text",
      geometry: {
        x: place.x,
        y: place.y,
        width,
        height,
        text: trimmed,
      },
      style: { color: strokeColor.value, fontSize: fontSize.value },
    });
  }

  function cancelText() {
    textPlacement.value = null;
  }

  return {
    subTool,
    strokeColor,
    strokeWidth,
    fontSize,
    preview,
    textPlacement,
    pointerDown,
    pointerMove,
    pointerUp,
    resetPointer,
    confirmText,
    cancelText,
  };
}
