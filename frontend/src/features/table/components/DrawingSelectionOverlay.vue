<script setup lang="ts">
import { computed, ref } from "vue";
import type { RoomDrawing } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { RemoteObjectSelection, TableToolMode } from "@/features/table/types";
import type { TabletopSelection } from "@/features/table/types";
import {
  cloneDrawingGeometry,
  getDrawingBounds,
  resizeDrawingGeometry,
  translateDrawingGeometry,
  DEFAULT_FONT_SIZE,
  type DrawingBounds,
  type DrawingResizeOrigin,
} from "@/features/table/drawingTypes";

type Corner = "tl" | "tr" | "bl" | "br";

const props = defineProps<{
  selection: TabletopSelection;
  drawings: RoomDrawing[];
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  viewportScale?: number;
  remoteSelections?: RemoteObjectSelection[];
}>();

const emit = defineEmits<{
  patchDrawing: [
    drawingId: number,
    payload: { geometry?: Record<string, unknown>; style?: Record<string, unknown> },
  ];
  beginDrawingInteraction: [drawingId: number];
  endDrawingInteraction: [drawingId: number];
}>();

const corners: { id: Corner; class: string; cursor: string }[] = [
  { id: "tl", class: "handleTl", cursor: "nwse-resize" },
  { id: "tr", class: "handleTr", cursor: "nesw-resize" },
  { id: "bl", class: "handleBl", cursor: "nesw-resize" },
  { id: "br", class: "handleBr", cursor: "nwse-resize" },
];

const selectedDrawing = computed(() => {
  if (props.selection?.type !== "drawing") return null;
  return props.drawings.find((d) => d.id === props.selection!.id) ?? null;
});

const canShowOverlay = computed(
  () =>
    (props.gameRole === "GM" || props.gameRole === "PL") &&
    (props.toolMode === "select" || props.toolMode === "hand") &&
    selectedDrawing.value != null,
);

const remoteClaimedSelected = computed(() => {
  const drawing = selectedDrawing.value;
  if (!drawing) return false;
  return props.remoteSelections?.some((claim) => claim.type === "drawing" && claim.id === drawing.id) ?? false;
});

const canEdit = computed(() => canShowOverlay.value && !remoteClaimedSelected.value);

const canResize = computed(() => canEdit.value);

const box = computed(() => {
  const drawing = selectedDrawing.value;
  if (!drawing) return null;
  return getDrawingBounds(drawing);
});

const boxStyle = computed(() => {
  const b = box.value;
  if (!b) return undefined;
  return {
    transform: `translate(${b.x}px, ${b.y}px)`,
    width: `${b.width}px`,
    height: `${b.height}px`,
  };
});

let dragPointerId: number | null = null;
let dragTargetId: number | null = null;
let dragStartX = 0;
let dragStartY = 0;
let dragOriginGeometry: Record<string, unknown> | null = null;
let dragInteractionStarted = false;

let resizePointerId: number | null = null;
let resizeCorner: Corner | null = null;
let resizeOriginBounds: DrawingBounds | null = null;
let resizeOrigin: DrawingResizeOrigin | null = null;
let resizeStartClientX = 0;
let resizeStartClientY = 0;
let resizeInteractionStarted = false;

const frameRef = ref<HTMLElement | null>(null);

function beginDrag(event: PointerEvent, drawing: RoomDrawing, captureEl: HTMLElement) {
  event.stopPropagation();
  dragPointerId = event.pointerId;
  dragTargetId = drawing.id;
  dragStartX = event.clientX;
  dragStartY = event.clientY;
  dragOriginGeometry = cloneDrawingGeometry(drawing);
  dragInteractionStarted = false;
  captureEl.setPointerCapture(event.pointerId);
}

function onDragDown(event: PointerEvent) {
  if (event.button !== 0) return;
  const drawing = selectedDrawing.value;
  if (!canEdit.value || !drawing) return;
  beginDrag(event, drawing, event.currentTarget as HTMLElement);
}

function onDragMove(event: PointerEvent) {
  if (dragPointerId !== event.pointerId || !dragOriginGeometry || dragTargetId == null) return;
  if (!dragInteractionStarted && Math.hypot(event.clientX - dragStartX, event.clientY - dragStartY) < 2) return;
  const drawing = props.drawings.find((d) => d.id === dragTargetId);
  if (!drawing) return;
  const vs = props.viewportScale ?? 1;
  const dx = (event.clientX - dragStartX) / vs;
  const dy = (event.clientY - dragStartY) / vs;
  const base = { ...drawing, geometry: dragOriginGeometry };
  if (!dragInteractionStarted) {
    dragInteractionStarted = true;
    emit("beginDrawingInteraction", drawing.id);
  }
  emit("patchDrawing", drawing.id, {
    geometry: translateDrawingGeometry(base, dx, dy),
  });
}

function onDragUp(event: PointerEvent) {
  if (dragPointerId !== event.pointerId) return;
  if (dragTargetId != null && dragInteractionStarted) emit("endDrawingInteraction", dragTargetId);
  dragPointerId = null;
  dragTargetId = null;
  dragOriginGeometry = null;
  dragInteractionStarted = false;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}

function cornerScenePoint(corner: Corner, b: DrawingBounds) {
  switch (corner) {
    case "tl":
      return { x: b.x, y: b.y };
    case "tr":
      return { x: b.x + b.width, y: b.y };
    case "bl":
      return { x: b.x, y: b.y + b.height };
    case "br":
      return { x: b.x + b.width, y: b.y + b.height };
  }
}

