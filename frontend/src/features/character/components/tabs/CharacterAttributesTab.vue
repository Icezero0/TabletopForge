<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_SKILLS,
  abilityMod, fmtMod,
} from "@/features/character/constants";
import BaseTagInput from "@/ui/base/BaseTagInput.vue";
import AbilityScoresGrid from "@/features/character/components/AbilityScoresGrid.vue";
import SkillSaveCompactList, { type CompactRow } from "@/features/character/components/SkillSaveCompactList.vue";

const props = defineProps<{
  modelValue: Record<string, unknown>;
  identityBlock: Record<string, unknown>;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function modelSnapshot(): Record<string, unknown> {
  const raw = props.modelValue;
  if (raw !== null && typeof raw === "object" && !Array.isArray(raw)) return raw;
  return {};
}

function identitySnapshot(): Record<string, unknown> {
  const raw = props.identityBlock;
  if (raw !== null && typeof raw === "object" && !Array.isArray(raw)) return raw;
  return {};
}

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...modelSnapshot(), [key]: value });
}

function updateMultiple(patches: Record<string, unknown>) {
  emit("update:modelValue", { ...modelSnapshot(), ...patches });
}

// ── Ability scores ──────────────────────────────────────────────────────────
const scores = computed(() => {
  const s = (modelSnapshot().ability_scores ?? {}) as Record<string, number>;
  const result: Record<string, number> = {};
  for (const k of ABILITY_KEYS) result[k] = Number(s[k] ?? 10);
  return result;
});
// ── Derived stats ───────────────────────────────────────────────────────────
const DERIVED_KEYS = ["ac", "max_hp", "speed", "initiative", "proficiency_bonus", "passive_perception"] as const;
type DerivedKey = (typeof DERIVED_KEYS)[number];

function getDerived(key: DerivedKey): { value: number; breakdown: string } {
  const d = (modelSnapshot().derived ?? {}) as Record<string, unknown>;
  const entry = d[key];
  if (entry && typeof entry === "object" && !Array.isArray(entry)) {
    const obj = entry as { value?: unknown; breakdown?: unknown };
    return {
      value: Number(obj.value) || 0,
      breakdown: String(obj.breakdown ?? ""),
    };
  }
  return { value: 0, breakdown: "" };
}
function setDerived(key: DerivedKey, field: "value" | "breakdown", raw: string) {
  const current = getDerived(key);
  const updated = { ...current, [field]: field === "value" ? (parseInt(raw) || 0) : raw };
  update("derived", { ...(modelSnapshot().derived as Record<string, unknown> ?? {}), [key]: updated });
}

// Hit dice by class (DnD 5e)
const HIT_DIE: Record<string, number> = {
  artificer: 8, barbarian: 12, bard: 8, cleric: 8, druid: 8,
  fighter: 10, monk: 8, paladin: 10, ranger: 10, rogue: 8,
  sorcerer: 6, warlock: 8, wizard: 6,
};

function setDerivedBoth(key: DerivedKey, value: number, breakdown: string) {
  update("derived", {
    ...(modelSnapshot().derived as Record<string, unknown> ?? {}),
    [key]: { value, breakdown },
  });
}

