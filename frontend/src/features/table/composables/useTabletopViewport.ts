import { computed, onMounted, onUnmounted, ref, type Ref } from "vue";
import type { TableToolMode } from "@/features/table/types";

const MIN_VIEWPORT_SCALE = 0.25;
const MAX_VIEWPORT_SCALE = 4;
const ZOOM_SENSITIVITY = 0.001;

export function useTabletopViewport(toolMode: Ref<TableToolMode>) {
  const viewportX = ref(0);
  const viewportY = ref(0);
  const viewportScale = ref(1);

  const viewportTransform = computed(
    () =>
      `translate(${viewportX.value}px, ${viewportY.value}px) scale(${viewportScale.value})`,
  );

  let panPointerId: number | null = null;
  let panStartX = 0;
  let panStartY = 0;
  let panOriginX = 0;
  let panOriginY = 0;

  function clampScale(value: number) {
    return Math.min(MAX_VIEWPORT_SCALE, Math.max(MIN_VIEWPORT_SCALE, value));
  }

  function onWheel(event: WheelEvent) {
    if (toolMode.value !== "hand") return;
    event.preventDefault();
    const el = event.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const mx = event.clientX - rect.left;
    const my = event.clientY - rect.top;
    const delta = -event.deltaY * ZOOM_SENSITIVITY;
    const oldScale = viewportScale.value;
    const newScale = clampScale(oldScale * (1 + delta));
    if (newScale === oldScale) return;
    viewportX.value = mx - ((mx - viewportX.value) * newScale) / oldScale;
    viewportY.value = my - ((my - viewportY.value) * newScale) / oldScale;
    viewportScale.value = newScale;
  }

  function shouldStartPan(event: PointerEvent) {
    if (toolMode.value !== "hand") return false;
    const target = event.target as Element;
    if (
      target.closest(
        ".mapItem, .selectionOverlay, .drawingSelectionOverlay, .textBoxEditor, .drawingLayer.drawMode",
      )
    ) {
      return false;
    }
    return true;
  }

  function onPointerDown(event: PointerEvent) {
    if (toolMode.value !== "hand") return;
    if (event.button !== 0) return;
    if (!shouldStartPan(event)) return;
    panPointerId = event.pointerId;
    panStartX = event.clientX;
    panStartY = event.clientY;
    panOriginX = viewportX.value;
    panOriginY = viewportY.value;
    (event.currentTarget as HTMLElement)?.setPointerCapture?.(event.pointerId);
  }

  function onPointerMove(event: PointerEvent) {
    if (panPointerId !== event.pointerId) return;
    viewportX.value = panOriginX + (event.clientX - panStartX);
    viewportY.value = panOriginY + (event.clientY - panStartY);
  }

  function onPointerUp(event: PointerEvent) {
    if (panPointerId !== event.pointerId) return;
    panPointerId = null;
    (event.currentTarget as HTMLElement)?.releasePointerCapture?.(event.pointerId);
  }

  function bindViewportEl(el: HTMLElement | null) {
    if (!el) return () => {};
    el.addEventListener("wheel", onWheel, { passive: false });
    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);
    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointercancel", onPointerUp);
    };
  }

  const viewportEl = ref<HTMLElement | null>(null);
  let unbind: (() => void) | null = null;

  onMounted(() => {
    unbind = bindViewportEl(viewportEl.value);
  });

  onUnmounted(() => {
    unbind?.();
  });

  function setViewportEl(el: HTMLElement | null) {
    unbind?.();
    viewportEl.value = el;
    unbind = bindViewportEl(el);
  }

  return {
    viewportX,
    viewportY,
    viewportScale,
    viewportTransform,
    setViewportEl,
  };
}
