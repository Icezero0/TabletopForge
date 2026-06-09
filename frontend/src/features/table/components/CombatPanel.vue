<script setup lang="ts">
import { computed, ref } from "vue";
import { XMarkIcon } from "@heroicons/vue/24/outline";
import type { GameRole, RoomCombatState, RoomMember, RoomToken } from "@/infra/api/rooms.api";
import CombatTokenAvatar from "@/features/table/components/CombatTokenAvatar.vue";
import { useDiceStore } from "@/stores/dice.store";

const props = defineProps<{
  roomId: number;
  tokens: RoomToken[];
  members: Pick<RoomMember, "user_id" | "game_role">[];
  combatState: RoomCombatState | null;
  gameRole: GameRole | "unknown";
  currentUserId: number | null;
  saving?: boolean;
}>();

const emit = defineEmits<{
  "update-combat": [state: RoomCombatState | null];
  error: [message: string];
  "select-token": [tokenId: number];
  "focus-token": [tokenId: number];
}>();

const diceStore = useDiceStore();
const dialogOpen = ref(false);
const dialogMode = ref<"start" | "edit">("start");
const selectedTokenIds = ref<Set<number>>(new Set());
const startingCombat = ref(false);

const isGm = computed(() => props.gameRole === "GM");
const activeCombat = computed(() =>
  props.combatState?.active ? props.combatState : null,
);

const tokenById = computed(() => {
  const map = new Map<number, RoomToken>();
  for (const token of props.tokens) map.set(token.id, token);
  return map;
});

const memberGameRoleByUserId = computed(() => {
  const map = new Map<number, GameRole>();
  for (const member of props.members) map.set(member.user_id, member.game_role);
  return map;
});

const combatRows = computed(() => {
  const state = activeCombat.value;
  if (!state) return [];
  return [...state.combatants]
    .sort((a, b) => a.turn_order - b.turn_order)
    .map((combatant, index) => ({
      combatant,
      token: tokenById.value.get(combatant.token_id) ?? null,
      active: index === state.turn_index,
      waiting: (combatant.ready_round ?? 1) > state.round,
    }));
});

const activeCombatRow = computed(() =>
  combatRows.value.find((row) => row.active) ?? null,
);

const canEndCurrentTurn = computed(() => {
  const row = activeCombatRow.value;
  const token = row?.token;
  if (row?.waiting) return false;
  if (!activeCombat.value || !token) return false;
  if (isGm.value) return true;
  if (props.currentUserId == null) return false;
  return token.linked_character_owner_id === props.currentUserId;
});

const activeCombatTokenIds = computed(() => new Set(
  activeCombat.value?.combatants.map((combatant) => combatant.token_id) ?? [],
));

const combatantByTokenId = computed(() => {
  const map = new Map<number, NonNullable<RoomCombatState["combatants"][number]>>();
  for (const combatant of activeCombat.value?.combatants ?? []) {
    map.set(combatant.token_id, combatant);
  }
  return map;
});

const availableTokens = computed(() =>
  props.tokens.filter(
    (token) =>
      (dialogMode.value === "edit" || !activeCombatTokenIds.value.has(token.id)) &&
      !selectedTokenIds.value.has(token.id),
  ),
);

const selectedTokens = computed(() =>
  props.tokens.filter((token) => selectedTokenIds.value.has(token.id)),
);

function openStartDialog() {
  dialogMode.value = "start";
  selectedTokenIds.value = new Set();
  dialogOpen.value = true;
}

function openEditDialog() {
  dialogMode.value = "edit";
  selectedTokenIds.value = new Set(activeCombat.value?.combatants.map((combatant) => combatant.token_id) ?? []);
  dialogOpen.value = true;
}

function panelNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function initiativeBonus(token: RoomToken) {
  const panel = token.panel;
  if (!panel || typeof panel !== "object") return 0;
  return panelNumber((panel as Record<string, unknown>).initiative) ?? 0;
}

function addToken(tokenId: number) {
  selectedTokenIds.value = new Set([...selectedTokenIds.value, tokenId]);
}

function removeToken(tokenId: number) {
  const next = new Set(selectedTokenIds.value);
  next.delete(tokenId);
  selectedTokenIds.value = next;
}

function initiativeFormula(bonus: number) {
  if (bonus === 0) return "d20";
  return bonus > 0 ? `d20+${bonus}` : `d20${bonus}`;
}

