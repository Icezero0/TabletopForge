<script setup lang="ts">
import { computed } from "vue";
import type { RoomCombatState, RoomToken } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { RemoteObjectSelection, TableToolMode } from "@/features/table/types";
import TokenItem from "@/features/table/components/TokenItem.vue";
import { canInspectToken, canManageToken } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  tokens: RoomToken[];
  combatState?: RoomCombatState | null;
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  gridCellFt: number;
  gridCellPx: number;
  selectedTokenId?: number | null;
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
  characterDataHiddenById?: Map<number, boolean>;
  playerColorByUserId?: Map<number, string>;
  remoteSelections?: RemoteObjectSelection[];
  isClientPointFogged?: (clientX: number, clientY: number) => boolean;
}>();

const emit = defineEmits<{
  selectToken: [tokenId: number];
  tokenContextMenu: [tokenId: number, event: MouseEvent];
}>();

const sortedTokens = computed(() => {
  const isGM = props.gameRole === "GM";
  return [...props.tokens]
    .filter((t) => {
      if (!t.visible) return false;
      if (t.character_hidden && !isGM && !isOwnHiddenToken(t)) return false;
      return true;
    })
    .sort((a, b) => a.z_index - b.z_index || a.id - b.id);
});

const activeCombatants = computed(() => (
  props.combatState?.active
    ? [...props.combatState.combatants].sort((a, b) => a.turn_order - b.turn_order)
    : []
));

const combatTokenIds = computed(() => new Set(activeCombatants.value.map((combatant) => combatant.token_id)));

const activeCombatTokenId = computed(() =>
  activeCombatants.value[props.combatState?.turn_index ?? -1]?.token_id ?? null,
);

function isOwnHiddenToken(token: RoomToken): boolean {
  if (props.gameRole !== "PL" || props.currentUserId == null) return false;
  const ownerId =
    token.linked_character_owner_id ??
    props.characterOwnerById.get(token.linked_character_id);
  return ownerId === props.currentUserId;
}

function isTokenDimmed(token: RoomToken): boolean {
  return !!token.character_hidden && (props.gameRole === "GM" || isOwnHiddenToken(token));
}

const canPick = computed(
  () => props.toolMode === "select" || props.toolMode === "hand",
);

function canPickToken(token: RoomToken): boolean {
  if (!canPick.value) return false;
  if (remoteSelectionFor(token.id)) return false;
  return (
    canInspectToken(token) ||
    canManageToken(token, props.gameRole, props.currentUserId, props.characterOwnerById)
  );
}

function remoteSelectionFor(tokenId: number) {
  return props.remoteSelections?.find((claim) => claim.type === "token" && claim.id === tokenId) ?? null;
}

function onTokenPointerDown(token: RoomToken, event: PointerEvent) {
  if (!canPickToken(token)) return;
  if (props.isClientPointFogged?.(event.clientX, event.clientY)) return;
  event.stopPropagation();
}

function onTokenClick(token: RoomToken, event: MouseEvent) {
  if (!canPickToken(token)) return;
  if (props.isClientPointFogged?.(event.clientX, event.clientY)) return;
  event.stopPropagation();
  emit("selectToken", token.id);
}

function onTokenContextMenu(token: RoomToken, event: MouseEvent) {
  if (!canPickToken(token)) return;
  if (props.isClientPointFogged?.(event.clientX, event.clientY)) return;
  event.preventDefault();
  event.stopPropagation();
  emit("tokenContextMenu", token.id, event);
}
</script>

<template>
  <div class="tokenLayer">
    <TokenItem
      v-for="token in sortedTokens"
      :key="token.id"
      :token="token"
      :grid-cell-ft="gridCellFt"
      :grid-cell-px="gridCellPx"
      :selected="selectedTokenId === token.id"
      :in-combat="combatTokenIds.has(token.id)"
      :active-combat-turn="activeCombatTokenId === token.id"
      :remote-selection-color="remoteSelectionFor(token.id)?.color"
      :inactive="!canPickToken(token)"
      :dimmed="isTokenDimmed(token)"
      :game-role="gameRole"
      :character-data-hidden="characterDataHiddenById?.get(token.linked_character_id) === true"
      :player-color-by-user-id="playerColorByUserId"
      @pointerdown="onTokenPointerDown(token, $event)"
      @click="onTokenClick(token, $event)"
      @contextmenu="onTokenContextMenu(token, $event)"
    />
  </div>
</template>

<style scoped>
.tokenLayer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.tokenLayer :deep(.tokenWrap:not(.inactive)) {
  pointer-events: auto;
  cursor: default;
}
</style>
