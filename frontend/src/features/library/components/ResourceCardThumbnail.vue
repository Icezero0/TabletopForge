<script setup lang="ts">
import { computed, toRef } from "vue";
import type { ResourceType } from "@/infra/api/library.api";
import { getResourceTypeMeta, MusicalNoteIcon } from "@/features/library/constants";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{
  type: ResourceType;
  assetId: number | null;
}>();

const meta = computed(() => getResourceTypeMeta(props.type));
const assetId = toRef(props, "assetId");
const { url, loading } = useAuthenticatedAssetUrl(assetId);
</script>

<template>
  <div class="thumbnail">
    <template v-if="meta.isImage">
      <div v-if="loading" class="placeholder">
        <AppIcon :icon="meta.icon" :size="32" />
      </div>
      <img v-else-if="url" :src="url" alt="" class="img" />
      <div v-else class="placeholder">
        <AppIcon :icon="meta.icon" :size="32" />
      </div>
    </template>

    <template v-else-if="meta.isAudio">
      <div class="placeholder audio">
        <AppIcon :icon="MusicalNoteIcon" :size="32" />
      </div>
    </template>

    <template v-else>
      <div class="placeholder">
        <AppIcon :icon="meta.icon" :size="32" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.thumbnail {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: var(--r-1) var(--r-1) 0 0;
  background: var(--c-surface-raised);
  display: flex;
  align-items: center;
  justify-content: center;
}

.img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--c-text-muted);
}

.audio {
  color: var(--c-accent);
}
</style>
