<script setup lang="ts">
import { computed } from "vue";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = defineProps<{
  mapId: number;
  assetId: number;
}>();

const emit = defineEmits<{
  naturalSize: [payload: { mapId: number; w: number; h: number }];
}>();

const assetIdRef = computed(() => props.assetId);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetIdRef);

function onImageLoad(event: Event) {
  const img = event.target as HTMLImageElement;
  emit("naturalSize", {
    mapId: props.mapId,
    w: img.naturalWidth,
    h: img.naturalHeight,
  });
}
</script>

<template>
  <img
    v-if="imageUrl"
    class="mapImage"
    :src="imageUrl"
    alt=""
    draggable="false"
    @load="onImageLoad"
  />
</template>

<style scoped>
.mapImage {
  display: block;
  max-width: none;
  user-select: none;
  pointer-events: none;
}
</style>
