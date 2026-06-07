<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { MeasureSubTool } from "@/features/table/types";

const props = defineProps<{
  subTool: MeasureSubTool;
}>();

const emit = defineEmits<{
  "update:subTool": [MeasureSubTool];
}>();

const { t } = useI18n();

const tools: { id: MeasureSubTool; labelKey: string }[] = [
  { id: "line", labelKey: "table.measure.line" },
  { id: "route", labelKey: "table.measure.route" },
];
</script>

<template>
  <div class="measureToolStrip" role="toolbar" :aria-label="t('table.measure.toolbar')">
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
  </div>
</template>

<style scoped>
.measureToolStrip {
  display: flex;
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
