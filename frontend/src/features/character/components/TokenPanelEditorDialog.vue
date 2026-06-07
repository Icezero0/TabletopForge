<script setup lang="ts">
import { ref, computed, watch, toRef } from "vue";
import { useI18n } from "vue-i18n";
import { XMarkIcon, ArrowPathIcon, PhotoIcon } from "@heroicons/vue/24/outline";
import {
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_SKILLS,
  abilityMod, fmtMod,
  type AbilityKey,
} from "@/features/character/constants";
import type { TokenConfigUpsert, TokenPanelInitial } from "@/infra/api/character.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import AbilityScoresGrid from "@/features/character/components/AbilityScoresGrid.vue";
import SkillSaveCompactList, { type CompactRow } from "@/features/character/components/SkillSaveCompactList.vue";
import EquipmentItemsList from "@/features/character/components/EquipmentItemsList.vue";

type Item = { name: string; quantity: number; notes: string };

const props = defineProps<{
  config: TokenConfigUpsert;
  attributesBlock: Record<string, unknown>;
  equipmentBlock: Record<string, unknown>;
}>();
const emit = defineEmits<{
  (e: "save", updated: TokenConfigUpsert): void;
  (e: "close"): void;
}>();

const { t } = useI18n();

// ── Token avatar ───────────────────────────────────────────────────────────
const assetId = toRef(() => props.config.asset_id ?? undefined);
const { url: avatarUrl } = useAuthenticatedAssetUrl(assetId);

// ── Local draft ────────────────────────────────────────────────────────────
const draft = ref<TokenPanelInitial>(JSON.parse(JSON.stringify(props.config.panel_initial ?? {})));

// ── String buffers for saving throws / skills ──────────────────────────────
// Allows typing "+", "-" mid-entry without the field resetting.
// Values are flushed to number|null only in save().
const saveStrings = ref<Record<string, string>>({});
const skillStrings = ref<Record<string, string>>({});

function numToStr(n: number | null | undefined): string {
  return n != null ? fmtMod(n) : "";
}
function initStringBuffers(panel: TokenPanelInitial) {
  const st = (panel.saving_throws ?? {}) as Record<string, number | null>;
  const sv = (panel.skills ?? {}) as Record<string, number | null>;
  const ss: Record<string, string> = {};
  const ks: Record<string, string> = {};
  for (const key of ABILITY_KEYS) ss[key] = numToStr(st[key]);
  for (const sk of DND5E_SKILLS) ks[sk.key] = numToStr(sv[sk.key]);
  saveStrings.value = ss;
  skillStrings.value = ks;
}
initStringBuffers(draft.value);

watch(() => props.config, (cfg) => {
  draft.value = JSON.parse(JSON.stringify(cfg.panel_initial ?? {}));
  initStringBuffers(draft.value);
}, { deep: true });

// ── Ability scores ─────────────────────────────────────────────────────────
const abilityScores = computed(() => {
  const s = (draft.value.ability_scores ?? {}) as Record<string, number>;
  const result: Record<string, number> = {};
  for (const k of ABILITY_KEYS) result[k] = Number(s[k] ?? 10);
  return result;
});
function updateAbilityScores(v: Record<string, number>) {
  draft.value = { ...draft.value, ability_scores: v };
}

// ── Status fields (AC / HP / Speed / PP) ──────────────────────────────────
function setField(key: keyof TokenPanelInitial, raw: string) {
  const n = parseInt(raw);
  draft.value = { ...draft.value, [key]: isNaN(n) ? null : n };
}

// ── Rows for SkillSaveCompactList ──────────────────────────────────────────
function abilityShort(ability: string): string {
  return t(ABILITY_LABEL_KEYS[ability as AbilityKey]).slice(0, 2);
}

const saveRows = computed<CompactRow[]>(() =>
  ABILITY_KEYS.map(key => ({
    key,
    label: abilityShort(key),
    value: saveStrings.value[key] ?? "",
    placeholder: fmtMod(abilityMod(abilityScores.value[key] ?? 10)),
  })),
);

