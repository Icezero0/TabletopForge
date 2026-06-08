<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { XMarkIcon } from "@heroicons/vue/24/outline";
import BaseDialog from "@/ui/base/BaseDialog.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import LibraryMapCard from "@/features/table/components/LibraryMapCard.vue";
import { getLibraryResources, type LibraryResource } from "@/infra/api/library.api";

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  pick: [resource: LibraryResource];
}>();

const { t } = useI18n();
const items = ref<LibraryResource[]>([]);
const loading = ref(false);

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return;
    loading.value = true;
    try {
      const result = await getLibraryResources({ type: "map_background", page_size: 100 });
      items.value = result.items.filter((r) => r.primary_asset_id != null);
    } catch {
      items.value = [];
    } finally {
      loading.value = false;
    }
  },
);

function close() {
  emit("update:modelValue", false);
}

function onPick(resource: LibraryResource) {
  if (!resource.primary_asset_id) return;
  emit("pick", resource);
  close();
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :max-width="720" :aria-label="t('table.assets.libraryPickerTitle')" @update:model-value="close">
    <div class="card">
      <div class="header">
        <span class="title">{{ t("table.assets.libraryPickerTitle") }}</span>
        <button type="button" class="closeBtn" @click="close">
          <AppIcon :icon="XMarkIcon" :size="18" />
        </button>
      </div>

      <div v-if="loading" class="emptyState">{{ t("common.loading") }}</div>
      <div v-else-if="!items.length" class="emptyState">{{ t("table.assets.libraryPickerEmpty") }}</div>
      <div v-else class="grid">
        <LibraryMapCard
          v-for="resource in items"
          :key="resource.id"
          :resource="resource"
          @pick="onPick(resource)"
        />
      </div>
    </div>
  </BaseDialog>
</template>

<style scoped>
.card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 16px;
  box-shadow: 0 10px 32px rgb(0 0 0 / 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--c-border);
  gap: 12px;
  flex-shrink: 0;
}

.title {
  font-size: 15px;
  font-weight: 650;
  color: var(--c-text);
}

.closeBtn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
  border-radius: 6px;
  flex-shrink: 0;
}

.closeBtn:hover {
  background: var(--c-hover);
  color: var(--c-text);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  padding: 16px 20px;
  overflow-y: auto;
  max-height: 60vh;
}

.emptyState {
  padding: 48px 20px;
  text-align: center;
  font-size: 13px;
  color: var(--c-text-muted);
}
</style>
