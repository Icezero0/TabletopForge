<script setup lang="ts">
import { computed, ref } from "vue";
import type { RoomDrawing } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode } from "@/features/table/types";
import type { DrawPreview } from "@/features/table/composables/useDrawingTools";
import { DRAWING_BAND_BASE, DRAWING_PICK_STROKE_HIT } from "@/features/table/constants";
import {
  brushPathFromPoints,
  findTopDrawingAt,
} from "@/features/table/drawingTypes";
import { clientToScene } from "@/features/table/utils/sceneCoords";

const props = defineProps<{
  drawings: RoomDrawing[];
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  preview: DrawPreview;
  selectedDrawingId?: number | null;
  editingDrawingId?: number | null;
  interactive?: boolean;
  subTool?: string;
}>();

const emit = defineEmits<{
  pointerDown: [x: number, y: number, event: PointerEvent];
  pointerMove: [x: number, y: number, event: PointerEvent];
  pointerUp: [x: number, y: number, event: PointerEvent];
  selectDrawing: [id: number];
  editText: [id: number];
  drawingContextMenu: [id: number, event: MouseEvent];
}>();

const svgRef = ref<SVGSVGElement | null>(null);
let pickPointerId: number | null = null;

const canDraw = computed(
  () =>
    props.interactive &&
    props.toolMode === "draw" &&
    (props.gameRole === "GM" || props.gameRole === "PL"),
);

const canPickDrawing = computed(
  () =>
    (props.toolMode === "select" || props.toolMode === "hand") &&
    (props.gameRole === "GM" || props.gameRole === "PL"),
);

const layerActive = computed(() => canDraw.value || canPickDrawing.value);

const drawCursor = computed(() => (canDraw.value ? "crosshair" : undefined));

const showPickTargets = computed(() => canPickDrawing.value && !canDraw.value);

const sortedDrawings = computed(() =>
  [...props.drawings].sort((a, b) => a.z_index - b.z_index || a.id - b.id),
);

function pickHitStrokeWidth(d: { style: Record<string, unknown> }) {
  return Math.max(DRAWING_PICK_STROKE_HIT, strokeW(d) + 12);
}

function normalizedRect(g: Record<string, unknown>) {
  const x = Number(g.x);
  const y = Number(g.y);
  const w = Number(g.width);
  const h = Number(g.height);
  return {
    x: w < 0 ? x + w : x,
    y: h < 0 ? y + h : y,
    width: Math.abs(w),
    height: Math.abs(h),
  };
}

function scenePoint(event: PointerEvent) {
  if (!svgRef.value) return { x: 0, y: 0 };
  return clientToScene(svgRef.value, event.clientX, event.clientY);
}

function onPointerDown(event: PointerEvent) {
  if (!layerActive.value) return;
  const pt = scenePoint(event);

  if (canPickDrawing.value) {
    const hit = findTopDrawingAt(props.drawings, pt.x, pt.y);
    if (hit) {
      event.preventDefault();
      event.stopPropagation();
      pickPointerId = event.pointerId;
      svgRef.value?.setPointerCapture(event.pointerId);
      emit("selectDrawing", hit.id);
      return;
    }
    if (!canDraw.value) return;
  }

  if (!canDraw.value) return;
  event.stopPropagation();
  event.preventDefault();
  if (props.subTool !== "text") {
    svgRef.value?.setPointerCapture(event.pointerId);
  }
  emit("pointerDown", pt.x, pt.y, event);
}

function onPointerMove(event: PointerEvent) {
  const pt = scenePoint(event);
  if (!canDraw.value) return;
  emit("pointerMove", pt.x, pt.y, event);
}

function onPointerUp(event: PointerEvent) {
  if (canPickDrawing.value && pickPointerId === event.pointerId) {
    pickPointerId = null;
    svgRef.value?.releasePointerCapture(event.pointerId);
    const pt = scenePoint(event);
    const hit = findTopDrawingAt(props.drawings, pt.x, pt.y);
    if (hit) {
      event.preventDefault();
      event.stopPropagation();
      emit("selectDrawing", hit.id);
    }
    return;
  }

  if (!canDraw.value) return;
  const pt = scenePoint(event);
  svgRef.value?.releasePointerCapture(event.pointerId);
  emit("pointerUp", pt.x, pt.y, event);
}

