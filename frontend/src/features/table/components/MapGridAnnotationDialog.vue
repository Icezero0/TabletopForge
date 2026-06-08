<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { XMarkIcon } from "@heroicons/vue/24/outline";
import BaseDialog from "@/ui/base/BaseDialog.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

type GridSample = { x: number; y: number; width: number; height: number };

const props = defineProps<{
  modelValue: boolean;
  assetId: number | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  annotate: [payload: { calibration: GridSample[] }];
  cancel: [];
}>();

const { t } = useI18n();

const assetIdRef = computed(() => props.assetId);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetIdRef);

// --- viewer state ---
const containerRef = ref<HTMLElement | null>(null);
const viewScale = ref(1);
const viewOffsetX = ref(0);
const viewOffsetY = ref(0);
const naturalWidth = ref(0);
const naturalHeight = ref(0);
const mode = ref<"pan" | "mark">("pan");

// --- drawing state ---
const drawStartX = ref(0);
const drawStartY = ref(0);
const drawing = ref<GridSample | null>(null); // in-progress rectangle
const samples = ref<GridSample[]>([]);        // committed rectangles
let activePointer: number | null = null;
let panOriginX = 0;
let panOriginY = 0;
let panStartClientX = 0;
let panStartClientY = 0;
let isDrawing = false;

// --- reset on open ---
watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      samples.value = [];
      drawing.value = null;
      mode.value = "pan";
      naturalWidth.value = 0;
      naturalHeight.value = 0;
    }
  },
);

// --- derived ---
const avgWidth = computed(() => {
  if (samples.value.length === 0) return null;
  return Math.round(samples.value.reduce((a, s) => a + s.width, 0) / samples.value.length * 10) / 10;
});
const avgHeight = computed(() => {
  if (samples.value.length === 0) return null;
  return Math.round(samples.value.reduce((a, s) => a + s.height, 0) / samples.value.length * 10) / 10;
});

function clientToImage(clientX: number, clientY: number) {
  const rect = containerRef.value?.getBoundingClientRect();
  if (!rect) return { x: 0, y: 0 };
  return {
    x: (clientX - rect.left - viewOffsetX.value) / viewScale.value,
    y: (clientY - rect.top - viewOffsetY.value) / viewScale.value,
  };
}

function onImageLoad(event: Event) {
  const img = event.target as HTMLImageElement;
  const container = containerRef.value;
  if (!container) return;
  naturalWidth.value = img.naturalWidth;
  naturalHeight.value = img.naturalHeight;
  const cw = container.clientWidth;
  const ch = container.clientHeight;
  const padding = 40;
  const fitScale = Math.min((cw - padding) / img.naturalWidth, (ch - padding) / img.naturalHeight, 1);
  viewScale.value = fitScale;
  viewOffsetX.value = (cw - img.naturalWidth * fitScale) / 2;
  viewOffsetY.value = (ch - img.naturalHeight * fitScale) / 2;
}

function onWheel(event: WheelEvent) {
  const container = containerRef.value;
  if (!container) return;
  const rect = container.getBoundingClientRect();
  const cx = event.clientX - rect.left;
  const cy = event.clientY - rect.top;
  const delta = -event.deltaY * 0.001;
  const oldScale = viewScale.value;
  const newScale = Math.min(8, Math.max(0.1, oldScale * (1 + delta)));
  viewOffsetX.value = cx - ((cx - viewOffsetX.value) * newScale) / oldScale;
  viewOffsetY.value = cy - ((cy - viewOffsetY.value) * newScale) / oldScale;
  viewScale.value = newScale;
}

function onPointerDown(event: PointerEvent) {
  if (event.button !== 0) return;
  activePointer = event.pointerId;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);

  if (mode.value === "pan") {
    panStartClientX = event.clientX;
    panStartClientY = event.clientY;
    panOriginX = viewOffsetX.value;
    panOriginY = viewOffsetY.value;
    isDrawing = false;
  } else {
    const { x, y } = clientToImage(event.clientX, event.clientY);
    drawStartX.value = x;
    drawStartY.value = y;
    drawing.value = null;
    isDrawing = true;
  }
}

