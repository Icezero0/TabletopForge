<script setup lang="ts">
import { computed, ref } from "vue";
import type { RoomMap } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode } from "@/features/table/types";
import type { TabletopSelection } from "@/features/table/types";
import { MAP_SCALE_MIN, MAP_SCALE_STEP } from "@/features/table/constants";

type Corner = "tl" | "tr" | "bl" | "br";
type Edge = "t" | "b" | "l" | "r";

const props = defineProps<{
  selection: TabletopSelection;
  maps: RoomMap[];
  mapNaturalSize: { w: number; h: number };
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  viewportScale?: number;
}>();

const emit = defineEmits<{
  patchMap: [mapId: number, payload: { x?: number; y?: number; scale?: number; scale_x?: number | null; scale_y?: number | null }];
  contextMenu: [mapId: number, event: MouseEvent];
}>();

const corners: { id: Corner; class: string; cursor: string }[] = [
  { id: "tl", class: "handleTl", cursor: "nwse-resize" },
  { id: "tr", class: "handleTr", cursor: "nesw-resize" },
  { id: "bl", class: "handleBl", cursor: "nesw-resize" },
  { id: "br", class: "handleBr", cursor: "nwse-resize" },
];

const edges: { id: Edge; class: string; cursor: string }[] = [
  { id: "t", class: "handleTm", cursor: "ns-resize" },
  { id: "b", class: "handleBm", cursor: "ns-resize" },
  { id: "l", class: "handleMl", cursor: "ew-resize" },
  { id: "r", class: "handleMr", cursor: "ew-resize" },
];

const selectedMap = computed(() => {
  if (props.selection?.type !== "map") return null;
  return props.maps.find((m) => m.id === props.selection!.id) ?? null;
});

const canShowOverlay = computed(
  () =>
    props.gameRole === "GM" &&
    (props.toolMode === "select" || props.toolMode === "hand") &&
    selectedMap.value != null &&
    props.mapNaturalSize.w > 0,
);

const canTransform = computed(
  () => canShowOverlay.value && selectedMap.value != null && !selectedMap.value.locked,
);

function effScaleX(map: RoomMap) { return map.scale_x ?? map.scale; }
function effScaleY(map: RoomMap) { return map.scale_y ?? map.scale; }

