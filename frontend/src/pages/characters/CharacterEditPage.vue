<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  defaultIdentity, defaultFlavor, defaultAttributes,
  defaultFeatures, defaultSpells, defaultEquipment,
  defaultTokenConfig,
} from "@/features/character/constants";
import {
  getCharacter, createCharacter, patchCharacter,
  type CharacterImportPreview,
  type CharacterKind,
} from "@/infra/api/character.api";
import { postRoomCharacter } from "@/infra/api/roomCharacters.api";
import { usePageReturnTo, RETURN_TO_QUERY } from "@/composables/useNavigationReturn";
import { useToastsStore } from "@/stores/toasts.store";
import CharacterImportDialog from "@/features/character/components/CharacterImportDialog.vue";
import CharacterIdentityTab from "@/features/character/components/tabs/CharacterIdentityTab.vue";
import CharacterAttributesTab from "@/features/character/components/tabs/CharacterAttributesTab.vue";
import CharacterFeaturesTab from "@/features/character/components/tabs/CharacterFeaturesTab.vue";
import CharacterSpellsTab from "@/features/character/components/tabs/CharacterSpellsTab.vue";
import CharacterEquipmentTab from "@/features/character/components/tabs/CharacterEquipmentTab.vue";
import CharacterExtrasTab from "@/features/character/components/tabs/CharacterExtrasTab.vue";
import CharacterTokenTab from "@/features/character/components/tabs/CharacterTokenTab.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import type { TokenConfigUpsert } from "@/infra/api/character.api";

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

const roomIdFromQuery = computed(() => {
  const raw = route.query.roomId;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
});

function normalizeKindFromQuery(raw: unknown): CharacterKind {
  if (raw === "pc_main" || raw === "pc_additional" || raw === "npc") return raw;
  if (raw === "pc") return "pc_main";
  if (raw === "additional") return "pc_additional";
  return "pc_main";
}

const kindFromQuery = computed(() => normalizeKindFromQuery(route.query.kind));

function routeQueryWithReturn() {
  const query: Record<string, string> = {};
  if (typeof route.query[RETURN_TO_QUERY] === "string") {
    query[RETURN_TO_QUERY] = route.query[RETURN_TO_QUERY];
  }
  if (roomIdFromQuery.value != null) {
    query.roomId = String(roomIdFromQuery.value);
  }
  if (kindFromQuery.value !== "pc_main") {
    query.kind = kindFromQuery.value;
  }
  return query;
}

