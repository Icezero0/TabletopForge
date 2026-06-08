<script setup lang="ts">
import { computed } from "vue";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = defineProps<{ entry: RoomCharacterEntry }>();
const emit = defineEmits<{ select: [] }>();

const assetIdRef = computed(() => props.entry.token_image_asset_id);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetIdRef);

function initial(name: string) {
  return name.trim().charAt(0).toUpperCase() || "?";
}
</script>

<template>
  <button type="button" class="card" @click="emit('select')">
    <div class="thumb">
      <img v-if="imageUrl" :src="imageUrl" class="thumbImg" :alt="entry.name" />
      <span v-else class="thumbInitial">{{ initial(entry.name) }}</span>
    </div>
    <span class="name">{{ entry.name }}</span>
  </button>
</template>

<style scoped>
.card {
  flex: 0 0 88px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: 12px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  color: var(--c-text);
  cursor: pointer;
  text-align: center;
  transition: background 0.12s ease, border-color 0.12s ease;
}

.card:hover {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-accent) 8%, var(--c-bg-subtle));
}

.thumb {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c-bg) 70%, var(--c-surface));
  flex-shrink: 0;
}

.thumbImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbInitial {
  font-size: 24px;
  font-weight: 600;
  color: var(--c-text-muted);
}

.name {
  font-size: 12px;
  font-weight: 500;
  word-break: break-all;
  line-height: 1.3;
}
</style>
