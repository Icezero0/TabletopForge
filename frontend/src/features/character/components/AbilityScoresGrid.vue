<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ABILITY_KEYS, ABILITY_LABEL_KEYS, abilityMod, fmtMod } from "@/features/character/constants";
import BaseNumberInput from "@/ui/base/BaseNumberInput.vue";

const props = defineProps<{
  modelValue: Record<string, number>;
}>();
const emit = defineEmits<{
  (e: "update:modelValue", v: Record<string, number>): void;
}>();
const { t } = useI18n();

function setScore(ability: string, raw: string) {
  const n = parseInt(raw);
  emit("update:modelValue", { ...props.modelValue, [ability]: isNaN(n) ? 10 : n });
}
</script>

<template>
  <div class="scores-grid">
    <div v-for="ability in ABILITY_KEYS" :key="ability" class="score-box">
      <div class="score-label">{{ t(ABILITY_LABEL_KEYS[ability]) }}</div>
      <div class="score-input-wrap">
        <BaseNumberInput
          compact
          :model-value="String(modelValue[ability] ?? 10)"
          :min="1"
          :max="30"
          @update:model-value="setScore(ability, $event)"
        />
      </div>
      <div class="score-mod">{{ fmtMod(abilityMod(modelValue[ability] ?? 10)) }}</div>
    </div>
  </div>
</template>

<style scoped>
.scores-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.score-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  padding: 8px 4px;
  background: var(--c-surface);
}
.score-label {
  font-size: 11px;
  color: var(--c-text-muted);
  text-align: center;
}
.score-input-wrap { width: 100px; }
.score-mod { font-size: 14px; font-weight: 500; color: var(--c-text); }
</style>
