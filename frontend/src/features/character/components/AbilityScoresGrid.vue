<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ABILITY_KEYS, ABILITY_LABEL_KEYS, abilityMod, fmtMod } from "@/features/character/constants";

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
      <div class="score-stepper">
        <button
          class="score-step-btn"
          @click="setScore(ability, String(Math.max(1, (modelValue[ability] ?? 10) - 1)))"
        >−</button>
        <input
          type="number"
          class="score-input"
          :value="modelValue[ability] ?? 10"
          @change="setScore(ability, ($event.target as HTMLInputElement).value)"
        />
        <button
          class="score-step-btn"
          @click="setScore(ability, String(Math.min(30, (modelValue[ability] ?? 10) + 1)))"
        >+</button>
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
.score-stepper { display: flex; align-items: center; gap: 2px; }
.score-step-btn {
  background: var(--c-surface-raised);
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  color: var(--c-text-muted);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  padding: 2px 6px;
  height: 32px;
  transition: background 0.12s, color 0.12s;
  flex-shrink: 0;
}
.score-step-btn:hover { background: var(--c-hover); color: var(--c-text); }
.score-input {
  width: 36px;
  text-align: center;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface-raised);
  color: var(--c-text);
  font-size: 16px;
  font-weight: 600;
  padding: 4px 2px;
  outline: none;
  -moz-appearance: textfield;
}
.score-input:focus { border-color: var(--c-accent); }
.score-input::-webkit-outer-spin-button,
.score-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.score-mod { font-size: 14px; font-weight: 500; color: var(--c-text); }
</style>
