<script setup lang="ts">
import { ref, computed, watch, toRef } from "vue";
import { useI18n } from "vue-i18n";
import {
  XMarkIcon,
  ArrowPathIcon,
  CheckIcon,
  PencilSquareIcon,
  PhotoIcon,
  PlusIcon,
  TrashIcon,
} from "@heroicons/vue/24/outline";
import {
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_CLASSES, DND5E_SKILLS, SPELLCASTING_ABILITY_OPTIONS,
  abilityMod, fmtMod,
  type AbilityKey,
} from "@/features/character/constants";
import type { TokenConfigUpsert, TokenPanelInitial } from "@/infra/api/character.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseTagInput from "@/ui/base/BaseTagInput.vue";
import AbilityScoresGrid from "@/features/character/components/AbilityScoresGrid.vue";
import SkillSaveCompactList, { type CompactRow } from "@/features/character/components/SkillSaveCompactList.vue";
import EquipmentItemsList from "@/features/character/components/EquipmentItemsList.vue";

type Item = { name: string; quantity: number; notes: string };
type TokenResource = { name: string; max: number; recovery: string };
type SkillProf = "none" | "proficient" | "expert" | "expertise";

const HIT_DIE_BY_CLASS: Record<string, number> = {
  artificer: 8,
  barbarian: 12,
  bard: 8,
  cleric: 8,
  druid: 8,
  fighter: 10,
  monk: 8,
  paladin: 10,
  ranger: 10,
  rogue: 8,
  sorcerer: 6,
  warlock: 8,
  wizard: 6,
};

