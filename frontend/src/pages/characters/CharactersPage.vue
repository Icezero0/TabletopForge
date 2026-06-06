<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { PlusIcon } from "@heroicons/vue/24/outline";
import { useCharacters } from "@/features/character/composables/useCharacters";
import CharacterCard from "@/features/character/components/CharacterCard.vue";
import type { Character } from "@/infra/api/character.api";
import { usePageReturnTo, useNavigationReturn } from "@/composables/useNavigationReturn";
import { useToastsStore } from "@/stores/toasts.store";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseConfirmDialog from "@/ui/base/BaseConfirmDialog.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import { ref } from "vue";

const { t } = useI18n();
const router = useRouter();
const { backTo, backText } = usePageReturnTo();
const { linkTarget } = useNavigationReturn();
const toasts = useToastsStore();
const chars = useCharacters();

const showDelete = ref(false);
const deleteTarget = ref<Character | null>(null);
const deleteLoading = ref(false);

function openDelete(character: Character) {
  deleteTarget.value = character;
  showDelete.value = true;
}

async function handleDeleteConfirm() {
  if (!deleteTarget.value) return;
  deleteLoading.value = true;
  try {
    await chars.remove(deleteTarget.value.id);
    showDelete.value = false;
    toasts.push({ message: t("character.toast.deleted"), tone: "success" });
  } catch {
    toasts.push({ message: t("character.toast.deleteFailed"), tone: "danger" });
  } finally {
    deleteLoading.value = false;
  }
}

onMounted(() => void chars.fetchPage(1));
</script>

<template>
  <AppPageShell
    :title="t('character.title')"
    :back-to="backTo"
    :back-text="backText"
    :max-width="1100"
  >
    <template #actions>
      <BaseButton variant="primary" @click="router.push(linkTarget('/characters/new'))">
        <span class="btn-icon-text">
          <AppIcon :icon="PlusIcon" :size="16" />
          {{ t("character.newCharacter") }}
        </span>
      </BaseButton>
    </template>

    <div class="content-card">
      <div v-if="chars.isLoading.value" class="state-msg">{{ t("common.loading") }}</div>

      <div v-else-if="chars.error.value" class="state-msg error">
        {{ t("character.errors.loadFailed") }}
      </div>

      <div v-else-if="!chars.items.value.length" class="empty">
        <div class="empty-title">{{ t("character.empty.title") }}</div>
      </div>

      <div v-else class="grid">
        <CharacterCard
          v-for="character in chars.items.value"
          :key="character.id"
          :character="character"
          @click="router.push(`/characters/${character.id}`)"
          @delete="openDelete"
        />
      </div>

      <div v-if="chars.totalPages.value > 1" class="pagination">
        <BaseButton variant="default" :disabled="chars.page.value <= 1" @click="chars.fetchPage(chars.page.value - 1)">
          {{ t("library.pagination.prev") }}
        </BaseButton>
        <span class="page-info">{{ chars.page.value }} / {{ chars.totalPages.value }}</span>
        <BaseButton variant="default" :disabled="chars.page.value >= chars.totalPages.value" @click="chars.fetchPage(chars.page.value + 1)">
          {{ t("library.pagination.next") }}
        </BaseButton>
      </div>
    </div>
  </AppPageShell>

  <BaseConfirmDialog
    v-model="showDelete"
    :title="t('character.delete.title')"
    :message="t('character.delete.message', { name: deleteTarget?.name ?? '' })"
    :confirm-text="t('character.delete.confirm')"
    :cancel-text="t('common.cancel')"
    variant="danger"
    :loading="deleteLoading"
    @confirm="handleDeleteConfirm"
  />
</template>

<style scoped>
.btn-icon-text { display: inline-flex; align-items: center; gap: 6px; }
.content-card {
  border: 1px solid var(--c-border); border-radius: var(--r-2);
  background: var(--c-surface); padding: 20px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}
.state-msg { padding: 40px 0; text-align: center; color: var(--c-text-muted); font-size: 14px; }
.state-msg.error { color: var(--c-danger, #e53e3e); }
.empty { padding: 60px 0; display: grid; gap: 8px; justify-items: center; text-align: center; }
.empty-title { font-size: 16px; font-weight: 500; color: var(--c-text); }
.pagination { display: flex; align-items: center; gap: 12px; justify-content: center; padding-top: 24px; }
.page-info { font-size: 13px; color: var(--c-text-muted); }
</style>
