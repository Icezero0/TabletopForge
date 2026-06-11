import {
  DND5E_CLASSES,
  abilityMod,
  type DND5EClass,
} from "@/features/character/constants";

export type CharacterResource = {
  name: string;
  max: number;
  recovery: string;
  notes: string;
};

export type ResourceTranslator = (
  key: string,
  named?: Record<string, unknown>,
) => string;

const HIT_DIE_BY_CLASS: Record<DND5EClass, number> = {
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

const FULL_CASTER_CLASSES = new Set(["bard", "cleric", "druid", "sorcerer", "wizard"]);
const HALF_CASTER_CLASSES = new Set(["paladin", "ranger"]);

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

const WARLOCK_PACT_SLOTS: Record<number, { level: number; slots: number }> = {
  1: { level: 1, slots: 1 },
  2: { level: 1, slots: 2 },
  3: { level: 2, slots: 2 },
  4: { level: 2, slots: 2 },
  5: { level: 3, slots: 2 },
  6: { level: 3, slots: 2 },
  7: { level: 4, slots: 2 },
  8: { level: 4, slots: 2 },
  9: { level: 5, slots: 2 },
  10: { level: 5, slots: 2 },
  11: { level: 5, slots: 3 },
  12: { level: 5, slots: 3 },
  13: { level: 5, slots: 3 },
  14: { level: 5, slots: 3 },
  15: { level: 5, slots: 3 },
  16: { level: 5, slots: 3 },
  17: { level: 5, slots: 4 },
  18: { level: 5, slots: 4 },
  19: { level: 5, slots: 4 },
  20: { level: 5, slots: 4 },
};

function normalizedClassKey(rawName: unknown, t: ResourceTranslator): DND5EClass | null {
  const name = String(rawName ?? "").trim().toLowerCase();
  if (!name) return null;
  for (const key of DND5E_CLASSES) {
    if (name === key || name === t(`character.classes.${key}`).toLowerCase()) return key;
  }
  return null;
}

function classesFromIdentity(identityBlock: Record<string, unknown>, t: ResourceTranslator) {
  const classes = (identityBlock.classes ?? []) as { name?: string; level?: number }[];
  return classes
    .map((cls) => ({
      key: normalizedClassKey(cls.name, t),
      level: Math.max(1, Number(cls.level) || 1),
    }))
    .filter((cls): cls is { key: DND5EClass; level: number } => cls.key != null);
}

function normalCasterLevelForClass(key: DND5EClass, level: number) {
  if (FULL_CASTER_CLASSES.has(key)) return level;
  if (key === "artificer") return Math.ceil(level / 2);
  if (HALF_CASTER_CLASSES.has(key)) return Math.floor(level / 2);
  return 0;
}

function addResource(resources: CharacterResource[], name: string, max: number, recovery: string, notes = "") {
  if (!name || max <= 0) return;
  resources.push({ name, max, recovery, notes });
}

function abilityScore(attributesBlock: Record<string, unknown>, key: string) {
  const scores = (attributesBlock.ability_scores ?? {}) as Record<string, number>;
  return Number(scores[key] ?? 10);
}

export function normalizeCharacterResource(raw: unknown): CharacterResource | null {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const item = raw as Record<string, unknown>;
  const name = String(item.name ?? "").trim();
  const max = Math.max(0, Number(item.max ?? 0));
  const recovery = String(item.recovery ?? "").trim();
  const notes = String(item.notes ?? "").trim();
  if (!name && max <= 0 && !recovery && !notes) return null;
  return { name, max, recovery, notes };
}

export function buildCommonResourcesFromCharacter(
  identityBlock: Record<string, unknown>,
  attributesBlock: Record<string, unknown>,
  t: ResourceTranslator,
): CharacterResource[] {
  const resources: CharacterResource[] = [];
  const classes = classesFromIdentity(identityBlock, t);
  const longRest = t("character.resources.recoveryLongRest");
  const shortRest = t("character.resources.recoveryShortRest");

  const hitDiceByDie = new Map<number, number>();
  for (const cls of classes) {
    const die = HIT_DIE_BY_CLASS[cls.key];
    hitDiceByDie.set(die, (hitDiceByDie.get(die) ?? 0) + cls.level);
  }
  for (const [die, max] of [...hitDiceByDie.entries()].sort((a, b) => a[0] - b[0])) {
    addResource(resources, t("character.resources.hitDiceResource", { die }), max, longRest);
  }

  const normalCasterLevel = Math.min(
    20,
    classes.reduce((sum, cls) => sum + normalCasterLevelForClass(cls.key, cls.level), 0),
  );
  const slots = MULTICLASS_SPELL_SLOTS[normalCasterLevel] ?? {};
  for (let level = 1; level <= 9; level += 1) {
    addResource(
      resources,
      t("character.resources.spellSlotResource", { level }),
      slots[String(level)] ?? 0,
      longRest,
    );
  }

  for (const cls of classes) {
    const level = cls.level;
    if (cls.key === "warlock") {
      const pact = WARLOCK_PACT_SLOTS[Math.min(20, level)];
      if (pact) {
        addResource(resources, t("character.resources.warlockPactSlot", { level: pact.level }), pact.slots, shortRest);
      }
    } else if (cls.key === "barbarian") {
      const max = level >= 17 ? 6 : level >= 12 ? 5 : level >= 6 ? 4 : level >= 3 ? 3 : 2;
      addResource(resources, t("character.resources.rage"), max, longRest);
    } else if (cls.key === "bard") {
      const charisma = abilityMod(abilityScore(attributesBlock, "charisma"));
      addResource(resources, t("character.resources.bardicInspiration"), Math.max(1, charisma), level >= 5 ? shortRest : longRest);
    } else if (cls.key === "cleric") {
      const max = level >= 18 ? 3 : level >= 6 ? 2 : level >= 2 ? 1 : 0;
      addResource(resources, t("character.resources.channelDivinity"), max, shortRest);
    } else if (cls.key === "druid") {
      addResource(resources, t("character.resources.wildShape"), level >= 2 ? 2 : 0, shortRest);
    } else if (cls.key === "fighter") {
      addResource(resources, t("character.resources.secondWind"), level >= 1 ? 1 : 0, shortRest);
      addResource(resources, t("character.resources.actionSurge"), level >= 17 ? 2 : level >= 2 ? 1 : 0, shortRest);
    } else if (cls.key === "monk") {
      addResource(resources, t("character.resources.ki"), level >= 2 ? level : 0, shortRest);
    } else if (cls.key === "paladin") {
      const charisma = abilityMod(abilityScore(attributesBlock, "charisma"));
      addResource(resources, t("character.resources.layOnHands"), level * 5, longRest);
      addResource(resources, t("character.resources.divineSense"), Math.max(1, charisma + 1), longRest);
      addResource(resources, t("character.resources.channelDivinity"), level >= 3 ? 1 : 0, shortRest);
    } else if (cls.key === "sorcerer") {
      addResource(resources, t("character.resources.sorceryPoints"), level >= 2 ? level : 0, longRest);
    } else if (cls.key === "wizard") {
      addResource(resources, t("character.resources.arcaneRecovery"), level >= 1 ? 1 : 0, longRest);
    }
  }

  return resources;
}
