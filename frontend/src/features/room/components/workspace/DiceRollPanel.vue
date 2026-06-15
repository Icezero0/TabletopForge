<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  BookmarkIcon,
  CheckIcon,
  EyeIcon,
  EyeSlashIcon,
  FolderArrowDownIcon,
  FolderIcon,
  PencilIcon,
  PencilSquareIcon,
  PlusIcon,
  TrashIcon,
  XMarkIcon,
} from "@heroicons/vue/24/outline";
import { Dices } from "lucide-vue-next";
import { useDiceStore, type DiceDraft } from "@/stores/dice.store";
import { useDicePresetsStore } from "@/stores/dicePresets.store";
import { useAuthStore } from "@/stores/auth.store";
import { useEntitiesStore } from "@/stores/entities.store";
import { useTabletopStore } from "@/stores/tabletop.store";
import type { DicePreset, DiceRoll, DiceRollDetail, DiceVisibility } from "@/infra/api/dice.api";
import type { GameRole } from "@/features/room/types";
import { canManageToken } from "@/features/table/utils/tokenDisplay";
import DiceActorAvatar from "@/features/room/components/workspace/DiceActorAvatar.vue";
import BaseEntitySelect from "@/ui/base/BaseEntitySelect.vue";
import BaseInput from "@/ui/base/BaseInput.vue";

const props = defineProps<{
  roomId: number;
  sceneId?: number | null;
  active?: boolean;
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
}>();

type EditorMode = "check" | "value";
type D20Mode = "normal" | "advantage" | "disadvantage" | "custom";
type ExtraTerm = {
  id: number;
  kind: "dice" | "modifier";
  count: number;
  faces: number;
  value: number;
};
type ActorOption = {
  key: string;
  value: string;
  label: string;
  type: "user" | "token";
  id: number | null;
  name: string;
  avatarUrl?: string | null;
  assetId?: number | null;
};
type EntitySelectSlotOption = {
  value: string;
  label: string;
  [key: string]: unknown;
};
type PresetManagerDraft = {
  id: number | null;
  kind: "folder" | "preset";
  name: string;
  formula: string;
  label: string;
  visibility: DiceVisibility;
  parentId: number | null;
};

const diceStore = useDiceStore();
const dicePresetsStore = useDicePresetsStore();
const auth = useAuthStore();
const entitiesStore = useEntitiesStore();
const tabletopStore = useTabletopStore();
const mode = ref<EditorMode>("check");
const d20Mode = ref<D20Mode>("normal");
const customD20Count = ref(2);
const customD20Keep = ref(1);
const customD20KeepMode = ref<"kh" | "kl">("kh");
const rollRepeat = ref(1);
const extraTerms = ref<ExtraTerm[]>([]);
const manualFormula = ref("");
const formulaEditorOpen = ref(false);
const label = ref("");
const visibility = ref<DiceVisibility>("public");
const actorType = ref<"user" | "token">("user");
const actorTokenId = ref<number | null>(null);
const actorDisplayName = ref("");
const panelActorPickerOpen = ref(false);
const presetMenuOpen = ref(false);
const presetNameDialogOpen = ref(false);
const presetManagerOpen = ref(false);
const presetNameDraft = ref("");
const presetParentId = ref<number | null>(null);
const movingPresetId = ref<number | null>(null);
const presetManagerEditing = ref(false);
const presetManagerDraft = ref<PresetManagerDraft>({
  id: null,
  kind: "preset",
  name: "",
  formula: "",
  label: "",
  visibility: "public",
  parentId: null,
});
const timelineRef = ref<HTMLElement | null>(null);
const preservingHistoryScroll = ref(false);
const hasActivatedScroll = ref(false);
const formulaHistory = ref<string[]>([]);
const formulaHistoryCursor = ref<number | null>(null);
const formulaHistoryDraft = ref("");

const FORMULA_HISTORY_LIMIT = 50;

const roomState = computed(() => diceStore.getRoomState(props.roomId, props.sceneId ?? null));
const rolls = computed(() => roomState.value.items);
const roomTokens = computed(() => tabletopStore.getTokens(props.roomId));
const formulaHistoryStorageKey = computed(() => `tabletopforge:dice-formula-history:${props.roomId}`);
const presets = computed(() => dicePresetsStore.flatPresets);
const presetChildren = computed(() => dicePresetsStore.childrenByParent(presetParentId.value));
const movingPreset = computed(() =>
  movingPresetId.value == null
    ? null
    : dicePresetsStore.items.find((item) => item.id === movingPresetId.value) ?? null,
);
const presetPath = computed(() => {
  const path: DicePreset[] = [];
  let cursor = presetParentId.value;
  while (cursor != null) {
    const folder = dicePresetsStore.items.find((item) => item.id === cursor && item.kind === "folder");
    if (!folder) break;
    path.unshift(folder);
    cursor = folder.parent_id;
  }
  return path;
});
const currentUserActor = computed<ActorOption>(() => ({
  key: auth.me?.id ? `user:${auth.me.id}` : "user:me",
  value: auth.me?.id ? `user:${auth.me.id}` : "user:me",
  label: auth.me?.username || auth.me?.email || "当前用户",
  type: "user",
  id: auth.me?.id ?? null,
  name: auth.me?.username || auth.me?.email || "当前用户",
  avatarUrl: auth.me?.avatar_url ?? null,
}));
const tokenActorOptions = computed<ActorOption[]>(() =>
  roomTokens.value
    .filter((token) =>
      canManageToken(
        token,
        props.gameRole,
        props.currentUserId,
        props.characterOwnerById,
      ),
    )
    .map((token) => ({
      key: `token:${token.id}`,
      value: `token:${token.id}`,
      label: token.name,
      type: "token",
      id: token.id,
      name: token.name,
      assetId: token.asset_id,
    })),
);
const allActorOptions = computed<ActorOption[]>(() => [
  currentUserActor.value,
  ...tokenActorOptions.value,
]);
const selectedActor = computed<ActorOption>(() => {
  if (actorType.value === "token" && actorTokenId.value != null) {
    return (
      tokenActorOptions.value.find((item) => item.id === actorTokenId.value) ?? {
        key: `token:${actorTokenId.value}`,
        value: `token:${actorTokenId.value}`,
        label: actorDisplayName.value || `指示物 #${actorTokenId.value}`,
        type: "token",
        id: actorTokenId.value,
        name: actorDisplayName.value || `指示物 #${actorTokenId.value}`,
        assetId: null,
      }
    );
  }
  return currentUserActor.value;
});
const selectedActorKey = computed({
  get: () => selectedActor.value.key,
  set: (value: string) => {
    const option = allActorOptions.value.find((item) => item.key === value);
    if (option) selectActor(option);
  },
});
const structuredFormula = computed(() => {
  const terms = extraTerms.value.map((term, index) => termFormula(term, mode.value === "value" && index === 0)).filter(Boolean);
  const repeat = Math.max(1, Math.floor(Number(rollRepeat.value) || 1));
  const prefix = repeat > 1 ? `${repeat}#` : "";
  if (mode.value === "value") {
    const body = terms.join("");
    return body ? `${prefix}${body}` : "";
  }
  const main =
    d20Mode.value === "advantage"
      ? "2d20kh1"
      : d20Mode.value === "disadvantage"
        ? "2d20kl1"
        : d20Mode.value === "custom"
          ? `${customD20RollCount.value}d20${customD20KeepMode.value}${customD20KeepCount.value}`
          : "1d20";
  return `${prefix}${main}${terms.join("")}`;
});
const customD20RollCount = computed(() => Math.max(1, Math.min(100, Math.floor(Number(customD20Count.value) || 1))));
const customD20KeepCount = computed(() =>
  Math.max(1, Math.min(customD20RollCount.value, Math.floor(Number(customD20Keep.value) || 1))),
);

