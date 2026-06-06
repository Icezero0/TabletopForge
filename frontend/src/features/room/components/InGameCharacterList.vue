<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import type { RoomToken } from "@/infra/api/rooms.api";
import InGameCharacterListItem from "@/features/room/components/InGameCharacterListItem.vue";
import FloatingPanel from "@/features/table/components/FloatingPanel.vue";

export type OnFieldTokenRow = {
  token: RoomToken;
  entry?: RoomCharacterEntry;
  instanceLabel?: string;
  ownerLabel: string;
};

const props = defineProps<{
  roomId: number;
  tokens: RoomToken[];
  characterById: Map<number, RoomCharacterEntry>;
  ownerNameByUserId: Map<number, string>;
  loading?: boolean;
  gameRole?: GameRole | "unknown";
}>();

const emit = defineEmits<{
  inspect: [payload: { characterId: number; tokenId?: number; tokenInstanceName?: string }];
}>();

const { t } = useI18n();

const onFieldRows = computed((): OnFieldTokenRow[] => {
  const linked = props.tokens.filter(
    (token) => token.visible && token.linked_character_id != null,
  );
  const byCharacter = new Map<number, RoomToken[]>();
  for (const token of linked) {
    const characterId = token.linked_character_id!;
    const group = byCharacter.get(characterId) ?? [];
    group.push(token);
    byCharacter.set(characterId, group);
  }

  const rows: OnFieldTokenRow[] = [];
  for (const group of byCharacter.values()) {
    const sorted = [...group].sort((a, b) => a.id - b.id);
    sorted.forEach((token, index) => {
      const characterId = token.linked_character_id!;
      const entry = props.characterById.get(characterId);
      const ownerId = entry?.owner_id ?? token.linked_character_owner_id ?? null;
      const ownerLabel =
        (ownerId != null ? props.ownerNameByUserId.get(ownerId) : null) ??
        (ownerId != null ? `User #${ownerId}` : "—");
      rows.push({
        token,
        entry,
        instanceLabel:
          sorted.length > 1 && index > 0
            ? t("table.characterList.instanceLabel", { n: index + 1 })
            : undefined,
        ownerLabel,
      });
    });
  }

  return rows.sort((a, b) => a.token.z_index - b.token.z_index || a.token.id - b.token.id);
});
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
      <p v-else-if="onFieldRows.length === 0" class="muted">
        {{ t("table.characterList.emptyOnField") }}
      </p>
      <ul v-else class="list">
        <InGameCharacterListItem
          v-for="row in onFieldRows"
          :key="row.token.id"
          :token="row.token"
          :entry="row.entry"
          :instance-label="row.instanceLabel"
          :owner-label="row.ownerLabel"
          :game-role="gameRole"
          @inspect="emit('inspect', $event)"
        />
      </ul>
    </div>
  </FloatingPanel>
</template>

<style scoped>
.listBody {
  min-width: 240px;
  max-width: 320px;
}

.muted {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
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
