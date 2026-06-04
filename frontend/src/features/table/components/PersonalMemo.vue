<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  roomId: number;
}>();

const { t } = useI18n();
const memoText = ref("");

watch(
  () => props.roomId,
  () => {
    memoText.value = "";
  },
);
</script>

<template>
  <div class="personalMemo">
    <textarea
      v-model="memoText"
      class="memoInput"
      :placeholder="t('table.inspector.memoPlaceholder')"
      rows="4"
    />
  </div>
</template>

<style scoped>
.personalMemo {
  min-height: 0;
}

.memoInput {
  width: 100%;
  min-height: 88px;
  resize: vertical;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--c-border) 80%, transparent);
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  font-size: 13px;
  line-height: 1.5;
  font-family: inherit;
  box-sizing: border-box;
}

.memoInput:focus {
  outline: 2px solid color-mix(in srgb, var(--c-primary) 35%, transparent);
  outline-offset: 1px;
}
</style>
