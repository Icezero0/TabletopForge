<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon } from "@heroicons/vue/24/outline";
import type { LibraryResource, ResourceType } from "@/infra/api/library.api";
import { useLibraryResources } from "@/features/library/composables/useLibraryResources";
import ResourceCard from "@/features/library/components/ResourceCard.vue";
import UploadResourceDialog from "@/features/library/components/UploadResourceDialog.vue";
import { usePageReturnTo } from "@/composables/useNavigationReturn";
import { useToastsStore } from "@/stores/toasts.store";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseConfirmDialog from "@/ui/base/BaseConfirmDialog.vue";
import BaseDialog from "@/ui/base/BaseDialog.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const { t } = useI18n();
const { backTo, backText } = usePageReturnTo();
const toasts = useToastsStore();
const lib = useLibraryResources();

const showUpload = ref(false);
const showDelete = ref(false);
const showRename = ref(false);
const targetResource = ref<LibraryResource | null>(null);
const renameValue = ref("");
const deleteLoading = ref(false);

const ALL_FILTER = "__all__";
const typeFilterValue = ref<string>(ALL_FILTER);

const typeFilterOptions = computed(() => [
  { value: ALL_FILTER, label: t("library.filter.all") },
  { value: "map_background", label: t("library.types.mapBackground") },
]);

watch(typeFilterValue, (v) => {
  lib.typeFilter.value = v === ALL_FILTER ? null : (v as ResourceType);
  void lib.fetchPage(1);
});

function openRename(resource: LibraryResource) {
  targetResource.value = resource;
  renameValue.value = resource.name;
  showRename.value = true;
}

function openDelete(resource: LibraryResource) {
  targetResource.value = resource;
  showDelete.value = true;
}

async function handleRenameConfirm() {
  if (!targetResource.value || !renameValue.value.trim()) return;
  try {
    await lib.rename(targetResource.value.id, renameValue.value.trim());
    showRename.value = false;
    toasts.push({ message: t("library.toast.renamed"), tone: "success" });
  } catch {
    toasts.push({ message: t("library.toast.renameFailed"), tone: "danger" });
  }
}

async function handleDeleteConfirm() {
  if (!targetResource.value) return;
  deleteLoading.value = true;
  try {
    await lib.remove(targetResource.value.id);
    showDelete.value = false;
    toasts.push({ message: t("library.toast.deleted"), tone: "success" });
  } catch (err: unknown) {
    const isInUse =
      err &&
      typeof err === "object" &&
      "response" in err &&
      (err as { response?: { data?: { error?: { reason?: string } } } }).response?.data?.error?.reason === "library_resource_in_use";
    toasts.push({
      message: isInUse ? t("library.toast.deleteInUse") : t("library.toast.deleteFailed"),
      tone: "danger",
    });
  } finally {
    deleteLoading.value = false;
  }
}

async function handleUploadSubmit(payload: {
  type: ResourceType;
  name: string;
  image?: File;
}) {
  try {
    await lib.create(payload);
    showUpload.value = false;
    toasts.push({ message: t("library.toast.created"), tone: "success" });
  } catch {
    toasts.push({ message: t("library.toast.createFailed"), tone: "danger" });
  }
}

onMounted(() => {
  void lib.fetchPage(1);
});
</script>

<template>
  <AppPageShell
    :title="t('library.title')"
    :back-to="backTo"
    :back-text="backText"
    :max-width="1100"
  >
    <template #actions>
      <BaseButton variant="primary" @click="showUpload = true">
        <span class="btn-icon-text">
          <AppIcon :icon="PlusIcon" :size="16" />
          {{ t("library.addResource") }}
        </span>
      </BaseButton>
    </template>

    <template #toolbar>
      <BaseSelect
        :model-value="typeFilterValue"
        :options="typeFilterOptions"
        :width="180"
        @update:model-value="typeFilterValue = $event"
      />
    </template>

    <div class="content-card">
      <div v-if="lib.isLoading.value" class="state-msg">{{ t("common.loading") }}</div>

      <div v-else-if="lib.error.value" class="state-msg error">
        {{ t("library.errors.loadFailed") }}
      </div>

      <div v-else-if="lib.items.value.length === 0" class="empty">
        <div class="empty-title">{{ t("library.empty.title") }}</div>
      </div>

      <div v-else class="grid">
        <ResourceCard
          v-for="resource in lib.items.value"
          :key="resource.id"
          :resource="resource"
          @rename="openRename"
          @delete="openDelete"
        />
      </div>

      <div v-if="lib.totalPages.value > 1" class="pagination">
        <BaseButton
          variant="default"
          :disabled="lib.page.value <= 1"
          @click="lib.fetchPage(lib.page.value - 1)"
        >
          {{ t("library.pagination.prev") }}
        </BaseButton>
        <span class="page-info">{{ lib.page.value }} / {{ lib.totalPages.value }}</span>
        <BaseButton
          variant="default"
          :disabled="lib.page.value >= lib.totalPages.value"
          @click="lib.fetchPage(lib.page.value + 1)"
        >
          {{ t("library.pagination.next") }}
        </BaseButton>
      </div>
    </div>
  </AppPageShell>

  <UploadResourceDialog
    v-model="showUpload"
    @submit="handleUploadSubmit"
  />

  <!-- Rename dialog -->
  <BaseDialog v-model="showRename" :max-width="400">
    <div class="rename-inner">
      <div class="rename-title">{{ t("library.rename.title") }}</div>
      <BaseInput
        v-model="renameValue"
        :placeholder="t('library.rename.placeholder')"
        @keydown.enter="handleRenameConfirm"
      />
      <div class="rename-actions">
        <BaseButton variant="default" @click="showRename = false">
          {{ t("common.cancel") }}
        </BaseButton>
        <BaseButton
          variant="primary"
          :disabled="!renameValue.trim()"
          @click="handleRenameConfirm"
        >
          {{ t("common.save") }}
        </BaseButton>
      </div>
    </div>
  </BaseDialog>

  <!-- Delete confirm -->
  <BaseConfirmDialog
    v-model="showDelete"
    :title="t('library.delete.title')"
    :message="t('library.delete.message', { name: targetResource?.name ?? '' })"
    :confirm-text="t('library.delete.confirm')"
    :cancel-text="t('common.cancel')"
    variant="danger"
    :loading="deleteLoading"
    @confirm="handleDeleteConfirm"
  />
</template>

<style scoped>
.btn-icon-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.content-card {
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface);
  padding: 20px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.state-msg {
  padding: 40px 0;
  text-align: center;
  color: var(--c-text-muted);
  font-size: 14px;
}

.state-msg.error {
  color: var(--c-danger, #e53e3e);
}

.empty {
  padding: 60px 0;
  display: grid;
  gap: 8px;
  justify-items: center;
  text-align: center;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--c-text);
}

.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding-top: 24px;
}

.page-info {
  font-size: 13px;
  color: var(--c-text-muted);
}

.rename-inner {
  padding: 24px;
  display: grid;
  gap: 16px;
}

.rename-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--c-text);
}

.rename-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
