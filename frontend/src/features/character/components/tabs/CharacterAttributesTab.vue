<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_SKILLS,
  abilityMod, fmtMod,
} from "@/features/character/constants";
import TagInput from "@/features/library/components/TagInput.vue";

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

// ── Ability scores ──────────────────────────────────────────────────────────
const scores = computed(() => {
  const s = (modelSnapshot().ability_scores ?? {}) as Record<string, number>;
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
  const dex = abilityMod(scores.value.dexterity);
  setDerivedBoth("ac", 10 + dex, `10 + 敏捷 ${dex}`);
}
function autoCalcInitiative() {
  const dex = abilityMod(scores.value.dexterity);
  setDerivedBoth("initiative", dex, `敏捷修正 ${dex}`);
}
function autoCalcPassivePerception() {
  const wis = abilityMod(scores.value.wisdom);
  const profBonus = getDerived("proficiency_bonus").value ?? 2;
  const percVal = wis + profBonus;
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
  const con = abilityMod(scores.value.constitution);
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

// ── Saving throws & skills (manual text modifiers) ─────────────────────────
const savingThrows = computed(
  () => (modelSnapshot().saving_throws ?? {}) as Record<string, string>,
);
const skillValues = computed(
  () => (modelSnapshot().skill_values ?? {}) as Record<string, string>,
);

function abilityShort(ability: string) {
  return t(ABILITY_LABEL_KEYS[ability as keyof typeof ABILITY_LABEL_KEYS]).slice(0, 2);
}

function setSave(ability: string, v: string) {
  update("saving_throws", { ...savingThrows.value, [ability]: v });
}
function setSkill(key: string, v: string) {
  update("skill_values", { ...skillValues.value, [key]: v });
}

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
      <div class="scores-grid">
        <div v-for="ability in ABILITY_KEYS" :key="ability" class="score-box">
          <div class="score-label">{{ t(ABILITY_LABEL_KEYS[ability]) }}</div>
          <div class="score-stepper">
            <button class="score-step-btn" @click="setScore(ability, String(Math.max(1, scores[ability] - 1)))">−</button>
            <input
              type="number"
              class="score-input"
              :value="scores[ability]"
              @change="setScore(ability, ($event.target as HTMLInputElement).value)"
            />
            <button class="score-step-btn" @click="setScore(ability, String(Math.min(30, scores[ability] + 1)))">+</button>
          </div>
          <div class="score-mod">{{ fmtMod(abilityMod(scores[ability])) }}</div>
        </div>
      </div>
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
      <div class="saves-grid">
        <div v-for="ability in ABILITY_KEYS" :key="ability" class="save-item">
          <span class="save-label">{{ abilityShort(ability) }}</span>
          <input
            type="text"
            class="compact-input"
            :value="savingThrows[ability] ?? ''"
            @input="setSave(ability, ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>
    </div>

    <!-- Skills -->
    <div class="section">
      <div class="section-title">{{ t("character.attributes.skills") }}</div>
      <div class="skills-grid">
        <div v-for="skill in DND5E_SKILLS" :key="skill.key" class="skill-item">
          <span class="skill-name">{{ t(skill.labelKey) }}</span>
          <input
            type="text"
            class="compact-input"
            :value="skillValues[skill.key] ?? ''"
            @input="setSkill(skill.key, ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>
    </div>

    <!-- Weapon + Armor + Tool proficiencies -->
    <div class="section">
      <div class="field">
        <label class="label">{{ t("character.attributes.weaponProficiencies") }}</label>
        <TagInput
          :model-value="weaponProfs"
          :placeholder="t('character.attributes.proficiencyPlaceholder')"
          @update:model-value="update('weapon_proficiencies', $event)"
        />
      </div>
      <div class="field">
        <label class="label">{{ t("character.attributes.armorProficiencies") }}</label>
        <TagInput
          :model-value="armorProfs"
          :placeholder="t('character.attributes.proficiencyPlaceholder')"
          @update:model-value="update('armor_proficiencies', $event)"
        />
      </div>
      <div class="field">
        <label class="label">{{ t("character.attributes.toolProficiencies") }}</label>
        <TagInput
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
        <TagInput
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

/* Saving throws — 3-col compact, label + input 左对齐紧贴 */
.saves-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px 10px; }
.save-item { display: flex; align-items: center; gap: 4px; justify-self: start; }
.save-label { font-size: 12px; font-weight: 600; color: var(--c-text-muted); white-space: nowrap; flex-shrink: 0; }

/* Skills — 3-col compact, label + input 左对齐紧贴 */
.skills-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px 10px; }
.skill-item { display: flex; align-items: center; gap: 4px; justify-self: start; max-width: 100%; }
.skill-name {
  font-size: 12px; color: var(--c-text); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; flex-shrink: 1; min-width: 0;
}

/* Shared compact input */
.compact-input {
  width: 44px; flex-shrink: 0; text-align: left; border: 1px solid var(--c-border);
  border-radius: var(--r-1); background: var(--c-surface); color: var(--c-text);
  padding: 3px 6px; font-size: 12px; font-family: inherit; outline: none;
}
.compact-input:focus { border-color: var(--c-accent); }
</style>