function rollValueFromDetail(detail: unknown, fallback: number) {
  const terms = (detail as { terms?: unknown[] } | null)?.terms;
  if (!Array.isArray(terms)) return fallback;
  const d20 = terms.find((term) => {
    const typed = term as { type?: unknown; faces?: unknown };
    return typed.type === "dice" && typed.faces === 20;
  }) as { rolls?: { value?: unknown; kept?: unknown }[] } | undefined;
  const kept = d20?.rolls?.find((roll) => roll.kept !== false);
  return typeof kept?.value === "number" && Number.isFinite(kept.value)
    ? kept.value
    : fallback;
}

async function rollInitiativeForToken(token: RoomToken, readyRound: number) {
  const bonus = initiativeBonus(token);
  const roll = await diceStore.roll(props.roomId, {
    actor_type: "token",
    actor_token_id: token.id,
    label: "先攻掷骰",
    formula: initiativeFormula(bonus),
    visibility: "public",
  });
  const total = roll.total ?? bonus;
  return {
    token_id: token.id,
    initiative_bonus: bonus,
    roll: rollValueFromDetail(roll.detail, total - bonus),
    initiative: total,
    turn_order: 0,
    ready_round: readyRound,
  };
}

function isPlayerToken(tokenId: number) {
  const token = tokenById.value.get(tokenId);
  if (!token) return false;
  const ownerUserId = token.linked_character_owner_id ?? token.owner_user_id;
  return memberGameRoleByUserId.value.get(ownerUserId) === "PL";
}

function sortCombatants<T extends { initiative: number; roll: number; token_id: number }>(combatants: T[]) {
  return [...combatants]
    .sort((a, b) => {
      const initiativeDiff = b.initiative - a.initiative;
      if (initiativeDiff !== 0) return initiativeDiff;

      const playerPriorityDiff = Number(isPlayerToken(b.token_id)) - Number(isPlayerToken(a.token_id));
      if (playerPriorityDiff !== 0) return playerPriorityDiff;

      return b.roll - a.roll || a.token_id - b.token_id;
    })
    .map((combatant, index) => ({ ...combatant, turn_order: index }));
}

async function applyCombatDialog() {
  const selected = selectedTokens.value;
  if (!selected.length) return;

  startingCombat.value = true;
  try {
    const rolled = [];
    for (const token of selected) {
      const existing = dialogMode.value === "edit" ? combatantByTokenId.value.get(token.id) : null;
      const readyRound = dialogMode.value === "edit" && activeCombat.value
        ? activeCombat.value.round + 1
        : 1;
      rolled.push(existing ? { ...existing } : await rollInitiativeForToken(token, readyRound));
    }

    const combatants = sortCombatants(rolled);
    const state = activeCombat.value;
    const currentTokenId = activeCombatRow.value?.combatant.token_id ?? null;
    const preservedTurnIndex = currentTokenId == null
      ? 0
      : combatants.findIndex((combatant) => combatant.token_id === currentTokenId);
    let nextRound = state?.round ?? 1;
    let nextTurnIndex = preservedTurnIndex;
    if (nextTurnIndex < 0) {
      const startIndex = state ? Math.min(state.turn_index, Math.max(0, combatants.length - 1)) : 0;
      nextTurnIndex = combatants.findIndex(
        (combatant, index) => index >= startIndex && (combatant.ready_round ?? 1) <= nextRound,
      );
      if (nextTurnIndex < 0) {
        nextTurnIndex = combatants.findIndex((combatant) => (combatant.ready_round ?? 1) <= nextRound);
      }
      if (nextTurnIndex < 0) {
        nextRound += 1;
        nextTurnIndex = combatants.findIndex((combatant) => (combatant.ready_round ?? 1) <= nextRound);
      }
      if (nextTurnIndex < 0) nextTurnIndex = 0;
    }

    emit("update-combat", {
      active: true,
      round: nextRound,
      turn_index: nextTurnIndex,
      combatants,
    });
    dialogOpen.value = false;
  } catch (error) {
    emit("error", error instanceof Error ? error.message : "先攻掷骰失败");
  } finally {
    startingCombat.value = false;
  }
}

function endCombat() {
  emit("update-combat", null);
}

