<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { ArrowUpTrayIcon } from "@heroicons/vue/24/outline";
import type { ResourceType } from "@/infra/api/library.api";
import { RESOURCE_TYPE_OPTIONS, getResourceTypeMeta } from "@/features/library/constants";
import BaseTagInput from "@/ui/base/BaseTagInput.vue";
import BaseDialog from "@/ui/base/BaseDialog.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseListItem from "@/ui/base/BaseListItem.vue";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void;
  (e: "submit", payload: { type: ResourceType; name: string; image?: File; audio?: File; tags?: string[]; comment?: string }): void;
}>();

const { t } = useI18n();

const type = ref<ResourceType>("map_background");
const name = ref("");
const tags = ref<string[]>([]);
const comment = ref("");
const file = ref<File | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const dragOver = ref(false);
const submitting = ref(false);
const validationError = ref("");

const typeOptions = computed(() =>
  RESOURCE_TYPE_OPTIONS.map((opt) => ({
    value: opt.value,
    label: t(opt.labelKey),
  })),
);

const currentMeta = computed(() => getResourceTypeMeta(type.value));

const needsFile = computed(() => currentMeta.value.isImage || currentMeta.value.isAudio);
const fileAccept = computed(() => currentMeta.value.isAudio ? "audio/*" : "image/*");
const dropSubKey = computed(() =>
  currentMeta.value.isAudio ? "library.upload.dropSubAudio" : "library.upload.dropSubImage",
);

const canSubmit = computed(() => {
  if (!name.value.trim()) return false;
  if (needsFile.value && !file.value) return false;
  return true;
});

watch(
  () => props.modelValue,
  (open) => {
    if (!open) {
      type.value = "map_background";
      name.value = "";
      tags.value = [];
      comment.value = "";
      file.value = null;
      validationError.value = "";
      submitting.value = false;
    }
  },
);

watch(type, () => {
  file.value = null;
  tags.value = [];
  comment.value = "";
  validationError.value = "";
});

function onDragOver(e: DragEvent) {
  e.preventDefault();
  dragOver.value = true;
}

function onDragLeave() {
  dragOver.value = false;
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  dragOver.value = false;
  const dropped = e.dataTransfer?.files[0];
  if (dropped) setFile(dropped);
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const selected = input.files?.[0];
  if (selected) setFile(selected);
}

function setFile(f: File) {
  validationError.value = "";
  if (currentMeta.value.isImage && !f.type.startsWith("image/")) {
    validationError.value = t("library.upload.invalidImageType");
    return;
  }
  if (currentMeta.value.isAudio && !f.type.startsWith("audio/")) {
    validationError.value = t("library.upload.invalidAudioType");
    return;
  }
  file.value = f;
  if (!name.value.trim()) {
    name.value = f.name.replace(/\.[^.]+$/, "");
  }
}

function clearFile() {
  file.value = null;
  if (fileInputRef.value) fileInputRef.value.value = "";
}

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return;
  submitting.value = true;
  try {
    emit("submit", {
      type: type.value,
      name: name.value.trim(),
      image: currentMeta.value.isImage ? (file.value ?? undefined) : undefined,
      audio: currentMeta.value.isAudio ? (file.value ?? undefined) : undefined,
      tags: currentMeta.value.hasTags && tags.value.length ? tags.value : undefined,
      comment: currentMeta.value.hasComment && comment.value.trim() ? comment.value.trim() : undefined,
    });
  } finally {
    submitting.value = false;
  }
}

function close() {
  emit("update:modelValue", false);
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :max-width="480" @update:model-value="close">
    <div class="dialog-inner">
      <BaseListItem :interactive="false">
        <div class="fields">
          <div class="dialog-title">{{ t("library.upload.title") }}</div>
          <div class="field">
            <label class="label">{{ t("library.upload.typeLabel") }}<span class="required">*</span></label>
            <BaseSelect
              :model-value="type"
              :options="typeOptions"
              @update:model-value="type = $event as ResourceType"
            />
          </div>

          <div class="field">
            <label class="label">{{ t("library.upload.nameLabel") }}<span class="required">*</span></label>
            <BaseInput
              v-model="name"
              :placeholder="t('library.upload.namePlaceholder')"
            />
          </div>

          <template v-if="needsFile">
            <div class="field">
              <label class="label">{{ t("library.upload.fileLabel") }}<span class="required">*</span></label>
              <div
                class="drop-zone"
                :class="{ active: dragOver, 'has-file': !!file }"
                @dragover="onDragOver"
                @dragleave="onDragLeave"
                @drop="onDrop"
                @click="fileInputRef?.click()"
              >
                <input
                  ref="fileInputRef"
                  type="file"
                  :accept="fileAccept"
                  class="hidden-input"
                  @change="onFileChange"
                />

                <template v-if="file">
                  <div class="file-name">{{ file.name }}</div>
                  <button class="clear-btn" type="button" @click.stop="clearFile">
                    {{ t("library.upload.clearFile") }}
                  </button>
                </template>
                <template v-else>
                  <AppIcon :icon="ArrowUpTrayIcon" :size="24" />
                  <div class="drop-hint">{{ t("library.upload.dropHint") }}</div>
                  <div class="drop-sub">{{ t(dropSubKey) }}</div>
                </template>
              </div>
              <div v-if="validationError" class="error-text">{{ validationError }}</div>
            </div>
          </template>

          <div v-if="currentMeta.hasTags" class="field">
            <label class="label">{{ t("library.upload.tagsLabel") }}</label>
            <BaseTagInput
              v-model="tags"
              :placeholder="t('library.upload.tagsPlaceholder')"
            />
          </div>

          <div v-if="currentMeta.hasComment" class="field">
            <label class="label">{{ t("library.upload.commentLabel") }}</label>
            <BaseTextarea
              v-model="comment"
              min-height="72px"
              :placeholder="t('library.upload.commentPlaceholder')"
            />
          </div>
          <div class="actions">
            <BaseButton variant="default" @click="close">{{ t("common.cancel") }}</BaseButton>
            <BaseButton
              variant="primary"
              :disabled="!canSubmit"
              :loading="submitting"
              @click="handleSubmit"
            >
              {{ t("library.upload.submit") }}
            </BaseButton>
          </div>
        </div>
      </BaseListItem>
    </div>
  </BaseDialog>
</template>

<style scoped>
.dialog-inner {
  padding: 24px;
  display: grid;
  gap: 18px;
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--c-text);
}

.fields {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 6px;
}

.label {
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-muted);
}

.required {
  margin-left: 3px;
  color: var(--c-danger, #e53e3e);
}

.drop-zone {
  border: 2px dashed var(--c-border);
  border-radius: var(--r-2);
  padding: 28px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer !important;
  transition: border-color 0.15s, background 0.15s;
  color: var(--c-text-muted);
}

.drop-zone:hover,
.drop-zone.active {
  border-color: var(--c-accent);
  background: var(--c-accent-subtle, rgba(0, 0, 0, 0.03));
}

.drop-zone.has-file {
  border-style: solid;
  border-color: var(--c-accent);
}

.hidden-input {
  display: none;
}

.drop-hint {
  font-size: 14px;
  font-weight: 500;
  color: var(--c-text);
}

.drop-sub {
  font-size: 12px;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text);
  word-break: break-all;
  text-align: center;
}

.clear-btn {
  background: none;
  border: none;
  color: var(--c-text-muted);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--r-1);
}

.clear-btn:hover {
  background: var(--c-surface-raised);
  color: var(--c-text);
}

.error-text {
  font-size: 12px;
  color: var(--c-danger, #e53e3e);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
