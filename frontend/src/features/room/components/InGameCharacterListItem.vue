<script setup lang="ts">
import { computed, toRef } from "vue";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import type { RoomToken } from "@/infra/api/rooms.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import { formatTokenPreview, tokenInitial } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  token: RoomToken;
  entry?: RoomCharacterEntry;
  instanceLabel?: string;
  ownerLabel: string;
  gameRole?: GameRole | "unknown";
}>();

const emit = defineEmits<{
  inspect: [payload: { characterId: number; tokenId: number; tokenInstanceName: string }];
}>();

const { t } = useI18n();

const assetId = toRef(() => props.entry?.token_image_asset_id ?? props.token.asset_id);
const { url: tokenUrl } = useAuthenticatedAssetUrl(assetId);

const displayName = computed(() => {
  const base = props.token.name.trim() || props.entry?.name || "?";
  return props.instanceLabel ? `${base} ${props.instanceLabel}` : base;
});

const ownerDisplay = computed(() => {
  if (props.entry?.kind === "pc" && props.entry.player_name?.trim()) {
    return props.entry.player_name.trim();
  }
  return props.ownerLabel;
});

const statsText = computed(() => {
  const summary = props.token.state_summary;
  if (!summary) return "—";
  return formatTokenPreview(summary, {
    damageLabel: t("room.characters.damageTakenShort"),
  }) || "—";
});

function onClick() {
  if (props.token.linked_character_id == null) return;
  emit("inspect", {
    characterId: props.token.linked_character_id,
    tokenId: props.token.id,
    tokenInstanceName: displayName.value,
  });
}
</script>

<template>
  <li class="row" @click="onClick">
    <div class="thumb">
      <img v-if="tokenUrl" :src="tokenUrl" class="thumbImg" :alt="displayName" />
      <span v-else class="thumbInitial">{{ tokenInitial(displayName) }}</span>
    </div>
    <div class="meta">
      <div class="nameRow">
        <span class="name">{{ displayName }}</span>
        <span v-if="entry" class="kind">{{ t(`room.characters.kindTag.${entry.kind}`) }}</span>
      </div>
      <div class="stats">{{ statsText }}</div>
      <div class="owner">
        {{ t("table.characterList.owner") }} {{ ownerDisplay }}
      </div>
    </div>
  </li>
</template>

<style scoped>
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  cursor: pointer;
}

.row:hover {
  border-color: color-mix(in srgb, var(--c-accent) 40%, var(--c-border));
}

.thumb {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  border: 1px solid var(--c-border);
}

.thumbImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbInitial {
  font-size: 13px;
  font-weight: 700;
}

.meta {
  flex: 1;
  min-width: 0;
}

.nameRow {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.name {
  font-size: 14px;
  font-weight: 600;
}

.kind {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-accent) 15%, transparent);
  color: var(--c-text-muted);
}

.stats {
  font-size: 12px;
  color: var(--c-text-muted);
  margin-top: 2px;
}

.owner {
  font-size: 11px;
  color: var(--c-text-muted);
  margin-top: 2px;
}
</style>