function endCurrentTurn() {
  const state = activeCombat.value;
  if (!state || !state.combatants.length || props.saving) return;
  const ordered = [...state.combatants].sort((a, b) => a.turn_order - b.turn_order);
  let nextRound = state.round;
  let nextIndex = -1;
  for (let index = state.turn_index + 1; index < ordered.length; index += 1) {
    if ((ordered[index]?.ready_round ?? 1) <= state.round) {
      nextIndex = index;
      break;
    }
  }
  if (nextIndex < 0) {
    nextRound = state.round + 1;
    nextIndex = ordered.findIndex((combatant) => (combatant.ready_round ?? 1) <= nextRound);
  }
  if (nextIndex < 0) nextIndex = 0;
  emit("update-combat", {
    ...state,
    round: nextRound,
    turn_index: nextIndex,
    combatants: state.combatants.map((combatant) => ({ ...combatant })),
  });
}
</script>

<template>
  <div class="combatPanel">
    <div v-if="!activeCombat" class="emptyState">
      <span>当前没有战斗</span>
      <button
        v-if="isGm"
        type="button"
        class="primaryBtn"
        :disabled="saving || tokens.length === 0"
        @click="openStartDialog"
      >
        开启战斗
      </button>
    </div>

    <div v-else class="combatList">
      <div class="combatMeta">
        <span class="roundLabel">第 {{ activeCombat.round }} 轮</span>
        <button
          type="button"
          class="primaryBtn turnEndBtn"
          :class="{ hiddenControl: !canEndCurrentTurn }"
          :disabled="saving || !canEndCurrentTurn"
          :tabindex="canEndCurrentTurn ? 0 : -1"
          :aria-hidden="!canEndCurrentTurn"
          @click="canEndCurrentTurn && endCurrentTurn()"
        >
          结束回合
        </button>
        <span v-if="isGm" class="combatActions">
          <button
            type="button"
            class="ghostBtn"
            :disabled="saving"
            @click="openEditDialog"
          >
            编辑
          </button>
          <button
            type="button"
            class="ghostBtn"
            :disabled="saving"
            @click="endCombat"
          >
            结束
          </button>
        </span>
        <span v-else class="combatEndPlaceholder" aria-hidden="true"></span>
      </div>

      <div class="combatQueue">
        <div
          v-for="row in combatRows"
          :key="row.combatant.token_id"
          class="combatRow"
          :class="{ active: row.active, waiting: row.waiting }"
          role="button"
          tabindex="0"
          @click="emit('select-token', row.combatant.token_id)"
          @dblclick="emit('focus-token', row.combatant.token_id)"
          @keydown.enter.prevent="emit('select-token', row.combatant.token_id)"
          @keydown.space.prevent="emit('select-token', row.combatant.token_id)"
        >
          <span class="turnMarker" aria-hidden="true" />
          <CombatTokenAvatar
            class="tokenAvatar large"
            :name="row.token?.name || '未知指示物'"
            :asset-id="row.token?.asset_id ?? null"
          />
          <span class="tokenName">{{ row.token?.name || '未知指示物' }}</span>
          <span class="initiativeValue">{{ row.combatant.initiative }}</span>
          <span v-if="row.waiting" class="waitingBadge">下轮</span>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="dialogOpen" class="modalOverlay">
        <div class="combatDialog" role="dialog" aria-modal="true" :aria-label="dialogMode === 'edit' ? '编辑参战者' : '开启战斗'">
          <div class="dialogHead">
            <div>
              <h2>{{ dialogMode === 'edit' ? '编辑参战者' : '开启战斗' }}</h2>
              <p>{{ dialogMode === 'edit' ? '调整本次战斗成员。新增指示物会自动投掷先攻。' : '从未参战指示物中选择本次战斗成员，并自动投掷先攻。' }}</p>
            </div>
            <button type="button" class="iconBtn" @click="dialogOpen = false">
              <XMarkIcon aria-hidden="true" />
            </button>
          </div>

          <div class="combatPicker">
            <section class="pickerSection">
              <div class="sectionHead">
                <span>未参战</span>
                <span>{{ availableTokens.length }}</span>
              </div>
              <TransitionGroup name="tokenMove" tag="div" class="tokenGrid">
                <button
                  v-for="token in availableTokens"
                  :key="token.id"
                  type="button"
                  class="tokenCard"
                  @click="addToken(token.id)"
                >
                  <CombatTokenAvatar class="tokenAvatar large" :name="token.name" :asset-id="token.asset_id" />
                  <span class="tokenPickName">{{ token.name }}</span>
                  <span class="tokenPickInit">先攻 {{ initiativeBonus(token) >= 0 ? '+' : '' }}{{ initiativeBonus(token) }}</span>
                </button>
                <div v-if="availableTokens.length === 0" key="available-empty" class="gridEmpty">没有可加入的指示物</div>
              </TransitionGroup>
            </section>

            <section class="pickerSection selectedSection">
              <div class="sectionHead">
                <span>已参战</span>
                <span>{{ selectedTokens.length }}</span>
              </div>
              <TransitionGroup name="tokenMove" tag="div" class="tokenGrid">
                <button
                  v-for="token in selectedTokens"
                  :key="token.id"
                  type="button"
                  class="tokenCard selected"
                  @click="removeToken(token.id)"
                >
                  <CombatTokenAvatar class="tokenAvatar large" :name="token.name" :asset-id="token.asset_id" />
                  <span class="tokenPickName">{{ token.name }}</span>
                  <span class="tokenPickInit">先攻 {{ initiativeBonus(token) >= 0 ? '+' : '' }}{{ initiativeBonus(token) }}</span>
                </button>
                <div v-if="selectedTokens.length === 0" key="selected-empty" class="gridEmpty">点击上方指示物加入战斗</div>
              </TransitionGroup>
            </section>
          </div>

          <div class="dialogActions">
            <button type="button" class="ghostBtn" @click="dialogOpen = false">取消</button>
            <button
              type="button"
              class="primaryBtn"
              :disabled="saving || startingCombat || selectedTokenIds.size === 0"
              @click="applyCombatDialog"
            >
              {{ startingCombat ? '投掷中…' : '确定' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.combatPanel {
  display: grid;
  min-height: 0;
  color: var(--c-text);
}

.emptyState {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px;
  color: var(--c-text-muted);
  font-size: 13px;
}

.combatList {
  display: grid;
  gap: 8px;
  padding: 8px;
}

.combatMeta {
  display: grid;
  grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
  align-items: center;
  gap: 10px;
  min-height: 34px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.roundLabel {
  justify-self: start;
  white-space: nowrap;
}

.combatActions,
.combatEndPlaceholder {
  justify-self: end;
}

.combatActions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.combatEndPlaceholder {
  display: block;
  width: 88px;
  height: 28px;
}

.turnEndBtn {
  justify-self: center;
  box-sizing: border-box;
  min-width: 88px;
  min-height: 34px;
}

.hiddenControl {
  visibility: hidden;
  pointer-events: none;
}

.combatQueue {
  display: flex;
  gap: 8px;
  width: max-content;
  max-width: calc(100vw - 56px);
  overflow-x: auto;
  overflow-y: visible;
  padding-bottom: 2px;
}

.combatRow {
  position: relative;
  display: grid;
  grid-template-rows: 36px minmax(16px, auto) auto;
  place-items: center;
  gap: 5px;
  width: 96px;
  aspect-ratio: 1;
  flex: 0 0 auto;
  padding: 10px 8px 8px;
  border: 1px solid color-mix(in srgb, var(--c-border) 75%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 86%, transparent);
  cursor: pointer;
  text-align: center;
  user-select: none;
  transition:
    border-color 0.16s ease,
    background 0.16s ease,
    box-shadow 0.16s ease,
    opacity 0.16s ease,
    transform 0.16s ease;
}

.combatRow:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--c-primary) 72%, transparent);
  outline-offset: 2px;
}

