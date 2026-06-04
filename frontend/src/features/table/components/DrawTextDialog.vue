<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import BaseButton from "@/ui/base/BaseButton.vue";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  confirm: [text: string];
  cancel: [];
}>();

const { t } = useI18n();
const text = ref("");

watch(
  () => props.open,
  (open) => {
    if (open) text.value = "";
  },
);

function submit() {
  emit("confirm", text.value);
}

function cancel() {
  emit("cancel");
}
</script>

<template>
  <div
    v-if="open"
    class="drawTextBackdrop"
    @click.self="cancel"
  >
    <div class="drawTextPanel" role="dialog">
      <label class="label">{{ t("table.draw.textPrompt") }}</label>
      <textarea
        v-model="text"
        class="input"
        rows="3"
        autofocus
        @keydown.enter.ctrl="submit"
      />
      <div class="actions">
        <BaseButton variant="default" @click="cancel">{{ t("common.cancel") }}</BaseButton>
        <BaseButton variant="primary" @click="submit">{{ t("table.draw.placeText") }}</BaseButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawTextBackdrop {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c-bg) 40%, transparent);
}

.drawTextPanel {
  width: min(360px, 92vw);
  padding: 16px;
  border-radius: 12px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  box-shadow: 0 12px 40px color-mix(in srgb, var(--c-bg) 50%, transparent);
}

.label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}

.input {
  width: 100%;
  resize: vertical;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg);
  color: var(--c-text);
  font: inherit;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
</style>