function onPointerMove(event: PointerEvent) {
  if (activePointer !== event.pointerId) return;

  if (mode.value === "pan" && !isDrawing) {
    viewOffsetX.value = panOriginX + (event.clientX - panStartClientX);
    viewOffsetY.value = panOriginY + (event.clientY - panStartClientY);
  } else if (isDrawing) {
    const { x: imgX, y: imgY } = clientToImage(event.clientX, event.clientY);
    const dx = imgX - drawStartX.value;
    const dy = imgY - drawStartY.value;
    if (Math.max(Math.abs(dx), Math.abs(dy)) >= 4) {
      drawing.value = {
        x: dx >= 0 ? drawStartX.value : drawStartX.value + dx,
        y: dy >= 0 ? drawStartY.value : drawStartY.value + dy,
        width: Math.abs(dx),
        height: Math.abs(dy),
      };
    }
  }
}

function onPointerUp(event: PointerEvent) {
  if (activePointer !== event.pointerId) return;
  activePointer = null;
  isDrawing = false;
  (event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);
  // commit in-progress rectangle if both dimensions are meaningful
  if (drawing.value && drawing.value.width >= 4 && drawing.value.height >= 4) {
    samples.value.push(drawing.value);
  }
  drawing.value = null;
}

function removeLast() {
  samples.value.pop();
}

function clearAll() {
  samples.value = [];
}

const wrapperStyle = computed(() => ({
  transform: `translate(${viewOffsetX.value}px, ${viewOffsetY.value}px)`,
  position: "absolute" as const,
  top: 0,
  left: 0,
}));

const imageStyle = computed(() =>
  naturalWidth.value
    ? { width: `${naturalWidth.value * viewScale.value}px`, height: `${naturalHeight.value * viewScale.value}px` }
    : {},
);

function squareStyle(s: GridSample) {
  const vs = viewScale.value;
  return {
    position: "absolute" as const,
    left: `${s.x * vs}px`,
    top: `${s.y * vs}px`,
    width: `${s.width * vs}px`,
    height: `${s.height * vs}px`,
  };
}

const drawingStyle = computed(() => {
  const d = drawing.value;
  if (!d) return null;
  const vs = viewScale.value;
  return {
    position: "absolute" as const,
    left: `${d.x * vs}px`,
    top: `${d.y * vs}px`,
    width: `${d.width * vs}px`,
    height: `${d.height * vs}px`,
  };
});

function onConfirm() {
  if (samples.value.length === 0) return;
  emit("annotate", { calibration: [...samples.value] });
  emit("update:modelValue", false);
}

// X button: cancel the upload entirely
function onCancel() {
  emit("cancel");
  emit("update:modelValue", false);
}

// Skip button: keep the map, just without annotation
function onSkip() {
  emit("update:modelValue", false);
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :max-width="760" :aria-label="t('table.map.gridAnnotationTitle')" @update:model-value="onCancel">
    <div class="card">
      <div class="header">
        <span class="title">{{ t("table.map.gridAnnotationTitle") }}</span>
        <button type="button" class="closeBtn" @click="onCancel">
          <AppIcon :icon="XMarkIcon" :size="18" />
        </button>
      </div>

      <div class="hint">{{ t("table.map.gridAnnotationHint") }}</div>

      <div class="modeBar">
        <button type="button" class="modeBtn" :class="{ active: mode === 'pan' }" @click="mode = 'pan'">
          {{ t("table.map.gridAnnotationModePan") }}
        </button>
        <button type="button" class="modeBtn" :class="{ active: mode === 'mark' }" @click="mode = 'mark'">
          {{ t("table.map.gridAnnotationModeMark") }}
        </button>
        <span v-if="samples.length > 0 || drawing" class="sizeHint">
          <template v-if="avgWidth != null">
            {{ t("table.map.gridAnnotationAvg", { n: samples.length, w: avgWidth, h: avgHeight }) }}
          </template>
          <template v-else-if="drawing">
            {{ Math.round(drawing.width) }}×{{ Math.round(drawing.height) }} px
          </template>
        </span>
        <div class="modeBarActions">
          <button v-if="samples.length > 0" type="button" class="actionBtn" @click="removeLast">
            {{ t("table.map.gridAnnotationRemoveLast") }}
          </button>
          <button v-if="samples.length > 1" type="button" class="actionBtn" @click="clearAll">
            {{ t("table.map.gridAnnotationClearAll") }}
          </button>
        </div>
      </div>

      <div
        ref="containerRef"
        class="viewer"
        :class="{ panCursor: mode === 'pan', markCursor: mode === 'mark' }"
        @wheel.prevent="onWheel"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      >
        <div :style="wrapperStyle">
          <img
            v-if="imageUrl"
            :src="imageUrl"
            :style="imageStyle"
            alt=""
            draggable="false"
            class="mapImg"
            @load="onImageLoad"
          />
          <!-- committed samples -->
          <div
            v-for="(s, i) in samples"
            :key="i"
            class="squareOverlay"
            :style="squareStyle(s)"
          >
            <span class="squareIndex">{{ i + 1 }}</span>
          </div>
          <!-- in-progress drawing -->
          <div v-if="drawingStyle" class="squareOverlay drawingOverlay" :style="drawingStyle" />
        </div>
      </div>

      <div class="footer">
        <button type="button" class="skipBtn" @click="onSkip">
          {{ t("common.skip") }}
        </button>
        <button type="button" class="confirmBtn" :disabled="samples.length === 0" @click="onConfirm">
          {{ t("common.confirm") }}
        </button>
      </div>
    </div>
  </BaseDialog>
</template>

<style scoped>
.card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 16px;
  box-shadow: 0 10px 32px rgb(0 0 0 / 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 80vh;
  max-height: 680px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--c-border);
  gap: 12px;
  flex-shrink: 0;
}

