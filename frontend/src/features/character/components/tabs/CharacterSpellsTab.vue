<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { DND5E_CLASSES, SPELLCASTING_ABILITY_OPTIONS, defaultSpells, abilityMod } from "@/features/character/constants";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseTagInput from "@/ui/base/BaseTagInput.vue";

const props = defineProps<{
  modelValue: Record<string, unknown> | null;
  identityBlock: Record<string, unknown>;
  attributesBlock: Record<string, unknown>;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

// Auto-init if null on mount
onMounted(() => {
  if (props.modelValue === null) {
    emit("update:modelValue", defaultSpells() as unknown as Record<string, unknown>);
  }
});

// Local fallback when modelValue is briefly null during init
const spells = computed(() => props.modelValue ?? (defaultSpells() as unknown as Record<string, unknown>));

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...spells.value, [key]: value });
}

const abilityOptions = computed(() =>
  SPELLCASTING_ABILITY_OPTIONS.map((a) => ({ value: a.value, label: t(a.labelKey) })),
);

function getDerivedValue(key: string): number {
  const d = spells.value[key] as { value: number } | undefined;
  return d?.value ?? 0;
}
function setDerivedValue(key: string, raw: string) {
  update(key, { value: parseInt(raw) || 0, breakdown: "" });
}
function setDerivedBoth(key: string, value: number, breakdown: string) {
  update(key, { value, breakdown });
}

function getProfBonus(): number {
  const derived = (props.attributesBlock.derived as Record<string, { value: number }> | undefined) ?? {};
  return derived.proficiency_bonus?.value ?? 2;
}
function getSpellAbilityMod(): number {
  const ability = (spells.value.spellcasting_ability as string) ?? "intelligence";
  const scores = (props.attributesBlock.ability_scores as Record<string, number> | undefined) ?? {};
  return abilityMod(scores[ability] ?? 10);
}
function autoCalcSpellSaveDC() {
  const prof = getProfBonus();
  const mod = getSpellAbilityMod();
  setDerivedBoth("spell_save_dc", 8 + prof + mod, `8 + 熟练 ${prof} + ${mod}`);
}
function autoCalcSpellAttackBonus() {
  const prof = getProfBonus();
  const mod = getSpellAbilityMod();
  setDerivedBoth("spell_attack_bonus", prof + mod, `熟练 ${prof} + ${mod}`);
}

const SPELL_LEVELS = ["0","1","2","3","4","5","6","7","8","9"] as const;
const expandedLevels = ref<Set<string>>(new Set());

const FULL_CASTER_CLASSES = new Set(["bard", "cleric", "druid", "sorcerer", "wizard"]);
const HALF_CASTER_CLASSES = new Set(["paladin", "ranger"]);
const ARTIFICER_CLASSES = new Set(["artificer"]);
const THIRD_CASTER_SUBCLASSES = new Set([
  "arcane trickster",
  "eldritch knight",
  "诡术师",
  "奥法骑士",
  "魔能骑士",
]);

const MULTICLASS_SPELL_SLOTS: Record<number, Record<string, number>> = {
  1: { "1": 2 },
  2: { "1": 3 },
  3: { "1": 4, "2": 2 },
  4: { "1": 4, "2": 3 },
  5: { "1": 4, "2": 3, "3": 2 },
  6: { "1": 4, "2": 3, "3": 3 },
  7: { "1": 4, "2": 3, "3": 3, "4": 1 },
  8: { "1": 4, "2": 3, "3": 3, "4": 2 },
  9: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 1 },
  10: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2 },
  11: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1 },
  12: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1 },
  13: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1 },
  14: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1 },
  15: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1 },
  16: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1 },
  17: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1, "9": 1 },
  18: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 1, "7": 1, "8": 1, "9": 1 },
  19: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 1, "8": 1, "9": 1 },
  20: { "1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 2, "8": 1, "9": 1 },
};

function normalizedClassKey(rawName: unknown): string {
  const name = String(rawName ?? "").trim().toLowerCase();
  if (!name) return "";
  for (const key of DND5E_CLASSES) {
    if (name === key || name === t(`character.classes.${key}`).toLowerCase()) return key;
  }
  return name;
}

function spellcasterLevelForClass(cls: { name?: string; level?: number; subclass?: string }) {
  const classKey = normalizedClassKey(cls.name);
  const level = Math.max(0, Number(cls.level) || 0);
  const subclass = String(cls.subclass ?? "").trim().toLowerCase();
  if (FULL_CASTER_CLASSES.has(classKey)) return level;
  if (ARTIFICER_CLASSES.has(classKey)) return Math.ceil(level / 2);
  if (HALF_CASTER_CLASSES.has(classKey)) return Math.floor(level / 2);
  if (THIRD_CASTER_SUBCLASSES.has(subclass)) return Math.floor(level / 3);
  return 0;
}

function autoCalcSpellSlots() {
  const classes = (props.identityBlock.classes ?? []) as { name?: string; level?: number; subclass?: string }[];
  const casterLevel = Math.min(
    20,
    Math.max(0, classes.reduce((sum, cls) => sum + spellcasterLevelForClass(cls), 0)),
  );
  const tableRow = MULTICLASS_SPELL_SLOTS[casterLevel] ?? {};
  const slots: Record<string, number> = {};
  for (let level = 1; level <= 9; level += 1) {
    slots[String(level)] = tableRow[String(level)] ?? 0;
  }
  update("spell_slots_max", slots);
}

