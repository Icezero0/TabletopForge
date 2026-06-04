<script setup lang="ts">
import { useI18n } from "vue-i18n";
import {
  ArrowUpLeftIcon,
  CursorArrowRaysIcon,
  HandRaisedIcon,
  MinusIcon,
  PencilSquareIcon,
  PlusIcon,
  ArrowsPointingOutIcon,
} from "@heroicons/vue/24/outline";
import type { TableToolMode } from "@/features/table/types";

const props = defineProps<{
  modelValue: TableToolMode;
  disabledTools?: TableToolMode[];
  gridCellPx?: number;
  gridCellFt?: number;
  canIncreaseGrid?: boolean;
  canDecreaseGrid?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [TableToolMode];
  increaseGrid: [];
  decreaseGrid: [];
}>();

const { t } = useI18n();

const tools: { mode: TableToolMode; labelKey: string; icon: typeof HandRaisedIcon }[] = [
  { mode: "select", labelKey: "table.tools.select", icon: ArrowUpLeftIcon },
  { mode: "hand", labelKey: "table.tools.hand", icon: HandRaisedIcon },
  { mode: "draw", labelKey: "table.tools.draw", icon: PencilSquareIcon },
  { mode: "pointer", labelKey: "table.tools.pointer", icon: CursorArrowRaysIcon },
];

function isDisabled(mode: TableToolMode) {
  return props.disabledTools?.includes(mode) ?? false;
}

function selectTool(mode: TableToolMode) {
  if (isDisabled(mode)) return;
  emit("update:modelValue", mode);
}
</script>

<template>
  <div class="topToolBar" role="toolbar" :aria-label="t('table.tools.toolbar')">
    <div class="toolGroup">
      <button
        v-for="tool in tools"
        :key="tool.mode"
        type="button"
        class="toolBtn"
        :class="{ active: modelValue === tool.mode, disabled: isDisabled(tool.mode) }"
        :disabled="isDisabled(tool.mode)"
        :title="t(tool.labelKey)"
        @click="selectTool(tool.mode)"
      >
        <component :is="tool.icon" class="toolIcon" aria-hidden="true" />
        <span class="toolLabel">{{ t(tool.labelKey) }}</span>
      </button>
    </div>

    <div
      v-if="gridCellPx != null"
      class="scaleControl"
      role="group"
      :aria-label="t('table.tools.gridScale')"
    >
      <span class="scaleControlLabel">{{ t("table.tools.gridScale") }}</span>
      <button
        type="button"
        class="toolBtn scaleBtn"
        :disabled="!canDecreaseGrid"
        :title="t('table.tools.gridScaleDecrease')"
        @click="emit('decreaseGrid')"
      >
        <MinusIcon class="toolIcon" aria-hidden="true" />
      </button>
      <span class="scaleValue">{{ t("table.tools.gridScaleValue", { ft: gridCellFt, px: gridCellPx }) }}</span>
      <button
        type="button"
        class="toolBtn scaleBtn"
        :disabled="!canIncreaseGrid"
        :title="t('table.tools.gridScaleIncrease')"
        @click="emit('increaseGrid')"
      >
        <PlusIcon class="toolIcon" aria-hidden="true" />
      </button>
    </div>

    <button
      type="button"
      class="toolBtn measureBtn"
      disabled
      :title="t('table.tools.measureDisabledHint')"
    >
      <ArrowsPointingOutIcon class="toolIcon" aria-hidden="true" />
      <span class="toolLabel">{{ t("table.tools.measure") }}</span>
    </button>
  </div>
</template>

<style scoped>
.topToolBar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 4px 8px;
}

.toolGroup {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.toolBtn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 13px;
  cursor: pointer;
}

.toolBtn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 10%, transparent);
  color: var(--c-text);
}

.toolBtn.active {
  background: color-mix(in srgb, var(--c-primary) 18%, transparent);
  border-color: color-mix(in srgb, var(--c-primary) 35%, transparent);
  color: var(--c-text);
}

.toolBtn:disabled,
.toolBtn.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.scaleControl {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px 0 10px;
  border-left: 1px solid color-mix(in srgb, var(--c-border) 80%, transparent);
  margin-left: 4px;
}

.scaleControlLabel {
  font-size: 12px;
  color: var(--c-text-muted);
  white-space: nowrap;
}

.scaleValue {
  min-width: 72px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
}

.scaleBtn {
  padding: 0 8px;
}

.measureBtn {
  margin-left: auto;
}

.toolIcon {
  width: 18px;
  height: 18px;
}

@media (max-width: 720px) {
  .toolLabel {
    display: none;
  }

  .toolBtn {
    padding: 0 10px;
  }
}
</style>
