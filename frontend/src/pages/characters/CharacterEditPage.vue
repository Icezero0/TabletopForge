<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  defaultIdentity, defaultFlavor, defaultAttributes,
  defaultFeatures, defaultSpells, defaultResources, defaultEquipment,
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_SKILLS,
} from "@/features/character/constants";
import {
  getCharacter, createCharacter, patchCharacter,
  type CharacterImportPreview,
  type CharacterPayload,
} from "@/infra/api/character.api";
import { postRoomCharacter } from "@/infra/api/roomCharacters.api";
import { usePageReturnTo, RETURN_TO_QUERY } from "@/composables/useNavigationReturn";
import { useToastsStore } from "@/stores/toasts.store";
import { useAuthStore } from "@/stores/auth.store";
import CharacterImportDialog from "@/features/character/components/CharacterImportDialog.vue";
import CharacterIdentityTab from "@/features/character/components/tabs/CharacterIdentityTab.vue";
import CharacterAttributesTab from "@/features/character/components/tabs/CharacterAttributesTab.vue";
import CharacterFeaturesTab from "@/features/character/components/tabs/CharacterFeaturesTab.vue";
import CharacterSpellsTab from "@/features/character/components/tabs/CharacterSpellsTab.vue";
import CharacterResourcesTab from "@/features/character/components/tabs/CharacterResourcesTab.vue";
import CharacterEquipmentTab from "@/features/character/components/tabs/CharacterEquipmentTab.vue";
import CharacterExtrasTab from "@/features/character/components/tabs/CharacterExtrasTab.vue";
import CharacterTokenTab from "@/features/character/components/tabs/CharacterTokenTab.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseConfirmDialog from "@/ui/base/BaseConfirmDialog.vue";
import BaseDialog from "@/ui/base/BaseDialog.vue";
import type { TokenConfigUpsert } from "@/infra/api/character.api";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const { backTo, backText } = usePageReturnTo("/characters");
const toasts = useToastsStore();
const auth = useAuthStore();

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

function routeQueryWithReturn() {
  const query: Record<string, string> = {};
  if (typeof route.query[RETURN_TO_QUERY] === "string") {
    query[RETURN_TO_QUERY] = route.query[RETURN_TO_QUERY];
  }
  if (roomIdFromQuery.value != null) {
    query.roomId = String(roomIdFromQuery.value);
  }
  return query;
}

const TABS = [
  { key: "identity",   label: () => t("character.tabs.identity") },
  { key: "attributes", label: () => t("character.tabs.attributes") },
  { key: "features",   label: () => t("character.tabs.features") },
  { key: "spells",     label: () => t("character.tabs.spells") },
  { key: "resources",  label: () => t("character.tabs.resources") },
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
const formResources = ref<{ name: string; max: number; recovery: string; notes: string }[]>(defaultResources());
const formEquipment = ref<Record<string, unknown>>(defaultEquipment() as unknown as Record<string, unknown>);
const formExtras = ref<Record<string, unknown>>({});
const formTokenConfigs = ref<TokenConfigUpsert[]>([]);
const ownerId = ref<number | null>(null);

const isLoading = ref(false);
const isSaving = ref(false);
const importDialogOpen = ref(false);
const importConfirmOpen = ref(false);
const exportMenuOpen = ref(false);
const plainTextExportOpen = ref(false);
const plainTextExportContent = ref("");

const OPEN_IMPORT_QUERY = "openImport";
type ExportFormat = "json" | "md" | "txt";

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
  resources: formResources.value,
  equipment: formEquipment.value,
  extras: formExtras.value,
  tokenConfigs: formTokenConfigs.value,
}));
const savedSnapshot = ref<string>("");
const canEditCharacter = computed(() =>
  !isEdit.value || (ownerId.value != null && auth.me?.id === ownerId.value),
);
const isReadOnly = computed(() => isEdit.value && !canEditCharacter.value);
const isDirty = computed(() => canEditCharacter.value && currentSnapshot.value !== savedSnapshot.value);

