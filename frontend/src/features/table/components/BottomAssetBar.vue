<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import BaseButton from "@/ui/base/BaseButton.vue";
import MapSpawnPopover from "@/features/table/components/MapSpawnPopover.vue";
import type { RoomMap } from "@/infra/api/rooms.api";

defineProps<{
  canAddMap?: boolean;
  maps?: RoomMap[];
  selectedMapId?: number | null;
}>();

const mapPopoverOpen = defineModel<boolean>("mapPopoverOpen", { default: false });

const emit = defineEmits<{
  addMap: [];
  selectMap: [mapId: number];
  openLibraryPicker: [];
}>();

const { t } = useI18n();
const mapAnchorRef = ref<HTMLElement | null>(null);

function toggleMapPopover(event: MouseEvent) {
  event.stopPropagation();
  mapPopoverOpen.value = !mapPopoverOpen.value;
}

function closeMapPopover() {
  mapPopoverOpen.value = false;
}

function onSelectMap(mapId: number) {
  emit("selectMap", mapId);
}
</script>

<template>
  <div class="bottomAssetBar">
    <div v-if="canAddMap" ref="mapAnchorRef" class="mapAnchor">
      <BaseButton variant="primary" @click="toggleMapPopover">
        {{ t("table.assets.addMap") }}
      </BaseButton>
      <MapSpawnPopover
        :open="mapPopoverOpen"
        :anchor-el="mapAnchorRef"
        :maps="maps ?? []"
        :selected-map-id="selectedMapId"
        @close="closeMapPopover"
        @select-map="onSelectMap"
        @add-map="emit('addMap')"
        @open-library-picker="emit('openLibraryPicker')"
      />
    </div>
  </div>
</template>

<style scoped>
.bottomAssetBar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 4px 8px;
}

.mapAnchor {
  position: relative;
}
</style>
