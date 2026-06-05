<script setup lang="ts">
import { useI18n } from "vue-i18n";

const props = defineProps<{ modelValue: Record<string, unknown> }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function update(key: string, value: string) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}
</script>

<template>
  <div class="tab-content">
    <div v-for="field in ['personality', 'ideals', 'bonds', 'flaws']" :key="field" class="field">
      <label class="label">{{ t(`character.flavor.${field}`) }}</label>
      <textarea
        class="sheet-textarea"
        rows="3"
        :placeholder="t(`character.flavor.${field}Placeholder`)"
        :value="(modelValue[field] as string) ?? ''"
        @input="update(field, ($event.target as HTMLTextAreaElement).value)"
      />
    </div>
    <div class="field">
      <label class="label">{{ t("character.flavor.backstory") }}</label>
      <textarea
        class="sheet-textarea tall"
        rows="8"
        :placeholder="t('character.flavor.backstoryPlaceholder')"
        :value="(modelValue.backstory as string) ?? ''"
        @input="update('backstory', ($event.target as HTMLTextAreaElement).value)"
      />
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 20px; }
.field { display: grid; gap: 5px; }
.label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }
.sheet-textarea {
  width: 100%; box-sizing: border-box; padding: 8px 10px; border: 1px solid var(--c-border);
  border-radius: var(--r-1); background: var(--c-surface); color: var(--c-text);
  font-size: 13px; font-family: inherit; resize: vertical; outline: none; transition: border-color 0.15s;
}
.sheet-textarea:focus { border-color: var(--c-accent); }
.sheet-textarea::placeholder { color: var(--c-text-muted); }
.sheet-textarea.tall { min-height: 160px; }
</style>