async function loadCharacter(id: number) {
  isLoading.value = true;
  try {
    const char = await getCharacter(id);
    ownerId.value = char.owner_id;
    formSystem.value = char.system;
    formPortraitAssetId.value = char.portrait_asset_id;
    // Ensure name is in identity block
    formIdentity.value = { ...char.identity as Record<string, unknown>, name: char.name };
    formFlavor.value = char.flavor as Record<string, unknown>;
    formAttributes.value = char.attributes as Record<string, unknown>;
    formFeatures.value = char.features as Record<string, unknown>;
    formSpells.value = (char.spells as Record<string, unknown> | null) ?? (defaultSpells() as unknown as Record<string, unknown>);
    formResources.value = char.resources ?? defaultResources();
    formEquipment.value = char.equipment as Record<string, unknown>;
    formExtras.value = char.extras as Record<string, unknown>;
    formTokenConfigs.value = (char.token_configs ?? [])
      .filter(tc => !tc.is_primary)
      .map(tc => ({
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
  if (!canEditCharacter.value) return;
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
      token_image_asset_id: formPortraitAssetId.value,
      identity: formIdentity.value,
      flavor: formFlavor.value,
      attributes: formAttributes.value,
      features: formFeatures.value,
      spells: formSpells.value,
      resources: formResources.value,
      equipment: formEquipment.value,
      extras: formExtras.value,
      token_configs: formTokenConfigs.value.filter(tc => !tc.is_primary),
    };

    if (isEdit.value) {
      await patchCharacter(characterId.value!, payload);
      savedSnapshot.value = currentSnapshot.value;
      toasts.push({ message: t("character.toast.saved"), tone: "success" });
      if (backTo.value.startsWith("/rooms/")) {
        await router.push({ path: backTo.value });
      }
    } else if (roomIdFromQuery.value != null) {
      await postRoomCharacter(roomIdFromQuery.value, payload);
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
  formResources.value = Array.isArray(draft.resources)
    ? draft.resources.map((item) => ({
        name: String((item as Record<string, unknown>)?.name ?? ""),
        max: Math.max(0, Number((item as Record<string, unknown>)?.max ?? 0)),
        recovery: String((item as Record<string, unknown>)?.recovery ?? ""),
        notes: String((item as Record<string, unknown>)?.notes ?? ""),
      }))
    : defaultResources();
  formEquipment.value = mergeImportBlock(
    defaultEquipment() as unknown as Record<string, unknown>,
    draft.equipment,
  );
  formExtras.value = mergeImportBlock({ notes: "" }, draft.extras);
}

function buildCharacterExportPayload(): CharacterPayload {
  return {
    name: charName.value,
    system: formSystem.value,
    portrait_asset_id: formPortraitAssetId.value,
    token_image_asset_id: formPortraitAssetId.value,
    identity: formIdentity.value,
    flavor: formFlavor.value,
    attributes: formAttributes.value,
    features: formFeatures.value,
    spells: formSpells.value,
    resources: formResources.value,
    equipment: formEquipment.value,
    extras: formExtras.value,
    token_configs: formTokenConfigs.value.filter(tc => !tc.is_primary),
  };
}

function safeFileName(name: string) {
  return (name || "character").replace(/[\\/:*?"<>|]+/g, "_").trim() || "character";
}

function downloadTextFile(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function unknownToText(value: unknown) {
  if (value == null || value === "") return "";
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function numberRecordValue(record: Record<string, unknown>, key: string) {
  const value = record[key];
  if (isRecord(value) && typeof value.value !== "undefined") {
    const base = unknownToText(value.value);
    const breakdown = unknownToText(value.breakdown);
    return base && breakdown ? `${base}（${breakdown}）` : base;
  }
  return unknownToText(value);
}

function classesText(identity: Record<string, unknown>) {
  if (!Array.isArray(identity.classes)) return "";
  return identity.classes
    .map((item) => {
      if (!isRecord(item)) return "";
      const rawName = unknownToText(item.name);
      const className = rawName ? t(`character.classes.${rawName}`) : "";
      const label = className && className !== `character.classes.${rawName}` ? className : rawName;
      const level = unknownToText(item.level);
      const subclass = unknownToText(item.subclass);
      return [label, level ? `${level}级` : "", subclass].filter(Boolean).join(" ");
    })
    .filter(Boolean)
    .join(" / ");
}

function localizedOption(prefix: string, value: unknown) {
  const raw = unknownToText(value);
  if (!raw) return "";
  const directKey = `${prefix}.${raw}`;
  const directLabel = t(directKey);
  if (directLabel !== directKey) return directLabel;

  const camel = raw.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase());
  const camelKey = `${prefix}.${camel}`;
  const camelLabel = t(camelKey);
  return camelLabel === camelKey ? raw : camelLabel;
}

function section(lines: string[], title: string, body: string[]) {
  const cleaned = body.filter(Boolean);
  if (!cleaned.length) return;
  lines.push("", `## ${title}`, ...cleaned);
}

function bullet(label: string, value: unknown) {
  const text = unknownToText(value);
  return text ? `- ${label}：${text}` : "";
}

function namedNotesList(items: unknown, fallbackSource = false) {
  if (!Array.isArray(items)) return [];
  return items
    .map((item) => {
      if (!isRecord(item)) return "";
      const name = unknownToText(item.name) || t("character.resources.unnamedResource");
      const source = fallbackSource ? unknownToText(item.source) : "";
      const notes = unknownToText(item.notes);
      const head = source ? `${name}（${source}）` : name;
      return notes ? `- ${head}：${notes}` : `- ${head}`;
    })
    .filter(Boolean);
}

function buildReadableCharacterLines(payload: CharacterPayload) {
  const identity = payload.identity ?? {};
  const flavor = payload.flavor ?? {};
  const attributes = payload.attributes ?? {};
  const features = payload.features ?? {};
  const spells = payload.spells ?? {};
  const equipment = payload.equipment ?? {};
  const extras = payload.extras ?? {};
  const resources = payload.resources ?? [];

  const lines: string[] = [`# ${payload.name || "Character"}`];
  const classes = classesText(identity);
  section(lines, t("character.tabs.identity"), [
    bullet(t("character.identity.name"), payload.name),
    bullet(t("character.identity.race"), identity.race),
    bullet(t("character.identity.gender"), identity.gender),
    bullet(t("character.identity.age"), identity.age),
    bullet(t("character.identity.height"), identity.height),
    bullet(t("character.identity.weight"), identity.weight),
    bullet(t("character.identity.alignment"), localizedOption("character.alignments", identity.alignment)),
    bullet(t("character.identity.background"), identity.background),
    classes ? `- ${t("character.identity.classes")}：${classes}` : "",
    bullet(t("character.identity.appearance"), identity.appearance),
  ]);

  section(lines, t("character.flavor.section"), [
    bullet(t("character.flavor.personality"), flavor.personality),
    bullet(t("character.flavor.ideals"), flavor.ideals),
    bullet(t("character.flavor.bonds"), flavor.bonds),
    bullet(t("character.flavor.flaws"), flavor.flaws),
    bullet(t("character.flavor.backstory"), flavor.backstory),
  ]);

  const abilityScores = isRecord(attributes.ability_scores) ? attributes.ability_scores : {};
  const derived = isRecord(attributes.derived) ? attributes.derived : {};
  const saveProfs = isRecord(attributes.saving_throw_profs) ? attributes.saving_throw_profs : {};
  const skillProfs = isRecord(attributes.skill_profs) ? attributes.skill_profs : {};
  section(lines, t("character.tabs.attributes"), [
    ...ABILITY_KEYS.map((key) => bullet(t(ABILITY_LABEL_KEYS[key]), abilityScores[key])),
    "",
    bullet(t("character.attributes.derived.ac"), numberRecordValue(derived, "ac")),
    bullet(t("character.attributes.derived.max_hp"), numberRecordValue(derived, "max_hp")),
    bullet(t("character.attributes.derived.speed"), numberRecordValue(derived, "speed")),
    bullet(t("character.attributes.derived.initiative"), numberRecordValue(derived, "initiative")),
    bullet(t("character.attributes.derived.proficiency_bonus"), numberRecordValue(derived, "proficiency_bonus")),
    bullet(t("character.attributes.derived.passive_perception"), numberRecordValue(derived, "passive_perception")),
  ]);

  const savingThrows = isRecord(attributes.saving_throws) ? attributes.saving_throws : {};
  section(lines, t("character.attributes.savingThrows"), ABILITY_KEYS
    .map((key) => bullet(t(ABILITY_LABEL_KEYS[key]), savingThrows[key]))
    .filter(Boolean));

  section(lines, t("character.export.savingThrowProficiencies"), ABILITY_KEYS
    .filter((key) => saveProfs[key])
    .map((key) => `- ${t(ABILITY_LABEL_KEYS[key])}`));

  const skillValues = isRecord(attributes.skill_values) ? attributes.skill_values : {};
  section(lines, t("character.attributes.skills"), DND5E_SKILLS
    .map((skill) => bullet(t(skill.labelKey), skillValues[skill.key]))
    .filter(Boolean));

  section(lines, t("character.export.skillProficiencies"), DND5E_SKILLS
    .filter((skill) => skillProfs[skill.key] === "proficient")
    .map((skill) => `- ${t(skill.labelKey)}`));

  section(lines, t("character.export.skillExpertise"), DND5E_SKILLS
    .filter((skill) => skillProfs[skill.key] === "expert" || skillProfs[skill.key] === "expertise")
    .map((skill) => `- ${t(skill.labelKey)}`));

  section(lines, t("character.features.proficiencies"), [
    bullet(t("character.features.weapons"), Array.isArray(attributes.weapon_proficiencies) ? attributes.weapon_proficiencies.join("、") : ""),
    bullet(t("character.features.armor"), Array.isArray(attributes.armor_proficiencies) ? attributes.armor_proficiencies.join("、") : ""),
    bullet(t("character.features.tools"), Array.isArray(attributes.tool_proficiencies) ? attributes.tool_proficiencies.join("、") : ""),
    bullet(t("character.attributes.languages"), Array.isArray(attributes.languages) ? attributes.languages.join("、") : ""),
  ]);

  section(lines, t("character.features.racialTraits"), namedNotesList(features.racial_traits));
  section(lines, t("character.features.classFeatures"), namedNotesList(features.class_features, true));
  section(lines, t("character.features.feats"), namedNotesList(features.feats));
  if (isRecord(features.custom_fields)) {
    section(lines, t("character.features.customFields"), Object.entries(features.custom_fields)
      .map(([key, value]) => bullet(key, value))
      .filter(Boolean));
  }

  if (isRecord(spells)) {
    const spellbook = isRecord(spells.spellbook) ? spells.spellbook : {};
    section(lines, t("character.tabs.spells"), [
      bullet(t("character.spells.spellcastingAbility"), spells.spellcasting_ability ? t(`character.abilities.${spells.spellcasting_ability}`) : ""),
      bullet(t("character.spells.spellSaveDC"), numberRecordValue(spells, "spell_save_dc")),
      bullet(t("character.spells.spellAttackBonus"), numberRecordValue(spells, "spell_attack_bonus")),
      Array.isArray(spells.cantrips) && spells.cantrips.length
        ? `- 0 环（${t("character.spells.cantrips")}）：${spells.cantrips.join("、")}`
        : "",
      ...Object.entries(spellbook)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([level, list]) => Array.isArray(list) && list.length
          ? `- ${level} 环：${list.join("、")}`
          : ""),
    ]);
  }

  section(lines, t("character.tabs.resources"), resources.map((resource) => {
    const recovery = resource.recovery ? ` / ${resource.recovery}` : "";
    const notes = resource.notes ? `（${resource.notes}）` : "";
    return `- ${resource.name || t("character.resources.unnamedResource")}：${resource.max}${recovery}${notes}`;
  }));

  const items = Array.isArray(equipment.items) ? equipment.items : [];
  const currency = isRecord(equipment.currency) ? equipment.currency : {};
  section(lines, t("character.tabs.equipment"), [
    ...items.map((item) => {
      if (!isRecord(item)) return "";
      const name = unknownToText(item.name) || t("character.resources.unnamedResource");
      const quantity = unknownToText(item.quantity) || "1";
      const tags = [
        item.magical ? t("character.equipment.magical") : "",
        item.requires_attunement ? t("character.equipment.requiresAttunement") : "",
        item.attuned ? t("character.equipment.attuned") : "",
      ].filter(Boolean).join(" / ");
      const notes = unknownToText(item.notes);
      return `- ${name} x${quantity}${tags ? `（${tags}）` : ""}${notes ? `：${notes}` : ""}`;
    }),
    bullet(t("character.equipment.currency"), ["cp", "sp", "ep", "gp", "pp"]
      .map((key) => `${t(`character.equipment.${key}`)} ${unknownToText(currency[key]) || 0}`)
      .join(" / ")),
  ]);

  section(lines, t("character.tabs.extras"), [
    bullet(t("character.extras.notes"), extras.notes),
  ]);

  section(lines, t("character.tabs.token"), (payload.token_configs ?? []).map((config) => {
    const kind = config.is_primary ? t("character.token.primaryToken") : t("character.token.secondaryTokens");
    return `- ${config.name || t("character.token.defaultPrimaryName")}（${kind}）`;
  }));

  return lines.filter((line, index, all) => line || all[index - 1] !== "");
}

function markdownFromPayload(payload: CharacterPayload) {
  return buildReadableCharacterLines(payload).join("\n");
}

function plainTextFromPayload(payload: CharacterPayload) {
  return buildReadableCharacterLines(payload)
    .map((line) => {
      if (line.startsWith("# ")) return line.slice(2);
      if (line.startsWith("## ")) return line.slice(3);
      return line;
    })
    .join("\n");
}

async function copyPlainTextExport() {
  const text = plainTextExportContent.value;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "true");
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      textarea.remove();
    }
    toasts.push({ message: t("character.export.copied"), tone: "success" });
  } catch {
    toasts.push({ message: t("character.export.copyFailed"), tone: "danger" });
  }
}

function exportCharacter(format: ExportFormat) {
  const payload = buildCharacterExportPayload();
  const json = JSON.stringify({ format: "tabletopforge.character.v1", character: payload }, null, 2);
  const base = safeFileName(payload.name);
  exportMenuOpen.value = false;
  if (format === "json") {
    downloadTextFile(`${base}.json`, json, "application/json;charset=utf-8");
    return;
  }
  if (format === "md") {
    downloadTextFile(`${base}.md`, markdownFromPayload(payload), "text/markdown;charset=utf-8");
    return;
  }
  if (format === "txt") {
    plainTextExportContent.value = plainTextFromPayload(payload);
    plainTextExportOpen.value = true;
    return;
  }
}

function openImportDialog() {
  if (!canEditCharacter.value) return;
  if (isDirty.value || isEdit.value) {
    importConfirmOpen.value = true;
    return;
  }
  importDialogOpen.value = true;
}

function confirmOpenImportDialog() {
  importConfirmOpen.value = false;
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
    <template v-if="canEditCharacter" #actions>
      <BaseButton variant="default" @click="openImportDialog">
        {{ t("character.import.action") }}
      </BaseButton>
      <div class="exportWrap">
        <BaseButton variant="default" @click="exportMenuOpen = !exportMenuOpen">
          {{ t("character.export.action") }}
        </BaseButton>
        <div v-if="exportMenuOpen" class="exportMenu">
          <button type="button" @click="exportCharacter('json')">{{ t("character.export.json") }}</button>
          <button type="button" @click="exportCharacter('md')">{{ t("character.export.md") }}</button>
          <button type="button" @click="exportCharacter('txt')">{{ t("character.export.txt") }}</button>
        </div>
      </div>
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
      <div class="tab-panel" :class="{ readonlyPanel: isReadOnly }" :aria-readonly="isReadOnly">
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
          :identity-block="formIdentity"
        />

        <CharacterSpellsTab
          v-show="activeTab === 'spells'"
          v-model="formSpells"
          :identity-block="formIdentity"
          :attributes-block="formAttributes"
        />

        <CharacterResourcesTab
          v-show="activeTab === 'resources'"
          v-model="formResources"
          :identity-block="formIdentity"
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
          :identity-block="formIdentity"
          :attributes-block="formAttributes"
          :features-block="formFeatures"
          :spells-block="formSpells"
          :resources-block="formResources"
          :equipment-block="formEquipment"
          :character-name="charName"
          :portrait-asset-id="formPortraitAssetId"
        />
      </div>
    </template>
  </AppPageShell>

  <CharacterImportDialog
    :open="canEditCharacter && importDialogOpen"
    @close="importDialogOpen = false"
    @imported="handleImportApplied"
  />

  <BaseConfirmDialog
    v-model="importConfirmOpen"
    :title="t('character.import.title')"
    :message="t('character.import.overwriteConfirm')"
    :confirm-text="t('common.confirm')"
    :cancel-text="t('common.cancel')"
    :close-on-overlay="false"
    @confirm="confirmOpenImportDialog"
  />

  <BaseDialog
    v-model="plainTextExportOpen"
    :aria-label="t('character.export.txt')"
    :max-width="720"
  >
    <div class="plainTextDialog">
      <div class="plainTextHeader">
        <h3>{{ t("character.export.txt") }}</h3>
      </div>
      <textarea class="plainTextArea" :value="plainTextExportContent" readonly />
      <div class="plainTextActions">
        <BaseButton type="button" variant="default" @click="plainTextExportOpen = false">
          {{ t("common.cancel") }}
        </BaseButton>
        <BaseButton type="button" variant="primary" @click="copyPlainTextExport">
          {{ t("character.export.copy") }}
        </BaseButton>
      </div>
    </div>
  </BaseDialog>
</template>

<style scoped>
.loading { padding: 40px 0; text-align: center; color: var(--c-text-muted); font-size: 14px; }

.exportWrap {
  position: relative;
  display: inline-flex;
}

.exportMenu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 40;
  min-width: 128px;
  display: grid;
  gap: 2px;
  padding: 6px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-surface);
  box-shadow: 0 16px 34px rgb(0 0 0 / 22%);
}

.exportMenu button {
  height: 30px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 13px;
  text-align: left;
  padding: 0 10px;
  cursor: pointer;
}

.exportMenu button:hover {
  background: color-mix(in srgb, var(--c-primary) 12%, transparent);
}

.plainTextDialog {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface);
  box-shadow: 0 18px 42px rgb(0 0 0 / 28%);
}

.plainTextHeader h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text);
}

.plainTextArea {
  width: 100%;
  min-height: 420px;
  max-height: min(62vh, 560px);
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-bg-subtle);
  color: var(--c-text);
  font: inherit;
  font-size: 13px;
  line-height: 1.65;
  resize: vertical;
  outline: none;
  overflow: auto;
  white-space: pre-wrap;
}

.plainTextArea:focus {
  border-color: var(--c-accent, var(--c-primary));
}

.plainTextActions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

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

.readonlyPanel {
  position: relative;
}

.readonlyPanel :deep(input),
.readonlyPanel :deep(textarea),
.readonlyPanel :deep(.trigger),
.readonlyPanel :deep(.tag-input) {
  pointer-events: none;
}

.readonlyPanel :deep(.auto-btn),
.readonlyPanel :deep(.action-btn),
.readonlyPanel :deep(.del-btn),
.readonlyPanel :deep(.remove-link),
.readonlyPanel :deep(.gallery-add),
.readonlyPanel :deep(.stepBtn),
.readonlyPanel :deep(.iconBtn),
.readonlyPanel :deep(.btn) {
  pointer-events: none;
}
</style>