let nextTermId = 1;

watch(() => roomState.value.draft, (draft) => {
  if (!draft) return;
  applyDraft(draft);
  diceStore.clearDraft(props.roomId, props.sceneId ?? null);
  formulaEditorOpen.value = true;
  void nextTick(scrollToBottom);
}, { immediate: true });

watch(rolls, () => {
  if (!props.active) return;
  if (preservingHistoryScroll.value) return;
  void nextTick(scrollToBottom);
});

onMounted(() => {
  loadFormulaHistory();
  void loadPresets();
  void nextTick(scrollToBottom);
});

watch(() => props.roomId, () => {
  loadFormulaHistory();
  resetFormulaHistoryCursor();
});

watch(
  () => props.active,
  (isActive) => {
    if (!isActive || hasActivatedScroll.value) return;
    hasActivatedScroll.value = true;
    void nextTick(scrollToBottom);
  },
  { immediate: true },
);

watch(tokenActorOptions, (options) => {
  if (actorType.value !== "token") return;
  if (actorTokenId.value != null && options.some((option) => option.id === actorTokenId.value)) return;
  selectUserActor();
});

function applyDraft(draft: DiceDraft) {
  if (
    draft.actorType === "token" &&
    draft.actorTokenId != null &&
    tokenActorOptions.value.some((option) => option.id === draft.actorTokenId)
  ) {
    actorType.value = "token";
    actorTokenId.value = draft.actorTokenId;
    actorDisplayName.value = draft.actorDisplayName;
  } else {
    actorType.value = "user";
    actorTokenId.value = null;
    actorDisplayName.value = currentUserActor.value.name;
  }
  label.value = draft.label;
  visibility.value = draft.visibility;
  manualFormula.value = draft.formula || "1d20";
  resetFormulaHistoryCursor();
  parseFormulaDraft(draft.formula);
}

function parseRollCommand(raw: string) {
  let normalized = raw.trim();
  if (/^[rR]/.test(normalized)) normalized = normalized.slice(1).trim();
  const match = normalized.match(/^(\d+)\s*#\s*(.+)$/);
  if (!match) return { repeat: 1, formula: normalized };
  const repeat = Math.max(1, Math.floor(Number(match[1]) || 1));
  return { repeat, formula: match[2]?.trim() ?? "" };
}

function loadFormulaHistory() {
  try {
    const raw = localStorage.getItem(formulaHistoryStorageKey.value);
    const parsed = raw ? JSON.parse(raw) : [];
    formulaHistory.value = Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === "string" && item.trim().length > 0).slice(-FORMULA_HISTORY_LIMIT)
      : [];
  } catch {
    formulaHistory.value = [];
  }
}

function saveFormulaHistory() {
  try {
    localStorage.setItem(formulaHistoryStorageKey.value, JSON.stringify(formulaHistory.value));
  } catch {
    // Local history is a convenience feature; storage failures should not block rolling.
  }
}

async function loadPresets(force = false) {
  try {
    await dicePresetsStore.load(force);
  } catch {
    // The roll panel remains usable even if preset loading fails.
  }
}

function rememberFormula(raw: string) {
  const formula = raw.trim();
  if (!formula) return;
  formulaHistory.value = [
    ...formulaHistory.value.filter((item) => item !== formula),
    formula,
  ].slice(-FORMULA_HISTORY_LIMIT);
  saveFormulaHistory();
  resetFormulaHistoryCursor();
}

function resetFormulaHistoryCursor() {
  formulaHistoryCursor.value = null;
  formulaHistoryDraft.value = "";
}

function handleFormulaInput() {
  resetFormulaHistoryCursor();
}

function handleFormulaKeydown(event: KeyboardEvent) {
  if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
  const history = formulaHistory.value;
  if (history.length === 0) return;

  event.preventDefault();
  if (event.key === "ArrowUp") {
    if (formulaHistoryCursor.value == null) {
      formulaHistoryDraft.value = manualFormula.value;
      formulaHistoryCursor.value = history.length - 1;
    } else {
      formulaHistoryCursor.value = Math.max(0, formulaHistoryCursor.value - 1);
    }
    manualFormula.value = history[formulaHistoryCursor.value] ?? manualFormula.value;
    return;
  }

  if (formulaHistoryCursor.value == null) return;
  if (formulaHistoryCursor.value < history.length - 1) {
    formulaHistoryCursor.value += 1;
    manualFormula.value = history[formulaHistoryCursor.value] ?? manualFormula.value;
    return;
  }
  manualFormula.value = formulaHistoryDraft.value;
  resetFormulaHistoryCursor();
}

function makeTerm(kind: ExtraTerm["kind"], patch: Partial<ExtraTerm> = {}): ExtraTerm {
  return {
    id: nextTermId++,
    kind,
    count: 1,
    faces: 6,
    value: 0,
    ...patch,
  };
}

function termFormula(term: ExtraTerm, omitLeadingPlus = false) {
  if (term.kind === "modifier") {
    const value = Number(term.value) || 0;
    if (value === 0) return "";
    if (omitLeadingPlus && value > 0) return `${value}`;
    return value > 0 ? `+${value}` : `${value}`;
  }
  const rawCount = Number(term.count) || 1;
  const sign = rawCount < 0 ? "-" : "+";
  const count = Math.max(1, Math.abs(rawCount));
  const faces = Math.max(2, Number(term.faces) || 6);
  if (omitLeadingPlus && sign === "+") return `${count}d${faces}`;
  return `${sign}${count}d${faces}`;
}

function parsedTermToEditor(term: ParsedTerm): ExtraTerm | null {
  if (term.type === "modifier") {
    return makeTerm("modifier", { value: term.sign * term.value });
  }
  if (term.keep) return null;
  return makeTerm("dice", { count: term.sign * term.count, faces: term.faces });
}

type ParsedTerm =
  | { type: "dice"; sign: number; count: number; faces: number; keep: "kh" | "kl" | null; keepCount: number | null }
  | { type: "modifier"; sign: number; value: number };

function normalizeFormulaInput(raw: string) {
  return parseRollCommand(raw)
    .formula
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/(\d*)d(优势|劣势)(\d*)/g, (_matched, countRaw: string, keepRaw: string, facesRaw: string) => {
      const baseCount = Number(countRaw || "1");
      const rollCount = baseCount * 2;
      const keep = keepRaw === "优势" ? "kh" : "kl";
      const faces = facesRaw || "20";
      return `${rollCount}d${faces}${keep}${baseCount}`;
    });
}

function parseTerms(raw: string): ParsedTerm[] | null {
  const normalized = normalizeFormulaInput(raw);
  if (!normalized) return [];
  const re = /([+-]?)(?:(\d*)d(\d*)((kh|kl)(\d+))?|(\d+))/g;
  const terms: ParsedTerm[] = [];
  let pos = 0;
  for (const match of normalized.matchAll(re)) {
    if (match.index !== pos) return null;
    pos = match.index + match[0].length;
    const sign = match[1] === "-" ? -1 : 1;
    if (match[7] != null) {
      terms.push({ type: "modifier", sign, value: Number(match[7]) });
      continue;
    }
    terms.push({
      type: "dice",
      sign,
      count: Number(match[2] || "1"),
      faces: Number(match[3] || "20"),
      keep: (match[5] as "kh" | "kl" | undefined) ?? null,
      keepCount: match[6] != null ? Number(match[6]) : null,
    });
  }
  return pos === normalized.length ? terms : null;
}

function resetFormulaEditorState() {
  rollRepeat.value = 1;
  mode.value = "check";
  d20Mode.value = "normal";
  customD20Count.value = 2;
  customD20Keep.value = 1;
  customD20KeepMode.value = "kh";
  extraTerms.value = [];
}

