<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import {
  getRoomPersonalMemo,
  putRoomPersonalMemo,
} from "@/infra/api/rooms.api";
import { getBackendErrorMessage } from "@/infra/http/client";

const props = defineProps<{
  roomId: number;
}>();

const { t } = useI18n();
const memoText = ref("");
const loading = ref(false);
const saving = ref(false);
const statusHint = ref("");
let loadToken = 0;
let saveTimer: ReturnType<typeof setTimeout> | null = null;
let suppressSave = false;

async function loadMemo(roomId: number) {
  const token = ++loadToken;
  if (roomId <= 0) {
    suppressSave = true;
    memoText.value = "";
    suppressSave = false;
    return;
  }

  loading.value = true;
  statusHint.value = t("common.loading");

  const data = await getRoomPersonalMemo(roomId).catch((error: unknown) => {
    if (token === loadToken) {
      statusHint.value = getBackendErrorMessage(error);
    }
    return null;
  });

  if (token !== loadToken) return;

  loading.value = false;
  if (data) {
    suppressSave = true;
    memoText.value = data.content;
    suppressSave = false;
    statusHint.value = "";
  }
}

function scheduleSave(content: string) {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => void persistMemo(content), 500);
}

async function persistMemo(content: string) {
  if (props.roomId <= 0 || loading.value) return;

  saving.value = true;
  statusHint.value = t("table.inspector.memoSaving");

  const result = await putRoomPersonalMemo(props.roomId, { content }).catch(
    (error: unknown) => {
      statusHint.value = getBackendErrorMessage(error);
      return null;
    },
  );

  saving.value = false;
  if (result) {
    statusHint.value = t("table.inspector.memoSaved");
  }
}

watch(
  () => props.roomId,
  (roomId) => {
    void loadMemo(roomId);
  },
  { immediate: true },
);

watch(memoText, (content) => {
  if (suppressSave || loading.value || props.roomId <= 0) return;
  scheduleSave(content);
});

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer);
});
</script>

<template>
  <div class="personalMemo">
    <textarea
      v-model="memoText"
      class="memoInput"
      :placeholder="t('table.inspector.memoPlaceholder')"
      :disabled="loading"
      rows="4"
    />
    <p v-if="statusHint" class="memoStatus">{{ statusHint }}</p>
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

.memoInput:disabled {
  opacity: 0.7;
}

.memoStatus {
  margin: 6px 0 0;
  font-size: 11px;
  color: var(--c-text-muted);
}
</style>