.title {
  font-size: 15px;
  font-weight: 650;
  color: var(--c-text);
}

.closeBtn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
  border-radius: 6px;
  flex-shrink: 0;
}
.closeBtn:hover { background: var(--c-hover); color: var(--c-text); }

.hint {
  padding: 8px 20px;
  font-size: 12px;
  color: var(--c-text-muted);
  flex-shrink: 0;
}

.modeBar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 20px;
  border-bottom: 1px solid var(--c-border);
  flex-shrink: 0;
}

.modeBtn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 12px;
  cursor: pointer;
}
.modeBtn:hover { background: var(--c-hover); color: var(--c-text); }
.modeBtn.active {
  background: color-mix(in srgb, var(--c-primary) 15%, transparent);
  border-color: color-mix(in srgb, var(--c-primary) 35%, transparent);
  color: var(--c-text);
}

.sizeHint {
  margin-left: 4px;
  font-size: 12px;
  color: var(--c-text-muted);
  font-variant-numeric: tabular-nums;
}

.modeBarActions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.actionBtn {
  height: 24px;
  padding: 0 8px;
  border-radius: 5px;
  border: 1px solid var(--c-border);
  background: transparent;
  color: var(--c-text-muted);
  font-size: 11px;
  cursor: pointer;
}
.actionBtn:hover { background: var(--c-hover); color: var(--c-text); }

.viewer {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  background: color-mix(in srgb, var(--c-bg) 60%, transparent);
  user-select: none;
}

.viewer.panCursor { cursor: grab; }
.viewer.panCursor:active { cursor: grabbing; }
.viewer.markCursor { cursor: crosshair; }

.mapImg {
  display: block;
  max-width: none;
  pointer-events: none;
}

.squareOverlay {
  box-sizing: border-box;
  border: 1px solid var(--c-primary);
  background: color-mix(in srgb, var(--c-primary) 8%, transparent);
  pointer-events: none;
}

.drawingOverlay {
  opacity: 0.6;
}

.squareIndex {
  position: absolute;
  top: 2px;
  left: 4px;
  font-size: 10px;
  font-weight: 700;
  color: var(--c-primary);
  line-height: 1;
  pointer-events: none;
}

.footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--c-border);
  flex-shrink: 0;
}

.skipBtn {
  height: 36px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: transparent;
  color: var(--c-text-muted);
  font-size: 13px;
  cursor: pointer;
}
.skipBtn:hover { background: var(--c-hover); color: var(--c-text); }

.confirmBtn {
  height: 36px;
  padding: 0 16px;
  border-radius: 8px;
  border: none;
  background: var(--c-primary);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}
.confirmBtn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.confirmBtn:not(:disabled):hover {
  opacity: 0.88;
}
</style>