function parseFormulaDraft(raw: string) {
  resetFormulaEditorState();
  const command = parseRollCommand(raw);
  rollRepeat.value = command.repeat;
  const terms = parseTerms(command.formula);
  if (!terms) {
    return;
  }
  const first = terms[0];
  const isNormalD20 =
    first?.type === "dice" &&
    first.sign > 0 &&
    first.count === 1 &&
    first.faces === 20 &&
    (first.keep == null || first.keepCount === 1);
  const isAdvD20 =
    first?.type === "dice" &&
    first.sign > 0 &&
    first.count === 2 &&
    first.faces === 20 &&
    first.keepCount === 1 &&
    (first.keep === "kh" || first.keep === "kl");
  const isCustomD20 =
    first?.type === "dice" &&
    first.sign > 0 &&
    first.faces === 20 &&
    first.keepCount != null &&
    first.keep != null;
  if (isNormalD20 || isAdvD20 || isCustomD20) {
    mode.value = "check";
    if (isAdvD20) {
      d20Mode.value = first.keep === "kh" ? "advantage" : "disadvantage";
    } else if (isCustomD20) {
      d20Mode.value = "custom";
      customD20Count.value = first.count;
      customD20Keep.value = first.keepCount ?? 1;
      customD20KeepMode.value = first.keep ?? "kh";
    } else {
      d20Mode.value = "normal";
    }
    const extras = terms.slice(1).map(parsedTermToEditor);
    if (extras.some(term => term == null)) {
      return;
    }
    extraTerms.value = extras as ExtraTerm[];
    return;
  }
  const valueTerms = terms.map(parsedTermToEditor);
  if (valueTerms.some(term => term == null)) {
    return;
  }
  mode.value = "value";
  extraTerms.value = valueTerms as ExtraTerm[];
}