.combatRow.active {
  border-color: color-mix(in srgb, var(--c-primary) 68%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 13%, var(--c-surface));
}

.combatRow:hover {
  border-color: color-mix(in srgb, var(--c-primary) 44%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 8%, var(--c-surface));
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, var(--c-primary) 20%, transparent),
    inset 0 10px 24px color-mix(in srgb, var(--c-primary) 8%, transparent);
}

.combatRow.active:hover {
  border-color: color-mix(in srgb, var(--c-primary) 82%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
}

.combatRow.waiting {
  border-style: dashed;
  border-color: color-mix(in srgb, var(--c-border) 82%, transparent);
  background: color-mix(in srgb, var(--c-surface) 72%, transparent);
  opacity: 0.62;
}

.combatRow.waiting:hover {
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
  opacity: 0.78;
}

.combatRow.waiting.active {
  opacity: 0.76;
}

.turnMarker {
  position: absolute;
  top: 5px;
  left: 50%;
  width: 28px;
  height: 3px;
  border-radius: 99px;
  transform: translateX(-50%);
  background: transparent;
}

.combatRow.active .turnMarker {
  background: var(--c-primary);
}

.tokenAvatar {
  width: 28px;
  height: 28px;
}

.tokenAvatar.large {
  width: 36px;
  height: 36px;
  transition:
    filter 0.16s ease,
    transform 0.16s ease;
}

.combatRow:hover .tokenAvatar.large {
  filter: saturate(1.08) brightness(1.06);
  transform: scale(1.04);
}

.tokenName,
.tokenPickName {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
}

.initiativeValue {
  color: var(--c-text);
  font-size: 12px;
  font-weight: 700;
}

.waitingBadge {
  position: absolute;
  top: 5px;
  right: 6px;
  padding: 1px 5px;
  border: 1px solid color-mix(in srgb, var(--c-border) 80%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-surface) 90%, transparent);
  color: var(--c-text-muted);
  font-size: 10px;
  font-weight: 700;
  line-height: 1.4;
}

