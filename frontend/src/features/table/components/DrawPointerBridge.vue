<script setup lang="ts">
const props = defineProps<{
  subTool: string;
  resolveScenePoint: (event: PointerEvent) => { x: number; y: number };
}>();

const emit = defineEmits<{
  pointerDown: [x: number, y: number, event: PointerEvent];
  pointerMove: [x: number, y: number, event: PointerEvent];
  pointerUp: [x: number, y: number, event: PointerEvent];
  eraserHover: [x: number, y: number];
  eraserLeave: [];
}>();

function onPointerDown(event: PointerEvent) {
  if (event.button !== 0) return;
  const pt = props.resolveScenePoint(event);
  event.preventDefault();
  event.stopPropagation();
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  emit("pointerDown", pt.x, pt.y, event);
}

function onPointerMove(event: PointerEvent) {
  const pt = props.resolveScenePoint(event);
  if (props.subTool === "eraser") {
    emit("eraserHover", pt.x, pt.y);
  }
  emit("pointerMove", pt.x, pt.y, event);
}

function onPointerUp(event: PointerEvent) {
  const pt = props.resolveScenePoint(event);
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
  emit("pointerUp", pt.x, pt.y, event);
}

function onPointerLeave() {
  if (props.subTool === "eraser") {
    emit("eraserLeave");
  }
}
</script>

<template>
  <div
    class="drawPointerBridge"
    :class="{ eraserMode: subTool === 'eraser' }"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @pointerleave="onPointerLeave"
  />
</template>

<style scoped>
.drawPointerBridge {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: auto;
  touch-action: none;
}

.drawPointerBridge:not(.eraserMode) {
  cursor: crosshair;
}

.drawPointerBridge.eraserMode {
  cursor: none;
}
</style>
