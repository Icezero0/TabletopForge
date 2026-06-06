<script setup lang="ts">
import { useI18n } from "vue-i18n";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";

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
      <BaseTextarea
        :model-value="(modelValue.notes as string) ?? ''"
        min-height="200px"
        @update:model-value="setNotes"
      />
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 10px; }
.field { display: grid; gap: 6px; }
.label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }</style>
