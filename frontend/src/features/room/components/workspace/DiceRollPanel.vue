<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { EyeIcon, EyeSlashIcon, PencilSquareIcon, PlusIcon, TrashIcon } from "@heroicons/vue/24/outline";
import { useDiceStore, type DiceDraft } from "@/stores/dice.store";
import { useAuthStore } from "@/stores/auth.store";
import { useEntitiesStore } from "@/stores/entities.store";
import { useTabletopStore } from "@/stores/tabletop.store";
import type { DiceRoll, DiceRollDetail, DiceVisibility } from "@/infra/api/dice.api";
import type { GameRole } from "@/features/room/types";
import { canManageToken } from "@/features/table/utils/tokenDisplay";
import DiceActorAvatar from "@/features/room/components/workspace/DiceActorAvatar.vue";

const props = defineProps<{
  roomId: number;
  active?: boolean;
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
}>();

type EditorMode = "check" | "value";
type ExtraTerm = {
  id: number;
  kind: "dice" | "modifier";
  count: number;
  faces: number;
  value: number;
};
type ActorOption = {
  key: string;
  type: "user" | "token";
  id: number | null;
  name: string;
  avatarUrl?: string | null;
  assetId?: number | null;
};

const diceStore = useDiceStore();
const auth = useAuthStore();
const entitiesStore = useEntitiesStore();
const tabletopStore = useTabletopStore();
const mode = ref<EditorMode>("check");
const d20Mode = ref<"normal" | "advantage" | "disadvantage">("normal");
const extraTerms = ref<ExtraTerm[]>([]);
const manualFormula = ref("");
const formulaEditorOpen = ref(false);
const label = ref("");
const visibility = ref<DiceVisibility>("public");
const actorType = ref<"user" | "token">("user");
const actorTokenId = ref<number | null>(null);
const actorDisplayName = ref("");
const panelActorPickerOpen = ref(false);
const timelineRef = ref<HTMLElement | null>(null);
const preservingHistoryScroll = ref(false);
const hasActivatedScroll = ref(false);
const formulaHistory = ref<string[]>([]);
const formulaHistoryCursor = ref<number | null>(null);
const formulaHistoryDraft = ref("");

const FORMULA_HISTORY_LIMIT = 50;

const roomState = computed(() => diceStore.getRoomState(props.roomId));
const rolls = computed(() => roomState.value.items);
const roomTokens = computed(() => tabletopStore.getTokens(props.roomId));
const formulaHistoryStorageKey = computed(() => `tabletopforge:dice-formula-history:${props.roomId}`);
const currentUserActor = computed<ActorOption>(() => ({
  key: auth.me?.id ? `user:${auth.me.id}` : "user:me",
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
        type: "token",
        id: actorTokenId.value,
        name: actorDisplayName.value || `指示物 #${actorTokenId.value}`,
        assetId: null,
      }
    );
  }
  return currentUserActor.value;
});
const structuredFormula = computed(() => {
  const terms = extraTerms.value.map((term, index) => termFormula(term, mode.value === "value" && index === 0)).filter(Boolean);
  if (mode.value === "value") return terms.join("");
  const main =
    d20Mode.value === "advantage"
      ? "2d20kh1"
      : d20Mode.value === "disadvantage"
        ? "2d20kl1"
        : "1d20";
  return `${main}${terms.join("")}`;
});

let nextTermId = 1;

