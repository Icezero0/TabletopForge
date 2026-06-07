<script setup lang="ts">
import { toRef } from "vue";
import type { LibraryResource } from "@/infra/api/library.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = defineProps<{
  resource: LibraryResource;
}>();

const emit = defineEmits<{
  pick: [];
}>();

const assetId = toRef(() => props.resource.primary_asset_id ?? null);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetId);
</script>

<template>
  <button type="button" class="card" @click="emit('pick')">
    <div class="thumb">
      <img v-if="imageUrl" :src="imageUrl" class="img" :alt="resource.name" />
      <span v-else class="placeholder" />
    </div>
    <span class="name">{{ resource.name }}</span>
  </button>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  padding: 8px;
  border-radius: 10px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.card:hover {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-accent) 8%, var(--c-bg-subtle));
}

.thumb {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c-bg) 60%, var(--c-surface));
}

.img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  display: block;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background: var(--c-border);
  opacity: 0.5;
}

.name {
  font-size: 12px;
  font-weight: 500;
  color: var(--c-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
