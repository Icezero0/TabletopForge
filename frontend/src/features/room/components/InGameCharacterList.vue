<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import InGameCharacterListItem from "@/features/room/components/InGameCharacterListItem.vue";
import FloatingPanel from "@/features/table/components/FloatingPanel.vue";

const props = defineProps<{
  roomId: number;
  entries: RoomCharacterEntry[];
  ownerNameByUserId: Map<number, string>;
  currentUserId?: number;
  loading?: boolean;
  gameRole?: GameRole | "unknown";
}>();

const emit = defineEmits<{
  inspect: [payload: { characterId: number }];
  addCharacter: [];
  toggleVisibility: [payload: { roomCharacterId: number; isHidden: boolean }];
  remove: [roomCharacterId: number];
}>();

const { t } = useI18n();

const isGm = () => props.gameRole === "GM";
</script>

<template>
  <FloatingPanel
    :title="t('table.characterList.title')"
    inline
    collapse-to="top-left"
    variant="character_list"
    :storage-key="`room-${roomId}-character-list`"
  >
    <div class="listBody">
      <div v-if="isGm() || gameRole === 'PL'" class="toolbar">
        <button class="addBtn" @click="emit('addCharacter')">
          + {{ t("table.characterList.addCharacter") }}
        </button>
      </div>
      <p v-if="loading" class="muted">{{ t("common.loading") }}</p>
      <p v-else-if="entries.length === 0" class="muted empty">
        {{ t("table.characterList.empty") }}
      </p>
      <ul v-else class="list">
        <InGameCharacterListItem
          v-for="entry in entries"
          :key="entry.room_character_id"
          :entry="entry"
          :owner-label="(entry.owner_id != null ? ownerNameByUserId.get(entry.owner_id) : null) ?? `User #${entry.owner_id}`"
          :game-role="gameRole"
          :current-user-id="currentUserId"
          @inspect="emit('inspect', $event)"
          @toggle-visibility="emit('toggleVisibility', $event)"
          @remove="emit('remove', $event)"
        />
      </ul>
    </div>
  </FloatingPanel>
</template>

<style scoped>
.listBody {
  min-width: 240px;
  max-width: 320px;
  padding: 8px;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
  padding-right: 4px;
}

.addBtn {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  color: var(--c-text);
  cursor: pointer;
}

.addBtn:hover {
  border-color: var(--c-accent);
  color: var(--c-accent);
}

.muted {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
}

.empty {
  text-align: center;
  padding: 12px 0;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
  max-height: min(40vh, 360px);
  overflow: auto;
}
</style>
