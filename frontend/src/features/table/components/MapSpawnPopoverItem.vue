<script setup lang="ts">
import { computed, toRef } from "vue";
import { useI18n } from "vue-i18n";
import type { RoomMap } from "@/infra/api/rooms.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = defineProps<{
  map: RoomMap;
  selected?: boolean;
}>();

const emit = defineEmits<{
  select: [];
}>();

const { t } = useI18n();
const assetId = toRef(() => props.map.asset_id);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetId);

const label = computed(() => t("table.assets.mapLabel", { id: props.map.id }));
</script>

<template>
  <button
    type="button"
    class="card"
    :class="{ selected }"
    @click="emit('select')"
  >
    <div class="thumb">
      <img v-if="imageUrl" :src="imageUrl" class="thumbImg" :alt="label" />
      <span v-else class="thumbFallback">#{{ map.id }}</span>
    </div>
    <span class="name">{{ label }}</span>
  </button>
</template>

<style scoped>
.card {
  flex: 0 0 132px;
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
}

.card:hover {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-accent) 8%, var(--c-bg-subtle));
}

.card.selected {
  border-color: var(--c-accent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--c-accent) 35%, transparent);
}

.thumb {
  width: 72px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c-bg) 70%, var(--c-surface));
}

.thumbImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbFallback {
  font-size: 12px;
  color: var(--c-text-muted);
}

.name {
  font-size: 12px;
  font-weight: 500;
}
</style>
