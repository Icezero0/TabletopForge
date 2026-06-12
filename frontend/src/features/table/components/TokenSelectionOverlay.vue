<script setup lang="ts">
import { computed } from "vue";
import type { RoomToken } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { RemoteObjectSelection, TableToolMode } from "@/features/table/types";
import type { TabletopSelection } from "@/features/table/types";
import { tokenSizePx, canManageToken } from "@/features/table/utils/tokenDisplay";

type Corner = "tl" | "tr" | "bl" | "br";

const props = defineProps<{
  selection: TabletopSelection;
  tokens: RoomToken[];
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  gridCellFt: number;
  gridCellPx: number;
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
  viewportScale?: number;
  remoteSelections?: RemoteObjectSelection[];
}>();

const emit = defineEmits<{
  previewToken: [
    tokenId: number,
    payload: { x?: number; y?: number; width?: number; height?: number },
  ];
  commitToken: [
    tokenId: number,
    payload: { x?: number; y?: number; width?: number; height?: number },
  ];
  beginTokenInteraction: [tokenId: number];
  endTokenInteraction: [tokenId: number];
  tokenContextMenu: [event: MouseEvent];
}>();

const corners: { id: Corner; class: string; cursor: string }[] = [
  { id: "tl", class: "handleTl", cursor: "nwse-resize" },
  { id: "tr", class: "handleTr", cursor: "nesw-resize" },
  { id: "bl", class: "handleBl", cursor: "nesw-resize" },
  { id: "br", class: "handleBr", cursor: "nwse-resize" },
];

const selectedToken = computed(() => {
  if (props.selection?.type !== "token") return null;
  return props.tokens.find((t) => t.id === props.selection!.id) ?? null;
});

function canManageSelected(token: RoomToken): boolean {
  return canManageToken(
    token,
    props.gameRole,
    props.currentUserId,
    props.characterOwnerById,
  );
}

const canShowOverlay = computed(
  () =>
    (props.toolMode === "select" || props.toolMode === "hand") &&
    selectedToken.value != null &&
    canManageSelected(selectedToken.value),
);

const remoteClaimedSelected = computed(() => {
  const token = selectedToken.value;
  if (!token) return false;
  return props.remoteSelections?.some((claim) => claim.type === "token" && claim.id === token.id) ?? false;
});

const canTransform = computed(
  () => canShowOverlay.value && selectedToken.value != null && !selectedToken.value.locked && !remoteClaimedSelected.value,
);

