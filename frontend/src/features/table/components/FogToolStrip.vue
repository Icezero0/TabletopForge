<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { FogSubTool } from "@/features/table/types";

const props = defineProps<{
  subTool: FogSubTool;
  brushRadius: number;
}>();

const emit = defineEmits<{
  "update:subTool": [FogSubTool];
  "update:brushRadius": [number];
}>();

const { t } = useI18n();

const tools: { id: FogSubTool; labelKey: string }[] = [
  { id: "erase", labelKey: "table.fog.erase" },
  { id: "fill", labelKey: "table.fog.fill" },
];

const BRUSH_RADIUS_MIN = 12;
const BRUSH_RADIUS_MAX = 180;
const BRUSH_RADIUS_STEP = 6;

function setBrushRadius(raw: string) {
  const value = Number(raw);
  if (!Number.isFinite(value)) return;
  emit(
    "update:brushRadius",
    Math.min(BRUSH_RADIUS_MAX, Math.max(BRUSH_RADIUS_MIN, value)),
  );
}
</script>

<template>
  <div class="fogToolStrip" role="toolbar" :aria-label="t('table.fog.toolbar')">
    <div class="toolGroup">
      <button
        v-for="tool in tools"
        :key="tool.id"
        type="button"
        class="subBtn"
        :class="{ active: subTool === tool.id }"
        :title="t(tool.labelKey)"
        @click="emit('update:subTool', tool.id)"
      >
        {{ t(tool.labelKey) }}
      </button>
    </div>
    <label class="brushControl">
      <span>{{ t("table.fog.brushSize") }}</span>
      <input
        type="range"
        :min="BRUSH_RADIUS_MIN"
        :max="BRUSH_RADIUS_MAX"
        :step="BRUSH_RADIUS_STEP"
        :value="brushRadius"
        @input="setBrushRadius(($event.target as HTMLInputElement).value)"
      />
      <span class="value">{{ brushRadius }}px</span>
    </label>
  </div>
</template>

<style scoped>
.fogToolStrip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 6px 8px;
}

.toolGroup {
  display: flex;
  align-items: center;
  gap: 4px;
}

.brushControl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding-left: 6px;
  border-left: 1px solid var(--c-border);
  color: var(--c-text-muted);
  font-size: 12px;
}

.brushControl input {
  width: 96px;
  accent-color: var(--c-primary);
}

.value {
  min-width: 44px;
  text-align: center;
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
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
</style>
