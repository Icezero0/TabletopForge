<script setup lang="ts">
const props = defineProps<{
  modelValue: string;
  placeholder?: string;
  min?: number;
  max?: number;
  disabled?: boolean;
  compact?: boolean;
}>();

const emit = defineEmits<{ (e: "update:modelValue", v: string): void }>();

function step(delta: number) {
  const current = parseInt(props.modelValue, 10);
  const next = (isNaN(current) ? 0 : current) + delta;
  if (props.min !== undefined && next < props.min) return;
  if (props.max !== undefined && next > props.max) return;
  emit("update:modelValue", String(next));
}
</script>

<template>
  <div class="wrap" :class="{ disabled, compact }">
    <button
      type="button"
      class="stepBtn"
      tabindex="-1"
      :disabled="disabled"
      @mousedown.prevent="step(-1)"
    >−</button>
    <input
      class="inp"
      type="text"
      inputmode="numeric"
      pattern="[0-9\-]*"
      :placeholder="placeholder"
      :disabled="disabled"
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <button
      type="button"
      class="stepBtn"
      tabindex="-1"
      :disabled="disabled"
      @mousedown.prevent="step(1)"
    >+</button>
  </div>
</template>

<style scoped>
.wrap {
  display: flex;
  align-items: stretch;
  height: 40px;
  min-width: 0;
  width: 100%;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface);
  overflow: hidden;
  transition: border-color 0.15s;
}

.wrap:focus-within {
  border-color: var(--c-accent, var(--c-primary));
}

.wrap.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.stepBtn {
  width: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  transition: background 0.12s, color 0.12s;
  user-select: none;
}

.compact .stepBtn {
  width: 22px;
}

.stepBtn:hover {
  background: var(--c-hover);
  color: var(--c-text);
}

.stepBtn:first-child {
  border-right: 1px solid var(--c-border);
}

.stepBtn:last-child {
  border-left: 1px solid var(--c-border);
}

.inp {
  flex: 1;
  min-width: 0;
  padding: 0 8px;
  border: none;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  text-align: center;
  outline: none;
}

.inp::placeholder {
  color: var(--c-text-muted);
}
</style>
