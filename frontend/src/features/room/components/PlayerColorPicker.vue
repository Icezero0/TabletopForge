<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { PLAYER_COLOR_PRESETS } from "@/features/room/constants/playerColors";

const props = defineProps<{
  modelValue: string | null;
  takenColors?: Set<string> | string[];
  disabled?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [string];
}>();

const { t } = useI18n();

const takenSet = computed(() => {
  if (!props.takenColors) return new Set<string>();
  return props.takenColors instanceof Set
    ? props.takenColors
    : new Set(props.takenColors);
});

function isTaken(color: string) {
  return takenSet.value.has(color) && color !== props.modelValue;
}

function select(color: string) {
  if (props.disabled || isTaken(color)) return;
  emit("update:modelValue", color);
}
</script>

<template>
  <div class="playerColorPicker" role="group" :aria-label="t('room.playerColor.label')">
    <div class="labelBlock">
      <span class="label">{{ t("room.playerColor.label") }}</span>
      <span class="hint">{{ t("room.playerColor.hint") }}</span>
    </div>
    <div class="swatches">
      <button
        v-for="color in PLAYER_COLOR_PRESETS"
        :key="color"
        type="button"
        class="swatch"
        :class="{
          active: modelValue === color,
          taken: isTaken(color),
        }"
        :style="{ '--swatch-color': color }"
        :disabled="disabled || isTaken(color)"
        :title="isTaken(color) ? t('room.playerColor.taken') : color"
        @click="select(color)"
      />
    </div>
  </div>
</template>

<style scoped>
.playerColorPicker {
  display: grid;
  gap: 8px;
}

.labelBlock {
  display: grid;
  gap: 2px;
}

.label {
  font-size: 12px;
  font-weight: 500;
  color: var(--c-text);
}

.hint {
  font-size: 11px;
  color: var(--c-text-muted);
  line-height: 1.4;
}

.swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.swatch {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 2px solid transparent;
  background: var(--swatch-color);
  cursor: pointer;
  padding: 0;
}

.swatch.active {
  border-color: var(--c-text);
  box-shadow: 0 0 0 2px var(--c-surface);
}

.swatch.taken {
  opacity: 0.35;
  cursor: not-allowed;
}

.swatch:disabled {
  cursor: not-allowed;
}
</style>
