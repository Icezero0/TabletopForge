<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { DrawSubTool } from "@/features/table/drawingTypes";

const props = defineProps<{
  subTool: DrawSubTool;
  strokeColor: string;
  strokeWidth: number;
  fontSize: number;
}>();

const emit = defineEmits<{
  "update:subTool": [DrawSubTool];
  "update:strokeColor": [string];
  "update:strokeWidth": [number];
  "update:fontSize": [number];
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

function bumpWidth(delta: number) {
  emit("update:strokeWidth", Math.min(24, Math.max(1, props.strokeWidth + delta)));
}

function bumpFontSize(delta: number) {
  emit("update:fontSize", Math.max(10, props.fontSize + delta));
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
      <button type="button" class="subBtn" @click="bumpWidth(-1)">−</button>
      <span class="value">{{ strokeWidth }}px</span>
      <button type="button" class="subBtn" @click="bumpWidth(1)">+</button>
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
