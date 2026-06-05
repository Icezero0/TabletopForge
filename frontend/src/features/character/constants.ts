export const ABILITY_KEYS = [
  "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
] as const;
export type AbilityKey = (typeof ABILITY_KEYS)[number];

export const ABILITY_LABEL_KEYS: Record<AbilityKey, string> = {
  strength: "character.abilities.strength",
  dexterity: "character.abilities.dexterity",
  constitution: "character.abilities.constitution",
  intelligence: "character.abilities.intelligence",
  wisdom: "character.abilities.wisdom",
  charisma: "character.abilities.charisma",
};

export const DND5E_SKILLS = [
  { key: "acrobatics",    ability: "dexterity"    as AbilityKey, labelKey: "character.skills.acrobatics" },
  { key: "animal_handling", ability: "wisdom"     as AbilityKey, labelKey: "character.skills.animalHandling" },
  { key: "arcana",        ability: "intelligence" as AbilityKey, labelKey: "character.skills.arcana" },
  { key: "athletics",     ability: "strength"     as AbilityKey, labelKey: "character.skills.athletics" },
  { key: "deception",     ability: "charisma"     as AbilityKey, labelKey: "character.skills.deception" },
  { key: "history",       ability: "intelligence" as AbilityKey, labelKey: "character.skills.history" },
  { key: "insight",       ability: "wisdom"       as AbilityKey, labelKey: "character.skills.insight" },
  { key: "intimidation",  ability: "charisma"     as AbilityKey, labelKey: "character.skills.intimidation" },
  { key: "investigation", ability: "intelligence" as AbilityKey, labelKey: "character.skills.investigation" },
  { key: "medicine",      ability: "wisdom"       as AbilityKey, labelKey: "character.skills.medicine" },
  { key: "nature",        ability: "intelligence" as AbilityKey, labelKey: "character.skills.nature" },
  { key: "perception",    ability: "wisdom"       as AbilityKey, labelKey: "character.skills.perception" },
  { key: "performance",   ability: "charisma"     as AbilityKey, labelKey: "character.skills.performance" },
  { key: "persuasion",    ability: "charisma"     as AbilityKey, labelKey: "character.skills.persuasion" },
  { key: "religion",      ability: "intelligence" as AbilityKey, labelKey: "character.skills.religion" },
  { key: "sleight_of_hand", ability: "dexterity" as AbilityKey, labelKey: "character.skills.sleightOfHand" },
  { key: "stealth",       ability: "dexterity"    as AbilityKey, labelKey: "character.skills.stealth" },
  { key: "survival",      ability: "wisdom"       as AbilityKey, labelKey: "character.skills.survival" },
] as const;

export const DND5E_CLASSES = [
  "artificer", "barbarian", "bard", "cleric", "druid",
  "fighter", "monk", "paladin", "ranger", "rogue",
  "sorcerer", "warlock", "wizard",
] as const;
export type DND5EClass = (typeof DND5E_CLASSES)[number];

export const DND5E_ALIGNMENT_OPTIONS = [
  { value: "", labelKey: "character.alignments.none" },
  { value: "lawful_good",    labelKey: "character.alignments.lawfulGood" },
  { value: "neutral_good",   labelKey: "character.alignments.neutralGood" },
  { value: "chaotic_good",   labelKey: "character.alignments.chaoticGood" },
  { value: "lawful_neutral", labelKey: "character.alignments.lawfulNeutral" },
  { value: "true_neutral",   labelKey: "character.alignments.trueNeutral" },
  { value: "chaotic_neutral",labelKey: "character.alignments.chaoticNeutral" },
  { value: "lawful_evil",    labelKey: "character.alignments.lawfulEvil" },
  { value: "neutral_evil",   labelKey: "character.alignments.neutralEvil" },
  { value: "chaotic_evil",   labelKey: "character.alignments.chaoticEvil" },
];

export const SPELLCASTING_ABILITY_OPTIONS = [
  { value: "intelligence", labelKey: "character.abilities.intelligence" },
  { value: "wisdom",       labelKey: "character.abilities.wisdom" },
  { value: "charisma",     labelKey: "character.abilities.charisma" },
];

export type ProficiencyLevel = "none" | "proficient" | "expertise";
export const PROFICIENCY_CYCLE: ProficiencyLevel[] = ["none", "proficient", "expertise"];

export function abilityMod(score: number): number {
  return Math.floor((Number(score) - 10) / 2);
}

export function fmtMod(mod: number): string {
  return mod >= 0 ? `+${mod}` : `${mod}`;
}

// Default structures for new characters (provide sane initial state)
export function defaultIdentity() {
  return {
    name: "",
    race: "", gender: "", age: "", height: "", weight: "", appearance: "",
    alignment: "", background: "",
    classes: [] as { name: string; level: number; subclass: string }[],
    gallery_asset_ids: [null, null, null] as (number | null)[],
  };
}

export function defaultFlavor() {
  return { personality: "", ideals: "", bonds: "", flaws: "", backstory: "" };
}

export function defaultAttributes() {
  return {
    ability_scores: {
      strength: 10, dexterity: 10, constitution: 10,
      intelligence: 10, wisdom: 10, charisma: 10,
    },
    derived: {
      ac:                { value: 10, breakdown: "" },
      max_hp:            { value: 0,  breakdown: "" },
      speed:             { value: 30, breakdown: "" },
      initiative:        { value: 0,  breakdown: "" },
      proficiency_bonus: { value: 2,  breakdown: "" },
      passive_perception:{ value: 10, breakdown: "" },
    },
    saving_throws: {} as Record<string, string>,
    skill_values: {} as Record<string, string>,
    weapon_proficiencies: [] as string[],
    armor_proficiencies: [] as string[],
    tool_proficiencies: [] as string[],
    languages: [] as string[],
  };
}

export function defaultFeatures() {
  return {
    racial_traits: [] as { name: string; notes: string }[],
    class_features: [] as { name: string; source: string; notes: string }[],
    proficiencies: { weapons: [] as string[], armor: [] as string[], tools: [] as string[] },
    custom_fields: {} as Record<string, string>,
  };
}

export function defaultSpells() {
  return {
    spellcasting_ability: "intelligence",
    spell_save_dc:      { value: 0, breakdown: "" },
    spell_attack_bonus: { value: 0, breakdown: "" },
    cantrips: [] as string[],
    spellbook: {
      "1": [], "2": [], "3": [], "4": [], "5": [],
      "6": [], "7": [], "8": [], "9": [],
    } as Record<string, string[]>,
    spell_slots_max: {
      "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
      "6": 0, "7": 0, "8": 0, "9": 0,
    } as Record<string, number>,
  };
}

export function defaultEquipment() {
  return {
    items: [] as {
      name: string; quantity: number;
      magical: boolean; requires_attunement: boolean; attuned: boolean; notes: string;
    }[],
    currency: { cp: 0, sp: 0, ep: 0, gp: 0, pp: 0 },
  };
}
