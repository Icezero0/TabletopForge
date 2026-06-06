<script setup lang="ts">
import { useI18n } from "vue-i18n";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";

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
      <BaseTextarea
        :rows="3"
        :placeholder="t(`character.flavor.${field}Placeholder`)"
        :model-value="(modelValue[field] as string) ?? ''"
        @update:model-value="update(field, $event)"
      />
    </div>
    <div class="field">
      <label class="label">{{ t("character.flavor.backstory") }}</label>
      <BaseTextarea
        :rows="8"
        min-height="160px"
        :placeholder="t('character.flavor.backstoryPlaceholder')"
        :model-value="(modelValue.backstory as string) ?? ''"
        @update:model-value="update('backstory', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 20px; }
.field { display: grid; gap: 5px; }
.label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }</style>
