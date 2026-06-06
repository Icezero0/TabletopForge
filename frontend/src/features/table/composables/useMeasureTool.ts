import { ref, type Ref } from "vue";
import { measureLineLabelFt } from "@/features/table/utils/gridMeasure";

export type MeasureState = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  labelFt: number;
};

type UseMeasureToolOptions = {
  gridCellPx: Ref<number>;
  gridCellFt: Ref<number>;
};

export function useMeasureTool(options: UseMeasureToolOptions) {
  const measureState = ref<MeasureState | null>(null);

  let pointerId: number | null = null;
  let startX = 0;
  let startY = 0;
  let dragging = false;

  function buildState(x1: number, y1: number, x2: number, y2: number): MeasureState | null {
    const pxDistance = Math.hypot(x2 - x1, y2 - y1);
    const labelFt = measureLineLabelFt(
      pxDistance,
      options.gridCellPx.value,
      options.gridCellFt.value,
    );
    if (labelFt < 1) return null;
    return { x1, y1, x2, y2, labelFt };
  }

  function clearMeasure() {
    pointerId = null;
    dragging = false;
    measureState.value = null;
  }

  function pointerDown(x: number, y: number, event: PointerEvent) {
    if (event.button !== 0) return;
    pointerId = event.pointerId;
    startX = x;
    startY = y;
    dragging = true;
    measureState.value = null;
    (event.currentTarget as HTMLElement | null)?.setPointerCapture?.(event.pointerId);
  }

  function pointerMove(x: number, y: number, event: PointerEvent) {
    if (pointerId !== event.pointerId || !dragging) return;
    measureState.value = buildState(startX, startY, x, y);
  }

  function pointerUp(_x: number, _y: number, event: PointerEvent) {
    if (pointerId !== event.pointerId) return;
    (event.currentTarget as HTMLElement | null)?.releasePointerCapture?.(event.pointerId);
    clearMeasure();
  }

  return {
    measureState,
    measurePointerDown: pointerDown,
    measurePointerMove: pointerMove,
    measurePointerUp: pointerUp,
    clearMeasure,
  };
}
