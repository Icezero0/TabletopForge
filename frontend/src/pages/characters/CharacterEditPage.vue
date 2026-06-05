<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  defaultIdentity, defaultFlavor, defaultAttributes,
  defaultFeatures, defaultSpells, defaultEquipment,
} from "@/features/character/constants";
import {
  getCharacter, createCharacter, patchCharacter,
} from "@/infra/api/character.api";
import { usePageReturnTo } from "@/composables/useNavigationReturn";
import { useToastsStore } from "@/stores/toasts.store";
import CharacterIdentityTab from "@/features/character/components/tabs/CharacterIdentityTab.vue";
import CharacterAttributesTab from "@/features/character/components/tabs/CharacterAttributesTab.vue";
import CharacterFeaturesTab from "@/features/character/components/tabs/CharacterFeaturesTab.vue";
import CharacterSpellsTab from "@/features/character/components/tabs/CharacterSpellsTab.vue";
import CharacterEquipmentTab from "@/features/character/components/tabs/CharacterEquipmentTab.vue";
import CharacterExtrasTab from "@/features/character/components/tabs/CharacterExtrasTab.vue";
import BaseButton from "@/ui/base/BaseButton.vue";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const { backTo, backText } = usePageReturnTo("/characters");
const toasts = useToastsStore();

const characterId = computed(() => {
  const id = route.params.id;
  return id && id !== "new" ? Number(id) : null;
});
const isEdit = computed(() => characterId.value !== null);

const TABS = [
  { key: "identity",   label: () => t("character.tabs.identity") },
  { key: "attributes", label: () => t("character.tabs.attributes") },
  { key: "features",   label: () => t("character.tabs.features") },
  { key: "spells",     label: () => t("character.tabs.spells") },
  { key: "equipment",  label: () => t("character.tabs.equipment") },
  { key: "extras",     label: () => t("character.tabs.extras") },
] as const;

const activeTab = ref<(typeof TABS)[number]["key"]>("identity");

// Form state
const formSystem = ref("dnd5e");
const formPortraitAssetId = ref<number | null>(null);
const formIdentity = ref<Record<string, unknown>>(defaultIdentity() as unknown as Record<string, unknown>);
const formFlavor = ref<Record<string, unknown>>(defaultFlavor() as unknown as Record<string, unknown>);
const formAttributes = ref<Record<string, unknown>>(defaultAttributes() as unknown as Record<string, unknown>);
const formFeatures = ref<Record<string, unknown>>(defaultFeatures() as unknown as Record<string, unknown>);
const formSpells = ref<Record<string, unknown>>(defaultSpells() as unknown as Record<string, unknown>);
const formEquipment = ref<Record<string, unknown>>(defaultEquipment() as unknown as Record<string, unknown>);
const formExtras = ref<Record<string, unknown>>({});

const isLoading = ref(false);
const isSaving = ref(false);

// Derive name from identity block (single source of truth)
const charName = computed(() => (formIdentity.value.name as string)?.trim() ?? "");

// ── Dirty state tracking ────────────────────────────────────────────────────
const currentSnapshot = computed(() => JSON.stringify({
  portraitAssetId: formPortraitAssetId.value,
  identity: formIdentity.value,
  flavor: formFlavor.value,
  attributes: formAttributes.value,
  features: formFeatures.value,
  spells: formSpells.value,
  equipment: formEquipment.value,
  extras: formExtras.value,
}));
const savedSnapshot = ref<string>("");
const isDirty = computed(() => currentSnapshot.value !== savedSnapshot.value);

async function loadCharacter(id: number) {
  isLoading.value = true;
  try {
    const char = await getCharacter(id);
    formSystem.value = char.system;
    formPortraitAssetId.value = char.portrait_asset_id;
    // Ensure name is in identity block
    formIdentity.value = { ...char.identity as Record<string, unknown>, name: char.name };
    formFlavor.value = char.flavor as Record<string, unknown>;
    formAttributes.value = char.attributes as Record<string, unknown>;
    formFeatures.value = char.features as Record<string, unknown>;
    formSpells.value = (char.spells as Record<string, unknown> | null) ?? (defaultSpells() as unknown as Record<string, unknown>);
    formEquipment.value = char.equipment as Record<string, unknown>;
    formExtras.value = char.extras as Record<string, unknown>;
    // Stamp snapshot after data is loaded
    savedSnapshot.value = currentSnapshot.value;
  } catch {
    toasts.push({ message: t("character.errors.loadFailed"), tone: "danger" });
    router.push("/characters");
  } finally {
    isLoading.value = false;
  }
}

