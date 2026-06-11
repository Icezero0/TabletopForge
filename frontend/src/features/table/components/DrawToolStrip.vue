<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { DrawSubTool, ShapeDrawMode } from "@/features/table/drawingTypes";

const props = defineProps<{
  subTool: DrawSubTool;
  strokeColor: string;
  strokeWidth: number;
  fontSize: number;
  shapeMode: ShapeDrawMode;
  maskOpacity: number;
}>();

const emit = defineEmits<{
  "update:subTool": [DrawSubTool];
  "update:strokeColor": [string];
  "update:strokeWidth": [number];
  "update:fontSize": [number];
  "update:shapeMode": [ShapeDrawMode];
  "update:maskOpacity": [number];
}>();

const { t } = useI18n();

const tools: { id: DrawSubTool; labelKey: string }[] = [
  { id: "brush", labelKey: "table.draw.brush" },
  { id: "line", labelKey: "table.draw.line" },
  { id: "rect", labelKey: "table.draw.rect" },
  { id: "ellipse", labelKey: "table.draw.ellipse" },
  { id: "text", labelKey: "table.draw.text" },
  { id: "boxSelect", labelKey: "table.draw.boxSelect" },
];

function selectSubTool(id: DrawSubTool) {
  emit("update:subTool", id);
}

const STROKE_WIDTH_MIN = 1;
const STROKE_WIDTH_MAX = 48;

function setStrokeWidth(raw: string) {
  const value = Number(raw);
  if (!Number.isFinite(value)) return;
  emit("update:strokeWidth", Math.min(STROKE_WIDTH_MAX, Math.max(STROKE_WIDTH_MIN, value)));
}

function bumpFontSize(delta: number) {
  emit("update:fontSize", Math.max(10, props.fontSize + delta));
}

function setMaskOpacity(raw: string) {
  const value = Number(raw);
  if (!Number.isFinite(value)) return;
  emit("update:maskOpacity", Math.min(1, Math.max(0, value / 100)));
}
</script>

<template>
  <div class="drawToolStrip" role="toolbar" :aria-label="t('table.draw.toolbar')">
    <div class="toolGroup">
      <button
        v-for="tool in tools"
        :key="tool.id"
        type="button"
        class="subBtn"
        :class="{ active: subTool === tool.id }"
        :title="t(tool.labelKey)"
        @click="selectSubTool(tool.id)"
      >
        {{ t(tool.labelKey) }}
      </button>
    </div>
    <div
      v-if="subTool !== 'text' && subTool !== 'boxSelect'"
      class="styleGroup"
    >
      <label class="colorLabel">
        <span class="srOnly">{{ t("table.draw.color") }}</span>
        <input
          type="color"
          :value="strokeColor"
          @input="emit('update:strokeColor', ($event.target as HTMLInputElement).value)"
        />
      </label>
      <label class="strokeControl">
        <span>{{ t("table.draw.brushSize") }}</span>
        <input
          type="range"
          :min="STROKE_WIDTH_MIN"
          :max="STROKE_WIDTH_MAX"
          step="1"
          :value="strokeWidth"
          @input="setStrokeWidth(($event.target as HTMLInputElement).value)"
        />
        <span class="value">{{ strokeWidth }}px</span>
      </label>
    </div>
    <div
      v-if="subTool === 'rect' || subTool === 'ellipse'"
      class="styleGroup shapeOptions"
    >
      <div class="segmented">
        <button
          type="button"
          class="segBtn"
          :class="{ active: shapeMode === 'outline' }"
          @click="emit('update:shapeMode', 'outline')"
        >
          {{ t("table.draw.outline") }}
        </button>
        <button
          type="button"
          class="segBtn"
          :class="{ active: shapeMode === 'mask' }"
          @click="emit('update:shapeMode', 'mask')"
        >
          {{ t("table.draw.mask") }}
        </button>
      </div>
      <label v-if="shapeMode === 'mask'" class="opacityControl">
        <span>{{ t("table.draw.opacity") }}</span>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          :value="Math.round(maskOpacity * 100)"
          @input="setMaskOpacity(($event.target as HTMLInputElement).value)"
        />
        <span class="value">{{ Math.round(maskOpacity * 100) }}%</span>
      </label>
    </div>
    <div
      v-if="subTool === 'text'"
      class="styleGroup"
    >
      <label class="colorLabel">
        <input
          type="color"
          :value="strokeColor"
          @input="emit('update:strokeColor', ($event.target as HTMLInputElement).value)"
        />
      </label>
      <button type="button" class="subBtn" @click="bumpFontSize(-2)">−</button>
      <span class="value">{{ fontSize }}px</span>
      <button type="button" class="subBtn" @click="bumpFontSize(2)">+</button>
    </div>
  </div>
</template>

<style scoped>
.drawToolStrip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 6px 8px;
}

.toolGroup,
.styleGroup {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.subBtn {
  height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 12px;
  cursor: pointer;
}

.subBtn:hover {
  background: color-mix(in srgb, var(--c-primary) 10%, transparent);
  color: var(--c-text);
}

.shapeOptions {
  padding-left: 6px;
  border-left: 1px solid var(--c-border);
}

.segmented {
  display: inline-flex;
  padding: 2px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-bg-subtle) 76%, transparent);
}

.segBtn {
  height: 26px;
  padding: 0 9px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 12px;
  cursor: pointer;
}

.segBtn.active {
  background: color-mix(in srgb, var(--c-primary) 18%, transparent);
  color: var(--c-text);
}

.opacityControl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.opacityControl input {
  width: 86px;
  accent-color: var(--c-primary);
}

.strokeControl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.strokeControl input {
  width: 96px;
  accent-color: var(--c-primary);
}

.subBtn.active {
  background: color-mix(in srgb, var(--c-primary) 18%, transparent);
  border-color: color-mix(in srgb, var(--c-primary) 35%, transparent);
  color: var(--c-text);
}

.colorLabel input {
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}

.value {
  min-width: 40px;
  text-align: center;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.srOnly {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