function onPickClick(event: MouseEvent) {
  if (!canPickDrawing.value) return;
  event.preventDefault();
  event.stopPropagation();
  const pt = scenePointFromClient(event.clientX, event.clientY);
  const hit = findTopDrawingAt(props.drawings, pt.x, pt.y);
  if (hit) emit("selectDrawing", hit.id);
}

function onDrawingContextMenu(event: MouseEvent) {
  if (!canPickDrawing.value) return;
  const pt = scenePointFromClient(event.clientX, event.clientY);
  const hit = findTopDrawingAt(props.drawings, pt.x, pt.y);
  if (!hit) return;
  event.preventDefault();
  event.stopPropagation();
  emit("selectDrawing", hit.id);
  emit("drawingContextMenu", hit.id, event);
}

function onTextDblClick(drawing: RoomDrawing, event: MouseEvent) {
  if (!canPickDrawing.value || drawing.kind !== "text") return;
  event.preventDefault();
  event.stopPropagation();
  emit("editText", drawing.id);
}

function stroke(d: { style: Record<string, unknown> }) {
  return String(d.style.color ?? "#e11d48");
}

function strokeW(d: { style: Record<string, unknown> }) {
  return Number(d.style.width ?? 3);
}

function textFontSize(d: { style: Record<string, unknown> }) {
  return Number(d.style.fontSize ?? 16);
}

function scenePointFromClient(clientX: number, clientY: number) {
  if (!svgRef.value) return { x: 0, y: 0 };
  return clientToScene(svgRef.value, clientX, clientY);
}

defineExpose({ scenePointFromClient });

function textBox(g: Record<string, unknown>) {
  const w = Number(g.width);
  const h = Number(g.height);
  return w > 0 && h > 0;
}

function previewLabelPos(p: DrawPreview) {
  if (!p) return { x: 0, y: 0 };
  if (p.kind === "rect") {
    const box = normalizedRect(p.geometry);
    return { x: box.x + box.width / 2, y: box.y - 8 };
  }
  if (p.kind === "ellipse") {
    const cx = Number(p.geometry.cx);
    const cy = Number(p.geometry.cy);
    const ry = Number(p.geometry.ry);
    return { x: cx, y: cy - ry - 8 };
  }
  return { x: 0, y: 0 };
}
</script>

