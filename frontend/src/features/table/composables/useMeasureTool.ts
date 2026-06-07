import { ref, type Ref } from "vue";
import { measureLineLabelFt } from "@/features/table/utils/gridMeasure";

export type MeasureLineState = {
  kind: "line";
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  labelFt: number;
};

export type MeasureRouteSegment = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  labelFt: number;
};

export type MeasureRouteState = {
  kind: "route";
  waypoints: [number, number][];
  cursor: [number, number] | null;
  segments: MeasureRouteSegment[];
  totalFt: number;
};

export type MeasureState = MeasureLineState | MeasureRouteState;

type UseMeasureToolOptions = {
  gridCellPx: Ref<number>;
  gridCellFt: Ref<number>;
};

export function useMeasureTool(options: UseMeasureToolOptions) {
  const measureState = ref<MeasureState | null>(null);

  // --- Line mode state ---
  let linePointerId: number | null = null;
  let lineStartX = 0;
  let lineStartY = 0;
  let lineDragging = false;

  function buildLineState(x1: number, y1: number, x2: number, y2: number): MeasureLineState | null {
    const pxDist = Math.hypot(x2 - x1, y2 - y1);
    const labelFt = measureLineLabelFt(pxDist, options.gridCellPx.value, options.gridCellFt.value);
    if (labelFt < 1) return null;
    return { kind: "line", x1, y1, x2, y2, labelFt };
  }

  // --- Route mode state ---
  let routeWaypoints: [number, number][] = [];
  let routeFinishedFlag = false;

  function buildRouteState(
    waypoints: [number, number][],
    cursor: [number, number] | null,
  ): MeasureRouteState {
    const allPoints = cursor ? [...waypoints, cursor] : waypoints;
    const segments: MeasureRouteSegment[] = [];
    let totalFt = 0;
    for (let i = 1; i < allPoints.length; i++) {
      const [x1, y1] = allPoints[i - 1];
      const [x2, y2] = allPoints[i];
      const pxDist = Math.hypot(x2 - x1, y2 - y1);
      const labelFt = measureLineLabelFt(pxDist, options.gridCellPx.value, options.gridCellFt.value);
      segments.push({ x1, y1, x2, y2, labelFt });
      totalFt += labelFt;
    }
    return { kind: "route", waypoints, cursor, segments, totalFt };
  }

  // --- Common ---
  function clearMeasure() {
    linePointerId = null;
    lineDragging = false;
    routeWaypoints = [];
    routeFinishedFlag = false;
    measureState.value = null;
  }

  // --- Line mode API ---
  function linePointerDown(x: number, y: number, event: PointerEvent) {
    if (event.button !== 0) return;
    linePointerId = event.pointerId;
    lineStartX = x;
    lineStartY = y;
    lineDragging = true;
    measureState.value = null;
    (event.currentTarget as HTMLElement | null)?.setPointerCapture?.(event.pointerId);
  }

  function linePointerMove(x: number, y: number, event: PointerEvent) {
    if (linePointerId !== event.pointerId || !lineDragging) return;
    measureState.value = buildLineState(lineStartX, lineStartY, x, y);
  }

  function linePointerUp(_x: number, _y: number, event: PointerEvent) {
    if (linePointerId !== event.pointerId) return;
    (event.currentTarget as HTMLElement | null)?.releasePointerCapture?.(event.pointerId);
    clearMeasure();
  }

  // --- Route mode API ---
  function routeClick(x: number, y: number) {
    if (routeFinishedFlag) {
      routeWaypoints = [];
      routeFinishedFlag = false;
    }
    routeWaypoints = [...routeWaypoints, [x, y]];
    measureState.value = buildRouteState(routeWaypoints, [x, y]);
  }

  function routeFinish() {
    if (routeWaypoints.length < 2) {
      clearMeasure();
      return;
    }
    routeFinishedFlag = true;
    measureState.value = buildRouteState(routeWaypoints, null);
  }

  function routePointerMove(x: number, y: number) {
    if (routeWaypoints.length === 0 || routeFinishedFlag) return;
    measureState.value = buildRouteState(routeWaypoints, [x, y]);
  }

  return {
    measureState,
    // Line mode
    measurePointerDown: linePointerDown,
    measurePointerMove: linePointerMove,
    measurePointerUp: linePointerUp,
    // Route mode
    routeClick,
    routeFinish,
    routePointerMove,
    // Common
    clearMeasure,
  };
}
