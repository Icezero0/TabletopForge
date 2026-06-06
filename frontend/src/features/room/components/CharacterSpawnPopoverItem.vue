<script setup lang="ts">
import { toRef } from "vue";
import { useI18n } from "vue-i18n";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import { tokenInitial } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  entry: RoomCharacterEntry;
  canSpawn: boolean;
  statsText?: string;
}>();

const emit = defineEmits<{
  spawn: [];
}>();

const { t } = useI18n();
const assetId = toRef(() => props.entry.token_image_asset_id);
const { url: tokenUrl } = useAuthenticatedAssetUrl(assetId);

function onClick() {
  if (!props.canSpawn) return;
  emit("spawn");
}
</script>

<template>
  <button
    type="button"
    class="card"
    :class="{ disabled: !canSpawn }"
    :disabled="!canSpawn"
    @click="onClick"
  >
    <div class="thumb">
      <img v-if="tokenUrl" :src="tokenUrl" class="thumbImg" :alt="entry.name" />
      <span v-else class="thumbInitial">{{ tokenInitial(entry.name) }}</span>
    </div>
    <span class="name">{{ entry.name }}</span>
    <span class="kind">{{ t(`room.characters.kindTag.${entry.kind}`) }}</span>
    <span v-if="entry.player_name" class="sub">{{ entry.player_name }}</span>
    <div v-if="statsText" class="stats">{{ statsText }}</div>
  </button>
</template>

<style scoped>
.card {
  flex: 0 0 132px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  border-radius: 12px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  color: var(--c-text);
  cursor: pointer;
  text-align: center;
}

.card:hover:not(.disabled) {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-accent) 8%, var(--c-bg-subtle));
}

.card.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.thumb {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
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
  font-size: 16px;
  font-weight: 700;
}

.name {
  font-size: 13px;
  font-weight: 600;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kind {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-accent) 15%, transparent);
  color: var(--c-text-muted);
}

.sub {
  font-size: 11px;
  color: var(--c-text-muted);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  font-size: 10px;
  color: var(--c-text-muted);
}
</style>
