<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon } from "@heroicons/vue/24/outline";
import { createLibraryResource } from "@/infra/api/library.api";
import { ABILITY_KEYS, DND5E_SKILLS, defaultTokenConfig, type AbilityKey } from "@/features/character/constants";
import type { TokenConfigUpsert, TokenPanelInitial } from "@/infra/api/character.api";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import TokenCard from "@/features/character/components/TokenCard.vue";
import TokenPanelEditorDialog from "@/features/character/components/TokenPanelEditorDialog.vue";
import AvatarCropDialog from "@/ui/domain/avatar/AvatarCropDialog.vue";

type Item = { name: string; quantity: number; notes: string };

const props = defineProps<{
  modelValue: TokenConfigUpsert[];
  attributesBlock: Record<string, unknown>;
  equipmentBlock: Record<string, unknown>;
  characterName: string;
  portraitAssetId: number | null;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: TokenConfigUpsert[]): void }>();
const { t } = useI18n();

const primaryConfig = () => props.modelValue.find(c => c.is_primary) ?? null;
const secondaryConfigs = () => props.modelValue.filter(c => !c.is_primary);

function push(configs: TokenConfigUpsert[]) {
  emit("update:modelValue", configs);
}

// ── Build primary token from character sheet ───────────────────────────────
function buildPanelFromCharacter(): TokenPanelInitial {
  const attrs = props.attributesBlock;
  const scores = (attrs.ability_scores ?? {}) as Record<string, number>;
  const derived = (attrs.derived ?? {}) as Record<string, { value: number }>;
  const saves = (attrs.saving_throws ?? {}) as Record<string, string>;
  const skills = (attrs.skill_values ?? {}) as Record<string, string>;

  const parseNum = (v: unknown): number | null => {
    const n = parseInt(String(v));
    return isNaN(n) ? null : n;
  };

  const newSaves: Record<string, number | null> = {};
  for (const key of ABILITY_KEYS) {
    newSaves[key] = parseNum(saves[key as AbilityKey]);
  }

  const newSkills: Record<string, number | null> = {};
  for (const sk of DND5E_SKILLS) {
    newSkills[sk.key] = parseNum(skills[sk.key]);
  }

  const equipItems = ((props.equipmentBlock.items ?? []) as Item[]).map(item => ({
    name: item.name ?? "",
    quantity: item.quantity ?? 1,
    notes: item.notes ?? "",
  }));

  const hpMax = parseNum(derived["max_hp"]?.value);
  return {
    ability_scores: { ...scores },
    ac: parseNum(derived["ac"]?.value),
    hp_current: hpMax,
    hp_max: hpMax,
    speed: parseNum(derived["speed"]?.value),
    pp: parseNum(derived["passive_perception"]?.value),
    saving_throws: newSaves,
    skills: newSkills,
    items: equipItems,
    weapons: [],
    armor: [],
    inherit_items_from_character: true,
  };
}

function addPrimary() {
  const cfg: TokenConfigUpsert = {
    id: undefined,
    is_primary: true,
    name: props.characterName,
    asset_id: props.portraitAssetId,
    sort_order: 0,
    panel_initial: buildPanelFromCharacter(),
  };
  push([cfg, ...secondaryConfigs()]);
}

function addSecondary() {
  const primary = primaryConfig() ? [primaryConfig()!] : [];
  push([...primary, ...secondaryConfigs(), defaultTokenConfig(false, secondaryConfigs().length) as TokenConfigUpsert]);
}

function removePrimary() { push(secondaryConfigs()); }

function removeSecondary(idx: number) {
  const primary = primaryConfig() ? [primaryConfig()!] : [];
  push([...primary, ...secondaryConfigs().filter((_, i) => i !== idx)]);
}

function copySecondary(idx: number) {
  const src = secondaryConfigs()[idx];
  const copy: TokenConfigUpsert = {
    id: undefined,
    is_primary: false,
    name: src.name,
    asset_id: src.asset_id,
    library_resource_id: src.library_resource_id,
    sort_order: secondaryConfigs().length,
    panel_initial: src.panel_initial ? { ...src.panel_initial } : undefined,
  };
  const primary = primaryConfig() ? [primaryConfig()!] : [];
  const secs = secondaryConfigs();
  push([...primary, ...secs.slice(0, idx + 1), copy, ...secs.slice(idx + 1)]);
}

