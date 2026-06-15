<script setup lang="ts">
import { toRef } from "vue";
import { useI18n } from "vue-i18n";
import { PencilSquareIcon, TrashIcon, PhotoIcon, DocumentDuplicateIcon } from "@heroicons/vue/24/outline";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import type { TokenConfigUpsert } from "@/infra/api/character.api";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{
  config: TokenConfigUpsert;
  isPrimary?: boolean;
  readonly?: boolean;
  syncLabel?: string;
}>();
const emit = defineEmits<{
  (e: "edit"): void;
  (e: "pickImage"): void;
  (e: "remove"): void;
  (e: "copy"): void;
  (e: "update:name", v: string): void;
}>();

const { t } = useI18n();

const assetId = toRef(() => props.config.asset_id ?? undefined);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetId);
</script>

<template>
  <div class="token-card" :class="{ readonly }">
    <button
      type="button"
      class="token-thumb"
      :disabled="readonly"
      @click="!readonly && emit('pickImage')"
    >
      <img v-if="imageUrl" :src="imageUrl" class="thumb-img" />
      <div v-else class="thumb-placeholder">
        <AppIcon :icon="PhotoIcon" :size="24" />
      </div>
      <div v-if="!readonly" class="thumb-overlay">{{ t("character.token.changeImage") }}</div>
    </button>

    <div class="token-meta">
      <input
        class="token-name-input"
        type="text"
        :value="config.name"
        :placeholder="t('character.token.namePlaceholder')"
        :readonly="readonly"
        :aria-readonly="readonly"
        @input="emit('update:name', ($event.target as HTMLInputElement).value)"
      />
      <span v-if="syncLabel" class="sync-pill">{{ syncLabel }}</span>
    </div>

    <div v-if="!readonly" class="token-actions">
      <button class="action-btn" :title="t('character.token.editPanel')" @click="emit('edit')">
        <AppIcon :icon="PencilSquareIcon" :size="16" />
      </button>
      <button v-if="!isPrimary" class="action-btn" :title="t('character.token.copySecondary')" @click="emit('copy')">
        <AppIcon :icon="DocumentDuplicateIcon" :size="16" />
      </button>
      <button class="action-btn del" :title="t('common.delete')" @click="emit('remove')">
        <AppIcon :icon="TrashIcon" :size="16" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.token-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface-raised);
}

.token-thumb {
  position: relative;
  width: 56px;
  height: 56px;
  padding: 0;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  border: 2px solid var(--c-border);
  background: var(--c-surface);
}
.token-thumb:disabled {
  cursor: default;
}

.thumb-img { width: 100%; height: 100%; object-fit: cover; }

.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-muted);
}

.thumb-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 10px;
  line-height: 1.3;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}
.token-thumb:hover .thumb-overlay { opacity: 1; }

.token-meta { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }

.token-name-input {
  font-size: 14px;
  font-weight: 500;
  color: var(--c-text);
  background: transparent;
  border: none;
  border-bottom: 1px solid transparent;
  outline: none;
  padding: 2px 0;
  width: 100%;
  font-family: inherit;
  transition: border-color 0.15s;
}
.token-name-input:hover { border-bottom-color: var(--c-border); }
.token-name-input:focus { border-bottom-color: var(--c-accent); }
.token-name-input[readonly] {
  cursor: default;
  border-bottom-color: transparent;
}
.token-name-input[readonly]:hover,
.token-name-input[readonly]:focus {
  border-bottom-color: transparent;
}
.token-name-input::placeholder { color: var(--c-text-muted); font-weight: 400; }

.sync-pill {
  width: fit-content;
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border: 1px solid color-mix(in srgb, var(--c-primary) 28%, var(--c-border));
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-primary) 12%, transparent);
  color: color-mix(in srgb, var(--c-primary) 82%, var(--c-text));
  font-size: 12px;
  line-height: 1;
}

.token-actions { display: flex; gap: 4px; flex-shrink: 0; }

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--c-text-muted);
  padding: 6px;
  border-radius: var(--r-1);
  display: flex;
  align-items: center;
  transition: color 0.12s, background 0.12s;
}
.action-btn:hover { color: var(--c-text); background: var(--c-hover); }
.action-btn.del:hover { color: var(--c-danger, #e53e3e); }
</style>