.primaryBtn,
.ghostBtn,
.iconBtn {
  border: 1px solid color-mix(in srgb, var(--c-border) 80%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 92%, transparent);
  color: var(--c-text);
  cursor: pointer;
}

.primaryBtn {
  padding: 7px 11px;
  border-color: color-mix(in srgb, var(--c-primary) 70%, transparent);
  background: var(--c-primary);
  color: white;
  font-size: 13px;
  font-weight: 700;
}

.ghostBtn {
  padding: 5px 9px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.primaryBtn:disabled,
.ghostBtn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.modalOverlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgb(2 6 23 / 0.54);
}

.combatDialog {
  width: min(620px, calc(100vw - 48px));
  max-height: min(82vh, 720px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  border: 1px solid color-mix(in srgb, var(--c-border) 80%, transparent);
  border-radius: 12px;
  background: var(--c-surface);
  box-shadow: 0 24px 80px rgb(0 0 0 / 0.32);
  overflow: hidden;
}

.dialogHead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid color-mix(in srgb, var(--c-border) 70%, transparent);
}

.dialogHead h2 {
  margin: 0;
  font-size: 16px;
}

.dialogHead p {
  margin: 6px 0 0;
  color: var(--c-text-muted);
  font-size: 12px;
}

.iconBtn {
  display: inline-grid;
  place-items: center;
  width: 30px;
  height: 30px;
  padding: 0;
}

.iconBtn svg {
  width: 18px;
  height: 18px;
}

.combatPicker {
  display: grid;
  grid-template-rows: minmax(120px, 1fr) minmax(120px, 1fr);
  gap: 12px;
  min-height: 0;
  padding: 12px;
  overflow: auto;
}

.pickerSection {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  min-height: 0;
}

.sectionHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--c-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.tokenGrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(92px, 104px));
  justify-content: start;
  align-content: start;
  gap: 8px;
  min-height: 132px;
  padding: 8px;
  border: 1px solid color-mix(in srgb, var(--c-border) 70%, transparent);
  border-radius: 10px;
  background: color-mix(in srgb, var(--c-bg) 40%, transparent);
  overflow: auto;
}

.tokenCard {
  display: grid;
  grid-template-rows: 36px auto auto;
  place-items: center;
  gap: 5px;
  width: 100%;
  aspect-ratio: 1;
  min-height: 100px;
  padding: 10px 8px;
  border: 1px solid color-mix(in srgb, var(--c-border) 75%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  text-align: center;
  cursor: pointer;
  will-change: transform, opacity;
}

.tokenCard.selected {
  border-color: color-mix(in srgb, var(--c-primary) 70%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 12%, var(--c-surface));
}

.tokenPickInit {
  color: var(--c-text-muted);
  font-size: 12px;
}

.gridEmpty {
  grid-column: 1 / -1;
  align-self: center;
  justify-self: center;
  padding: 18px 8px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.tokenMove-move,
.tokenMove-enter-active,
.tokenMove-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease,
    filter 0.18s ease;
}

.tokenMove-enter-from,
.tokenMove-leave-to {
  opacity: 0;
  filter: saturate(0.8);
  transform: scale(0.94) translateY(6px);
}

.tokenMove-leave-active {
  pointer-events: none;
}

.dialogActions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid color-mix(in srgb, var(--c-border) 70%, transparent);
}

@media (max-width: 640px) {
  .tokenGrid {
    grid-template-columns: repeat(auto-fill, minmax(88px, 1fr));
  }
}
</style>
