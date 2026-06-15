<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import {
  getRoomPersonalMemo,
  putRoomPersonalMemo,
} from "@/infra/api/rooms.api";
import { getBackendErrorMessage } from "@/infra/http/client";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";

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
    <BaseTextarea
      v-model="memoText"
      class="memoInput"
      :placeholder="t('table.inspector.memoPlaceholder')"
      :disabled="loading"
      :rows="3"
      min-height="84px"
      max-height="100%"
    />
    <p v-if="statusHint" class="memoStatus">{{ statusHint }}</p>
  </div>
</template>

<style scoped>
.personalMemo {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 6px;
  height: 100%;
  min-height: 0;
}

.memoStatus {
  margin: 0;
  font-size: 11px;
  color: var(--c-text-muted);
}
</style>