const TABS = [
  { key: "identity",   label: () => t("character.tabs.identity") },
  { key: "attributes", label: () => t("character.tabs.attributes") },
  { key: "features",   label: () => t("character.tabs.features") },
  { key: "spells",     label: () => t("character.tabs.spells") },
  { key: "equipment",  label: () => t("character.tabs.equipment") },
  { key: "extras",     label: () => t("character.tabs.extras") },
  { key: "token",      label: () => t("character.tabs.token") },
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
const formTokenConfigs = ref<TokenConfigUpsert[]>([]);

const isLoading = ref(false);
const isSaving = ref(false);
const importDialogOpen = ref(false);

const OPEN_IMPORT_QUERY = "openImport";

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
  tokenConfigs: formTokenConfigs.value,
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
    formTokenConfigs.value = (char.token_configs ?? []).map(tc => ({
      id: tc.id,
      is_primary: tc.is_primary,
      name: tc.name,
      asset_id: tc.asset_id,
      library_resource_id: tc.library_resource_id,
      panel_initial: tc.panel_initial,
      sort_order: tc.sort_order,
    }));
    // Stamp snapshot after data is loaded
    savedSnapshot.value = currentSnapshot.value;
  } catch {
    toasts.push({ message: t("character.errors.loadFailed"), tone: "danger" });
    router.push({ path: "/characters", query: routeQueryWithReturn() });
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
  if (formTokenConfigs.value.some(tc => !tc.name?.trim())) {
    activeTab.value = "token";
    toasts.push({ message: t("character.errors.tokenNameRequired"), tone: "danger" });
    return;
  }

  isSaving.value = true;
  try {
    const payload = {
      name: charName.value,
      system: formSystem.value,
      portrait_asset_id: formPortraitAssetId.value,
      token_image_asset_id: formPortraitAssetId.value ?? undefined,
      identity: formIdentity.value,
      flavor: formFlavor.value,
      attributes: formAttributes.value,
      features: formFeatures.value,
      spells: formSpells.value,
      equipment: formEquipment.value,
      extras: formExtras.value,
      token_configs: formTokenConfigs.value,
    };

    if (isEdit.value) {
      await patchCharacter(characterId.value!, payload);
      savedSnapshot.value = currentSnapshot.value;
      toasts.push({ message: t("character.toast.saved"), tone: "success" });
      if (backTo.value.startsWith("/rooms/")) {
        await router.push({ path: backTo.value });
      }
    } else if (roomIdFromQuery.value != null) {
      await postRoomCharacter(roomIdFromQuery.value, {
        kind: kindFromQuery.value,
        ...payload,
      });
      savedSnapshot.value = currentSnapshot.value;
      toasts.push({ message: t("room.characters.created"), tone: "success" });
      if (backTo.value.startsWith("/rooms/")) {
        await router.push({
          path: backTo.value,
          query: { openCharacterPopover: "1" },
        });
      } else {
        await router.push({
          path: `/rooms/${roomIdFromQuery.value}`,
          query: { openCharacterPopover: "1" },
        });
      }
    } else {
      const created = await createCharacter(payload);
      savedSnapshot.value = currentSnapshot.value;
      toasts.push({ message: t("character.toast.created"), tone: "success" });
      await router.replace({
        path: `/characters/${created.id}`,
        query: routeQueryWithReturn(),
      });
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function mergeImportBlock(
  defaults: Record<string, unknown>,
  patch: unknown,
): Record<string, unknown> {
  const base = structuredClone(defaults);
  if (!isRecord(patch)) return base;

  const incoming = structuredClone(patch);
  for (const [key, val] of Object.entries(incoming)) {
    if (isRecord(val) && isRecord(base[key])) {
      base[key] = { ...base[key], ...val };
    } else {
      base[key] = val;
    }
  }
  return base;
}

function applyImportDraft(draft: CharacterImportPreview) {
  const importedName = draft.name?.trim() ?? "";
  const identityName = isRecord(draft.identity)
    ? String(draft.identity.name ?? "").trim()
    : "";
  const resolvedName = importedName || identityName;

  formIdentity.value = mergeImportBlock(
    defaultIdentity() as unknown as Record<string, unknown>,
    isRecord(draft.identity)
      ? { ...draft.identity, ...(resolvedName ? { name: resolvedName } : {}) }
      : resolvedName
        ? { name: resolvedName }
        : undefined,
  );
  formFlavor.value = mergeImportBlock(
    defaultFlavor() as unknown as Record<string, unknown>,
    draft.flavor,
  );
  formAttributes.value = mergeImportBlock(
    defaultAttributes() as unknown as Record<string, unknown>,
    draft.attributes,
  );
  formFeatures.value = mergeImportBlock(
    defaultFeatures() as unknown as Record<string, unknown>,
    draft.features,
  );
  if (isRecord(draft.spells)) {
    formSpells.value = mergeImportBlock(
      defaultSpells() as unknown as Record<string, unknown>,
      draft.spells,
    );
  } else if (draft.spells === null) {
    formSpells.value = structuredClone(
      defaultSpells() as unknown as Record<string, unknown>,
    );
  }
  formEquipment.value = mergeImportBlock(
    defaultEquipment() as unknown as Record<string, unknown>,
    draft.equipment,
  );
  formExtras.value = mergeImportBlock({ notes: "" }, draft.extras);
}

function openImportDialog() {
  if (isDirty.value || isEdit.value) {
    if (!window.confirm(t("character.import.overwriteConfirm"))) return;
  }
  importDialogOpen.value = true;
}

function handleImportApplied(preview: CharacterImportPreview) {
  applyImportDraft(preview);
  activeTab.value = "identity";
  toasts.push({ message: t("character.import.applied"), tone: "success" });
}

function replaceQueryWithoutOpenImport() {
  const query: Record<string, string> = { ...routeQueryWithReturn() };
  for (const [key, value] of Object.entries(route.query)) {
    if (key === OPEN_IMPORT_QUERY) continue;
    if (typeof value === "string" && !(key in query)) {
      query[key] = value;
    }
  }
  return query;
}

function applyOpenImportFromQuery() {
  if (route.query[OPEN_IMPORT_QUERY] !== "1") return;
  importDialogOpen.value = true;
  void router.replace({ path: route.path, query: replaceQueryWithoutOpenImport() });
}

onMounted(async () => {
  if (isEdit.value) {
    await loadCharacter(characterId.value!);
  } else {
    savedSnapshot.value = currentSnapshot.value;
  }
  applyOpenImportFromQuery();
  window.addEventListener("beforeunload", handleBeforeUnload);
});
onUnmounted(() => window.removeEventListener("beforeunload", handleBeforeUnload));
</script>

<template>
  <AppPageShell :title="pageTitle" :back-to="backTo" :back-text="backTo.startsWith('/rooms/') ? backText : t('character.title')" :max-width="900">
    <template #actions>
      <BaseButton variant="default" @click="openImportDialog">
        {{ t("character.import.aiImport") }}
      </BaseButton>
      <BaseButton variant="primary" :loading="isSaving" :disabled="isSaving || !isDirty" @click="save">
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
          v-show="activeTab === 'identity'"
          v-model="formIdentity"
          v-model:flavor="formFlavor"
          :portrait-asset-id="formPortraitAssetId"
          @update:portrait-asset-id="formPortraitAssetId = $event"
        />

        <CharacterAttributesTab
          v-show="activeTab === 'attributes'"
          v-model="formAttributes"
          :identity-block="formIdentity"
        />

        <CharacterFeaturesTab
          v-show="activeTab === 'features'"
          v-model="formFeatures"
        />

        <CharacterSpellsTab
          v-show="activeTab === 'spells'"
          v-model="formSpells"
          :attributes-block="formAttributes"
        />

        <CharacterEquipmentTab
          v-show="activeTab === 'equipment'"
          v-model="formEquipment"
        />

        <CharacterExtrasTab
          v-show="activeTab === 'extras'"
          v-model="formExtras"
        />

        <CharacterTokenTab
          v-show="activeTab === 'token'"
          v-model="formTokenConfigs"
          :attributes-block="formAttributes"
          :equipment-block="formEquipment"
          :character-name="charName"
          :portrait-asset-id="formPortraitAssetId"
        />
      </div>
    </template>
  </AppPageShell>

  <CharacterImportDialog
    :open="importDialogOpen"
    @close="importDialogOpen = false"
    @imported="handleImportApplied"
  />
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