function autoCalcAC() {
  const dex = abilityMod(scores.value.dexterity ?? 10);
  setDerivedBoth("ac", 10 + dex, `10 + 敏捷 ${dex}`);
}
function autoCalcInitiative() {
  const dex = abilityMod(scores.value.dexterity ?? 10);
  setDerivedBoth("initiative", dex, `敏捷修正 ${dex}`);
}
function autoCalcPassivePerception() {
  const wis = abilityMod(scores.value.wisdom ?? 10);
  const profBonusVal = getDerived("proficiency_bonus").value ?? 2;
  const percVal = wis + profBonusVal;
  setDerivedBoth("passive_perception", 10 + percVal, `10 + 察觉 ${percVal}`);
}
function autoCalcProfBonus() {
  const classList = (identitySnapshot().classes as { level: number }[]) ?? [];
  const totalLevel = Math.max(1, classList.reduce((sum, c) => sum + (Number(c.level) || 0), 0));
  const bonus = Math.floor((totalLevel - 1) / 4) + 2;
  setDerivedBoth("proficiency_bonus", bonus, `角色总等级 ${totalLevel}`);
}
function autoCalcMaxHP() {
  const classList = (identitySnapshot().classes as { name: string; level: number }[]) ?? [];
  const con = abilityMod(scores.value.constitution ?? 10);
  const totalLevel = classList.reduce((sum, c) => sum + (Number(c.level) || 0), 0);
  if (totalLevel === 0) return;

  let hp = 0;
  let isFirst = true;
  const parts: string[] = [];
  for (const cls of classList) {
    const lvl = Number(cls.level) || 0;
    if (lvl <= 0) continue;
    const avg = Math.floor((HIT_DIE[cls.name] ?? 8) / 2) + 1;
    const maxDie = HIT_DIE[cls.name] ?? 8;
    const classHp = isFirst
      ? maxDie + (lvl - 1) * avg
      : lvl * avg;
    hp += classHp;
    isFirst = false;
    parts.push(`${t(`character.classes.${cls.name}`)}${lvl}级 ${classHp}`);
  }
  hp += con * totalLevel;
  parts.push(`体质 ${con}×${totalLevel}`);
  setDerivedBoth("max_hp", Math.max(1, hp), parts.join(" + "));
}

const AUTO_CALC: Partial<Record<DerivedKey, () => void>> = {
  ac: autoCalcAC,
  max_hp: autoCalcMaxHP,
  initiative: autoCalcInitiative,
  proficiency_bonus: autoCalcProfBonus,
  passive_perception: autoCalcPassivePerception,
};

// ── Saving throws ───────────────────────────────────────────────────────────
const savingThrows = computed(
  () => (modelSnapshot().saving_throws ?? {}) as Record<string, string>,
);
const saveAutos = computed(
  () => (modelSnapshot().saving_throw_autos ?? {}) as Record<string, boolean>,
);
const saveProfs = computed(
  () => (modelSnapshot().saving_throw_profs ?? {}) as Record<string, boolean>,
);

// ── Skills ──────────────────────────────────────────────────────────────────
const skillValues = computed(
  () => (modelSnapshot().skill_values ?? {}) as Record<string, string>,
);
const skillAutos = computed(
  () => (modelSnapshot().skill_value_autos ?? {}) as Record<string, boolean>,
);

type SkillProf = "none" | "proficient" | "expert";
const skillProfs = computed(
  () => (modelSnapshot().skill_profs ?? {}) as Record<string, SkillProf>,
);

// ── Proficiency bonus & auto-calc ──────────────────────────────────────────
const profBonus = computed(() => getDerived("proficiency_bonus").value || 2);

function calcSaveValue(ability: string, proficient?: boolean): string {
  const mod = abilityMod(scores.value[ability] ?? 10);
  const hasProf = proficient !== undefined ? proficient : !!saveProfs.value[ability];
  return fmtMod(mod + (hasProf ? profBonus.value : 0));
}

function calcSkillValue(key: string, prof?: SkillProf): string {
  const skill = DND5E_SKILLS.find(s => s.key === key);
  if (!skill) return "+0";
  const mod = abilityMod(scores.value[skill.ability] ?? 10);
  const p = prof !== undefined ? prof : (skillProfs.value[key] ?? "none");
  const bonus = p === "proficient" ? profBonus.value : p === "expert" ? profBonus.value * 2 : 0;
  return fmtMod(mod + bonus);
}

