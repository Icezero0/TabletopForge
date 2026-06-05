<script setup lang="ts">
import { useI18n } from "vue-i18n";

const props = defineProps<{ modelValue: Record<string, unknown> }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function setNotes(v: string) {
  emit("update:modelValue", { ...props.modelValue, notes: v });
}
</script>

<template>
  <div class="tab-content">
    <div class="field">
      <label class="label">{{ t("character.extras.notes") }}</label>
      <textarea
        class="notes-area"
        :value="(modelValue.notes as string) ?? ''"
        @input="setNotes(($event.target as HTMLTextAreaElement).value)"
      />
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 10px; }
.field { display: grid; gap: 6px; }
.label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }
.notes-area {
  width: 100%; min-height: 200px; resize: vertical;
  border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text);
  padding: 10px 12px; font-size: 13px; font-family: inherit;
  outline: none; line-height: 1.6;
}
.notes-area:focus { border-color: var(--c-accent); }
.notes-area::placeholder { color: var(--c-text-muted); }
</style>
