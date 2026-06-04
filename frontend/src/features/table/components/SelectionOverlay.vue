<script setup lang="ts">
import { computed, ref } from "vue";
import type { RoomMap } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode } from "@/features/table/types";
import type { TabletopSelection } from "@/features/table/types";
import { MAP_SCALE_MIN, MAP_SCALE_STEP } from "@/features/table/constants";

type Corner = "tl" | "tr" | "bl" | "br";

const props = defineProps<{
  selection: TabletopSelection;
  maps: RoomMap[];
  mapNaturalSize: { w: number; h: number };
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  viewportScale?: number;
}>();

const emit = defineEmits<{
  patchMap: [mapId: number, payload: { x?: number; y?: number; scale?: number }];
}>();

const corners: { id: Corner; class: string; cursor: string }[] = [
  { id: "tl", class: "handleTl", cursor: "nwse-resize" },
  { id: "tr", class: "handleTr", cursor: "nesw-resize" },
  { id: "bl", class: "handleBl", cursor: "nesw-resize" },
  { id: "br", class: "handleBr", cursor: "nwse-resize" },
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

const box = computed(() => {
  const map = selectedMap.value;
  if (!map || !props.mapNaturalSize.w) return null;
  return {
    x: map.x,
    y: map.y,
    width: props.mapNaturalSize.w * map.scale,
    height: props.mapNaturalSize.h * map.scale,
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

function startDrag(event: PointerEvent, map?: RoomMap) {
  const target = map ?? selectedMap.value;
  if (!target || target.locked) return;
  if (props.gameRole !== "GM") return;
  if (props.toolMode !== "select" && props.toolMode !== "hand") return;
  if (!frameRef.value) return;
  beginDrag(event, target, frameRef.value);
}

defineExpose({ startDrag });

function cornerScenePoint(corner: Corner, b: { x: number; y: number; width: number; height: number }) {
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

function anchorForCorner(corner: Corner, b: { x: number; y: number; width: number; height: number }) {
  switch (corner) {
    case "br":
      return { x: b.x, y: b.y };
    case "bl":
      return { x: b.x + b.width, y: b.y };
    case "tr":
      return { x: b.x, y: b.y + b.height };
    case "tl":
      return { x: b.x + b.width, y: b.y + b.height };
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
  const w = nw * nextScale;
  const h = nh * nextScale;
  const curW = nw * map.scale;
  const curH = nh * map.scale;

  switch (corner) {
    case "br":
      emit("patchMap", map.id, { scale: nextScale });
      break;
    case "bl":
      emit("patchMap", map.id, { scale: nextScale, x: map.x + curW - w });
      break;
    case "tr":
      emit("patchMap", map.id, { scale: nextScale, y: map.y + curH - h });
      break;
    case "tl":
      emit("patchMap", map.id, {
        scale: nextScale,
        x: map.x + curW - w,
        y: map.y + curH - h,
      });
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
    />
    <div
      v-for="c in corners"
      v-show="canTransform"
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
