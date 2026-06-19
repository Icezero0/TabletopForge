<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

const props = withDefaults(
  defineProps<{
    count: number;
    disabled?: boolean;
    placeholderMinHeight?: number;
    placeholderRadius?: number | string;
  }>(),
  {
    disabled: false,
    placeholderMinHeight: 48,
    placeholderRadius: 14,
  },
);

const emit = defineEmits<{
  (e: "reorder", payload: { from: number; to: number }): void;
}>();

type PointerDragState = {
  index: number;
  pointerId: number;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
  offsetX: number;
  offsetY: number;
  width: number;
  height: number;
  active: boolean;
};

const listRef = ref<HTMLElement | { $el?: HTMLElement } | null>(null);
const dragState = ref<PointerDragState | null>(null);
const draggingIndex = ref<number | null>(null);
const insertionIndex = ref<number | null>(null);
const suppressHover = ref(false);
const settling = ref(false);
const floatingMarkup = ref("");
const listGap = ref(6);
let suppressHoverTimer: number | null = null;
let settleTimer: number | null = null;

const itemIndexes = computed(() =>
  Array.from({ length: Math.max(0, props.count) }, (_, index) => index),
);

const placeholderStyle = computed(() => ({
  height: `${dragState.value?.height ?? props.placeholderMinHeight}px`,
  borderRadius:
    typeof props.placeholderRadius === "number"
      ? `${props.placeholderRadius}px`
      : props.placeholderRadius,
}));

const floatingStyle = computed(() => {
  const state = dragState.value;
  if (!state?.active) return undefined;
  return {
    left: `${state.currentX - state.offsetX}px`,
    top: `${state.currentY - state.offsetY}px`,
    width: `${state.width}px`,
    minHeight: `${state.height}px`,
  };
});

function isInteractiveTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(
    target.closest(
      "button,input,textarea,select,a,[contenteditable='true'],[data-no-sort-drag]",
    ),
  );
}

function getListElement() {
  const value = listRef.value;
  if (value instanceof HTMLElement) return value;
  return value?.$el instanceof HTMLElement ? value.$el : null;
}

function resolveInsertionIndex(container: HTMLElement, clientY: number) {
  const dragging = draggingIndex.value;
  if (dragging == null) return 0;
  let insertion = 0;
  const elements = Array.from(container.querySelectorAll<HTMLElement>("[data-sort-index]"));
  for (const element of elements) {
    const index = Number(element.dataset.sortIndex);
    if (index === dragging) continue;
    const rect = element.getBoundingClientRect();
    if (clientY < rect.top + rect.height / 2) return insertion;
    insertion += 1;
  }
  return insertion;
}

function beginActiveDrag(state: PointerDragState) {
  state.active = true;
  draggingIndex.value = state.index;
  insertionIndex.value = state.index;
}

function getSlotTransform(index: number) {
  const dragging = draggingIndex.value;
  const insertion = insertionIndex.value;
  const state = dragState.value;
  if (dragging == null || insertion == null || !state?.active || index === dragging) return undefined;
  const distance = state.height + listGap.value;
  if (insertion > dragging && index > dragging && index <= insertion) {
    return { transform: `translateY(-${distance}px)` };
  }
  if (insertion < dragging && index >= insertion && index < dragging) {
    return { transform: `translateY(${distance}px)` };
  }
  return undefined;
}

function handlePointerMove(event: PointerEvent) {
  const state = dragState.value;
  if (!state || event.pointerId !== state.pointerId) return;

  const distance = Math.hypot(event.clientX - state.startX, event.clientY - state.startY);
  if (!state.active && distance >= 4) beginActiveDrag(state);
  if (!state.active) return;

  event.preventDefault();
  dragState.value = {
    ...state,
    currentX: event.clientX,
    currentY: event.clientY,
  };
  const container = getListElement();
  if (container) insertionIndex.value = resolveInsertionIndex(container, event.clientY);
}

function clearDragState() {
  window.removeEventListener("pointermove", handlePointerMove);
  window.removeEventListener("pointerup", handlePointerUp);
  window.removeEventListener("pointercancel", handlePointerCancel);
  document.body.classList.remove("base-sortable-dragging");
  floatingMarkup.value = "";
  dragState.value = null;
  draggingIndex.value = null;
  insertionIndex.value = null;
}

function brieflySuppressHover() {
  suppressHover.value = true;
  if (suppressHoverTimer != null) window.clearTimeout(suppressHoverTimer);
  suppressHoverTimer = window.setTimeout(() => {
    suppressHover.value = false;
    suppressHoverTimer = null;
  }, 80);
}

