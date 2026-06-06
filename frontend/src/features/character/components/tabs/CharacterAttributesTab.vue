<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_SKILLS,
  abilityMod, fmtMod,
} from "@/features/character/constants";
import BaseTagInput from "@/ui/base/BaseTagInput.vue";

const props = defineProps<{
  modelValue: Record<string, unknown>;
  identityBlock: Record<string, unknown>;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

// ── Ability scores ──────────────────────────────────────────────────────────
const scores = computed(() => {
  const s = (props.modelValue.ability_scores ?? {}) as Record<string, number>;
  const result: Record<string, number> = {};
  for (const k of ABILITY_KEYS) result[k] = Number(s[k] ?? 10);
  return result;
});
function setScore(ability: string, raw: string) {
  update("ability_scores", { ...scores.value, [ability]: parseInt(raw) || 0 });
}

// ── Derived stats ───────────────────────────────────────────────────────────
const DERIVED_KEYS = ["ac", "max_hp", "speed", "initiative", "proficiency_bonus", "passive_perception"] as const;
type DerivedKey = (typeof DERIVED_KEYS)[number];

function getDerived(key: DerivedKey): { value: number; breakdown: string } {
  const d = (props.modelValue.derived ?? {}) as Record<string, { value: number; breakdown: string }>;
  return d[key] ?? { value: 0, breakdown: "" };
}
function setDerived(key: DerivedKey, field: "value" | "breakdown", raw: string) {
  const current = getDerived(key);
  const updated = { ...current, [field]: field === "value" ? (parseInt(raw) || 0) : raw };
  update("derived", { ...(props.modelValue.derived as Record<string, unknown> ?? {}), [key]: updated });
}

// Hit dice by class (DnD 5e)
const HIT_DIE: Record<string, number> = {
  artificer: 8, barbarian: 12, bard: 8, cleric: 8, druid: 8,
  fighter: 10, monk: 8, paladin: 10, ranger: 10, rogue: 8,
  sorcerer: 6, warlock: 8, wizard: 6,
};

// Write value + breakdown in one emit to avoid second call overwriting the first
function setDerivedBoth(key: DerivedKey, value: number, breakdown: string) {
  update("derived", {
    ...(props.modelValue.derived as Record<string, unknown> ?? {}),
    [key]: { value, breakdown },
  });
}

// Auto-calc functions
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
  const profBonus = getDerived("proficiency_bonus").value ?? 2;
  const percVal = wis + profBonus;
  setDerivedBoth("passive_perception", 10 + percVal, `10 + 察觉 ${percVal}`);
}
function autoCalcProfBonus() {
  const classList = (props.identityBlock.classes as { level: number }[]) ?? [];
  const totalLevel = Math.max(1, classList.reduce((sum, c) => sum + (Number(c.level) || 0), 0));
  const bonus = Math.floor((totalLevel - 1) / 4) + 2;
  setDerivedBoth("proficiency_bonus", bonus, `角色总等级 ${totalLevel}`);
}
function autoCalcMaxHP() {
  const classList = (props.identityBlock.classes as { name: string; level: number }[]) ?? [];
  const con = abilityMod(scores.value.constitution ?? 10);
  const totalLevel = classList.reduce((sum, c) => sum + (Number(c.level) || 0), 0);
  if (totalLevel === 0) return;

  // Fixed average per level: first level = max die, subsequent = floor(die/2)+1
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

// Map which keys get auto-calc and which function to call
const AUTO_CALC: Partial<Record<DerivedKey, () => void>> = {
  ac: autoCalcAC,
  max_hp: autoCalcMaxHP,
  initiative: autoCalcInitiative,
  proficiency_bonus: autoCalcProfBonus,
  passive_perception: autoCalcPassivePerception,
};

// ── Saving throws ───────────────────────────────────────────────────────────
const savingThrows = computed(
  () => (props.modelValue.saving_throws ?? {}) as Record<string, string>,
);
const saveAutos = computed(
  () => (props.modelValue.saving_throw_autos ?? {}) as Record<string, boolean>,
);

// ── Skills ──────────────────────────────────────────────────────────────────
const skillValues = computed(
  () => (props.modelValue.skill_values ?? {}) as Record<string, string>,
);
const skillAutos = computed(
  () => (props.modelValue.skill_value_autos ?? {}) as Record<string, boolean>,
);

// Ability short labels (first 2 chars)
function abilityShort(ability: string) {
  return t(ABILITY_LABEL_KEYS[ability as keyof typeof ABILITY_LABEL_KEYS]).slice(0, 2);
}

// ── Saving throw proficiencies ─────────────────────────────────────────────
const saveProfs = computed(
  () => (props.modelValue.saving_throw_profs ?? {}) as Record<string, boolean>,
);

// ── Skill proficiencies ─────────────────────────────────────────────────────
type SkillProf = "none" | "proficient" | "expert";
const skillProfs = computed(
  () => (props.modelValue.skill_profs ?? {}) as Record<string, SkillProf>,
);

// ── Computed placeholder values ────────────────────────────────────────────
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
// If flag is unset: treat as auto when the stored value is empty (backward compat)
function isAutoSave(ability: string): boolean {
  const flag = saveAutos.value[ability];
  return flag !== undefined ? flag : !(savingThrows.value[ability]?.trim());
}
function isAutoSkill(key: string): boolean {
  const flag = skillAutos.value[key];
  return flag !== undefined ? flag : !(skillValues.value[key]?.trim());
}

// Display value: empty string when auto (lets placeholder show), stored value otherwise
function saveDisplayValue(ability: string): string {
  return isAutoSave(ability) ? "" : (savingThrows.value[ability] ?? "");
}
function skillDisplayValue(key: string): string {
  return isAutoSkill(key) ? "" : (skillValues.value[key] ?? "");
}

// Placeholder: always shows the computed reference value
function savePlaceholder(ability: string): string { return calcSaveValue(ability); }
function skillPlaceholder(skillKey: string): string { return calcSkillValue(skillKey); }

// ── Batch update helper ────────────────────────────────────────────────────
function updateMultiple(patches: Record<string, unknown>) {
  emit("update:modelValue", { ...props.modelValue, ...patches });
}

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

// ── Prof toggles — also refresh stored value when field is in auto state ───
function toggleSaveProf(ability: string) {
  const newProf = !saveProfs.value[ability];
  const patches: Record<string, unknown> = {
    saving_throw_profs: { ...saveProfs.value, [ability]: newProf },
  };
  if (isAutoSave(ability)) {
    patches.saving_throws = { ...savingThrows.value, [ability]: calcSaveValue(ability, newProf) };
  }
  updateMultiple(patches);
}
function cycleSkillProf(key: string) {
  const cur = skillProfs.value[key] ?? "none";
  const next: SkillProf = cur === "none" ? "proficient" : cur === "proficient" ? "expert" : "none";
  const patches: Record<string, unknown> = {
    skill_profs: { ...skillProfs.value, [key]: next },
  };
  if (isAutoSkill(key)) {
    patches.skill_values = { ...skillValues.value, [key]: calcSkillValue(key, next) };
  }
  updateMultiple(patches);
}

// ── Proficiencies ────────────────────────────────────────────────────────────
const weaponProfs = computed(() => (props.modelValue.weapon_proficiencies as string[]) ?? []);
const armorProfs = computed(() => (props.modelValue.armor_proficiencies as string[]) ?? []);
const toolProfs = computed(() => (props.modelValue.tool_proficiencies as string[]) ?? []);
const languages = computed(() => (props.modelValue.languages as string[]) ?? []);
</script>

<template>
  <div class="tab-content">
    <!-- Ability scores -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.abilityScores") }}</div>
      <div class="scores-grid">
        <div v-for="ability in ABILITY_KEYS" :key="ability" class="score-box">
          <div class="score-label">{{ t(ABILITY_LABEL_KEYS[ability]) }}</div>
          <div class="score-stepper">
            <button class="score-step-btn" @click="setScore(ability, String(Math.max(1, (scores[ability] ?? 10) - 1)))">−</button>
            <input
              type="number"
              class="score-input"
              :value="scores[ability]"
              @change="setScore(ability, ($event.target as HTMLInputElement).value)"
            />
            <button class="score-step-btn" @click="setScore(ability, String(Math.min(30, (scores[ability] ?? 10) + 1)))">+</button>
          </div>
          <div class="score-mod">{{ fmtMod(abilityMod(scores[ability] ?? 10)) }}</div>
        </div>
      </div>
    </div>

    <!-- Derived stats (no section title per request) -->
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

    <!-- Saving throws (manual) -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.savingThrows") }}</div>
      <div class="saves-grid">
        <div v-for="ability in ABILITY_KEYS" :key="ability" class="save-item">
          <button class="prof-dot" :class="{ proficient: !!saveProfs[ability] }" :title="saveProfs[ability] ? '熟练' : ''" @click="toggleSaveProf(ability)" />
          <span class="save-label">{{ abilityShort(ability) }}</span>
          <input
            type="text"
            class="compact-input"
            :value="saveDisplayValue(ability)"
            :placeholder="savePlaceholder(ability)"
            @input="setSave(ability, ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>
    </div>

    <!-- Skills (manual, compact 3-col) -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.skills") }}</div>
      <div class="skills-grid">
        <div v-for="skill in DND5E_SKILLS" :key="skill.key" class="skill-item">
          <button
            class="prof-dot"
            :class="skillProfs[skill.key] ?? 'none'"
            :title="skillProfs[skill.key] === 'proficient' ? '熟练' : skillProfs[skill.key] === 'expert' ? '专精' : ''"
            @click="cycleSkillProf(skill.key)"
          />
          <span class="skill-name">{{ t(skill.labelKey) }}</span>
          <input
            type="text"
            class="compact-input"
            :value="skillDisplayValue(skill.key)"
            :placeholder="skillPlaceholder(skill.key)"
            @input="setSkill(skill.key, ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>
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

/* Ability scores */
.scores-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
.score-box {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  border: 1px solid var(--c-border); border-radius: var(--r-2);
  padding: 8px 4px; background: var(--c-surface);
}
.score-label { font-size: 11px; color: var(--c-text-muted); text-align: center; }
.score-stepper { display: flex; align-items: center; gap: 2px; }
.score-step-btn {
  background: var(--c-surface-raised); border: 1px solid var(--c-border);
  border-radius: var(--r-1); color: var(--c-text-muted); cursor: pointer;
  font-size: 14px; font-weight: 600; line-height: 1;
  padding: 2px 6px; height: 32px; transition: background 0.12s, color 0.12s;
  flex-shrink: 0;
}
.score-step-btn:hover { background: var(--c-hover); color: var(--c-text); }
.score-input {
  width: 36px; text-align: center; border: 1px solid var(--c-border);
  border-radius: var(--r-1); background: var(--c-surface-raised);
  color: var(--c-text); font-size: 16px; font-weight: 600; padding: 4px 2px; outline: none;
  -moz-appearance: textfield;
}
.score-input:focus { border-color: var(--c-accent); }
.score-input::-webkit-outer-spin-button,
.score-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.score-mod { font-size: 14px; font-weight: 500; color: var(--c-text); }

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

/* Saving throws — 3-col compact */
.saves-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px 10px; }
.save-item { display: flex; align-items: center; gap: 6px; }
.save-label { font-size: 12px; font-weight: 600; color: var(--c-text-muted); white-space: nowrap; flex-shrink: 0; }