async function save() {
  if (!charName.value) {
    activeTab.value = "identity";
    toasts.push({ message: t("character.errors.nameRequired"), tone: "danger" });
    return;
  }

  isSaving.value = true;
  try {
    const payload = {
      name: charName.value,
      system: formSystem.value,
      portrait_asset_id: formPortraitAssetId.value,
      identity: formIdentity.value,
      flavor: formFlavor.value,
      attributes: formAttributes.value,
      features: formFeatures.value,
      spells: formSpells.value,
      equipment: formEquipment.value,
      extras: formExtras.value,
    };

    if (isEdit.value) {
      await patchCharacter(characterId.value!, payload);
      savedSnapshot.value = currentSnapshot.value;
      toasts.push({ message: t("character.toast.saved"), tone: "success" });
    } else {
      const created = await createCharacter(payload);
      savedSnapshot.value = currentSnapshot.value;
      toasts.push({ message: t("character.toast.created"), tone: "success" });
      router.replace(`/characters/${created.id}`);
    }
  } catch {
    toasts.push({ message: isEdit.value ? t("character.toast.saveFailed") : t("character.toast.createFailed"), tone: "danger" });
  } finally {
    isSaving.value = false;
  }
}

const pageTitle = computed(() =>
  isEdit.value
    ? (charName.value || t("character.editCharacter"))
    : t("character.newCharacter"),
);

// In-app navigation guard
onBeforeRouteLeave(() => {
  if (isDirty.value) {
    return window.confirm(t("character.confirmLeave"));
  }
});

// Browser tab close / refresh guard
function handleBeforeUnload(e: BeforeUnloadEvent) {
  if (isDirty.value) {
    e.preventDefault();
    e.returnValue = "";
  }
}

onMounted(() => {
  if (isEdit.value) {
    void loadCharacter(characterId.value!);
  } else {
    savedSnapshot.value = currentSnapshot.value;
  }
  window.addEventListener("beforeunload", handleBeforeUnload);
});
onUnmounted(() => window.removeEventListener("beforeunload", handleBeforeUnload));
</script>

<template>
  <AppPageShell :title="pageTitle" :back-to="backTo" :back-text="backTo.startsWith('/rooms/') ? backText : t('character.title')" :max-width="900">
    <template #actions>
      <BaseButton variant="primary" :loading="isSaving" :disabled="isEdit && !isDirty" @click="save">
        {{ isEdit ? t("common.save") : t("character.create") }}
      </BaseButton>
    </template>

    <div v-if="isLoading" class="loading">{{ t("common.loading") }}</div>

    <template v-else>
      <!-- Tab nav -->
      <div class="tab-nav">
        <button
          v-for="tab in TABS"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label() }}
        </button>
      </div>

      <!-- Tab content -->
      <div class="tab-panel">
        <CharacterIdentityTab
          v-if="activeTab === 'identity'"
          v-model="formIdentity"
          v-model:flavor="formFlavor"
          :portrait-asset-id="formPortraitAssetId"
          @update:portrait-asset-id="formPortraitAssetId = $event"
        />

        <CharacterAttributesTab
          v-else-if="activeTab === 'attributes'"
          v-model="formAttributes"
          :identity-block="formIdentity"
        />

        <CharacterFeaturesTab
          v-else-if="activeTab === 'features'"
          v-model="formFeatures"
        />

        <CharacterSpellsTab
          v-else-if="activeTab === 'spells'"
          v-model="formSpells"
          :attributes-block="formAttributes"
        />

        <CharacterEquipmentTab
          v-else-if="activeTab === 'equipment'"
          v-model="formEquipment"
        />

        <CharacterExtrasTab
          v-else-if="activeTab === 'extras'"
          v-model="formExtras"
        />
      </div>
    </template>
  </AppPageShell>
</template>

<style scoped>
.loading { padding: 40px 0; text-align: center; color: var(--c-text-muted); font-size: 14px; }

.tab-nav {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--c-border);
  margin-bottom: 24px;
}

.tab-btn {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-muted);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.tab-btn:hover { color: var(--c-text); }

.tab-btn.active {
  color: var(--c-text);
  border-bottom-color: var(--c-accent);
}

.tab-panel {
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface);
  padding: 24px;
}
</style>