function patchAt(target: TokenConfigUpsert, patch: Partial<TokenConfigUpsert>) {
  push(props.modelValue.map(c => c === target ? { ...c, ...patch } : c));
}

// ── Image upload + crop ───────────────────────────────────────────────────
const uploadingFor = ref<TokenConfigUpsert | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const cropOpen = ref(false);
const cropFile = ref<File | null>(null);

function triggerImagePick(cfg: TokenConfigUpsert) {
  uploadingFor.value = cfg;
  fileInputRef.value?.click();
}

function onImagePicked(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  (e.target as HTMLInputElement).value = "";
  if (!file || !uploadingFor.value) return;
  cropFile.value = file;
  cropOpen.value = true;
}

async function onCropDone(file: File) {
  const target = uploadingFor.value;
  if (!target) return;
  uploadingFor.value = null;
  cropFile.value = null;
  try {
    const name = target.name || props.characterName || file.name.replace(/\.[^.]+$/, "");
    const resource = await createLibraryResource({ type: "token", name, image: file });
    patchAt(target, { library_resource_id: resource.id, asset_id: resource.primary_asset_id });
  } catch { /* ignore */ }
}

function onCropCancel() {
  uploadingFor.value = null;
  cropFile.value = null;
}

// ── Panel editor ──────────────────────────────────────────────────────────
const editorOpen = ref(false);
const editingConfig = ref<TokenConfigUpsert | null>(null);

function openEditor(cfg: TokenConfigUpsert) {
  editingConfig.value = cfg;
  editorOpen.value = true;
}

function onPanelSaved(updated: TokenConfigUpsert) {
  const target = editingConfig.value;
  if (!target) return;
  push(props.modelValue.map(c => c === target ? updated : c));
  editorOpen.value = false;
  editingConfig.value = null;
}

function closeEditor() {
  editorOpen.value = false;
  editingConfig.value = null;
}
</script>

<template>
  <!-- Single root element: required for v-show in parent to work correctly -->
  <div class="tab-content">
    <input ref="fileInputRef" type="file" accept="image/*" class="sr-only" @change="onImagePicked" />

    <AvatarCropDialog
      v-model="cropOpen"
      :file="cropFile"
      :title="t('profile.crop.title')"
      :output-size="512"
      @done="onCropDone"
      @cancel="onCropCancel"
    />

    <!-- Primary Token -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.token.primaryToken") }}</span>
      </div>
      <div v-if="!primaryConfig()" class="empty-row">
        <BaseButton variant="default" @click="addPrimary">
          <span class="btn-icon-text">
            <AppIcon :icon="PlusIcon" :size="14" />
            {{ t("character.token.generateFromSheet") }}
          </span>
        </BaseButton>
      </div>
      <TokenCard
        v-else
        :config="primaryConfig()!"
        :is-primary="true"
        @edit="openEditor(primaryConfig()!)"
        @pick-image="triggerImagePick(primaryConfig()!)"
        @remove="removePrimary"
        @update:name="patchAt(primaryConfig()!, { name: $event })"
      />
    </div>

    <!-- Secondary Tokens -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.token.secondaryTokens") }}</span>
        <BaseButton variant="default" @click="addSecondary">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.token.addSecondary") }}</span>
        </BaseButton>
      </div>
      <div v-if="!secondaryConfigs().length" class="empty-hint">{{ t("character.token.noSecondary") }}</div>
      <TokenCard
        v-for="(cfg, i) in secondaryConfigs()"
        :key="i"
        :config="cfg"
        :is-primary="false"
        @edit="openEditor(cfg)"
        @pick-image="triggerImagePick(cfg)"
        @remove="removeSecondary(i)"
        @copy="copySecondary(i)"
        @update:name="patchAt(cfg, { name: $event })"
      />
    </div>

    <!-- Panel editor dialog — Teleport renders to body regardless of v-show on parent -->
    <TokenPanelEditorDialog
      v-if="editorOpen"
      :config="(editingConfig as TokenConfigUpsert)"
      :attributes-block="attributesBlock"
      :equipment-block="equipmentBlock"
      @save="onPanelSaved"
      @close="closeEditor"
    />
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 24px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
.section { display: grid; gap: 10px; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.empty-row { display: flex; align-items: center; gap: 12px; }
.empty-hint { font-size: 13px; color: var(--c-text-muted); }
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }
</style>