/* Skills — 3-col compact */
.skills-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px 10px; }
.skill-item { display: flex; align-items: center; gap: 5px; }
.skill-name { font-size: 12px; color: var(--c-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 1; min-width: 0; }

/* Prof dots — 三态: 空心 / 圆环 / 圆环+内部圆 */
.prof-dot {
  position: relative;
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid var(--c-border); background: transparent;
  cursor: pointer; flex-shrink: 0; padding: 0;
  transition: border-color 0.12s, border-width 0.12s;
}
.prof-dot.proficient {
  border: 3px solid var(--c-primary);
  background: transparent;
}
.prof-dot.expert {
  border: 3px solid var(--c-primary);
  background: transparent;
}
.prof-dot.expert::after {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  width: 4px; height: 4px;
  border-radius: 50%;
  background: var(--c-primary);
  transform: translate(-50%, -50%);
}

/* Shared compact input */
.compact-input {
  width: 48px; flex-shrink: 0; text-align: center; border: 1px solid var(--c-border);
  border-radius: var(--r-1); background: var(--c-surface); color: var(--c-text);
  padding: 3px 4px; font-size: 12px; font-family: inherit; outline: none;
}
.compact-input:focus { border-color: var(--c-accent); }
.compact-input::placeholder { color: var(--c-text-muted); opacity: 0.5; }
</style>