const props = defineProps<{
  config: TokenConfigUpsert;
  identityBlock: Record<string, unknown>;
  attributesBlock: Record<string, unknown>;
  spellsBlock: Record<string, unknown> | null;
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

function profBonusFor(panel: TokenPanelInitial = draft.value): number {
  const bonus = Number(panel.proficiency_bonus ?? 2);
  return Number.isFinite(bonus) ? bonus : 2;
}

// ── Status fields (AC / HP / Speed / PP) ──────────────────────────────────
function setField(key: keyof TokenPanelInitial, raw: string) {
  const n = parseInt(raw);
  draft.value = { ...draft.value, [key]: isNaN(n) ? null : n };
}

// ── Spells ────────────────────────────────────────────────────────────────
const SPELL_LEVELS = ["0","1","2","3","4","5","6","7","8","9"] as const;
const expandedSpellLevels = ref<Set<string>>(new Set());

const spellcastingAbilityOptions = computed(() =>
  SPELLCASTING_ABILITY_OPTIONS.map((ability) => ({
    value: ability.value,
    label: t(ability.labelKey),
  })),
);

function setSpellcastingAbility(value: string) {
  draft.value = { ...draft.value, spellcasting_ability: value };
}

function getSpellDerivedValue(key: "spell_save_dc" | "spell_attack_bonus"): number {
  return draft.value[key]?.value ?? 0;
}

function setSpellDerivedValue(key: "spell_save_dc" | "spell_attack_bonus", raw: string) {
  const value = parseInt(raw);
  draft.value = {
    ...draft.value,
    [key]: { value: isNaN(value) ? 0 : value, breakdown: "" },
  };
}

function spellLevelLabel(level: string) {
  return level === "0"
    ? `0 环 (${t("character.spells.cantrips")})`
    : t("character.spells.level", { level });
}

function toggleSpellLevel(level: string) {
  const next = new Set(expandedSpellLevels.value);
  next.has(level) ? next.delete(level) : next.add(level);
  expandedSpellLevels.value = next;
}

function spellsForLevel(level: string): string[] {
  return draft.value.spellbook?.[level] ?? [];
}

function setSpellsForLevel(level: string, spells: string[]) {
  draft.value = {
    ...draft.value,
    spellbook: {
      ...(draft.value.spellbook ?? {}),
      [level]: spells,
    },
  };
}

// ── Resources ─────────────────────────────────────────────────────────────
const draftResources = computed(() => (draft.value.resources ?? []) as TokenResource[]);
const editingResourceIndex = ref<number | null>(null);
const editingResourceDraft = ref<TokenResource | null>(null);
const resourceRows = computed(() => {
  if (
    editingResourceIndex.value === draftResources.value.length &&
    editingResourceDraft.value
  ) {
    return [...draftResources.value, editingResourceDraft.value];
  }
  return draftResources.value;
});

function parseResourceNumber(raw: string) {
  const value = parseInt(raw);
  return isNaN(value) ? 0 : Math.max(0, value);
}

function updateResource(index: number, patch: Partial<TokenResource>) {
  const resources = draftResources.value.map((resource, i) =>
    i === index ? { ...resource, ...patch } : resource,
  );
  draft.value = { ...draft.value, resources };
}

function addResource() {
  editingResourceIndex.value = draftResources.value.length;
  editingResourceDraft.value = { name: "", max: 0, recovery: "" };
}

function removeResource(index: number) {
  draft.value = {
    ...draft.value,
    resources: draftResources.value.filter((_, i) => i !== index),
  };
  if (editingResourceIndex.value === index) {
    cancelResourceEdit();
  }
}

function beginResourceEdit(index: number) {
  editingResourceIndex.value = index;
  editingResourceDraft.value = { ...draftResources.value[index]! };
}

function updateResourceDraft(patch: Partial<TokenResource>) {
  if (!editingResourceDraft.value) return;
  editingResourceDraft.value = { ...editingResourceDraft.value, ...patch };
}

function normalizeResource(resource: TokenResource): TokenResource {
  return {
    name: resource.name.trim(),
    max: Math.max(0, resource.max),
    recovery: resource.recovery.trim(),
  };
}

function commitResourceEdit() {
  const index = editingResourceIndex.value;
  const next = editingResourceDraft.value;
  if (index == null || !next) return false;
  const normalized = normalizeResource(next);
  if (index >= draftResources.value.length) {
    draft.value = {
      ...draft.value,
      resources: [...draftResources.value, normalized],
    };
  } else {
    updateResource(index, normalized);
  }
  return true;
}

function saveResourceEdit() {
  if (!commitResourceEdit()) return;
  cancelResourceEdit();
}

function cancelResourceEdit() {
  editingResourceIndex.value = null;
  editingResourceDraft.value = null;
}

function hitDieForClass(rawName: unknown): number | null {
  const name = String(rawName ?? "").trim().toLowerCase();
  if (!name) return null;
  for (const key of DND5E_CLASSES) {
    if (name === key || name === t(`character.classes.${key}`).toLowerCase()) {
      return HIT_DIE_BY_CLASS[key] ?? null;
    }
  }
  return null;
}

function buildResourcesFromCharacter(): TokenResource[] {
  const resources: TokenResource[] = [];
  const hitDiceByDie = new Map<number, number>();
  const classes = (props.identityBlock.classes ?? []) as { name?: string; level?: number }[];
  for (const cls of classes) {
    const die = hitDieForClass(cls.name);
    if (!die) continue;
    const level = Math.max(1, Number(cls.level) || 1);
    hitDiceByDie.set(die, (hitDiceByDie.get(die) ?? 0) + level);
  }
  for (const [die, max] of [...hitDiceByDie.entries()].sort((a, b) => a[0] - b[0])) {
    resources.push({
      name: t("character.token.hitDiceResource", { die }),
      max,
      recovery: t("character.token.recoveryLongRest"),
    });
  }

  const slots = ((props.spellsBlock ?? {}).spell_slots_max ?? {}) as Record<string, number>;
  for (let level = 1; level <= 9; level += 1) {
    const max = Number(slots[String(level)] ?? 0);
    if (max <= 0) continue;
    resources.push({
      name: t("character.token.spellSlotResource", { level }),
      max,
      recovery: t("character.token.recoveryLongRest"),
    });
  }
  return resources;
}

// ── Rows for SkillSaveCompactList ──────────────────────────────────────────
function abilityShort(ability: string): string {
  return t(ABILITY_LABEL_KEYS[ability as AbilityKey]).slice(0, 2);
}

const saveRows = computed<CompactRow[]>(() =>
  ABILITY_KEYS.map(key => {
    const profs = (draft.value.saving_throw_profs ?? {}) as Record<string, boolean>;
    return {
      key,
      label: abilityShort(key),
      value: saveStrings.value[key] ?? "",
      placeholder: numToStr(abilityMod(abilityScores.value[key] ?? 10) + (profs[key] ? profBonusFor() : 0)),
      profState: (profs[key] ? "proficient" : "none") as CompactRow["profState"],
    };
  }),
);

const skillRows = computed<CompactRow[]>(() =>
  DND5E_SKILLS.map(sk => {
    const profs = (draft.value.skill_profs ?? {}) as Record<string, SkillProf>;
    const prof = profs[sk.key] ?? "none";
    const multiplier = prof === "proficient" ? 1 : (prof === "expert" || prof === "expertise") ? 2 : 0;
    return {
      key: sk.key,
      label: t(sk.labelKey),
      value: skillStrings.value[sk.key] ?? "",
      placeholder: numToStr(abilityMod(abilityScores.value[sk.ability] ?? 10) + profBonusFor() * multiplier),
      profState: (prof === "expertise" ? "expert" : prof) as CompactRow["profState"],
    };
  }),
);

function handleSaveUpdate(key: string, value: string) {
  saveStrings.value = { ...saveStrings.value, [key]: value };
}
function handleSkillUpdate(key: string, value: string) {
  skillStrings.value = { ...skillStrings.value, [key]: value };
}

function toggleSaveProf(key: string) {
  const profs = (draft.value.saving_throw_profs ?? {}) as Record<string, boolean>;
  draft.value = {
    ...draft.value,
    saving_throw_profs: { ...profs, [key]: !profs[key] },
  };
}

function cycleSkillProf(key: string) {
  const profs = (draft.value.skill_profs ?? {}) as Record<string, SkillProf>;
  const cur = profs[key] ?? "none";
  const next: SkillProf = cur === "none" ? "proficient" : cur === "proficient" ? "expert" : "none";
  draft.value = {
    ...draft.value,
    skill_profs: { ...profs, [key]: next },
  };
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
  cancelResourceEdit();
  const attrs = props.attributesBlock as Record<string, unknown>;
  const scores = (attrs.ability_scores ?? {}) as Record<string, number>;
  const derived = (attrs.derived ?? {}) as Record<string, { value: number }>;
  const saves = (attrs.saving_throws ?? {}) as Record<string, string>;
  const saveAutos = (attrs.saving_throw_autos ?? {}) as Record<string, boolean>;
  const saveProfs = (attrs.saving_throw_profs ?? {}) as Record<string, boolean>;
  const skills = (attrs.skill_values ?? {}) as Record<string, string>;
  const skillAutos = (attrs.skill_value_autos ?? {}) as Record<string, boolean>;
  const skillProfs = (attrs.skill_profs ?? {}) as Record<string, SkillProf>;

  const parseNum = (v: unknown) => {
    const raw = String(v ?? "").trim();
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  };
  const profBonus = parseNum(derived.proficiency_bonus?.value) ?? 2;
  const isAuto = (raw: unknown, flag: boolean | undefined) =>
    flag !== undefined ? flag : !String(raw ?? "").trim();

  const newSaves: Record<string, number | null> = {};
  for (const key of ABILITY_KEYS) {
    const raw = saves[key];
    const override = parseNum(raw);
    newSaves[key] = !isAuto(raw, saveAutos[key]) && override != null ? override : null;
  }

  const newSkills: Record<string, number | null> = {};
  for (const sk of DND5E_SKILLS) {
    const raw = skills[sk.key];
    const override = parseNum(raw);
    newSkills[sk.key] = !isAuto(raw, skillAutos[sk.key]) && override != null ? override : null;
  }

  const equipItems = ((props.equipmentBlock.items ?? []) as Item[]).map(item => ({
    name: item.name ?? "",
    quantity: item.quantity ?? 1,
    notes: item.notes ?? "",
  }));
  const spells = props.spellsBlock ?? {};

  const hpMax = parseNum(derived.max_hp?.value);
  draft.value = {
    ...draft.value,
    ability_scores: { ...scores },
    ac: parseNum(derived.ac?.value),
    hp_current: hpMax,
    hp_max: hpMax,
    initiative: parseNum(derived.initiative?.value),
    speed: parseNum(derived.speed?.value),
    pp: parseNum(derived.passive_perception?.value),
    proficiency_bonus: profBonus,
    saving_throws: newSaves,
    saving_throw_profs: { ...saveProfs },
    skills: newSkills,
    skill_profs: { ...skillProfs },
    items: equipItems,
    spellcasting_ability: (spells.spellcasting_ability as string | undefined) ?? "intelligence",
    spell_save_dc: {
      value: parseNum((spells.spell_save_dc as { value?: unknown } | undefined)?.value) ?? 0,
      breakdown: "",
    },
    spell_attack_bonus: {
      value: parseNum((spells.spell_attack_bonus as { value?: unknown } | undefined)?.value) ?? 0,
      breakdown: "",
    },
    spellbook: { ...((spells.spellbook ?? {}) as Record<string, string[]>) },
    resources: buildResourcesFromCharacter(),
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
  commitResourceEdit();
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
const tabs = ["overview", "skillsSaves", "spells", "resources", "inventory"] as const;
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
                <span class="stat-label">{{ t("character.token.initiative") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.initiative ?? ''"
                  :placeholder="'—'"
                  @change="setField('initiative', ($event.target as HTMLInputElement).value)"
                />
              </div>
              <div class="stat-item">
                <span class="stat-label">{{ t("character.token.proficiencyBonus") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="draft.proficiency_bonus ?? ''"
                  :placeholder="'—'"
                  @change="setField('proficiency_bonus', ($event.target as HTMLInputElement).value)"
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
          <div class="skill-save-stack">
            <div class="field-group">
              <div class="field-group-title">{{ t("character.token.savingThrows") }}</div>
              <SkillSaveCompactList
                :rows="saveRows"
                :show-prof-dots="true"
                :columns="6"
                @update-value="handleSaveUpdate"
                @toggle-prof="toggleSaveProf"
              />
            </div>
            <div class="field-group">
              <div class="field-group-title">{{ t("character.token.skills") }}</div>
              <SkillSaveCompactList
                :rows="skillRows"
                :show-prof-dots="true"
                :columns="3"
                @update-value="handleSkillUpdate"
                @toggle-prof="cycleSkillProf"
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

        <!-- Spells -->
        <div v-show="activeTab === 'spells'" class="panel-body">
          <div class="field-group">
            <div class="field-group-title">{{ t("character.spells.spellcastingAbility") }}</div>
            <div class="spell-stat-row">
              <div class="spell-stat-item ability-select-item">
                <span class="stat-label">{{ t("character.spells.spellcastingAbility") }}</span>
                <BaseSelect
                  :model-value="draft.spellcasting_ability ?? 'intelligence'"
                  :options="spellcastingAbilityOptions"
                  :width="150"
                  @update:model-value="setSpellcastingAbility"
                />
              </div>
              <div class="spell-stat-item">
                <span class="stat-label">{{ t("character.spells.spellSaveDC") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="getSpellDerivedValue('spell_save_dc')"
                  @change="setSpellDerivedValue('spell_save_dc', ($event.target as HTMLInputElement).value)"
                />
              </div>
              <div class="spell-stat-item">
                <span class="stat-label">{{ t("character.spells.spellAttackBonus") }}</span>
                <input
                  class="stat-input no-spin"
                  type="number"
                  :value="getSpellDerivedValue('spell_attack_bonus')"
                  @change="setSpellDerivedValue('spell_attack_bonus', ($event.target as HTMLInputElement).value)"
                />
              </div>
            </div>
          </div>

          <div class="field-group">
            <div class="field-group-title">{{ t("character.spells.spellbook") }}</div>
            <div class="spellbook-levels">
              <div v-for="level in SPELL_LEVELS" :key="level" class="spellbook-level">
                <button class="spellbook-toggle" type="button" @click="toggleSpellLevel(level)">
                  <span>{{ spellLevelLabel(level) }}</span>
                  <span class="spell-count">{{ spellsForLevel(level).length }}</span>
                  <span class="chevron" :class="{ open: expandedSpellLevels.has(level) }">▾</span>
                </button>
                <div v-if="expandedSpellLevels.has(level)" class="spellbook-list">
                  <BaseTagInput
                    :model-value="spellsForLevel(level)"
                    :placeholder="t('character.spells.spellPlaceholder')"
                    @update:model-value="setSpellsForLevel(level, $event)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Resources -->
        <div v-show="activeTab === 'resources'" class="panel-body resources-panel">
          <div class="resource-header">
            <BaseButton variant="default" @click="addResource">
              <span class="btn-icon-text">
                <AppIcon :icon="PlusIcon" :size="14" />
                {{ t("character.token.addResource") }}
              </span>
            </BaseButton>
          </div>

          <div v-if="!resourceRows.length" class="empty-resource">—</div>
          <div v-else class="resource-list">
            <div
              v-for="(resource, index) in resourceRows"
              :key="index"
              class="resource-row"
              :class="{ editing: editingResourceIndex === index && editingResourceDraft }"
            >
              <template v-if="editingResourceIndex === index && editingResourceDraft">
                <label class="resource-name">
                  <span class="resource-label">{{ t("character.token.resourceName") }}</span>
                  <input
                    class="resource-input"
                    type="text"
                    :value="editingResourceDraft.name"
                    :placeholder="t('character.token.resourceNamePlaceholder')"
                    @input="updateResourceDraft({ name: ($event.target as HTMLInputElement).value })"
                  />
                </label>
                <label class="resource-number">
                  <span class="resource-label">{{ t("character.token.resourceMax") }}</span>
                  <input
                    class="resource-input no-spin"
                    type="number"
                    min="0"
                    :value="editingResourceDraft.max"
                    @change="updateResourceDraft({ max: parseResourceNumber(($event.target as HTMLInputElement).value) })"
                  />
                </label>
                <label class="resource-recovery">
                  <span class="resource-label">{{ t("character.token.resourceRecovery") }}</span>
                  <input
                    class="resource-input"
                    type="text"
                    :value="editingResourceDraft.recovery"
                    :placeholder="t('character.token.resourceRecoveryPlaceholder')"
                    @input="updateResourceDraft({ recovery: ($event.target as HTMLInputElement).value })"
                  />
                </label>
                <div class="resource-actions">
                  <button
                    class="resource-icon-button confirm"
                    type="button"
                    :title="t('common.save')"
                    @click="saveResourceEdit"
                  >
                    <AppIcon :icon="CheckIcon" :size="16" />
                  </button>
                  <button
                    class="resource-icon-button"
                    type="button"
                    :title="t('common.cancel')"
                    @click="cancelResourceEdit"
                  >
                    <AppIcon :icon="XMarkIcon" :size="16" />
                  </button>
                </div>
              </template>
              <template v-else>
                <div class="resource-display">
                  <span class="resource-display-name">{{ resource.name || t("character.token.unnamedResource") }}</span>
                </div>
                <div class="resource-display-limit">
                  <span class="resource-limit-label">{{ t("character.token.resourceMax") }}</span>
                  <span class="resource-limit-value">{{ resource.max }}</span>
                </div>
                <div class="resource-display-recovery">
                  <span v-if="resource.recovery">{{ resource.recovery }}</span>
                  <span v-else class="resource-empty">—</span>
                </div>
                <div class="resource-actions">
                  <button
                    class="resource-icon-button"
                    type="button"
                    :title="t('character.token.editResource')"
                    @click="beginResourceEdit(index)"
                  >
                    <AppIcon :icon="PencilSquareIcon" :size="16" />
                  </button>
                  <button
                    class="resource-icon-button danger"
                    type="button"
                    :title="t('character.token.removeResource')"
                    @click="removeResource(index)"
                  >
                    <AppIcon :icon="TrashIcon" :size="16" />
                  </button>
                </div>
              </template>
            </div>
          </div>
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
  width: min(860px, 100%);
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
  flex: 1; overflow-y: auto; overflow-x: hidden;
  padding: 20px; display: grid; gap: 20px;
  align-content: start;
  min-width: 0;
}

/* Field groups */
.field-group { display: grid; gap: 10px; min-width: 0; }
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

/* Skills and saves layout */
.skill-save-stack {
  display: grid;
  gap: 22px;
  min-width: 0;
}

/* Spells */
.spell-stat-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) minmax(140px, 1fr) minmax(140px, 1fr);
  gap: 12px;
  align-items: center;
  min-width: 0;
}

.spell-stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.ability-select-item {
  justify-content: flex-start;
}

.spellbook-levels {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.spellbook-level {
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  overflow: hidden;
  min-width: 0;
}

.spellbook-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  background: var(--c-surface-raised);
  color: var(--c-text);
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
}

.spellbook-toggle:hover {
  background: var(--c-hover);
}

.spell-count {
  min-width: 20px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--c-surface);
  color: var(--c-text-muted);
  font-size: 11px;
  text-align: center;
}

.chevron {
  margin-left: auto;
  transition: transform 0.15s;
}

.chevron.open {
  transform: rotate(180deg);
}

.spellbook-list {
  padding: 10px 12px;
  background: var(--c-surface);
}

/* Resources */
.resources-panel {
  gap: 6px;
}

.resource-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.empty-resource {
  font-size: 13px;
  color: var(--c-text-muted);
}

.resource-list {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.resource-row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) max-content max-content auto;
  gap: 14px;
  align-items: center;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface-raised);
}

.resource-row.editing {
  grid-template-columns: minmax(180px, 1fr) 96px minmax(140px, 0.8fr) auto;
  gap: 10px;
  align-items: center;
}

.resource-display {
  min-width: 0;
  display: flex;
  align-items: center;
  color: var(--c-text);
}

.resource-display-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  font-size: 14px;
}

.resource-display-recovery {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 7px;
  border: 1px solid var(--c-border);
  border-radius: 999px;
  background: var(--c-surface);
  color: var(--c-text-muted);
  font-size: 11px;
  font-weight: 600;
  justify-self: start;
}

.resource-display-limit {
  justify-self: start;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
}

.resource-limit-label {
  color: var(--c-text-muted);
  font-size: 10px;
  font-weight: 700;
}

.resource-limit-value {
  color: var(--c-text);
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.resource-empty {
  color: var(--c-text-muted);
}

.resource-name,
.resource-number,
.resource-recovery {
  display: grid;
  gap: 4px;
  min-width: 0;
  align-self: end;
}

.resource-label {
  color: var(--c-text-muted);
  font-size: 11px;
  font-weight: 600;
}

.resource-input {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text);
  padding: 6px 8px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
}

.resource-input:focus {
  border-color: var(--c-accent);
}

.resource-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  align-self: center;
}

.resource-icon-button {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text-muted);
  cursor: pointer;
}

.resource-icon-button:hover {
  color: var(--c-text);
  border-color: var(--c-accent);
}

.resource-icon-button.confirm:hover {
  color: var(--c-success, #3aa675);
  border-color: color-mix(in srgb, var(--c-success, #3aa675) 60%, var(--c-border));
}

.resource-icon-button.danger:hover {
  color: var(--c-danger);
  border-color: color-mix(in srgb, var(--c-danger) 60%, var(--c-border));
}

/* Footer */
.dialog-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 16px 20px; border-top: 1px solid var(--c-border);
}

@media (max-width: 720px) {
  .dialog {
    width: 100%;
  }

  .skill-save-stack :deep(.compact-list) {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }

  .spell-stat-row {
    grid-template-columns: 1fr;
  }

  .resource-row.editing {
    grid-template-columns: 1fr;
  }
}
</style>