watch(() => roomState.value.draft, (draft) => {
  if (!draft) return;
  applyDraft(draft);
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
  const count = Math.max(1, Number(term.count) || 1);
  const faces = Math.max(2, Number(term.faces) || 6);
  return `${omitLeadingPlus ? "" : "+"}${count}d${faces}`;
}

function parsedTermToEditor(term: ParsedTerm): ExtraTerm | null {
  if (term.type === "modifier") {
    return makeTerm("modifier", { value: term.sign * term.value });
  }
  if (term.sign < 0 || term.keep) return null;
  return makeTerm("dice", { count: term.count, faces: term.faces });
}

type ParsedTerm =
  | { type: "dice"; sign: number; count: number; faces: number; keep: "kh1" | "kl1" | null }
  | { type: "modifier"; sign: number; value: number };

function normalizeFormulaInput(raw: string) {
  return raw
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
  const re = /([+-]?)(?:(\d*)d(\d*)(kh1|kl1)?|(\d+))/g;
  const terms: ParsedTerm[] = [];
  let pos = 0;
  for (const match of normalized.matchAll(re)) {
    if (match.index !== pos) return null;
    pos = match.index + match[0].length;
    const sign = match[1] === "-" ? -1 : 1;
    if (match[5] != null) {
      terms.push({ type: "modifier", sign, value: Number(match[5]) });
      continue;
    }
    terms.push({
      type: "dice",
      sign,
      count: Number(match[2] || "1"),
      faces: Number(match[3] || "20"),
      keep: (match[4] as "kh1" | "kl1" | undefined) ?? null,
    });
  }
  return pos === normalized.length ? terms : null;
}

function parseFormulaDraft(raw: string) {
  const terms = parseTerms(raw);
  if (!terms) {
    return;
  }
  const first = terms[0];
  const isNormalD20 =
    first?.type === "dice" &&
    first.sign > 0 &&
    first.count === 1 &&
    first.faces === 20 &&
    first.keep == null;
  const isAdvD20 =
    first?.type === "dice" &&
    first.sign > 0 &&
    first.count === 2 &&
    first.faces === 20 &&
    (first.keep === "kh1" || first.keep === "kl1");
  if (isNormalD20 || isAdvD20) {
    mode.value = "check";
    d20Mode.value = first.keep === "kh1" ? "advantage" : first.keep === "kl1" ? "disadvantage" : "normal";
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
    await diceStore.loadOlderRolls(props.roomId, 30);
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
    return findToken(roll.actor_token_id)?.name || roll.actor_display_name || "指示物";
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
  return findToken(roll.actor_token_id)?.asset_id ?? null;
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

function togglePanelActorPicker() {
  panelActorPickerOpen.value = !panelActorPickerOpen.value;
}

async function submitRoll() {
  if (!props.roomId || roomState.value.isRolling) return;
  const nextFormula = manualFormula.value.trim();
  if (!nextFormula) return;
  await diceStore.roll(props.roomId, {
    actor_type: actorType.value,
    actor_token_id: actorType.value === "token" ? actorTokenId.value : null,
    label: label.value.trim(),
    formula: nextFormula,
    visibility: visibility.value,
  });
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
        <div class="panelActorSelect">
          <button
            type="button"
            class="panelActorSelectBtn"
            :class="{ open: panelActorPickerOpen }"
            aria-haspopup="listbox"
            :aria-expanded="panelActorPickerOpen"
            @click="togglePanelActorPicker"
          >
            <DiceActorAvatar
              :kind="selectedActor.type"
              :name="selectedActor.name"
              :avatar-url="selectedActor.avatarUrl"
              :asset-id="selectedActor.assetId"
            />
            <span class="panelActorName">{{ selectedActor.name }}</span>
            <span class="tokenPickerArrow" aria-hidden="true"></span>
          </button>
          <div v-if="panelActorPickerOpen" class="panelActorMenu" role="listbox">
            <button
              v-for="option in allActorOptions"
              :key="option.key"
              type="button"
              class="panelActorOption"
              :class="{ selected: option.key === selectedActor.key }"
              role="option"
              :aria-selected="option.key === selectedActor.key"
              @click="selectActor(option)"
            >
              <DiceActorAvatar
                :kind="option.type"
                :name="option.name"
                :avatar-url="option.avatarUrl"
                :asset-id="option.assetId"
              />
              <span class="panelActorOptionName">{{ option.name }}</span>
            </button>
          </div>
        </div>
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
          </div>

          <div v-if="mode === 'check'" class="structuredEditor">
            <div class="formattedRow">
              <span class="mainDie">d20</span>
              <div class="advantageToggle" role="group" aria-label="优势状态">
                <button type="button" :class="{ active: d20Mode === 'normal' }" @click="d20Mode = 'normal'">普通</button>
                <button type="button" :class="{ active: d20Mode === 'advantage' }" @click="d20Mode = 'advantage'">优势</button>
                <button type="button" :class="{ active: d20Mode === 'disadvantage' }" @click="d20Mode = 'disadvantage'">劣势</button>
              </div>
            </div>
            <div class="termList">
              <div v-for="term in extraTerms" :key="term.id" class="termRow">
                <button type="button" class="termKindToggle" @click="toggleTermKind(term)">
                  {{ term.kind === "dice" ? "骰子" : "加值" }}
                </button>
                <template v-if="term.kind === 'dice'">
                  <input v-model.number="term.count" class="numInput" type="number" min="1" max="100" />
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
                  <input v-model.number="term.count" class="numInput" type="number" min="1" max="100" />
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

.panelActorSelect {
  position: relative;
  flex: 0 0 144px;
  min-width: 0;
}

.panelActorSelectBtn {
  width: 100%;
  height: 28px;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px 3px 4px;
  border: 1px solid var(--c-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-surface) 92%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.panelActorSelectBtn:hover,
.panelActorSelectBtn.open {
  border-color: color-mix(in srgb, var(--c-primary) 32%, var(--c-border));
  background: color-mix(in srgb, var(--c-surface) 86%, var(--c-bg));
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
  flex: 1;
  text-align: left;
}

.panelActorMenu {
  position: absolute;
  z-index: 360;
  left: 0;
  right: 0;
  bottom: calc(100% + 6px);
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

.panelActorOption {
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

.panelActorOption:hover {
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 24%, transparent);
}

.panelActorOption.selected {
  background: color-mix(in srgb, var(--c-primary) 16%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
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
  display: grid;
  gap: 7px;
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
