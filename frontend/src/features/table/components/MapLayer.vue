<script setup lang="ts">
import { computed } from "vue";
import type { RoomMap } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode } from "@/features/table/types";
import MapImageItem from "@/features/table/components/MapImageItem.vue";

const props = defineProps<{
  maps: RoomMap[];
  toolMode: TableToolMode;
  gameRole: GameRole | "unknown";
}>();

const emit = defineEmits<{
  select: [mapId: number];
  mapContextMenu: [mapId: number, event: MouseEvent];
  naturalSize: [payload: { mapId: number; w: number; h: number }];
}>();

const sortedMaps = computed(() =>
  [...props.maps].sort((a, b) => a.z_index - b.z_index || a.id - b.id),
);

const canPickMap = computed(
  () =>
    props.gameRole === "GM" &&
    (props.toolMode === "select" || props.toolMode === "hand"),
);

function isLockedInHandMode(map: RoomMap) {
  return props.toolMode === "hand" && map.locked;
}

function onMapPointerDown(event: PointerEvent) {
  if (!canPickMap.value) return;
  if (event.button === 1) return;
  event.stopPropagation();
}

function onMapClick(map: RoomMap, event: MouseEvent) {
  if (!canPickMap.value) return;
  event.stopPropagation();
  emit("select", map.id);
}

function onMapContextMenu(map: RoomMap, event: MouseEvent) {
  if (!canPickMap.value) return;
  event.preventDefault();
  event.stopPropagation();
  emit("mapContextMenu", map.id, event);
}
</script>

<template>
  <div class="mapLayer">
    <div
      v-for="map in sortedMaps"
      :key="map.id"
      class="mapItem"
      :class="{ inactive: !canPickMap }"
      :style="{
        transform: `translate(${map.x}px, ${map.y}px) scale(${map.scale_x ?? map.scale}, ${map.scale_y ?? map.scale})`,
        pointerEvents: isLockedInHandMode(map) ? 'none' : undefined,
      }"
      @pointerdown="onMapPointerDown($event)"
      @click="onMapClick(map, $event)"
      @contextmenu="onMapContextMenu(map, $event)"
    >
      <MapImageItem
        :map-id="map.id"
        :asset-id="map.asset_id"
        @natural-size="emit('naturalSize', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.mapLayer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.mapItem {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  pointer-events: auto;
}

.mapItem.inactive {
  pointer-events: none;
}
</style>