const box = computed(() => {
  const token = selectedToken.value;
  if (!token) return null;
  const size = tokenSizePx(token.width, props.gridCellFt, props.gridCellPx);
  return { x: token.x, y: token.y, width: size, height: size };
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
let dragOriginX = 0;
let dragOriginY = 0;
let lastDragPayload: { x?: number; y?: number } | null = null;
let dragInteractionStarted = false;

let resizePointerId: number | null = null;
let resizeCorner: Corner | null = null;
let resizeOriginSizeFt = 1;
let resizeAnchorX = 0;
let resizeAnchorY = 0;
let resizeOriginDist = 1;
let resizeStartClientX = 0;
let resizeStartClientY = 0;
let resizeStartCornerX = 0;
let resizeStartCornerY = 0;
let lastResizePayload: { x?: number; y?: number; width?: number; height?: number } | null = null;
let resizeInteractionStarted = false;

function pxToFt(px: number) {
  if (props.gridCellPx <= 0) return px;
  return (px / props.gridCellPx) * props.gridCellFt;
}

function beginDrag(event: PointerEvent, token: RoomToken, captureEl: HTMLElement) {
  event.stopPropagation();
  dragPointerId = event.pointerId;
  dragTargetId = token.id;
  dragStartX = event.clientX;
  dragStartY = event.clientY;
  dragOriginX = token.x;
  dragOriginY = token.y;
  lastDragPayload = null;
  dragInteractionStarted = false;
  captureEl.setPointerCapture(event.pointerId);
}

function onDragDown(event: PointerEvent) {
  if (event.button !== 0) return;
  const token = selectedToken.value;
  if (!canTransform.value || !token) return;
  beginDrag(event, token, event.currentTarget as HTMLElement);
}

function onDragMove(event: PointerEvent) {
  if (dragPointerId !== event.pointerId || dragTargetId == null) return;
  if (!dragInteractionStarted && Math.hypot(event.clientX - dragStartX, event.clientY - dragStartY) < 2) return;
  const vs = props.viewportScale ?? 1;
  const dx = (event.clientX - dragStartX) / vs;
  const dy = (event.clientY - dragStartY) / vs;
  lastDragPayload = { x: dragOriginX + dx, y: dragOriginY + dy };
  if (!dragInteractionStarted) {
    dragInteractionStarted = true;
    emit("beginTokenInteraction", dragTargetId);
  }
  emit("previewToken", dragTargetId, lastDragPayload);
}

function onDragUp(event: PointerEvent) {
  if (dragPointerId !== event.pointerId) return;
  if (dragTargetId != null && lastDragPayload) {
    emit("commitToken", dragTargetId, lastDragPayload);
  } else if (dragTargetId != null && dragInteractionStarted) {
    emit("endTokenInteraction", dragTargetId);
  }
  dragPointerId = null;
  dragTargetId = null;
  lastDragPayload = null;
  dragInteractionStarted = false;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}

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

function patchSizeForCorner(token: RoomToken, corner: Corner, nextSizeFt: number, b: { width: number; height: number }) {
  const w = tokenSizePx(nextSizeFt, props.gridCellFt, props.gridCellPx);
  const h = w;
  const curW = b.width;
  const curH = b.height;
  const payload: { width: number; height: number; x?: number; y?: number } = {
    width: nextSizeFt,
    height: nextSizeFt,
  };

  switch (corner) {
    case "br":
      break;
    case "bl":
      payload.x = token.x + curW - w;
      break;
    case "tr":
      payload.y = token.y + curH - h;
      break;
    case "tl":
      payload.x = token.x + curW - w;
      payload.y = token.y + curH - h;
      break;
  }
  lastResizePayload = payload;
  emit("previewToken", token.id, payload);
}

function onResizeDown(corner: Corner, event: PointerEvent) {
  if (event.button !== 0) return;
  const token = selectedToken.value;
  const b = box.value;
  if (!canTransform.value || !token || !b) return;
  event.stopPropagation();
  resizePointerId = event.pointerId;
  resizeCorner = corner;
  resizeOriginSizeFt = token.width;
  const anchor = anchorForCorner(corner, b);
  resizeAnchorX = anchor.x;
  resizeAnchorY = anchor.y;
  const cp = cornerScenePoint(corner, b);
  resizeStartCornerX = cp.x;
  resizeStartCornerY = cp.y;
  resizeOriginDist = Math.hypot(cp.x - anchor.x, cp.y - anchor.y) || 1;
  resizeStartClientX = event.clientX;
  resizeStartClientY = event.clientY;
  resizeInteractionStarted = false;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function onResizeMove(event: PointerEvent) {
  const token = selectedToken.value;
  const corner = resizeCorner;
  const b = box.value;
  if (!token || !corner || !b || resizePointerId !== event.pointerId) return;
  if (!resizeInteractionStarted && Math.hypot(event.clientX - resizeStartClientX, event.clientY - resizeStartClientY) < 2) return;

  const vs = props.viewportScale ?? 1;
  const dx = (event.clientX - resizeStartClientX) / vs;
  const dy = (event.clientY - resizeStartClientY) / vs;
  const newCornerX = resizeStartCornerX + dx;
  const newCornerY = resizeStartCornerY + dy;
  const newDist = Math.hypot(newCornerX - resizeAnchorX, newCornerY - resizeAnchorY);
  const ratio = newDist / resizeOriginDist;
  const nextPx = tokenSizePx(resizeOriginSizeFt, props.gridCellFt, props.gridCellPx) * ratio;
  const nextSizeFt = Math.max(props.gridCellFt * 0.25, pxToFt(nextPx));
  if (!resizeInteractionStarted) {
    resizeInteractionStarted = true;
    emit("beginTokenInteraction", token.id);
  }
  patchSizeForCorner(token, corner, nextSizeFt, b);
}

function onResizeUp(event: PointerEvent) {
  if (resizePointerId !== event.pointerId) return;
  const token = selectedToken.value;
  if (token && lastResizePayload) {
    emit("commitToken", token.id, lastResizePayload);
  } else if (token && resizeInteractionStarted) {
    emit("endTokenInteraction", token.id);
  }
  resizePointerId = null;
  resizeCorner = null;
  lastResizePayload = null;
  resizeInteractionStarted = false;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
}
function onContextMenu(event: MouseEvent) {
  if (!selectedToken.value) return;
  event.preventDefault();
  event.stopPropagation();
  emit("tokenContextMenu", event);
}
</script>

<template>
  <div
    v-show="canShowOverlay && box"
    class="tokenSelectionOverlay"
    :class="{ remoteClaimed: remoteClaimedSelected }"
    :style="boxStyle"
  >
    <div
      class="selectionFrame"
      :class="{ editable: canTransform, locked: selectedToken?.locked }"
      @contextmenu="onContextMenu"
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
.tokenSelectionOverlay {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 215;
  pointer-events: none;
}

.tokenSelectionOverlay.remoteClaimed {
  transition: transform 80ms linear;
}

.selectionFrame {
  position: absolute;
  inset: 0;
  border: 2px solid var(--color-accent, #6b9fff);
  border-radius: 50%;
  box-sizing: border-box;
  pointer-events: auto;
  cursor: default;
}

.selectionFrame.editable {
  cursor: move;
}

.selectionFrame.locked {
  cursor: not-allowed;
}

.resizeHandle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--color-accent, #6b9fff);
  border: 1px solid #fff;
  border-radius: 2px;
  pointer-events: auto;
}

.handleTl {
  left: -5px;
  top: -5px;
}

.handleTr {
  right: -5px;
  top: -5px;
}

.handleBl {
  left: -5px;
  bottom: -5px;
}

.handleBr {
  right: -5px;
  bottom: -5px;
}
</style>
