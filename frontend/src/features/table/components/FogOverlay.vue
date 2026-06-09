<script setup lang="ts">
import { computed, useId } from "vue";
import type { GameRole } from "@/features/room/types";
import type { FogSubTool } from "@/features/table/types";
import type { RoomFogMapMask, RoomFogState, RoomMap } from "@/infra/api/rooms.api";
import { FOG_LAYER_Z, SCENE_ORIGIN, SCENE_SPAN } from "@/features/table/constants";

const props = defineProps<{
  fogState: RoomFogState | null;
  maps: RoomMap[];
  gameRole: GameRole | "unknown";
  previewPoint?: { x: number; y: number } | null;
  previewMode?: FogSubTool;
  previewRadius?: number;
}>();

const uid = useId().replace(/:/g, "");
const opacity = computed(() => (props.gameRole === "GM" ? 0.6 : 0.95));
const previewRadius = computed(() => props.previewRadius ?? 48);
const mapById = computed(() => new Map(props.maps.map((map) => [map.id, map])));
const masks = computed(() => Object.values(props.fogState?.maps ?? {}));

function maskId(mask: RoomFogMapMask) {
  return `fog-mask-${uid}-${mask.map_id}`;
}

function mapWidth(mask: RoomFogMapMask) {
  const map = mapById.value.get(mask.map_id);
  return mask.map_width * (map?.scale_x ?? map?.scale ?? 1);
}

function mapHeight(mask: RoomFogMapMask) {
  const map = mapById.value.get(mask.map_id);
  return mask.map_height * (map?.scale_y ?? map?.scale ?? 1);
}
</script>

<template>
  <svg
    v-if="masks.length || previewPoint"
    class="fogOverlay"
    :viewBox="`${SCENE_ORIGIN} ${SCENE_ORIGIN} ${SCENE_SPAN} ${SCENE_SPAN}`"
    :style="{
      left: `${SCENE_ORIGIN}px`,
      top: `${SCENE_ORIGIN}px`,
      width: `${SCENE_SPAN}px`,
      height: `${SCENE_SPAN}px`,
      opacity,
      zIndex: FOG_LAYER_Z,
    }"
    aria-hidden="true"
  >
    <defs>
      <mask
        v-for="mask in masks"
        :id="maskId(mask)"
        :key="`mask-${mask.map_id}`"
        style="mask-type: luminance"
        maskUnits="userSpaceOnUse"
        :x="mapById.get(mask.map_id)?.x ?? 0"
        :y="mapById.get(mask.map_id)?.y ?? 0"
        :width="mapWidth(mask)"
        :height="mapHeight(mask)"
      >
        <image
          :href="mask.data_url"
          :x="mapById.get(mask.map_id)?.x ?? 0"
          :y="mapById.get(mask.map_id)?.y ?? 0"
          :width="mapWidth(mask)"
          :height="mapHeight(mask)"
          preserveAspectRatio="none"
        />
      </mask>
    </defs>

    <template v-for="mask in masks" :key="`fog-${mask.map_id}`">
      <rect
        v-if="mapById.has(mask.map_id)"
        :x="mapById.get(mask.map_id)!.x"
        :y="mapById.get(mask.map_id)!.y"
        :width="mapWidth(mask)"
        :height="mapHeight(mask)"
        fill="black"
        :mask="`url(#${maskId(mask)})`"
      />
    </template>

    <circle
      v-if="previewPoint"
      class="brushPreview"
      :class="{ erase: previewMode === 'erase', fill: previewMode === 'fill' }"
      :cx="previewPoint.x"
      :cy="previewPoint.y"
      :r="previewRadius"
    />
  </svg>
</template>

<style scoped>
.fogOverlay {
  position: absolute;
  pointer-events: none;
  overflow: visible;
}

.brushPreview {
  fill: rgb(0 0 0 / 18%);
  stroke: rgb(255 255 255 / 88%);
  stroke-width: 2;
  stroke-dasharray: 8 6;
  vector-effect: non-scaling-stroke;
}

.brushPreview.fill {
  fill: rgb(0 0 0 / 26%);
  stroke: rgb(0 0 0 / 80%);
}

.brushPreview.erase {
  fill: rgb(255 255 255 / 18%);
}
</style>