<template>
  <svg
    ref="svgRef"
    class="drawingLayer"
    :class="{
      interactive: layerActive,
      pickMode: canPickDrawing && !canDraw,
      handTool: toolMode === 'hand',
      drawMode: canDraw,
    }"
    :style="{
      ...(drawCursor ? { cursor: drawCursor } : {}),
      zIndex: DRAWING_BAND_BASE,
    }"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @click="onPickClick"
    @contextmenu="onDrawingContextMenu"
  >
    <g
      v-for="drawing in sortedDrawings"
      v-show="drawing.id !== editingDrawingId"
      :key="drawing.id"
      class="drawingItem"
      :class="{ selected: selectedDrawingId === drawing.id }"
    >
      <path
        v-if="drawing.kind === 'brush' && showPickTargets"
        class="hitTarget"
        :d="brushPathFromPoints((drawing.geometry.points as number[][]) || [])"
        fill="none"
        stroke="transparent"
        :stroke-width="pickHitStrokeWidth(drawing)"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        v-if="drawing.kind === 'brush'"
        class="visibleShape"
        :d="brushPathFromPoints((drawing.geometry.points as number[][]) || [])"
        fill="none"
        :stroke="stroke(drawing)"
        :stroke-width="strokeW(drawing)"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <line
        v-if="drawing.kind === 'line' && showPickTargets"
        class="hitTarget"
        :x1="Number(drawing.geometry.x1)"
        :y1="Number(drawing.geometry.y1)"
        :x2="Number(drawing.geometry.x2)"
        :y2="Number(drawing.geometry.y2)"
        stroke="transparent"
        :stroke-width="pickHitStrokeWidth(drawing)"
        stroke-linecap="round"
      />
      <line
        v-if="drawing.kind === 'line'"
        class="visibleShape"
        :x1="Number(drawing.geometry.x1)"
        :y1="Number(drawing.geometry.y1)"
        :x2="Number(drawing.geometry.x2)"
        :y2="Number(drawing.geometry.y2)"
        :stroke="stroke(drawing)"
        :stroke-width="strokeW(drawing)"
        stroke-linecap="round"
      />
      <rect
        v-if="drawing.kind === 'rect' && showPickTargets"
        class="hitTarget"
        :x="Number(drawing.geometry.width) < 0 ? Number(drawing.geometry.x) + Number(drawing.geometry.width) : Number(drawing.geometry.x)"
        :y="Number(drawing.geometry.height) < 0 ? Number(drawing.geometry.y) + Number(drawing.geometry.height) : Number(drawing.geometry.y)"
        :width="Math.abs(Number(drawing.geometry.width))"
        :height="Math.abs(Number(drawing.geometry.height))"
        fill="none"
        stroke="transparent"
        :stroke-width="DRAWING_PICK_STROKE_HIT"
      />
      <rect
        v-if="drawing.kind === 'rect'"
        class="visibleShape"
        :x="Number(drawing.geometry.width) < 0 ? Number(drawing.geometry.x) + Number(drawing.geometry.width) : Number(drawing.geometry.x)"
        :y="Number(drawing.geometry.height) < 0 ? Number(drawing.geometry.y) + Number(drawing.geometry.height) : Number(drawing.geometry.y)"
        :width="Math.abs(Number(drawing.geometry.width))"
        :height="Math.abs(Number(drawing.geometry.height))"
        fill="none"
        :stroke="stroke(drawing)"
        :stroke-width="strokeW(drawing)"
      />
      <ellipse
        v-if="drawing.kind === 'ellipse' && showPickTargets"
        class="hitTarget"
        :cx="Number(drawing.geometry.cx)"
        :cy="Number(drawing.geometry.cy)"
        :rx="Number(drawing.geometry.rx)"
        :ry="Number(drawing.geometry.ry)"
        fill="none"
        stroke="transparent"
        :stroke-width="DRAWING_PICK_STROKE_HIT"
      />
      <ellipse
        v-if="drawing.kind === 'ellipse'"
        class="visibleShape"
        :cx="Number(drawing.geometry.cx)"
        :cy="Number(drawing.geometry.cy)"
        :rx="Number(drawing.geometry.rx)"
        :ry="Number(drawing.geometry.ry)"
        fill="none"
        :stroke="stroke(drawing)"
        :stroke-width="strokeW(drawing)"
      />
      <g
        v-if="drawing.kind === 'text'"
        class="textGroup"
        @dblclick="onTextDblClick(drawing, $event)"
      >
        <rect
          v-if="textBox(drawing.geometry) && showPickTargets"
          class="hitTarget fillHit"
          :x="Number(drawing.geometry.x) - 6"
          :y="Number(drawing.geometry.y) - 6"
          :width="Number(drawing.geometry.width) + 12"
          :height="Number(drawing.geometry.height) + 12"
          fill="rgba(0,0,0,0.001)"
          stroke="transparent"
        />
        <foreignObject
          v-if="textBox(drawing.geometry)"
          :x="Number(drawing.geometry.x)"
          :y="Number(drawing.geometry.y)"
          :width="Number(drawing.geometry.width)"
          :height="Number(drawing.geometry.height)"
        >
          <div
            xmlns="http://www.w3.org/1999/xhtml"
            class="textBoxContent visibleShape"
            :style="{ color: stroke(drawing), fontSize: `${textFontSize(drawing)}px` }"
          >
            {{ drawing.geometry.text }}
          </div>
        </foreignObject>
        <rect
          v-if="!textBox(drawing.geometry) && showPickTargets"
          class="hitTarget fillHit"
          :x="Number(drawing.geometry.x) - 8"
          :y="Number(drawing.geometry.y) - textFontSize(drawing) - 8"
          :width="Math.max(48, String(drawing.geometry.text ?? '').length * textFontSize(drawing) * 0.55 + 16)"
          :height="textFontSize(drawing) * 1.5 + 16"
          fill="rgba(0,0,0,0.001)"
          stroke="transparent"
        />
        <text
          v-if="!textBox(drawing.geometry)"
          class="visibleShape drawTextLegacy"
          :x="Number(drawing.geometry.x)"
          :y="Number(drawing.geometry.y)"
          :fill="stroke(drawing)"
          :font-size="textFontSize(drawing)"
        >
          {{ drawing.geometry.text }}
        </text>
      </g>
    </g>

    <g
      v-if="preview && preview.kind !== 'marquee'"
      class="preview"
      opacity="0.65"
    >
      <path
        v-if="preview.kind === 'brush'"
        :d="brushPathFromPoints((preview.geometry.points as number[][]) || [])"
        fill="none"
        :stroke="stroke(preview)"
        :stroke-width="strokeW(preview)"
        stroke-linecap="round"
      />
      <line
        v-else-if="preview.kind === 'line'"
        :x1="Number(preview.geometry.x1)"
        :y1="Number(preview.geometry.y1)"
        :x2="Number(preview.geometry.x2)"
        :y2="Number(preview.geometry.y2)"
        :stroke="stroke(preview)"
        :stroke-width="strokeW(preview)"
      />
      <rect
        v-else-if="preview.kind === 'rect'"
        :x="normalizedRect(preview.geometry).x"
        :y="normalizedRect(preview.geometry).y"
        :width="normalizedRect(preview.geometry).width"
        :height="normalizedRect(preview.geometry).height"
        fill="none"
        :stroke="stroke(preview)"
        :stroke-width="strokeW(preview)"
        stroke-dasharray="4 3"
      />
      <ellipse
        v-else-if="preview.kind === 'ellipse'"
        :cx="Number(preview.geometry.cx)"
        :cy="Number(preview.geometry.cy)"
        :rx="Number(preview.geometry.rx)"
        :ry="Number(preview.geometry.ry)"
        fill="none"
        :stroke="stroke(preview)"
        :stroke-width="strokeW(preview)"
      />
      <text
        v-if="preview.measureLabel"
        :x="previewLabelPos(preview)!.x"
        :y="previewLabelPos(preview)!.y"
        class="measureLabel"
      >
        {{ preview.measureLabel }}
      </text>
    </g>
    <rect
      v-else-if="preview?.kind === 'marquee'"
      :x="Number(preview.geometry.x)"
      :y="Number(preview.geometry.y)"
      :width="Number(preview.geometry.width)"
      :height="Number(preview.geometry.height)"
      fill="color-mix(in srgb, var(--c-primary) 12%, transparent)"
      stroke="var(--c-primary)"
      stroke-width="1"
      stroke-dasharray="4 3"
    />

  </svg>