const box = computed(() => {
  const map = selectedMap.value;
  if (!map || !props.mapNaturalSize.w) return null;
  return {
    x: map.x,
    y: map.y,
    width: props.mapNaturalSize.w * effScaleX(map),
    height: props.mapNaturalSize.h * effScaleY(map),
  };
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
let dragTargetMapId: number | null = null;
let dragStartX = 0;
let dragStartY = 0;
let dragOriginX = 0;
let dragOriginY = 0;

// --- corner resize state ---
let resizePointerId: number | null = null;
let resizeCorner: Corner | null = null;
let resizeOriginScale = 1;
let resizeAnchorX = 0;
let resizeAnchorY = 0;
let resizeOriginDist = 1;
let resizeStartClientX = 0;
let resizeStartClientY = 0;
let resizeStartCornerX = 0;
let resizeStartCornerY = 0;

// --- edge resize state ---
let edgePointerId: number | null = null;
let edgeEdge: Edge | null = null;
let edgeOriginScaleX = 1;
let edgeOriginScaleY = 1;
let edgeOriginW = 0;
let edgeOriginH = 0;
let edgeOriginMapX = 0;
let edgeOriginMapY = 0;
let edgeStartClientX = 0;
let edgeStartClientY = 0;

const frameRef = ref<HTMLElement | null>(null);

function roundScale(value: number) {
  return Math.max(MAP_SCALE_MIN, Math.round(value / MAP_SCALE_STEP) * MAP_SCALE_STEP);
}

function beginDrag(event: PointerEvent, map: RoomMap, captureEl: HTMLElement) {
  event.stopPropagation();
  dragPointerId = event.pointerId;
  dragTargetMapId = map.id;
  dragStartX = event.clientX;
  dragStartY = event.clientY;
  dragOriginX = map.x;
  dragOriginY = map.y;
  captureEl.setPointerCapture(event.pointerId);
}

function onDragDown(event: PointerEvent) {
  const map = selectedMap.value;
  if (!canTransform.value || !map) return;
  beginDrag(event, map, event.currentTarget as HTMLElement);
}

function onDragMove(event: PointerEvent) {
  if (dragPointerId !== event.pointerId || dragTargetMapId == null) return;
  const map = props.maps.find((m) => m.id === dragTargetMapId);
  if (!map) return;
  const vs = props.viewportScale ?? 1;
  const dx = (event.clientX - dragStartX) / vs;
  const dy = (event.clientY - dragStartY) / vs;
  emit("patchMap", map.id, { x: dragOriginX + dx, y: dragOriginY + dy });
}

function onDragUp(event: PointerEvent) {
  if (dragPointerId !== event.pointerId) return;
  dragPointerId = null;
  dragTargetMapId = null;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}

function onContextMenu(event: MouseEvent) {
  const map = selectedMap.value;
  if (!map) return;
  event.preventDefault();
  event.stopPropagation();
  emit("contextMenu", map.id, event);
}

function startDrag(event: PointerEvent, map?: RoomMap) {
  const target = map ?? selectedMap.value;
  if (!target || target.locked) return;
  if (props.gameRole !== "GM") return;
  if (props.toolMode !== "select" && props.toolMode !== "hand") return;
  if (!frameRef.value) return;
  beginDrag(event, target, frameRef.value);
}

defineExpose({ startDrag });

// --- corner resize ---
function cornerScenePoint(corner: Corner, b: { x: number; y: number; width: number; height: number }) {
  switch (corner) {
    case "tl": return { x: b.x, y: b.y };
    case "tr": return { x: b.x + b.width, y: b.y };
    case "bl": return { x: b.x, y: b.y + b.height };
    case "br": return { x: b.x + b.width, y: b.y + b.height };
  }
}

function anchorForCorner(corner: Corner, b: { x: number; y: number; width: number; height: number }) {
  switch (corner) {
    case "br": return { x: b.x, y: b.y };
    case "bl": return { x: b.x + b.width, y: b.y };
    case "tr": return { x: b.x, y: b.y + b.height };
    case "tl": return { x: b.x + b.width, y: b.y + b.height };
  }
}

function onResizeDown(corner: Corner, event: PointerEvent) {
  const map = selectedMap.value;
  const b = box.value;
  if (!canTransform.value || !map || !b) return;
  event.stopPropagation();
  resizePointerId = event.pointerId;
  resizeCorner = corner;
  resizeOriginScale = map.scale;
  const anchor = anchorForCorner(corner, b);
  resizeAnchorX = anchor.x;
  resizeAnchorY = anchor.y;
  const cp = cornerScenePoint(corner, b);
  resizeStartCornerX = cp.x;
  resizeStartCornerY = cp.y;
  resizeOriginDist = Math.hypot(cp.x - anchor.x, cp.y - anchor.y) || 1;
  resizeStartClientX = event.clientX;
  resizeStartClientY = event.clientY;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function patchScaleForCorner(map: RoomMap, corner: Corner, nextScale: number) {
  const nw = props.mapNaturalSize.w;
  const nh = props.mapNaturalSize.h;
  const curW = nw * effScaleX(map);
  const curH = nh * effScaleY(map);
  const w = nw * nextScale;
  const h = nh * nextScale;
  // corner resize resets to uniform scale (clears scale_x/scale_y)
  switch (corner) {
    case "br":
      emit("patchMap", map.id, { scale: nextScale, scale_x: null, scale_y: null });
      break;
    case "bl":
      emit("patchMap", map.id, { scale: nextScale, scale_x: null, scale_y: null, x: map.x + curW - w });
      break;
    case "tr":
      emit("patchMap", map.id, { scale: nextScale, scale_x: null, scale_y: null, y: map.y + curH - h });
      break;
    case "tl":
      emit("patchMap", map.id, { scale: nextScale, scale_x: null, scale_y: null, x: map.x + curW - w, y: map.y + curH - h });
      break;
  }
}

function onResizeMove(event: PointerEvent) {
  const map = selectedMap.value;
  const corner = resizeCorner;
  if (!map || !corner || resizePointerId !== event.pointerId) return;
  const vs = props.viewportScale ?? 1;
  const dx = (event.clientX - resizeStartClientX) / vs;
  const dy = (event.clientY - resizeStartClientY) / vs;
  const newCornerX = resizeStartCornerX + dx;
  const newCornerY = resizeStartCornerY + dy;
  const newDist = Math.hypot(newCornerX - resizeAnchorX, newCornerY - resizeAnchorY);
  const ratio = newDist / resizeOriginDist;
  const nextScale = roundScale(resizeOriginScale * ratio);
  patchScaleForCorner(map, corner, nextScale);
}

function onResizeUp(event: PointerEvent) {
  if (resizePointerId !== event.pointerId) return;
  resizePointerId = null;
  resizeCorner = null;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}

// --- edge resize ---
function onEdgeDown(edge: Edge, event: PointerEvent) {
  const map = selectedMap.value;
  const b = box.value;
  if (!canTransform.value || !map || !b) return;
  event.stopPropagation();
  edgePointerId = event.pointerId;
  edgeEdge = edge;
  edgeOriginScaleX = effScaleX(map);
  edgeOriginScaleY = effScaleY(map);
  edgeOriginW = b.width;
  edgeOriginH = b.height;
  edgeOriginMapX = map.x;
  edgeOriginMapY = map.y;
  edgeStartClientX = event.clientX;
  edgeStartClientY = event.clientY;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function onEdgeMove(event: PointerEvent) {
  const map = selectedMap.value;
  const edge = edgeEdge;
  if (!map || !edge || edgePointerId !== event.pointerId) return;
  const nw = props.mapNaturalSize.w;
  const nh = props.mapNaturalSize.h;
  const vs = props.viewportScale ?? 1;
  const dx = (event.clientX - edgeStartClientX) / vs;
  const dy = (event.clientY - edgeStartClientY) / vs;

  switch (edge) {
    case "r": {
      const newSx = roundScale((edgeOriginW + dx) / nw);
      emit("patchMap", map.id, { scale_x: newSx, scale_y: edgeOriginScaleY });
      break;
    }
    case "l": {
      const newSx = roundScale((edgeOriginW - dx) / nw);
      emit("patchMap", map.id, { scale_x: newSx, scale_y: edgeOriginScaleY, x: edgeOriginMapX + dx });
      break;
    }
    case "b": {
      const newSy = roundScale((edgeOriginH + dy) / nh);
      emit("patchMap", map.id, { scale_x: edgeOriginScaleX, scale_y: newSy });
      break;
    }
    case "t": {
      const newSy = roundScale((edgeOriginH - dy) / nh);
      emit("patchMap", map.id, { scale_x: edgeOriginScaleX, scale_y: newSy, y: edgeOriginMapY + dy });
      break;
    }
  }
}

function onEdgeUp(event: PointerEvent) {
  if (edgePointerId !== event.pointerId) return;
  edgePointerId = null;
  edgeEdge = null;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}
</script>

<template>
  <div
    v-show="canShowOverlay && box"
    class="selectionOverlay"
    :style="boxStyle"
  >
    <div
      ref="frameRef"
      class="selectionFrame"
      :class="{ editable: canTransform, locked: selectedMap?.locked }"
      @pointerdown="onDragDown"
      @pointermove="onDragMove"
      @pointerup="onDragUp"
      @pointercancel="onDragUp"
      @contextmenu="onContextMenu"
    />
    <!-- corner handles: proportional resize -->
    <div
      v-for="c in corners"
      v-show="canTransform"
      :key="c.id"
      class="resizeHandle cornerHandle"
      :class="c.class"
      :style="{ cursor: c.cursor }"
      @pointerdown="onResizeDown(c.id, $event)"
      @pointermove="onResizeMove"
      @pointerup="onResizeUp"
      @pointercancel="onResizeUp"
      @contextmenu="onContextMenu"
    />
    <!-- edge handles: single-axis resize -->
    <div
      v-for="e in edges"
      v-show="canTransform"
      :key="e.id"
      class="resizeHandle edgeHandle"
      :class="e.class"
      :style="{ cursor: e.cursor }"
      @pointerdown="onEdgeDown(e.id, $event)"
      @pointermove="onEdgeMove"
      @pointerup="onEdgeUp"
      @pointercancel="onEdgeUp"
      @contextmenu="onContextMenu"
    />
  </div>
</template>

<style scoped>
.selectionOverlay {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  pointer-events: none;
  z-index: 210;
}

.selectionFrame {
  position: absolute;
  inset: 0;
  border: 2px solid color-mix(in srgb, var(--c-primary) 80%, transparent);
  border-radius: 2px;
  box-sizing: border-box;
}

.selectionFrame.locked {
  border-style: dashed;
  opacity: 0.85;
}

.selectionFrame.editable {
  pointer-events: auto;
  cursor: move;
}

.resizeHandle {
  position: absolute;
  background: var(--c-primary);
  border: 2px solid var(--c-surface);
  pointer-events: auto;
}

.resizeHandle::before {
  content: "";
  position: absolute;
  inset: -8px;
}

/* corner handles: square */
.cornerHandle {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}

.handleTl { top: -8px; left: -8px; }
.handleTr { top: -8px; right: -8px; }
.handleBl { bottom: -8px; left: -8px; }
.handleBr { bottom: -8px; right: -8px; }

/* edge handles: rectangular */
.edgeHandle {
  border-radius: 3px;
}

.handleTm {
  width: 24px;
  height: 8px;
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.handleBm {
  width: 24px;
  height: 8px;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.handleMl {
  width: 8px;
  height: 24px;
  left: -5px;
  top: 50%;
  transform: translateY(-50%);
}

.handleMr {
  width: 8px;
  height: 24px;
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
}
</style>