// ── Auto flag helpers ──────────────────────────────────────────────────────
function isAutoSave(ability: string): boolean {
  const flag = saveAutos.value[ability];
  return flag !== undefined ? flag : !(savingThrows.value[ability]?.trim());
}
function isAutoSkill(key: string): boolean {
  const flag = skillAutos.value[key];
  return flag !== undefined ? flag : !(skillValues.value[key]?.trim());
}

function saveDisplayValue(ability: string): string {
  return isAutoSave(ability) ? "" : (savingThrows.value[ability] ?? "");
}
function skillDisplayValue(key: string): string {
  return isAutoSkill(key) ? "" : (skillValues.value[key] ?? "");
}

function savePlaceholder(ability: string): string { return calcSaveValue(ability); }
function skillPlaceholder(key: string): string { return calcSkillValue(key); }

// ── setSave / setSkill ─────────────────────────────────────────────────────
function setSave(ability: string, v: string) {
  const isAuto = v.trim() === "";
  updateMultiple({
    saving_throws: { ...savingThrows.value, [ability]: isAuto ? calcSaveValue(ability) : v },
    saving_throw_autos: { ...saveAutos.value, [ability]: isAuto },
  });
}
function setSkill(key: string, v: string) {
  const isAuto = v.trim() === "";
  updateMultiple({
    skill_values: { ...skillValues.value, [key]: isAuto ? calcSkillValue(key) : v },
    skill_value_autos: { ...skillAutos.value, [key]: isAuto },
  });
}

// ── Prof toggles ───────────────────────────────────────────────────────────
function toggleSaveProf(ability: string) {
  update("saving_throw_profs", { ...saveProfs.value, [ability]: !saveProfs.value[ability] });
}
function cycleSkillProf(key: string) {
  const cur = skillProfs.value[key] ?? "none";
  const next: SkillProf = cur === "none" ? "proficient" : cur === "proficient" ? "expert" : "none";
  update("skill_profs", { ...skillProfs.value, [key]: next });
}

function abilityShort(ability: string) {
  return t(ABILITY_LABEL_KEYS[ability as keyof typeof ABILITY_LABEL_KEYS]).slice(0, 2);
}

// ── Rows for SkillSaveCompactList ──────────────────────────────────────────
const saveRows = computed<CompactRow[]>(() =>
  ABILITY_KEYS.map(ability => ({
    key: ability,
    label: abilityShort(ability),
    value: saveDisplayValue(ability),
    placeholder: savePlaceholder(ability),
    profState: (saveProfs.value[ability] ? "proficient" : "none") as CompactRow["profState"],
  })),
);
const skillRows = computed<CompactRow[]>(() =>
  DND5E_SKILLS.map(sk => ({
    key: sk.key,
    label: t(sk.labelKey),
    value: skillDisplayValue(sk.key),
    placeholder: skillPlaceholder(sk.key),
    profState: (skillProfs.value[sk.key] ?? "none") as CompactRow["profState"],
  })),
);

// ── Proficiencies ────────────────────────────────────────────────────────────
const weaponProfs = computed(() => (modelSnapshot().weapon_proficiencies as string[]) ?? []);
const armorProfs = computed(() => (modelSnapshot().armor_proficiencies as string[]) ?? []);
const toolProfs = computed(() => (modelSnapshot().tool_proficiencies as string[]) ?? []);
const languages = computed(() => (modelSnapshot().languages as string[]) ?? []);
</script>