function scrollToBottom() {
  const el = timelineRef.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

async function loadOlderRolls() {
  const el = timelineRef.value;
  if (!el || !props.roomId || roomState.value.isLoadingHistory || roomState.value.nextBeforeId == null) return;

  const previousScrollHeight = el.scrollHeight;
  preservingHistoryScroll.value = true;
  try {
    await diceStore.loadOlderRolls(props.roomId, props.sceneId ?? null, 30);
    await nextTick();
    el.scrollTop += el.scrollHeight - previousScrollHeight;
  } finally {
    preservingHistoryScroll.value = false;
  }
}

function handleTimelineScroll() {
  const el = timelineRef.value;
  if (!el || el.scrollTop > 24) return;
  void loadOlderRolls();
}

function termText(detail: DiceRollDetail | null) {
  if (!detail) return "";
  const pieces: string[] = [];
  for (const term of detail.terms) {
    if (term.type === "modifier") {
      pieces.push(`${term.total >= 0 ? "+" : ""}${term.total}`);
      continue;
    }
    const rolls = term.rolls.map((roll) => roll.kept ? String(roll.value) : `(${roll.value})`).join(", ");
    pieces.push(`${term.sign < 0 ? "-" : ""}${term.count}d${term.faces}${term.keep ?? ""}[${rolls}]`);
  }
  return pieces.join(" ");
}

function isCriticalSuccess(detail: DiceRollDetail | null) {
  const first = detail?.terms.find(term => term.type === "dice");
  if (!first || first.faces !== 20) return false;
  return first.rolls.some(roll => roll.kept && roll.value === 20);
}

function isCriticalFailure(detail: DiceRollDetail | null) {
  const first = detail?.terms.find(term => term.type === "dice");
  if (!first || first.faces !== 20) return false;
  return first.rolls.some(roll => roll.kept && roll.value === 1);
}

function findToken(tokenId: number | null | undefined) {
  if (!tokenId) return null;
  return roomTokens.value.find((token) => token.id === tokenId) ?? null;
}

function findUser(userId: number | null | undefined) {
  if (!userId) return null;
  if (auth.me?.id === userId) return auth.me;
  return entitiesStore.getUser(userId);
}

function rollActorName(roll: DiceRoll) {
  if (roll.actor_type === "token") {
    return roll.actor_display_name || findToken(roll.actor_token_id)?.name || "指示物";
  }
  const user = findUser(roll.roller_user_id);
  return user?.username || user?.email || roll.actor_display_name || "用户";
}

function rollActorAvatarUrl(roll: DiceRoll) {
  if (roll.actor_type === "token") return null;
  return findUser(roll.roller_user_id)?.avatar_url ?? null;
}

function rollActorAssetId(roll: DiceRoll) {
  if (roll.actor_type !== "token") return null;
  return roll.actor_asset_id ?? findToken(roll.actor_token_id)?.asset_id ?? null;
}

function selectUserActor() {
  actorType.value = "user";
  actorTokenId.value = null;
  actorDisplayName.value = currentUserActor.value.name;
  panelActorPickerOpen.value = false;
}

function selectTokenActor(tokenId: number | null | undefined = actorTokenId.value) {
  const fallback = tokenActorOptions.value[0] ?? null;
  const option = tokenActorOptions.value.find((item) => item.id === tokenId) ?? fallback;
  if (!option) return;
  actorType.value = "token";
  actorTokenId.value = option.id;
  actorDisplayName.value = option.name;
  panelActorPickerOpen.value = false;
}

function selectActor(option: ActorOption) {
  if (option.type === "user") {
    selectUserActor();
    return;
  }
  selectTokenActor(option.id);
}

function handleActorPickerOpenChange(open: boolean) {
  panelActorPickerOpen.value = open;
  if (open) presetMenuOpen.value = false;
}

function asActorOption(option: EntitySelectSlotOption | null): ActorOption {
  return (option as ActorOption | null) ?? currentUserActor.value;
}

function togglePresetMenu() {
  presetMenuOpen.value = !presetMenuOpen.value;
  if (presetMenuOpen.value) {
    panelActorPickerOpen.value = false;
    void loadPresets();
  }
}

function openSavePresetDialog() {
  const formula = manualFormula.value.trim();
  if (!formula) return;
  presetNameDraft.value = label.value.trim() || formula;
  presetMenuOpen.value = false;
  presetNameDialogOpen.value = true;
}

async function confirmSavePreset() {
  const formula = manualFormula.value.trim();
  const name = presetNameDraft.value.trim();
  if (!formula || !name) return;
  const sameName = presets.value.find((preset) => preset.name === name);
  if (sameName) {
    await dicePresetsStore.update(sameName.id, {
      formula,
      label: label.value.trim(),
      visibility: visibility.value,
    });
  } else {
    await dicePresetsStore.create({
      kind: "preset",
      name,
      formula,
      label: label.value.trim(),
      visibility: visibility.value,
      sort_order: nextPresetSortOrder(null),
    });
  }
  presetNameDialogOpen.value = false;
}

function nextPresetSortOrder(parentId: number | null) {
  const siblings = dicePresetsStore.childrenByParent(parentId);
  return siblings.reduce((max, item) => Math.max(max, item.sort_order), -1) + 1;
}

function openPresetManager() {
  presetMenuOpen.value = false;
  presetManagerOpen.value = true;
  closePresetEditor();
  void loadPresets();
}

function startPresetCreate(kind: "folder" | "preset") {
  presetManagerEditing.value = true;
  presetManagerDraft.value = {
    id: null,
    kind,
    name: "",
    formula: kind === "preset" ? manualFormula.value.trim() : "",
    label: kind === "preset" ? label.value.trim() : "",
    visibility: kind === "preset" ? visibility.value : "public",
    parentId: presetParentId.value,
  };
}

function startPresetEdit(preset: DicePreset) {
  presetManagerEditing.value = true;
  presetManagerDraft.value = {
    id: preset.id,
    kind: preset.kind,
    name: preset.name,
    formula: preset.formula,
    label: preset.label,
    visibility: preset.visibility,
    parentId: preset.parent_id,
  };
}

function closePresetEditor() {
  presetManagerEditing.value = false;
  presetManagerDraft.value = {
    id: null,
    kind: "preset",
    name: "",
    formula: "",
    label: "",
    visibility: "public",
    parentId: presetParentId.value,
  };
}

async function savePresetManagerDraft() {
  const draft = presetManagerDraft.value;
  const name = draft.name.trim();
  if (!name) return;
  if (draft.kind === "preset" && !draft.formula.trim()) return;
  const payload = {
    kind: draft.kind,
    name,
    parent_id: draft.parentId,
    formula: draft.kind === "preset" ? draft.formula.trim() : "",
    label: draft.kind === "preset" ? draft.label.trim() : "",
    visibility: draft.kind === "preset" ? draft.visibility : "public",
  };
  if (draft.id == null) {
    await dicePresetsStore.create({
      ...payload,
      sort_order: nextPresetSortOrder(draft.parentId),
    });
  } else {
    await dicePresetsStore.update(draft.id, payload);
  }
  closePresetEditor();
}

function loadPreset(preset: DicePreset) {
  manualFormula.value = preset.formula;
  label.value = preset.label;
  visibility.value = preset.visibility;
  resetFormulaHistoryCursor();
  parseFormulaDraft(preset.formula);
  presetMenuOpen.value = false;
}

async function deletePreset(preset: DicePreset) {
  await dicePresetsStore.remove(preset.id);
  if (presetParentId.value === preset.id) presetParentId.value = null;
  if (presetManagerDraft.value.id === preset.id) closePresetEditor();
  if (movingPresetId.value === preset.id) movingPresetId.value = null;
}

async function movePreset(preset: DicePreset, direction: -1 | 1) {
  await dicePresetsStore.move(preset.id, direction);
}

function startPresetMove(preset: DicePreset) {
  movingPresetId.value = movingPresetId.value === preset.id ? null : preset.id;
  if (movingPresetId.value != null && presetManagerDraft.value.id === preset.id) {
    closePresetEditor();
  }
}

function cancelPresetMove() {
  movingPresetId.value = null;
}

function isPresetDescendant(itemId: number, possibleAncestorId: number) {
  let cursor = dicePresetsStore.items.find((item) => item.id === itemId)?.parent_id ?? null;
  while (cursor != null) {
    if (cursor === possibleAncestorId) return true;
    cursor = dicePresetsStore.items.find((item) => item.id === cursor)?.parent_id ?? null;
  }
  return false;
}

function canMovePresetTo(parentId: number | null) {
  const moving = movingPreset.value;
  if (!moving) return false;
  if ((moving.parent_id ?? null) === parentId) return false;
  if (parentId == null) return true;
  if (moving.id === parentId) return false;
  if (moving.kind === "folder" && isPresetDescendant(parentId, moving.id)) return false;
  return dicePresetsStore.items.some((item) => item.id === parentId && item.kind === "folder");
}

async function movePresetTo(parentId: number | null) {
  const moving = movingPreset.value;
  if (!moving || !canMovePresetTo(parentId)) return;
  await dicePresetsStore.update(moving.id, {
    parent_id: parentId,
    sort_order: nextPresetSortOrder(parentId),
  });
  movingPresetId.value = null;
}

function enterPresetFolder(folder: DicePreset) {
  if (folder.kind !== "folder") return;
  presetParentId.value = folder.id;
  if (!movingPreset.value) closePresetEditor();
}

function goToPresetFolder(folderId: number | null) {
  presetParentId.value = folderId;
  if (!movingPreset.value) closePresetEditor();
}

async function submitRoll() {
  if (!props.roomId || roomState.value.isRolling) return;
  const nextFormula = manualFormula.value.trim();
  if (!nextFormula) return;
  const command = parseRollCommand(nextFormula);
  if (!command.formula) return;
  for (let i = 0; i < command.repeat; i++) {
    await diceStore.roll(props.roomId, props.sceneId ?? null, {
      actor_type: actorType.value,
      actor_token_id: actorType.value === "token" ? actorTokenId.value : null,
      label: label.value.trim(),
      formula: command.formula,
      visibility: visibility.value,
    });
  }
  rememberFormula(nextFormula);
  manualFormula.value = "";
}

function switchMode(nextMode: EditorMode) {
  mode.value = nextMode;
}

function openFormulaEditor() {
  parseFormulaDraft(manualFormula.value);
  formulaEditorOpen.value = true;
}

function applyFormulaEditor() {
  const next = structuredFormula.value;
  if (next) manualFormula.value = next;
  resetFormulaHistoryCursor();
  formulaEditorOpen.value = false;
}

function setRollRepeat(value: number) {
  rollRepeat.value = Math.max(1, Math.floor(Number(value) || 1));
}

function stepRollRepeat(delta: number) {
  setRollRepeat(rollRepeat.value + delta);
}

function setCustomD20Count(value: number) {
  customD20Count.value = Math.max(1, Math.min(100, Math.floor(Number(value) || 1)));
  if (customD20Keep.value > customD20Count.value) {
    customD20Keep.value = customD20Count.value;
  }
}

function setCustomD20Keep(value: number) {
  customD20Keep.value = Math.max(1, Math.min(customD20RollCount.value, Math.floor(Number(value) || 1)));
}

function addTerm() {
  extraTerms.value = [...extraTerms.value, makeTerm(mode.value === "check" ? "modifier" : "dice")];
}

function toggleTermKind(term: ExtraTerm) {
  term.kind = term.kind === "dice" ? "modifier" : "dice";
}

function removeTerm(id: number) {
  extraTerms.value = extraTerms.value.filter(term => term.id !== id);
}

function toggleVisibility() {
  visibility.value = visibility.value === "blind" ? "public" : "blind";
}
</script>

<template>
  <div class="dicePanel">
    <div ref="timelineRef" class="diceTimeline" @scroll="handleTimelineScroll">
      <div v-if="roomState.isLoading" class="empty">加载中…</div>
      <div v-else-if="rolls.length === 0" class="empty">还没有掷骰记录。</div>
      <div v-if="roomState.isLoadingHistory" class="historyLoading">加载更早记录…</div>
      <article v-for="roll in rolls" :key="roll.id" class="rollItem" :class="{ blind: roll.visibility === 'blind' }">
        <div class="rollHead">
          <span class="actor">
            <DiceActorAvatar
              :kind="roll.actor_type"
              :name="rollActorName(roll)"
              :avatar-url="rollActorAvatarUrl(roll)"
              :asset-id="rollActorAssetId(roll)"
            />
            <span class="actorName">{{ rollActorName(roll) }}</span>
          </span>
          <span v-if="roll.label" class="label">{{ roll.label }}</span>
          <span v-if="roll.visibility === 'blind'" class="visibility">暗骰</span>
        </div>
        <div class="rollMain">
          <span class="formula">{{ roll.formula }}</span>
          <span v-if="!roll.hidden && isCriticalSuccess(roll.detail)" class="critBadge">大成功</span>
          <span v-else-if="!roll.hidden && isCriticalFailure(roll.detail)" class="critBadge fail">大失败</span>
          <strong v-if="!roll.hidden" class="total">{{ roll.total }}</strong>
          <strong v-else class="total hidden">?</strong>
        </div>
        <div v-if="!roll.hidden && roll.detail" class="detail">{{ termText(roll.detail) }}</div>
      </article>
    </div>

    <form class="diceEditor" @submit.prevent="submitRoll">
      <div class="panelActorRow">
        <div class="presetSelect">
          <button
            type="button"
            class="presetIconBtn"
            :class="{ open: presetMenuOpen }"
            title="掷骰预设"
            aria-label="掷骰预设"
            aria-haspopup="menu"
            :aria-expanded="presetMenuOpen"
            @click="togglePresetMenu"
          >
            <BookmarkIcon class="presetIcon" />
          </button>
          <div v-if="presetMenuOpen" class="presetMenu" role="menu" @click.stop>
            <button type="button" class="presetMenuItem" role="menuitem" :disabled="!manualFormula.trim()" @click="openSavePresetDialog">
              保存预设
            </button>
            <button type="button" class="presetMenuItem" role="menuitem" @click="openPresetManager">
              编辑预设
            </button>
            <div class="presetMenuDivider"></div>
            <div class="presetMenuTitle">加载预设</div>
            <button
              v-for="preset in presets"
              :key="preset.id"
              type="button"
              class="presetMenuItem presetLoadItem"
              role="menuitem"
              @click="loadPreset(preset)"
            >
              <span class="presetName">{{ preset.name }}</span>
              <span class="presetFormula">{{ preset.formula }}</span>
            </button>
            <div v-if="presets.length === 0" class="presetEmpty">暂无掷骰预设</div>
          </div>
        </div>
        <BaseEntitySelect
          v-model="selectedActorKey"
          :options="allActorOptions"
          width="144px"
          @open-change="handleActorPickerOpenChange"
        >
          <template #selected="{ option }">
            <DiceActorAvatar
              :kind="asActorOption(option).type"
              :name="asActorOption(option).name"
              :avatar-url="asActorOption(option).avatarUrl"
              :asset-id="asActorOption(option).assetId"
            />
            <span class="panelActorName">{{ asActorOption(option).name }}</span>
          </template>
          <template #option="{ option }">
              <DiceActorAvatar
                :kind="asActorOption(option).type"
                :name="asActorOption(option).name"
                :avatar-url="asActorOption(option).avatarUrl"
                :asset-id="asActorOption(option).assetId"
              />
              <span class="panelActorOptionName">{{ asActorOption(option).name }}</span>
          </template>
        </BaseEntitySelect>
        <input v-model="label" class="labelInput panelLabelInput" type="text" placeholder="标签" />
      </div>
      <div class="compactRollRow">
        <button
          type="button"
          class="visibilityIconBtn"
          :class="{ blind: visibility === 'blind' }"
          title="暗骰"
          aria-label="暗骰"
          @click="toggleVisibility"
        >
          <EyeSlashIcon v-if="visibility === 'blind'" class="visibilityIcon" />
          <EyeIcon v-else class="visibilityIcon" />
        </button>
        <input
          v-model="manualFormula"
          class="formulaInput"
          type="text"
          @input="handleFormulaInput"
          @keydown="handleFormulaKeydown"
        />
        <button type="button" class="editorIconBtn" title="编辑" aria-label="编辑" @click="openFormulaEditor">
          <PencilSquareIcon class="editorIcon" />
        </button>
        <button class="rollBtn" type="submit" :disabled="roomState.isRolling">{{ roomState.isRolling ? "掷骰中…" : "掷骰" }}</button>
      </div>
      <p v-if="roomState.error" class="error">{{ roomState.error }}</p>
    </form>

    <Teleport to="body">
      <div v-if="presetNameDialogOpen" class="modalBackdrop">
        <form class="formulaModal presetNameModal" @submit.prevent="confirmSavePreset">
          <div class="modalHeader">
            <div>
              <h3 class="modalTitle">保存掷骰预设</h3>
            </div>
            <button type="button" class="modalClose" @click="presetNameDialogOpen = false">×</button>
          </div>

          <label class="presetNameField">
            <span>掷骰预设名称</span>
            <BaseInput v-model="presetNameDraft" placeholder="输入掷骰预设名称" />
          </label>

          <div class="presetFormulaPreview">
            <span>公式</span>
            <code>{{ manualFormula.trim() || "—" }}</code>
          </div>

          <div class="modalFooter">
            <button type="button" class="ghostBtn" @click="presetNameDialogOpen = false">取消</button>
            <button type="submit" class="rollBtn" :disabled="!presetNameDraft.trim() || !manualFormula.trim()">保存</button>
          </div>
        </form>
      </div>

      <div v-if="presetManagerOpen" class="modalBackdrop">
        <div class="formulaModal presetManagerModal">
          <div class="modalHeader">
            <div>
              <h3 class="modalTitle">编辑掷骰预设</h3>
            </div>
            <button type="button" class="modalClose" @click="presetManagerOpen = false">×</button>
          </div>

          <div class="presetBreadcrumb">
            <button
              type="button"
              class="breadcrumbBtn"
              @click="goToPresetFolder(null)"
            >
              全部预设
            </button>
            <template v-for="folder in presetPath" :key="folder.id">
              <span class="breadcrumbSep">/</span>
              <button
                type="button"
                class="breadcrumbBtn"
                @click="goToPresetFolder(folder.id)"
              >
                {{ folder.name }}
              </button>
            </template>
          </div>

          <div class="presetManagerGrid">
            <section class="presetListPanel">
              <div v-if="movingPreset" class="presetMoveNotice">
                <span>正在移动「{{ movingPreset.name }}」</span>
                <div class="presetMoveActions">
                  <button
                    type="button"
                    class="presetMoveApply"
                    :disabled="!canMovePresetTo(presetParentId)"
                    @click="movePresetTo(presetParentId)"
                  >
                    移动到此处
                  </button>
                  <button type="button" class="presetMoveCancel" @click="cancelPresetMove">取消</button>
                </div>
              </div>
              <div class="presetItemList">
                <div
                  v-for="item in presetChildren"
                  :key="item.id"
                  class="presetManagerItem"
                  :class="{
                    active: presetManagerEditing && presetManagerDraft.id === item.id,
                    moving: movingPresetId === item.id,
                    moveDisabled: Boolean(movingPreset && (item.kind !== 'folder' || item.id === movingPreset.id)),
                  }"
                >
                  <button
                    type="button"
                    class="presetItemMain"
                    :disabled="Boolean(movingPreset && (item.kind !== 'folder' || item.id === movingPreset.id))"
                    @click="item.kind === 'folder' ? enterPresetFolder(item) : loadPreset(item)"
                  >
                    <FolderIcon v-if="item.kind === 'folder'" class="smallIcon" />
                      <Dices v-else class="smallIcon" />
                      <span class="presetItemText">
                        <strong>{{ item.name }}</strong>
                        <small>{{ item.kind === "folder" ? "分组" : item.formula }}</small>
                      </span>
                  </button>
                  <button type="button" class="iconMiniBtn" title="上移" @click="movePreset(item, -1)">
                    <ArrowUpIcon class="smallIcon" />
                  </button>
                  <button type="button" class="iconMiniBtn" title="下移" @click="movePreset(item, 1)">
                    <ArrowDownIcon class="smallIcon" />
                  </button>
                  <button type="button" class="iconMiniBtn" title="移动" @click="startPresetMove(item)">
                    <FolderArrowDownIcon class="smallIcon" />
                  </button>
                  <button type="button" class="iconMiniBtn" title="编辑" @click="startPresetEdit(item)">
                    <PencilIcon class="smallIcon" />
                  </button>
                  <button type="button" class="iconMiniBtn danger" title="删除" @click="deletePreset(item)">
                    <TrashIcon class="smallIcon" />
                  </button>
                </div>
                <div v-if="presetChildren.length === 0" class="presetEmpty large">当前分组没有掷骰预设。</div>
                <button
                  type="button"
                  class="presetAddItem"
                  :disabled="Boolean(movingPreset)"
                  @click="startPresetCreate('preset')"
                >
                  <PlusIcon class="smallIcon" />
                  <span>添加</span>
                </button>
              </div>
            </section>

            <form class="presetEditPanel" @submit.prevent="savePresetManagerDraft">
              <template v-if="presetManagerEditing">
                <div class="rollModeRow">
                  <button
                    type="button"
                    class="rollModeBtn"
                    :class="{ active: presetManagerDraft.kind === 'preset' }"
                    @click="startPresetCreate('preset')"
                  >
                    掷骰预设
                  </button>
                  <button
                    type="button"
                    class="rollModeBtn"
                    :class="{ active: presetManagerDraft.kind === 'folder' }"
                    @click="startPresetCreate('folder')"
                  >
                    分组
                  </button>
                </div>
                <label class="presetNameField">
                  <span>名称</span>
                  <BaseInput v-model="presetManagerDraft.name" />
                </label>
                <template v-if="presetManagerDraft.kind === 'preset'">
                  <label class="presetNameField">
                    <span>公式</span>
                    <BaseInput v-model="presetManagerDraft.formula" />
                  </label>
                  <label class="presetNameField">
                    <span>标签</span>
                    <BaseInput v-model="presetManagerDraft.label" />
                  </label>
                  <div class="visibilityEditRow">
                    <button
                      type="button"
                      class="visibilityIconBtn"
                      :class="{ blind: presetManagerDraft.visibility === 'blind' }"
                      title="暗骰"
                      aria-label="暗骰"
                      @click="presetManagerDraft.visibility = presetManagerDraft.visibility === 'blind' ? 'public' : 'blind'"
                    >
                      <EyeSlashIcon v-if="presetManagerDraft.visibility === 'blind'" class="visibilityIcon" />
                      <EyeIcon v-else class="visibilityIcon" />
                    </button>
                    <span>暗骰</span>
                  </div>
                </template>
                <div class="modalFooter">
                  <button type="button" class="ghostBtn" @click="closePresetEditor">
                    <XMarkIcon class="smallIcon" />
                    取消
                  </button>
                  <button
                    type="submit"
                    class="rollBtn"
                    :disabled="dicePresetsStore.isSaving || !presetManagerDraft.name.trim() || (presetManagerDraft.kind === 'preset' && !presetManagerDraft.formula.trim())"
                  >
                    <CheckIcon class="smallIcon" />
                    保存
                  </button>
                </div>
              </template>
              <div v-else class="presetEditorEmpty">编辑或添加掷骰预设。</div>
            </form>
          </div>
        </div>
      </div>

      <div v-if="formulaEditorOpen" class="modalBackdrop">
        <div class="formulaModal">
          <div class="modalHeader">
            <div>
              <h3 class="modalTitle">掷骰编辑</h3>
            </div>
            <button type="button" class="modalClose" @click="formulaEditorOpen = false">×</button>
          </div>

          <div class="rollSettingsHeader">
            <div class="rollModeRow">
              <button type="button" class="rollModeBtn" :class="{ active: mode === 'check' }" @click="switchMode('check')">检定</button>
              <button type="button" class="rollModeBtn" :class="{ active: mode === 'value' }" @click="switchMode('value')">数值</button>
            </div>
            <div class="repeatStepper" aria-label="掷骰次数">
              <span class="repeatLabel">次数</span>
              <button type="button" class="repeatBtn" :disabled="rollRepeat <= 1" @click="stepRollRepeat(-1)">−</button>
              <input
                class="repeatInput"
                type="number"
                min="1"
                :value="rollRepeat"
                @change="setRollRepeat(Number(($event.target as HTMLInputElement).value))"
              />
              <button type="button" class="repeatBtn" @click="stepRollRepeat(1)">+</button>
            </div>
          </div>

          <div v-if="mode === 'check'" class="structuredEditor">
            <div class="formattedRow">
              <span class="mainDie">d20</span>
              <div class="advantageToggle" role="group" aria-label="优势状态">
                <button type="button" :class="{ active: d20Mode === 'normal' }" @click="d20Mode = 'normal'">普通</button>
                <button type="button" :class="{ active: d20Mode === 'advantage' }" @click="d20Mode = 'advantage'">优势</button>
                <button type="button" :class="{ active: d20Mode === 'disadvantage' }" @click="d20Mode = 'disadvantage'">劣势</button>
                <button type="button" :class="{ active: d20Mode === 'custom' }" @click="d20Mode = 'custom'">自定义</button>
              </div>
            </div>
            <div v-if="d20Mode === 'custom'" class="customKeepRow">
              <label class="customKeepField">
                <span>投掷</span>
                <input
                  class="numInput"
                  type="number"
                  min="1"
                  max="100"
                  :value="customD20Count"
                  @change="setCustomD20Count(Number(($event.target as HTMLInputElement).value))"
                />
                <span>次</span>
              </label>
              <div class="advantageToggle compact" role="group" aria-label="保留方式">
                <button type="button" :class="{ active: customD20KeepMode === 'kh' }" @click="customD20KeepMode = 'kh'">取高</button>
                <button type="button" :class="{ active: customD20KeepMode === 'kl' }" @click="customD20KeepMode = 'kl'">取低</button>
              </div>
              <label class="customKeepField">
                <span>保留</span>
                <input
                  class="numInput"
                  type="number"
                  min="1"
                  :max="customD20RollCount"
                  :value="customD20Keep"
                  @change="setCustomD20Keep(Number(($event.target as HTMLInputElement).value))"
                />
                <span>个</span>
              </label>
            </div>
            <div class="termList">
              <div v-for="term in extraTerms" :key="term.id" class="termRow">
                <button type="button" class="termKindToggle" @click="toggleTermKind(term)">
                  {{ term.kind === "dice" ? "骰子" : "加值" }}
                </button>
                <template v-if="term.kind === 'dice'">
                  <input v-model.number="term.count" class="numInput" type="number" min="-100" max="100" />
                  <span>d</span>
                  <input v-model.number="term.faces" class="numInput" type="number" min="2" max="1000" />
                </template>
                <input v-else v-model.number="term.value" class="numInput wide" type="number" />
                <button type="button" class="removeTermBtn" title="删除" aria-label="删除" @click="removeTerm(term.id)">
                  <TrashIcon class="removeTermIcon" />
                </button>
              </div>
              <button type="button" class="addTermItem" title="添加项" aria-label="添加项" @click="addTerm">
                <PlusIcon class="addTermIcon" />
              </button>
            </div>
          </div>

          <div v-else class="structuredEditor">
            <div class="termList">
              <div v-for="term in extraTerms" :key="term.id" class="termRow">
                <button type="button" class="termKindToggle" @click="toggleTermKind(term)">
                  {{ term.kind === "dice" ? "骰子" : "加值" }}
                </button>
                <template v-if="term.kind === 'dice'">
                  <input v-model.number="term.count" class="numInput" type="number" min="-100" max="100" />
                  <span>d</span>
                  <input v-model.number="term.faces" class="numInput" type="number" min="2" max="1000" />
                </template>
                <input v-else v-model.number="term.value" class="numInput wide" type="number" />
                <button type="button" class="removeTermBtn" title="删除" aria-label="删除" @click="removeTerm(term.id)">
                  <TrashIcon class="removeTermIcon" />
                </button>
              </div>
              <button type="button" class="addTermItem" title="添加项" aria-label="添加项" @click="addTerm">
                <PlusIcon class="addTermIcon" />
              </button>
            </div>
          </div>

          <div class="modalFormula">
            <span>公式</span>
            <code>{{ structuredFormula || "—" }}</code>
          </div>

          <div class="modalFooter">
            <button type="button" class="ghostBtn" @click="formulaEditorOpen = false">取消</button>
            <button type="button" class="rollBtn" @click="applyFormulaEditor">应用</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.dicePanel {
  min-height: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 8px;
}

