<script setup lang="ts">
import { computed } from "vue";
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
  selectedCharacterId?: number | null;
}>();

const emit = defineEmits<{
  inspect: [payload: { characterId: number }];
  toggleVisibility: [payload: { roomCharacterId: number; isHidden: boolean }];
  remove: [roomCharacterId: number];
}>();

const { t } = useI18n();

const visibleEntries = computed(() =>
  props.entries.filter((entry) => {
    if (!entry.is_hidden) return true;
    if (props.gameRole === "GM") return true;
    if (props.gameRole === "PL") {
      return props.currentUserId != null && entry.owner_id === props.currentUserId;
    }
    return false;
  }),
);
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
      <p v-if="loading" class="muted">{{ t("common.loading") }}</p>
      <p v-else-if="visibleEntries.length === 0" class="muted empty">
        {{ t("table.characterList.empty") }}
      </p>
      <ul v-else class="list">
        <InGameCharacterListItem
          v-for="entry in visibleEntries"
          :key="entry.room_character_id"
          :entry="entry"
          :owner-label="(entry.owner_id != null ? ownerNameByUserId.get(entry.owner_id) : null) ?? `User #${entry.owner_id}`"
          :game-role="gameRole"
          :current-user-id="currentUserId"
          :selected="entry.character_id === selectedCharacterId"
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
  overflow: hidden;
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
  overflow: visible;
}
</style>