<template>
  <div class="tab-content">
    <!-- Ability scores -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.abilityScores") }}</div>
      <AbilityScoresGrid
        :model-value="scores"
        @update:model-value="v => update('ability_scores', v)"
      />
    </div>

    <!-- Derived stats -->
    <div class="section">
      <div class="derived-hint">{{ t("character.attributes.autoCalcHint") }}</div>
      <div class="derived-grid">
        <template v-for="key in DERIVED_KEYS" :key="key">
          <div class="derived-row">
            <div class="derived-name">{{ t(`character.attributes.derived.${key}`) }}</div>
            <input
              type="number"
              class="derived-value no-spin"
              :value="getDerived(key).value"
              @change="setDerived(key, 'value', ($event.target as HTMLInputElement).value)"
            />
            <input
              type="text"
              class="derived-breakdown"
              :placeholder="t('character.attributes.breakdown')"
              :value="getDerived(key).breakdown"
              @input="setDerived(key, 'breakdown', ($event.target as HTMLInputElement).value)"
            />
            <button v-if="AUTO_CALC[key]" class="auto-btn" @click="AUTO_CALC[key]!()">
              {{ t("character.attributes.autoCalc") }}
            </button>
            <div v-else class="auto-btn-spacer" />
          </div>
        </template>
      </div>
    </div>

    <!-- Saving throws -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.savingThrows") }}</div>
      <SkillSaveCompactList
        :rows="saveRows"
        :show-prof-dots="true"
        @update-value="(key, val) => setSave(key, val)"
        @toggle-prof="toggleSaveProf"
      />
    </div>

    <!-- Skills -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.skills") }}</div>
      <SkillSaveCompactList
        :rows="skillRows"
        :show-prof-dots="true"
        @update-value="(key, val) => setSkill(key, val)"
        @toggle-prof="cycleSkillProf"
      />
    </div>

    <!-- Weapon + Armor + Tool proficiencies -->
    <div class="section">
      <div class="field">
        <label class="label">{{ t("character.attributes.weaponProficiencies") }}</label>
        <BaseTagInput
          :model-value="weaponProfs"
          :placeholder="t('character.attributes.proficiencyPlaceholder')"
          @update:model-value="update('weapon_proficiencies', $event)"
        />
      </div>
      <div class="field">
        <label class="label">{{ t("character.attributes.armorProficiencies") }}</label>
        <BaseTagInput
          :model-value="armorProfs"
          :placeholder="t('character.attributes.proficiencyPlaceholder')"
          @update:model-value="update('armor_proficiencies', $event)"
        />
      </div>
      <div class="field">
        <label class="label">{{ t("character.attributes.toolProficiencies") }}</label>
        <BaseTagInput
          :model-value="toolProfs"
          :placeholder="t('character.attributes.proficiencyPlaceholder')"
          @update:model-value="update('tool_proficiencies', $event)"
        />
      </div>
    </div>

    <!-- Languages -->
    <div class="section">
      <div class="field">
        <label class="label">{{ t("character.attributes.languages") }}</label>
        <BaseTagInput
          :model-value="languages"
          :placeholder="t('character.attributes.languagesPlaceholder')"
          @update:model-value="update('languages', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 24px; }
.section { display: grid; gap: 10px; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.derived-hint { font-size: 12px; color: var(--c-text-muted); }
.field { display: grid; gap: 5px; }
.label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }

/* Derived stats */
.derived-grid { display: grid; gap: 5px; }
.derived-row { display: grid; grid-template-columns: 100px 58px 1fr 68px; gap: 6px; align-items: center; }
.derived-name { font-size: 13px; color: var(--c-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.derived-value, .derived-breakdown {
  border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text); padding: 4px 6px;
  font-size: 13px; font-family: inherit; outline: none;
}
.derived-value { width: 100%; text-align: center; }
.derived-breakdown { width: 100%; }
.derived-value:focus, .derived-breakdown:focus { border-color: var(--c-accent); }
.derived-breakdown::placeholder { color: var(--c-text-muted); }
.no-spin { -moz-appearance: textfield; }
.no-spin::-webkit-outer-spin-button,
.no-spin::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.auto-btn {
  white-space: nowrap; font-size: 11px; padding: 3px 6px; border-radius: var(--r-1);
  border: 1px solid var(--c-border); background: var(--c-surface-raised);
  color: var(--c-text-muted); cursor: pointer; transition: background 0.12s;
}
.auto-btn:hover { background: var(--c-hover); color: var(--c-text); }
.auto-btn-spacer { height: 24px; }

</style>