const skillRows = computed<CompactRow[]>(() =>
  DND5E_SKILLS.map(sk => ({
    key: sk.key,
    label: t(sk.labelKey),
    value: skillStrings.value[sk.key] ?? "",
    placeholder: fmtMod(abilityMod(abilityScores.value[sk.ability] ?? 10)),
  })),
);

function handleSaveUpdate(key: string, value: string) {
  saveStrings.value = { ...saveStrings.value, [key]: value };
}
function handleSkillUpdate(key: string, value: string) {
  skillStrings.value = { ...skillStrings.value, [key]: value };
}

// ── Items ──────────────────────────────────────────────────────────────────
const isPrimary = computed(() => props.config.is_primary);
const draftItems = computed(() => (draft.value.items ?? []) as Item[]);
const inventoryItems = computed<Item[]>(() =>
  isPrimary.value
    ? ((props.equipmentBlock.items ?? []) as Item[])
    : draftItems.value
);
function updateDraftItems(v: Item[]) {
  draft.value = { ...draft.value, items: v };
}

// ── Sync from character sheet ──────────────────────────────────────────────
function syncFromCharacter() {
  const attrs = props.attributesBlock as Record<string, unknown>;
  const scores = (attrs.ability_scores ?? {}) as Record<string, number>;
  const derived = (attrs.derived ?? {}) as Record<string, { value: number }>;
  const saves = (attrs.saving_throws ?? {}) as Record<string, string>;
  const skills = (attrs.skill_values ?? {}) as Record<string, string>;

  const parseNum = (v: unknown) => {
    const n = parseInt(String(v));
    return isNaN(n) ? null : n;
  };

  const newSaves: Record<string, number | null> = {};
  for (const key of ABILITY_KEYS) newSaves[key] = parseNum(saves[key]);

  const newSkills: Record<string, number | null> = {};
  for (const sk of DND5E_SKILLS) newSkills[sk.key] = parseNum(skills[sk.key]);

  const equipItems = ((props.equipmentBlock.items ?? []) as Item[]).map(item => ({
    name: item.name ?? "",
    quantity: item.quantity ?? 1,
    notes: item.notes ?? "",
  }));

  const hpMax = parseNum(derived.max_hp?.value);
  draft.value = {
    ...draft.value,
    ability_scores: { ...scores },
    ac: parseNum(derived.ac?.value),
    hp_current: hpMax,
    hp_max: hpMax,
    speed: parseNum(derived.speed?.value),
    pp: parseNum(derived.passive_perception?.value),
    saving_throws: newSaves,
    skills: newSkills,
    items: equipItems,
  };
  // Keep string buffers in sync with the synced numbers
  const newSaveStrings: Record<string, string> = {};
  const newSkillStrings: Record<string, string> = {};
  for (const key of ABILITY_KEYS) newSaveStrings[key] = numToStr(newSaves[key]);
  for (const sk of DND5E_SKILLS) newSkillStrings[sk.key] = numToStr(newSkills[sk.key]);
  saveStrings.value = newSaveStrings;
  skillStrings.value = newSkillStrings;
}

// ── Save / close ───────────────────────────────────────────────────────────
function save() {
  // Flush string buffers → number|null before emitting
  const newSaves: Record<string, number | null> = {};
  for (const key of ABILITY_KEYS) {
    const n = parseInt(saveStrings.value[key] ?? "");
    newSaves[key] = isNaN(n) ? null : n;
  }
  const newSkills: Record<string, number | null> = {};
  for (const sk of DND5E_SKILLS) {
    const n = parseInt(skillStrings.value[sk.key] ?? "");
    newSkills[sk.key] = isNaN(n) ? null : n;
  }
  const finalDraft = { ...draft.value, saving_throws: newSaves, skills: newSkills };
  emit("save", { ...props.config, panel_initial: finalDraft });
}

// ── Tabs ───────────────────────────────────────────────────────────────────
const tabs = ["overview", "skillsSaves", "inventory"] as const;
type PanelTab = (typeof tabs)[number];
const activeTab = ref<PanelTab>("overview");
</script>

