<script setup lang="ts">
import { toRef } from "vue";
import type { Character } from "@/infra/api/character.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import { tokenInitial } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  character: Character;
  inRoom?: boolean;
  inRoomLabel?: string;
}>();

const emit = defineEmits<{
  pick: [character: Character];
}>();

const assetId = toRef(() => props.character.token_image_asset_id ?? props.character.portrait_asset_id ?? null);
const { url: imgUrl } = useAuthenticatedAssetUrl(assetId);

</script>

<template>
  <li
    class="pickItem"
    :class="{ inRoom }"
    @click="!inRoom && emit('pick', character)"
  >
    <div class="pickThumb">
      <img v-if="imgUrl" :src="imgUrl" class="pickThumbImg" :alt="character.name" />
      <span v-else class="pickThumbInitial">{{ tokenInitial(character.name) }}</span>
    </div>
    <div class="pickMeta">
      <span class="pickName">{{ character.name }}</span>
    </div>
    <span v-if="inRoom" class="inRoomBadge">{{ inRoomLabel }}</span>
  </li>
</template>

<style scoped>
.pickItem {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  cursor: pointer;
  list-style: none;
}

.pickItem:hover:not(.inRoom) {
  border-color: var(--c-accent);
}

.pickItem.inRoom {
  opacity: 0.55;
  cursor: default;
}

.pickThumb {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c-accent) 15%, var(--c-bg));
  border: 1px solid var(--c-border);
}

.pickThumbImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pickThumbInitial {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-accent);
}

.pickMeta {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.pickName {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
}

.inRoomBadge {
  font-size: 11px;
  color: var(--c-text-muted);
  flex-shrink: 0;
}
</style>
