<script setup lang="ts">
import { computed } from "vue";
import type { RoomToken } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode } from "@/features/table/types";
import TokenItem from "@/features/table/components/TokenItem.vue";
import { canInspectToken, canManageToken } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  tokens: RoomToken[];
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
  gridCellFt: number;
  gridCellPx: number;
  selectedTokenId?: number | null;
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
  playerColorByUserId?: Map<number, string>;
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
      if (!isGM && t.character_hidden) return false;
      return true;
    })
    .sort((a, b) => a.z_index - b.z_index || a.id - b.id);
});

function isTokenDimmed(token: RoomToken): boolean {
  return props.gameRole === "GM" && !!token.character_hidden;
}

const canPick = computed(
  () => props.toolMode === "select" || props.toolMode === "hand",
);

function canPickToken(token: RoomToken): boolean {
  if (!canPick.value) return false;
  return (
    canInspectToken(token) ||
    canManageToken(token, props.gameRole, props.currentUserId, props.characterOwnerById)
  );
}

function onTokenPointerDown(token: RoomToken, event: PointerEvent) {
  if (!canPickToken(token)) return;
  event.stopPropagation();
}

function onTokenClick(token: RoomToken, event: MouseEvent) {
  if (!canPickToken(token)) return;
  event.stopPropagation();
  emit("selectToken", token.id);
}

function onTokenContextMenu(token: RoomToken, event: MouseEvent) {
  if (!canPickToken(token)) return;
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
      :inactive="!canPickToken(token)"
      :dimmed="isTokenDimmed(token)"
      :game-role="gameRole"
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
