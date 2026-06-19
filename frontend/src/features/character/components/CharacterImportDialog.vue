<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import {
  importCharacterPreview,
  type CharacterImportPreview,
} from "@/infra/api/character.api";
import { getBackendErrorMessage } from "@/infra/http/client";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
  imported: [preview: CharacterImportPreview];
}>();

const { t } = useI18n();

const rawText = ref("");
const mode = ref<"file" | "ai">("file");
const loading = ref(false);
const error = ref("");
const progress = ref(0);
const attempt = ref(0);

const MAX_LENGTH = 50000;
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1500;
/** 假进度默认约 3 分钟走到上限，API 提前返回则直接跳到 100% */
const FAKE_PROGRESS_DURATION_MS = 3 * 60_000;
const PROGRESS_CAP = 88;
const PROGRESS_TICK_MS = 500;

let progressTimer: ReturnType<typeof setInterval> | null = null;
let progressStartedAt = 0;

const statusText = computed(() => {
  const percent = Math.round(progress.value);
  if (attempt.value > 1) {
    return t("character.import.retryingPercent", {
      attempt: attempt.value,
      max: MAX_RETRIES,
      percent,
    });
  }
  return t("character.import.progressPercent", { percent });
});

watch(
  () => props.open,
  (open) => {
    if (!open) {
      stopFakeProgress();
      return;
    }
    rawText.value = "";
    mode.value = "file";
    error.value = "";
    loading.value = false;
    progress.value = 0;
    attempt.value = 0;
  },
);

function close() {
  if (loading.value) return;
  emit("close");
}

function tickFakeProgress() {
  const elapsed = Date.now() - progressStartedAt;
  const ratio = Math.min(1, elapsed / FAKE_PROGRESS_DURATION_MS);
  progress.value = Math.max(
    1,
    Math.min(PROGRESS_CAP, Math.round(1 + ratio * (PROGRESS_CAP - 1))),
  );
}

function startFakeProgress() {
  stopFakeProgress();
  progressStartedAt = Date.now();
  progress.value = 1;
  tickFakeProgress();
  progressTimer = setInterval(tickFakeProgress, PROGRESS_TICK_MS);
}

function stopFakeProgress(success = false) {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  if (success) progress.value = 100;
}

function delay(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function submit() {
  const text = rawText.value.trim();
  if (!text) {
    error.value = t("character.import.textRequired");
    return;
  }

  loading.value = true;
  error.value = "";

  let lastError: unknown;
  for (let i = 1; i <= MAX_RETRIES; i++) {
    attempt.value = i;
    if (i > 1) {
      progress.value = 0;
    }
    startFakeProgress();
    try {
      const preview = await importCharacterPreview(text);
      stopFakeProgress(true);
      await delay(300);
      loading.value = false;
      emit("imported", preview);
      close();
      return;
    } catch (e) {
      lastError = e;
      stopFakeProgress();
      progress.value = 0;
      if (i < MAX_RETRIES) {
        await delay(RETRY_DELAY_MS * i);
      }
    }
  }

  stopFakeProgress();
  const message = getBackendErrorMessage(lastError);
  error.value = message
    ? `${message} — ${t("character.import.retriesExhausted", { count: MAX_RETRIES })}`
    : t("character.import.failed");
  loading.value = false;
  attempt.value = 0;
}

function normalizeImportedPayload(value: unknown): CharacterImportPreview {
  const record = value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
  const payload = (record.character && typeof record.character === "object" && !Array.isArray(record.character))
    ? record.character as Record<string, unknown>
    : record;
  return payload as CharacterImportPreview;
}

async function importFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  input.value = "";
  if (!file) return;
  loading.value = true;
  error.value = "";
  try {
    if (!file.name.toLowerCase().endsWith(".json") && file.type !== "application/json") {
      throw new Error("Unsupported import file");
    }
    const text = await file.text();
    const parsed = JSON.parse(text.trim());
    emit("imported", normalizeImportedPayload(parsed));
    loading.value = false;
    close();
  } catch {
    error.value = t("character.import.fileFailed");
    loading.value = false;
  } finally {
    loading.value = false;
  }
}

onUnmounted(() => stopFakeProgress());
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="backdrop">
      <div class="dialog">
        <h3 class="title">{{ t("character.import.title") }}</h3>
        <div class="modeSwitch" role="tablist">
          <button type="button" :class="{ active: mode === 'file' }" @click="mode = 'file'">
            {{ t("character.import.fileImport") }}
          </button>
          <button type="button" :class="{ active: mode === 'ai' }" @click="mode = 'ai'">
            {{ t("character.import.aiImport") }}
          </button>
        </div>

        <template v-if="mode === 'file'">
          <p class="hint">{{ t("character.import.fileHint") }}</p>
          <label class="fileDrop">
            <span>{{ t("character.import.chooseFile") }}</span>
            <input type="file" accept=".json,application/json" :disabled="loading" @change="importFile" />
          </label>
        </template>

        <template v-else>
          <p class="hint">{{ t("character.import.hint") }}</p>
          <BaseTextarea
            v-model="rawText"
            min-height="220px"
            max-height="400px"
            :rows="12"
            :placeholder="t('character.import.placeholder')"
            :maxlength="MAX_LENGTH"
            :disabled="loading"
          />
          <p class="counter">{{ rawText.length }} / {{ MAX_LENGTH }}</p>
        </template>

        <p v-if="loading" class="status-text">{{ statusText }}</p>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="actions">
          <BaseButton type="button" variant="default" :disabled="loading" @click="close">
            {{ t("common.cancel") }}
          </BaseButton>
          <BaseButton
            v-if="mode === 'ai'"
            type="button"
            variant="primary"
            :loading="loading"
            :disabled="loading"
            @click="submit"
          >
            {{ t("character.import.apply") }}
          </BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.45);
  padding: 16px;
}

.dialog {
  width: min(560px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  padding: 20px;
  display: grid;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.hint {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
  line-height: 1.5;
}

.modeSwitch {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-bg-subtle);
  width: fit-content;
}

.modeSwitch button {
  min-width: 88px;
  height: 30px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.modeSwitch button.active {
  background: color-mix(in srgb, var(--c-primary) 18%, transparent);
  color: var(--c-text);
  font-weight: 700;
}

.fileDrop {
  min-height: 144px;
  display: grid;
  place-items: center;
  border: 1px dashed var(--c-border);
  border-radius: 8px;
  background: var(--c-bg-subtle);
  color: var(--c-text);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.fileDrop:hover {
  border-color: var(--c-accent);
}

.fileDrop input {
  display: none;
}


.counter {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
  text-align: right;
}

.status-text {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--c-text);
  text-align: center;
}

.error {
  margin: 0;
  font-size: 13px;
  color: var(--c-danger, #dc2626);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