function boundsFromCorner(corner: Corner, origin: DrawingBounds, x: number, y: number): DrawingBounds {
  switch (corner) {
    case "br":
      return {
        x: origin.x,
        y: origin.y,
        width: Math.max(8, x - origin.x),
        height: Math.max(8, y - origin.y),
      };
    case "bl":
      return {
        x: x,
        y: origin.y,
        width: Math.max(8, origin.x + origin.width - x),
        height: Math.max(8, y - origin.y),
      };
    case "tr":
      return {
        x: origin.x,
        y: y,
        width: Math.max(8, x - origin.x),
        height: Math.max(8, origin.y + origin.height - y),
      };
    case "tl":
      return {
        x,
        y,
        width: Math.max(8, origin.x + origin.width - x),
        height: Math.max(8, origin.y + origin.height - y),
      };
  }
}

function onResizeDown(corner: Corner, event: PointerEvent) {
  if (event.button !== 0) return;
  const drawing = selectedDrawing.value;
  const b = box.value;
  if (!canResize.value || !drawing || !b) return;
  event.stopPropagation();
  resizePointerId = event.pointerId;
  resizeCorner = corner;
  resizeOriginBounds = { ...b };
  resizeOrigin = {
    bounds: { ...b },
    fontSize:
      drawing.kind === "text"
        ? ((drawing.style.fontSize as number) || DEFAULT_FONT_SIZE)
        : undefined,
  };
  resizeStartClientX = event.clientX;
  resizeStartClientY = event.clientY;
  resizeInteractionStarted = false;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function onResizeMove(event: PointerEvent) {
  const drawing = selectedDrawing.value;
  const corner = resizeCorner;
  const origin = resizeOriginBounds;
  if (!drawing || !corner || !origin || resizePointerId !== event.pointerId) return;
  if (!resizeInteractionStarted && Math.hypot(event.clientX - resizeStartClientX, event.clientY - resizeStartClientY) < 2) return;
  const vs = props.viewportScale ?? 1;
  const cornerPt = cornerScenePoint(corner, origin);
  const sceneX = cornerPt.x + (event.clientX - resizeStartClientX) / vs;
  const sceneY = cornerPt.y + (event.clientY - resizeStartClientY) / vs;
  const next = boundsFromCorner(corner, origin, sceneX, sceneY);
  const { geometry, style } = resizeDrawingGeometry(
    drawing,
    corner,
    next,
    resizeOrigin ?? undefined,
  );
  if (!resizeInteractionStarted) {
    resizeInteractionStarted = true;
    emit("beginDrawingInteraction", drawing.id);
  }
  emit("patchDrawing", drawing.id, { geometry, style });
}

function onResizeUp(event: PointerEvent) {
  if (resizePointerId !== event.pointerId) return;
  const drawingId = selectedDrawing.value?.id;
  if (drawingId != null && resizeInteractionStarted) emit("endDrawingInteraction", drawingId);
  resizePointerId = null;
  resizeCorner = null;
  resizeOriginBounds = null;
  resizeOrigin = null;
  resizeInteractionStarted = false;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}

function startDrag(event: PointerEvent, drawing?: RoomDrawing) {
  if (event.button !== 0) return;
  const target = drawing ?? selectedDrawing.value;
  if (!target) return;
  if (props.toolMode !== "select" && props.toolMode !== "hand") return;
  if (props.gameRole !== "GM" && props.gameRole !== "PL") return;
  if (remoteClaimedSelected.value) return;
  if (!frameRef.value) return;
  beginDrag(event, target, frameRef.value);
}

defineExpose({ startDrag });
</script>

<template>
  <div
    v-show="canShowOverlay && box"
    class="drawingSelectionOverlay"
    :style="boxStyle"
  >
    <div
      ref="frameRef"
      class="selectionFrame"
      :class="{ locked: remoteClaimedSelected }"
      @pointerdown="onDragDown"
      @pointermove="onDragMove"
      @pointerup="onDragUp"
      @pointercancel="onDragUp"
    />
    <div
      v-for="c in corners"
      v-show="canResize"
      :key="c.id"
      class="resizeHandle"
      :class="c.class"
      :style="{ cursor: c.cursor }"
      @pointerdown="onResizeDown(c.id, $event)"
      @pointermove="onResizeMove"
      @pointerup="onResizeUp"
      @pointercancel="onResizeUp"
    />
  </div>
</template>

<style scoped>
.drawingSelectionOverlay {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  pointer-events: none;
  z-index: 220;
}

.selectionFrame {
  position: absolute;
  inset: 0;
  border: 2px solid color-mix(in srgb, var(--c-primary) 80%, transparent);
  border-radius: 2px;
  box-sizing: border-box;
  pointer-events: auto;
  cursor: move;
}

.selectionFrame.locked {
  cursor: default;
}

.resizeHandle {
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 3px;
  background: var(--c-primary);
  border: 2px solid var(--c-surface);
  pointer-events: auto;
}

.resizeHandle::before {
  content: "";
  position: absolute;
  inset: -8px;
}

.handleTl {
  top: -10px;
  left: -10px;
}

.handleTr {
  top: -10px;
  right: -10px;
}

.handleBl {
  bottom: -10px;
  left: -10px;
}

.handleBr {
  bottom: -10px;
  right: -10px;
}
</style>