function handlePointerUp(event: PointerEvent) {
  const state = dragState.value;
  if (!state || event.pointerId !== state.pointerId) return;
  const from = state.index;
  const to = insertionIndex.value ?? from;
  const shouldReorder = state.active && !props.disabled && from !== to;
  if (shouldReorder) {
    settling.value = true;
    emit("reorder", { from, to });
    clearDragState();
    brieflySuppressHover();
    settleTimer = window.setTimeout(() => {
      settling.value = false;
      settleTimer = null;
    }, 80);
    return;
  }
  clearDragState();
  brieflySuppressHover();
}

function handlePointerCancel(event: PointerEvent) {
  const state = dragState.value;
  if (!state || event.pointerId !== state.pointerId) return;
  clearDragState();
  brieflySuppressHover();
}

function handlePointerDown(index: number, event: PointerEvent) {
  if (props.disabled || event.button !== 0 || isInteractiveTarget(event.target)) return;
  const source = event.currentTarget as HTMLElement | null;
  if (!source) return;
  event.preventDefault();
  event.stopPropagation();
  window.getSelection()?.removeAllRanges();
  const rect = source.getBoundingClientRect();
  const list = getListElement();
  if (list) {
    const styles = window.getComputedStyle(list);
    listGap.value = parseFloat(styles.rowGap || styles.gap || "6") || 0;
  }
  const clone = source.cloneNode(true) as HTMLElement;
  clone.classList.add("baseSortableFloatingClone");
  floatingMarkup.value = clone.outerHTML;
  dragState.value = {
    index,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    currentX: event.clientX,
    currentY: event.clientY,
    offsetX: event.clientX - rect.left,
    offsetY: event.clientY - rect.top,
    width: rect.width,
    height: rect.height,
    active: false,
  };
  document.body.classList.add("base-sortable-dragging");
  window.addEventListener("pointermove", handlePointerMove, { passive: false });
  window.addEventListener("pointerup", handlePointerUp);
  window.addEventListener("pointercancel", handlePointerCancel);
}

onBeforeUnmount(() => {
  clearDragState();
  if (suppressHoverTimer != null) window.clearTimeout(suppressHoverTimer);
  if (settleTimer != null) window.clearTimeout(settleTimer);
});
</script>

<template>
  <div
    ref="listRef"
    class="baseSortableList"
    :class="{
      dragging: draggingIndex != null,
      suppressHover,
      settling,
    }"
  >
    <div
      v-for="index in itemIndexes"
      :key="`item-${index}`"
      class="baseSortableSlot"
      :class="{ placeholder: draggingIndex === index }"
      :style="draggingIndex === index ? placeholderStyle : getSlotTransform(index)"
      :data-sort-index="index"
    >
      <template v-if="draggingIndex === index">
        <div class="baseSortablePlaceholderInner" />
      </template>
      <template v-else>
        <div
          class="baseSortableItem"
          :class="{ canDrag: !disabled }"
          @pointerdown="handlePointerDown(index, $event)"
        >
          <slot :index="index" />
        </div>
      </template>
    </div>
  </div>

  <Teleport to="body">
    <div
      v-if="dragState?.active && draggingIndex != null"
      class="baseSortableFloating"
      :style="floatingStyle"
      v-html="floatingMarkup"
    />
  </Teleport>
</template>

<style scoped>
.baseSortableList {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.baseSortableList.dragging {
  cursor: grabbing;
}

.baseSortableSlot.placeholder {
  box-sizing: border-box;
  border: 1px dashed color-mix(in srgb, var(--c-accent) 60%, transparent);
  background: color-mix(in srgb, var(--c-accent) 10%, transparent);
}

.baseSortableSlot {
  min-width: 0;
  transition: transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1);
  will-change: transform;
}

.baseSortableList.settling .baseSortableSlot {
  transition: none;
}

.baseSortablePlaceholderInner {
  height: 100%;
}

.baseSortableItem {
  min-width: 0;
  touch-action: none;
}

.baseSortableList.dragging .baseSortableItem,
.baseSortableList.suppressHover .baseSortableItem {
  pointer-events: none;
}

.baseSortableItem.canDrag {
  cursor: grab;
}

.baseSortableItem.canDrag:active {
  cursor: grabbing;
}

.baseSortableFloating {
  position: fixed;
  z-index: 10000;
  pointer-events: none;
  opacity: 1;
  transform: translateZ(0);
  filter: drop-shadow(0 10px 24px rgb(0 0 0 / 0.28));
}

</style>

<style>
body.base-sortable-dragging {
  user-select: none;
  cursor: grabbing;
}

body.base-sortable-dragging,
body.base-sortable-dragging * {
  user-select: none !important;
}

.baseSortableFloating .item.interactive,
.baseSortableFloating .resource-row:not(.editing) {
  background: color-mix(in srgb, var(--c-hover) 55%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-border) 65%, var(--c-text));
  box-shadow: 0 10px 22px rgb(0 0 0 / 0.08);
}

.baseSortableFloating .item,
.baseSortableFloating .resource-row {
  cursor: grabbing !important;
}
</style>
