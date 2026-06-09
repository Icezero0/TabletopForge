import { computed, onMounted, onUnmounted, ref, watch, type Ref } from "vue";
import type { TableToolMode } from "@/features/table/types";
import { readPersistedState, writePersistedState } from "@/stores/persistence";

const MIN_VIEWPORT_SCALE = 0.25;
const MAX_VIEWPORT_SCALE = 4;
const ZOOM_SENSITIVITY = 0.001;

type PersistedViewport = { x: number; y: number; scale: number };

function viewportStorageKey(roomId: number) {
  return `room-${roomId}-viewport`;
}

export function useTabletopViewport(
  toolMode: Ref<TableToolMode>,
  roomId?: Ref<number | null | undefined>,
) {
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

  // --- persistence ---

  function loadPersistedViewport(id: number | null | undefined) {
    if (!id) return;
    const saved = readPersistedState<PersistedViewport | null>(viewportStorageKey(id), null);
    if (saved) {
      viewportX.value = saved.x;
      viewportY.value = saved.y;
      viewportScale.value = Math.min(MAX_VIEWPORT_SCALE, Math.max(MIN_VIEWPORT_SCALE, saved.scale));
    }
  }

  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  function scheduleSave() {
    if (!roomId?.value) return;
    if (saveTimer !== null) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      if (!roomId?.value) return;
      writePersistedState<PersistedViewport>(viewportStorageKey(roomId.value), {
        x: viewportX.value,
        y: viewportY.value,
        scale: viewportScale.value,
      });
    }, 500);
  }

  if (roomId) {
    watch(roomId, (id) => loadPersistedViewport(id), { immediate: true });
  }

  // --- viewport interaction ---

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
    scheduleSave();
  }

  function shouldStartPan(event: PointerEvent) {
    const isPrimaryHandPan = toolMode.value === "hand" && event.button === 0;
    const isMiddleViewportPan = (toolMode.value === "select" || toolMode.value === "hand") && event.button === 1;
    if (!isPrimaryHandPan && !isMiddleViewportPan) return false;
    const target = event.target as Element;
    if (isMiddleViewportPan) {
      return !target.closest(".textBoxEditor, .drawingLayer.drawMode");
    }
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
    if (!shouldStartPan(event)) return;
    event.preventDefault();
    event.stopPropagation();
    panPointerId = event.pointerId;
    panStartX = event.clientX;
    panStartY = event.clientY;
    panOriginX = viewportX.value;
    panOriginY = viewportY.value;
    (event.currentTarget as HTMLElement)?.setPointerCapture?.(event.pointerId);
  }

  function onAuxClick(event: MouseEvent) {
    if ((toolMode.value === "select" || toolMode.value === "hand") && event.button === 1) {
      event.preventDefault();
    }
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
    scheduleSave();
  }

  function bindViewportEl(el: HTMLElement | null) {
    if (!el) return () => {};
    el.addEventListener("wheel", onWheel, { passive: false });
    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);
    el.addEventListener("auxclick", onAuxClick);
    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointercancel", onPointerUp);
      el.removeEventListener("auxclick", onAuxClick);
    };
  }

  const viewportEl = ref<HTMLElement | null>(null);
  let unbind: (() => void) | null = null;

  onMounted(() => {
    unbind = bindViewportEl(viewportEl.value);
  });

  onUnmounted(() => {
    unbind?.();
    if (saveTimer !== null) clearTimeout(saveTimer);
  });

  function setViewportEl(el: HTMLElement | null) {
    unbind?.();
    viewportEl.value = el;
    unbind = bindViewportEl(el);
  }

  function resetViewport() {
    viewportX.value = 0;
    viewportY.value = 0;
    viewportScale.value = 1;
    scheduleSave();
  }

  return {
    viewportX,
    viewportY,
    viewportScale,
    viewportTransform,
    setViewportEl,
    resetViewport,
  };
}