function toggleLevel(lvl: string) {
  const s = new Set(expandedLevels.value);
  s.has(lvl) ? s.delete(lvl) : s.add(lvl);
  expandedLevels.value = s;
}
function getSpellsForLevel(lvl: string): string[] {
  const book = (spells.value.spellbook ?? {}) as Record<string, string[]>;
  return book[lvl] ?? [];
}
function updateSpellsForLevel(lvl: string, lvlSpells: string[]) {
  const book = { ...((spells.value.spellbook ?? {}) as Record<string, string[]>), [lvl]: lvlSpells };
  update("spellbook", book);
}
function getSlotMax(lvl: string): number {
  const slots = (spells.value.spell_slots_max ?? {}) as Record<string, number>;
  return slots[lvl] ?? 0;
}
function setSlotMax(lvl: string, v: string) {
  const slots = { ...((spells.value.spell_slots_max ?? {}) as Record<string, number>), [lvl]: parseInt(v) || 0 };
  update("spell_slots_max", slots);
}

</script>

<template>
  <div class="tab-content">
    <!-- Spellcasting ability + derived -->
    <div class="section">
      <div class="derived-hint">{{ t("character.attributes.autoCalcHint") }}</div>
      <div class="casting-stats">
        <div class="stat-item">
          <span class="stat-label">{{ t("character.spells.spellcastingAbility") }}</span>
          <BaseSelect
            :model-value="(spells.spellcasting_ability as string) ?? 'intelligence'"
            :options="abilityOptions"
            :width="130"
            @update:model-value="update('spellcasting_ability', $event)"
          />
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ t("character.spells.spellSaveDC") }}</span>
          <input type="number" class="derived-val no-spin" :value="getDerivedValue('spell_save_dc')" @change="setDerivedValue('spell_save_dc', ($event.target as HTMLInputElement).value)" />
          <button class="auto-btn" @click="autoCalcSpellSaveDC">{{ t("character.attributes.autoCalc") }}</button>
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ t("character.spells.spellAttackBonus") }}</span>
          <input type="number" class="derived-val no-spin" :value="getDerivedValue('spell_attack_bonus')" @change="setDerivedValue('spell_attack_bonus', ($event.target as HTMLInputElement).value)" />
          <button class="auto-btn" @click="autoCalcSpellAttackBonus">{{ t("character.attributes.autoCalc") }}</button>
        </div>
      </div>
    </div>

    <!-- Spellbook by level -->
    <div class="section">
      <div class="section-header">
        <div class="section-title">{{ t("character.spells.spellbook") }}</div>
        <button class="auto-btn" @click="autoCalcSpellSlots">
          {{ t("character.spells.autoCalcSpellSlots") }}
        </button>
      </div>
      <div class="spell-levels">
        <div v-for="lvl in SPELL_LEVELS" :key="lvl" class="spell-level">
          <button class="level-toggle" @click="toggleLevel(lvl)">
            <span>{{ lvl === "0" ? "0 环 (戏法)" : t("character.spells.level", { level: lvl }) }}</span>
            <span v-if="lvl !== '0'" class="slot-info">{{ t("character.spells.slotMax") }}: <input type="number" class="slot-input no-spin" :value="getSlotMax(lvl)" @click.stop @change.stop="setSlotMax(lvl, ($event.target as HTMLInputElement).value)" /></span>
            <span class="chevron" :class="{ open: expandedLevels.has(lvl) }">▾</span>
          </button>
          <div v-if="expandedLevels.has(lvl)" class="spell-list">
            <BaseTagInput
              :model-value="getSpellsForLevel(lvl)"
              :placeholder="t('character.spells.spellPlaceholder')"
              @update:model-value="updateSpellsForLevel(lvl, $event)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 24px; }
.section { display: grid; gap: 8px; }
.section-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.derived-hint { font-size: 12px; color: var(--c-text-muted); }
.casting-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.auto-btn {
  white-space: nowrap; font-size: 11px; padding: 3px 6px; border-radius: var(--r-1);
  border: 1px solid var(--c-border); background: var(--c-surface-raised);
  color: var(--c-text-muted); cursor: pointer; transition: background 0.12s;
  flex-shrink: 0;
}
.auto-btn:hover { background: var(--c-hover); color: var(--c-text); }
.stat-item { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.stat-label { font-size: 13px; color: var(--c-text-muted); white-space: nowrap; flex-shrink: 0; }
.derived-val {
  width: 56px; text-align: center; border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text); padding: 5px 6px;
  font-size: 13px; font-family: inherit; outline: none;
}
.derived-val:focus { border-color: var(--c-accent); }
.spell-levels { display: grid; gap: 4px; }
.spell-level { border: 1px solid var(--c-border); border-radius: var(--r-1); overflow: hidden; }
.level-toggle {
  width: 100%; display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: var(--c-surface-raised); border: none; cursor: pointer; color: var(--c-text);
  font-size: 13px; font-weight: 500; text-align: left;
}
.level-toggle:hover { background: var(--c-hover); }
.level-count { color: var(--c-text-muted); font-weight: 400; }
.slot-info { font-size: 12px; color: var(--c-text-muted); display: flex; align-items: center; gap: 4px; }
.slot-input {
  width: 36px; text-align: center; border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text); padding: 1px 2px; font-size: 12px; outline: none;
}
.chevron { margin-left: auto; transition: transform 0.15s; }
.chevron.open { transform: rotate(180deg); }
.spell-list { padding: 10px 12px; background: var(--c-surface); }

/* Hide number input spinners */
.no-spin::-webkit-outer-spin-button,
.no-spin::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.no-spin { -moz-appearance: textfield; }
</style>