</template>

<style scoped>
.drawingLayer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
}

.drawingLayer.interactive.drawMode {
  pointer-events: auto;
}

.drawingLayer.pickMode {
  pointer-events: none;
}

.drawingLayer.pickMode :deep(.hitTarget) {
  pointer-events: stroke;
  cursor: pointer;
}

.drawingLayer.pickMode :deep(.hitTarget.fillHit) {
  pointer-events: all;
}

.drawingLayer.pickMode :deep(.visibleShape),
.drawingLayer.pickMode :deep(.textBoxContent),
.drawingLayer.pickMode :deep(.drawTextLegacy) {
  pointer-events: none;
}

.drawingLayer.pickMode.handTool :deep(.hitTarget) {
  cursor: grab;
}

.drawingLayer.pickMode :deep(.drawingItem:hover .visibleShape),
.drawingLayer.pickMode :deep(.drawingItem.selected .visibleShape) {
  filter: drop-shadow(0 0 4px color-mix(in srgb, var(--c-primary) 80%, transparent));
}

.drawingLayer.pickMode :deep(.drawingItem:hover .textGroup .textBoxContent),
.drawingLayer.pickMode :deep(.drawingItem.selected .textGroup .textBoxContent) {
  filter: drop-shadow(0 0 3px color-mix(in srgb, var(--c-primary) 55%, transparent));
}

.drawingLayer.drawMode {
  cursor: crosshair;
}

.textBoxContent {
  width: 100%;
  height: 100%;
  overflow: visible;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 4px 6px;
  box-sizing: border-box;
  line-height: 1.35;
  user-select: none;
  pointer-events: none;
}

.drawTextLegacy {
  user-select: none;
  pointer-events: none;
}

.measureLabel {
  fill: var(--c-text);
  font-size: 12px;
  font-weight: 600;
  text-anchor: middle;
  paint-order: stroke;
  stroke: var(--c-surface);
  stroke-width: 3px;
  pointer-events: none;
}

</style>