.diceTimeline {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 0 6px 6px;
  margin: 0 -14px;
  border-top: 1px solid color-mix(in srgb, var(--c-border) 78%, transparent);
  border-bottom: 1px solid var(--c-border);
  scrollbar-gutter: stable;
}

.empty {
  min-height: 100%;
  display: grid;
  place-items: center;
  color: var(--c-text-muted);
  font-size: 13px;
}

.historyLoading {
  justify-self: center;
  padding: 4px 8px;
  border-radius: 999px;
  color: var(--c-text-muted);
  background: color-mix(in srgb, var(--c-surface) 88%, var(--c-bg));
  font-size: 11px;
}

.rollItem {
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid color-mix(in srgb, var(--c-border) 82%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 88%, var(--c-bg));
}

.rollHead,
.rollMain,
.editorTop,
.modeRow,
.formattedRow,
.termRow,
.compactRollRow,
.submitRow {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.actor {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 12px;
}

.actorName {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text-muted);
  font-size: 12px;
}

.visibility {
  margin-left: auto;
  color: var(--c-text-muted);
  font-size: 11px;
}

.formula {
  color: var(--c-text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}

.total {
  margin-left: auto;
  color: var(--c-text);
  font-size: 22px;
  line-height: 1;
}

.total.hidden {
  color: var(--c-text-muted);
}

.critBadge {
  margin-left: 2px;
  padding: 1px 6px;
  border: 1px solid color-mix(in srgb, var(--c-success, #3aa675) 45%, var(--c-border));
  border-radius: 999px;
  color: var(--c-success, #3aa675);
  background: color-mix(in srgb, var(--c-success, #3aa675) 10%, var(--c-surface));
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.critBadge.fail {
  color: var(--c-danger);
  border-color: color-mix(in srgb, var(--c-danger) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-danger) 10%, var(--c-surface));
}

.detail {
  color: var(--c-text-muted);
  font-size: 11px;
  overflow-wrap: anywhere;
}

.diceEditor {
  display: grid;
  gap: 7px;
}

.compactRollRow {
  gap: 6px;
}

.panelActorRow {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.presetSelect {
  position: relative;
  flex: 0 0 auto;
}

.presetIconBtn {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
}

.presetIconBtn:hover,
.presetIconBtn.open {
  color: var(--c-text);
  border-color: color-mix(in srgb, var(--c-primary) 32%, var(--c-border));
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
}

.presetIcon {
  width: 16px;
  height: 16px;
}

.presetMenu {
  position: absolute;
  z-index: 370;
  left: 0;
  bottom: calc(100% + 6px);
  width: max-content;
  min-width: 112px;
  max-width: 220px;
  max-height: 260px;
  overflow-y: auto;
  overflow-x: hidden;
  display: grid;
  gap: 3px;
  padding: 5px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.32);
}

.presetMenuItem {
  width: 100%;
  min-width: 0;
  max-width: 210px;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 8px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

.presetMenuItem:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 24%, transparent);
}

.presetMenuItem:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.presetLoadRow {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 28px;
  align-items: stretch;
  gap: 3px;
}

.presetLoadItem {
  display: grid;
  grid-template-columns: minmax(0, max-content);
  align-items: start;
  gap: 2px;
}

.presetDeleteBtn {
  width: 28px;
  min-height: 30px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
}

.presetDeleteBtn:hover {
  color: var(--c-danger);
  background: color-mix(in srgb, var(--c-danger) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-danger) 24%, transparent);
}

.presetDeleteIcon {
  width: 15px;
  height: 15px;
}

.presetName,
.presetFormula {
  min-width: 0;
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.presetName {
  font-weight: 700;
}

.presetFormula {
  color: var(--c-text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}

.presetMenuTitle,
.presetEmpty {
  padding: 4px 8px 3px;
  color: var(--c-text-muted);
  font-size: 11px;
}

.presetMenuDivider {
  height: 1px;
  margin: 3px 4px;
  background: var(--c-border);
}

.panelActorName,
.panelActorOptionName {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.panelActorName {
  min-width: 0;
  flex: 1;
  text-align: left;
}

.panelLabelInput {
  flex: 1;
}

.labelInput,
.formulaInput,
.numInput {
  height: 28px;
  min-width: 0;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
}

.labelInput,
.formulaInput {
  flex: 1;
  padding: 0 8px;
}

.numInput {
  width: 54px;
  text-align: center;
  appearance: textfield;
  -moz-appearance: textfield;
}

.numInput::-webkit-outer-spin-button,
.numInput::-webkit-inner-spin-button {
  margin: 0;
  appearance: none;
  -webkit-appearance: none;
}

.numInput.wide {
  width: 86px;
}

.structuredEditor {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.mainDie {
  height: 28px;
  min-width: 46px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-primary) 12%, var(--c-surface));
  color: var(--c-text);
  font-size: 12px;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.termList {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.termRow {
  min-width: 0;
  min-height: 38px;
  padding: 5px;
  border: 1px solid color-mix(in srgb, var(--c-border) 82%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 90%, var(--c-bg));
}

.advantageToggle {
  height: 28px;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  padding: 2px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
}

.advantageToggle button {
  height: 22px;
  min-width: 42px;
  padding: 0 7px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.advantageToggle button.active {
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
  color: var(--c-text);
}

.advantageToggle.compact button {
  min-width: 38px;
}

.customKeepRow {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.customKeepField {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.termKindToggle {
  width: 54px;
  height: 28px;
  flex-shrink: 0;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.termKindToggle:hover {
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
}

.emptyTerms {
  color: var(--c-text-muted);
  font-size: 12px;
}

.ghostBtn,
.rollBtn,
.miniBtn {
  height: 26px;
  padding: 0 9px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.visibilityIconBtn {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px dashed var(--c-border);
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
  opacity: 0.55;
}

.editorIconBtn {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
}

.editorIconBtn:hover {
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
}

.addTermItem {
  width: 100%;
  min-height: 36px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px dashed color-mix(in srgb, var(--c-border) 88%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 88%, var(--c-bg));
  color: var(--c-text-muted);
  cursor: pointer;
}

.addTermItem:hover {
  color: var(--c-text);
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 8%, var(--c-surface));
}

.visibilityIconBtn:hover {
  opacity: 0.85;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
}

.visibilityIconBtn.blind {
  color: var(--c-text);
  border-style: solid;
  opacity: 1;
  border-color: color-mix(in srgb, var(--c-text-muted) 55%, var(--c-border));
  background: color-mix(in srgb, var(--c-text-muted) 14%, var(--c-surface));
}

.visibilityIcon {
  width: 16px;
  height: 16px;
}

.editorIcon {
  width: 16px;
  height: 16px;
}

.addTermIcon {
  width: 16px;
  height: 16px;
}

.removeTermIcon {
  width: 15px;
  height: 15px;
}

.miniBtn {
  height: 28px;
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
  white-space: nowrap;
}

.removeTermBtn {
  width: 28px;
  height: 28px;
  margin-left: auto;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: var(--c-text-muted);
  padding: 0;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}

.removeTermBtn:hover {
  color: var(--c-danger);
  border-color: color-mix(in srgb, var(--c-danger) 55%, var(--c-border));
}

.actorHint {
  margin-left: auto;
  color: var(--c-text-muted);
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.submitRow code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text-muted);
}

.rollBtn {
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
  color: var(--c-text);
}

.rollBtn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  margin: 0;
  color: var(--c-danger);
  font-size: 12px;
}

.modalBackdrop {
  position: fixed;
  inset: 0;
  z-index: 700;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.52);
}

.formulaModal {
  width: min(448px, 100%);
  max-height: min(720px, 92vh);
  overflow: auto;
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-surface);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.34);
}

.presetNameModal {
  width: min(360px, 100%);
}

.presetManagerModal {
  width: min(760px, 100%);
}

.presetBreadcrumb {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 8px;
  border: 1px solid var(--c-border);
  border-radius: 7px;
  background: color-mix(in srgb, var(--c-surface) 92%, var(--c-bg));
  overflow-x: auto;
}

.breadcrumbBtn {
  flex: 0 0 auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.breadcrumbBtn:hover {
  color: color-mix(in srgb, var(--c-primary) 72%, var(--c-text));
}

.breadcrumbSep {
  color: var(--c-text-muted);
  font-size: 12px;
}

.presetManagerGrid {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(220px, 0.85fr);
  gap: 12px;
}

.presetListPanel,
.presetEditPanel {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 10px;
  border: 1px solid color-mix(in srgb, var(--c-border) 86%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 92%, var(--c-bg));
}

.presetEditPanel {
  height: 350px;
  grid-template-rows: auto auto auto auto 1fr auto;
}

.presetEditPanel > .modalFooter {
  grid-row: -1;
  align-self: end;
}

.modalFooter .ghostBtn,
.modalFooter .rollBtn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.presetItemList {
  min-width: 0;
  max-height: 360px;
  overflow-y: auto;
  scrollbar-gutter: stable;
  display: grid;
  gap: 5px;
}

.presetMoveNotice {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 8px;
  border: 1px dashed color-mix(in srgb, var(--c-primary) 42%, var(--c-border));
  border-radius: 7px;
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
  font-size: 12px;
}

.presetMoveNotice span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.presetMoveActions {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.presetMoveApply {
  height: 24px;
  padding: 0 8px;
  border: 1px solid color-mix(in srgb, var(--c-primary) 38%, var(--c-border));
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-primary) 14%, var(--c-surface));
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}

.presetMoveApply:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 22%, var(--c-surface));
}

.presetMoveApply:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.presetMoveCancel {
  flex: 0 0 auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.presetMoveCancel:hover {
  color: var(--c-text);
}

.presetManagerItem {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) repeat(5, 28px);
  align-items: center;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--c-border);
  border-radius: 7px;
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
}

.presetManagerItem.active {
  border-color: color-mix(in srgb, var(--c-primary) 42%, var(--c-border));
}

.presetManagerItem.moving {
  border-color: color-mix(in srgb, var(--c-primary) 60%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 12%, var(--c-surface));
}

.presetManagerItem.moveTarget {
  border-style: dashed;
  border-color: color-mix(in srgb, var(--c-primary) 52%, var(--c-border));
}

.presetManagerItem.moveDisabled {
  opacity: 0.52;
}

.presetItemMain {
  min-width: 0;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 6px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.presetItemMain:hover {
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
}

.presetItemMain:disabled {
  cursor: not-allowed;
}

.presetItemText {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.presetItemText strong,
.presetItemText small {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.presetItemText strong {
  font-size: 12px;
}

.presetItemText small {
  color: var(--c-text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}

.presetAddItem {
  min-width: 0;
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 10px;
  border: 1px dashed color-mix(in srgb, var(--c-border) 88%, transparent);
  border-radius: 7px;
  background: color-mix(in srgb, var(--c-surface) 92%, var(--c-bg));
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.presetAddItem:hover:not(:disabled) {
  color: var(--c-text);
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 8%, var(--c-surface));
}

.presetAddItem:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.presetEditorEmpty {
  min-height: 100%;
  display: grid;
  place-items: center;
  padding: 24px 12px;
  color: var(--c-text-muted);
  text-align: center;
  font-size: 12px;
}

.iconMiniBtn {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
}

.iconMiniBtn:hover {
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 24%, transparent);
}

.iconMiniBtn.danger:hover {
  color: var(--c-danger);
  background: color-mix(in srgb, var(--c-danger) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-danger) 24%, transparent);
}

.smallIcon {
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
}

.visibilityEditRow {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--c-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.presetEmpty.large {
  padding: 24px 8px;
  text-align: center;
}

.presetNameField {
  display: grid;
  gap: 6px;
  color: var(--c-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.presetNameField :deep(.inp) {
  width: 100%;
}

.presetFormulaPreview {
  min-width: 0;
  display: grid;
  gap: 5px;
  color: var(--c-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.presetFormulaPreview code {
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 90%, var(--c-bg));
  color: var(--c-text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.modalHeader {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.modalTitle {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.modalSubtitle {
  margin-top: 3px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.modalClose {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.modalClose:hover {
  color: var(--c-text);
}

.actorPicker {
  min-width: 0;
  display: block;
  padding: 8px;
  border: 1px solid color-mix(in srgb, var(--c-border) 82%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 90%, var(--c-bg));
}

.actorPickerHeader {
  min-width: 0;
  min-height: 32px;
  display: flex;
  align-items: center;
  gap: 7px;
}

.actorModeRow {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  align-self: center;
  height: 28px;
  padding: 2px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
}

.actorModeBtn {
  height: 22px;
  min-width: 48px;
  padding: 0 8px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.actorModeBtn.active {
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
  color: var(--c-text);
}

.actorModeBtn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.rollSettingsHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.rollModeRow {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 2px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
}

.rollModeBtn {
  height: 22px;
  min-width: 48px;
  padding: 0 8px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.rollModeBtn.active {
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
  color: var(--c-text);
}

.repeatStepper {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  color: var(--c-text-muted);
  font-size: 12px;
}

.repeatLabel {
  font-weight: 600;
}

.repeatBtn {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}

.repeatBtn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.repeatInput {
  width: 42px;
  height: 24px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text);
  text-align: center;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  outline: none;
  appearance: textfield;
  -moz-appearance: textfield;
}

.repeatInput:focus {
  border-color: var(--c-accent);
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
}

.repeatInput::-webkit-outer-spin-button,
.repeatInput::-webkit-inner-spin-button {
  margin: 0;
  appearance: none;
  -webkit-appearance: none;
}

.userActorChip,
.tokenPicker {
  flex: 0 0 128px;
  width: 128px;
  min-width: 0;
}

.userActorChip {
  height: 32px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 3px 8px 3px 4px;
  border: 1px solid transparent;
  border-radius: 999px;
}

.actorDisplayName {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text);
  font-size: 12px;
  font-weight: 700;
}

.tokenPicker {
  position: relative;
}

.tokenPickerBtn {
  width: 100%;
  height: 32px;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 3px 8px 3px 4px;
  border: 1px solid var(--c-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-surface) 92%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.tokenPickerBtn:hover,
.tokenPickerBtn.open {
  border-color: color-mix(in srgb, var(--c-primary) 32%, var(--c-border));
  background: color-mix(in srgb, var(--c-surface) 86%, var(--c-bg));
}

.tokenPickerBtn:focus-visible {
  outline: none;
  border-color: color-mix(in srgb, var(--c-primary) 56%, var(--c-border));
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--c-primary) 16%, transparent);
}

.tokenPickerName,
.tokenPickerOptionName {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.tokenPickerName {
  flex: 1;
  text-align: left;
}

.tokenPickerArrow {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-right: 1.5px solid var(--c-text-muted);
  border-bottom: 1.5px solid var(--c-text-muted);
  transform: rotate(45deg) translateY(-2px);
}

.tokenPickerBtn.open .tokenPickerArrow {
  transform: rotate(225deg) translate(-1px, -1px);
}

.tokenPickerMenu {
  position: absolute;
  z-index: 760;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  max-height: 220px;
  overflow-y: auto;
  display: grid;
  gap: 3px;
  padding: 5px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.32);
}

.tokenPickerOption {
  min-width: 0;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 7px 4px 4px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.tokenPickerOption:hover {
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 24%, transparent);
}

.tokenPickerOption.selected {
  background: color-mix(in srgb, var(--c-primary) 16%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
}

.modalFormula {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid color-mix(in srgb, var(--c-border) 82%, transparent);
  border-radius: 6px;
  background: color-mix(in srgb, var(--c-surface) 88%, var(--c-bg));
  color: var(--c-text-muted);
  font-size: 12px;
}

.modalFormula code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text);
}

.modalFooter {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
