<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    rows?: number;
    minHeight?: string;
    resize?: "none" | "vertical" | "both";
    disabled?: boolean;
  }>(),
  { resize: "vertical" },
);

defineEmits<{ (e: "update:modelValue", v: string): void }>();
</script>

<template>
  <textarea
    class="textarea"
    :style="minHeight ? { minHeight } : undefined"
    :rows="rows"
    :placeholder="placeholder"
    :disabled="disabled"
    :value="modelValue"
    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>

<style scoped>
.textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text);
  font-size: 13px;
  font-family: inherit;
  line-height: 1.6;
  outline: none;
  transition: border-color 0.15s;
  resize: v-bind(resize);
  scrollbar-width: none;
}

.textarea::-webkit-scrollbar {
  display: none;
}

.textarea:focus {
  border-color: var(--c-accent, var(--c-primary));
}

.textarea::placeholder {
  color: var(--c-text-muted);
}

.textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
