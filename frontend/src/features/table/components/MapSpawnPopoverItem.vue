<script setup lang="ts">
import { toRef } from "vue";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = defineProps<{
  assetId: number | null;
  name: string;
  selected?: boolean;
}>();

const emit = defineEmits<{
  select: [];
}>();

const assetId = toRef(() => props.assetId);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetId);
</script>

<template>
  <button
    type="button"
    class="card"
    :class="{ selected }"
    @click="emit('select')"
  >
    <div class="thumb">
      <img v-if="imageUrl" :src="imageUrl" class="thumbImg" :alt="name" />
      <span v-else class="thumbFallback">?</span>
    </div>
    <span class="name">{{ name }}</span>
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
  word-break: break-all;
  line-height: 1.3;
}
</style>