<template>
  <Teleport to="body">
    <div class="backdrop">
      <div class="dialog">

        <!-- Header -->
        <div class="dialog-header">
          <div class="header-identity">
            <div class="header-avatar">
              <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
              <AppIcon v-else :icon="PhotoIcon" :size="22" class="avatar-placeholder-icon" />
            </div>
            <div class="dialog-title-row">
              <h3 class="dialog-title">{{ config.name || t("character.token.unnamed") }}</h3>
              <span class="dialog-subtitle">{{ t("character.token.panelEditor") }}</span>
            </div>
          </div>
          <div class="header-actions">
            <BaseButton
              v-if="config.is_primary"
              variant="default"
              :title="t('character.token.syncFromCharacter')"
              @click="syncFromCharacter"
            >
              <span class="btn-icon-text">
                <AppIcon :icon="ArrowPathIcon" :size="14" />
                {{ t("character.token.syncFromCharacter") }}
              </span>
            </BaseButton>
            <button class="close-btn" @click="emit('close')">
              <AppIcon :icon="XMarkIcon" :size="18" />
            </button>
          </div>
        </div>

        <!-- Sub-tabs -->
        <div class="sub-tab-nav">
          <button
            v-for="tab in tabs"
            :key="tab"
            class="sub-tab-btn"
            :class="{ active: activeTab === tab }"
            @click="activeTab = tab"
          >
            {{ t(`character.token.panelTab.${tab}`) }}
          </button>
        </div>

        <!-- Overview -->
        <div v-show="activeTab === 'overview'" class="panel-body">
          <!-- Ability Scores -->
          <div class="field-group">
            <div class="field-group-title">{{ t("character.token.abilityScores") }}</div>
            <AbilityScoresGrid
              :model-value="abilityScores"
              @update:model-value="updateAbilityScores"
            />
          </div>

          <!-- Status -->
          <div class="field-group">
            <div class="field-group-title">{{ t("character.token.derivedStats") }}</div>
            <div class="status-bar">
              <div class="stat-item">
                <span class="stat-label">{{ t("character.token.ac") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.ac ?? ''"
                  :placeholder="'—'"
                  @change="setField('ac', ($event.target as HTMLInputElement).value)"
                />
              </div>
              <div class="stat-item hp-item">
                <span class="stat-label">{{ t("character.token.hp") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.hp_current ?? ''"
                  :placeholder="t('character.token.hpCurrentPlaceholder')"
                  @change="setField('hp_current', ($event.target as HTMLInputElement).value)"
                />
                <span class="stat-sep">/</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.hp_max ?? ''"
                  :placeholder="t('character.token.hpMaxPlaceholder')"
                  @change="setField('hp_max', ($event.target as HTMLInputElement).value)"
                />
              </div>
              <div class="stat-item">
                <span class="stat-label">{{ t("character.token.speed") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.speed ?? ''"
                  :placeholder="'—'"
                  @change="setField('speed', ($event.target as HTMLInputElement).value)"
                />
              </div>
              <div class="stat-item">
                <span class="stat-label">{{ t("character.token.pp") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.pp ?? ''"
                  :placeholder="'—'"
                  @change="setField('pp', ($event.target as HTMLInputElement).value)"
                />
              </div>
            </div>
          </div>

          <!-- Weapons / Armor placeholders -->
          <div class="field-group placeholder-group">
            <div class="field-group-title">{{ t("character.token.weapons") }}</div>
            <div class="placeholder-hint">{{ t("character.token.comingSoon") }}</div>
          </div>
          <div class="field-group placeholder-group">
            <div class="field-group-title">{{ t("character.token.armor") }}</div>
            <div class="placeholder-hint">{{ t("character.token.comingSoon") }}</div>
          </div>
        </div>

        <!-- Skills & Saves -->
        <div v-show="activeTab === 'skillsSaves'" class="panel-body">
          <div class="two-col">
            <div class="field-group">
              <div class="field-group-title">{{ t("character.token.savingThrows") }}</div>
              <SkillSaveCompactList
                :rows="saveRows"
                :columns="2"
                @update-value="handleSaveUpdate"
              />
            </div>
            <div class="field-group">
              <div class="field-group-title">{{ t("character.token.skills") }}</div>
              <SkillSaveCompactList
                :rows="skillRows"
                :columns="2"
                @update-value="handleSkillUpdate"
              />
            </div>
          </div>
        </div>

        <!-- Inventory -->
        <div v-show="activeTab === 'inventory'" class="panel-body">
          <EquipmentItemsList
            :model-value="inventoryItems"
            :readonly="isPrimary"
            @update:model-value="updateDraftItems"
          />
        </div>

        <!-- Footer -->
        <div class="dialog-footer">
          <BaseButton variant="default" @click="emit('close')">{{ t("common.cancel") }}</BaseButton>
          <BaseButton variant="primary" @click="save">{{ t("common.save") }}</BaseButton>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed; inset: 0; z-index: 600;
  display: grid; place-items: center;
  background: rgba(0,0,0,0.5); padding: 16px;
}

.dialog {
  width: min(720px, 100%);
  max-height: 90vh;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.dialog-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 0; gap: 12px;
}
.header-identity { display: flex; align-items: center; gap: 12px; }
.header-avatar {
  width: 44px; height: 44px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid var(--c-border);
  background: var(--c-surface-raised);
  display: flex; align-items: center; justify-content: center;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder-icon { color: var(--c-text-muted); }
.dialog-title-row { display: flex; align-items: baseline; gap: 8px; }
.dialog-title { margin: 0; font-size: 16px; font-weight: 600; }
.dialog-subtitle { font-size: 13px; color: var(--c-text-muted); }
.header-actions { display: flex; align-items: center; gap: 8px; }
.close-btn {
  background: none; border: none; cursor: pointer;
  color: var(--c-text-muted); padding: 4px; border-radius: var(--r-1);
  display: flex; align-items: center; transition: color 0.12s;
}
.close-btn:hover { color: var(--c-text); }
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }

/* Sub-tabs */
.sub-tab-nav {
  display: flex; gap: 2px;
  border-bottom: 1px solid var(--c-border);
  padding: 0 20px; margin-top: 12px;
}
.sub-tab-btn {
  background: none; border: none;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  padding: 8px 14px; font-size: 13px; font-weight: 500;
  color: var(--c-text-muted); cursor: pointer;
  transition: color 0.15s, border-color 0.15s; white-space: nowrap;
}
.sub-tab-btn:hover { color: var(--c-text); }
.sub-tab-btn.active { color: var(--c-text); border-bottom-color: var(--c-accent); }

/* Panel body */
.panel-body {
  flex: 1; overflow-y: auto;
  padding: 20px; display: grid; gap: 20px;
  align-content: start;
}

/* Field groups */
.field-group { display: grid; gap: 10px; }
.field-group-title {
  font-size: 13px; font-weight: 600; color: var(--c-text-muted);
  text-transform: uppercase; letter-spacing: 0.05em;
}

/* Status bar */
.status-bar { display: flex; flex-wrap: wrap; gap: 20px 28px; align-items: center; }
.stat-item { display: flex; align-items: center; gap: 7px; }
.hp-item { gap: 5px; }
.stat-label { font-size: 12px; color: var(--c-text-muted); white-space: nowrap; }
.stat-sep { font-size: 14px; color: var(--c-text-muted); }
.stat-input {
  width: 58px; text-align: center;
  border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text);
  padding: 5px 4px; font-size: 14px; font-family: inherit; outline: none;
}
.stat-input:focus { border-color: var(--c-accent); }
.stat-input::placeholder { color: var(--c-text-muted); opacity: 0.5; }
.hp-item .stat-input { width: 48px; }
.no-spin { -moz-appearance: textfield; }
.no-spin::-webkit-inner-spin-button, .no-spin::-webkit-outer-spin-button { -webkit-appearance: none; }

/* Placeholders */
.placeholder-group { opacity: 0.5; }
.placeholder-hint { font-size: 13px; color: var(--c-text-muted); font-style: italic; }

/* Two-column layout */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }

/* Footer */
.dialog-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 16px 20px; border-top: 1px solid var(--c-border);
}
</style>
