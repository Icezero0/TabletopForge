<script setup lang="ts">
import { computed } from "vue";
import type { MeasureState } from "@/features/table/composables/useMeasureTool";
import { MEASURE_LAYER_Z } from "@/features/table/constants";

const props = defineProps<{
  state: MeasureState | null;
}>();

const lineMidpoint = computed(() => {
  if (!props.state || props.state.kind !== "line") return { x: 0, y: 0 };
  const { x1, y1, x2, y2 } = props.state;
  return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 };
});

const routePolylinePoints = computed(() => {
  if (!props.state || props.state.kind !== "route") return "";
  const { waypoints, cursor } = props.state;
  const all = cursor ? [...waypoints, cursor] : waypoints;
  return all.map(([x, y]) => `${x},${y}`).join(" ");
});

const routeLastPoint = computed((): [number, number] => {
  if (!props.state || props.state.kind !== "route") return [0, 0];
  const { waypoints, cursor } = props.state;
  return cursor ?? waypoints[waypoints.length - 1] ?? [0, 0];
});
</script>

<template>
  <svg
    v-if="state"
    class="measureOverlay"
    aria-hidden="true"
    :style="{ zIndex: MEASURE_LAYER_Z }"
  >
    <!-- Line mode -->
    <template v-if="state.kind === 'line'">
      <line
        :x1="state.x1"
        :y1="state.y1"
        :x2="state.x2"
        :y2="state.y2"
        class="measureLine"
      />
      <circle :cx="state.x1" :cy="state.y1" r="3" class="measureAnchor" />
      <circle :cx="state.x2" :cy="state.y2" r="3" class="measureAnchor" />
      <text :x="lineMidpoint.x" :y="lineMidpoint.y" class="measureLabel">
        {{ state.labelFt }} ft
      </text>
    </template>

    <!-- Route mode -->
    <template v-if="state.kind === 'route'">
      <polyline
        v-if="routePolylinePoints"
        :points="routePolylinePoints"
        class="measureLine"
        fill="none"
      />
      <!-- Per-segment labels -->
      <template v-for="(seg, i) in state.segments" :key="i">
        <text
          v-if="seg.labelFt >= 1"
          :x="(seg.x1 + seg.x2) / 2"
          :y="(seg.y1 + seg.y2) / 2"
          class="measureLabel"
        >
          {{ seg.labelFt }} ft
        </text>
      </template>
      <!-- Waypoint anchors -->
      <circle
        v-for="([x, y], i) in state.waypoints"
        :key="i"
        :cx="x"
        :cy="y"
        r="3"
        class="measureAnchor"
      />
      <!-- Cursor anchor -->
      <circle
        v-if="state.cursor"
        :cx="state.cursor[0]"
        :cy="state.cursor[1]"
        r="3"
        class="measureAnchorCursor"
      />
      <!-- Total label at last point -->
      <text
        v-if="state.totalFt >= 1"
        :x="routeLastPoint[0]"
        :y="routeLastPoint[1] - 14"
        class="measureTotalLabel"
      >
        {{ state.totalFt }} ft
      </text>
    </template>
  </svg>
</template>

<style scoped>
.measureOverlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.measureLine {
  stroke: var(--c-primary);
  stroke-width: 5;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 2px color-mix(in srgb, var(--c-bg) 80%, transparent));
}

.measureAnchor {
  fill: var(--c-primary);
  stroke: var(--c-surface);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}

.measureAnchorCursor {
  fill: color-mix(in srgb, var(--c-primary) 50%, transparent);
  stroke: var(--c-primary);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
}

.measureLabel {
  fill: var(--c-text);
  font-size: 13px;
  font-weight: 700;
  text-anchor: middle;
  dominant-baseline: middle;
  paint-order: stroke;
  stroke: var(--c-surface);
  stroke-width: 4px;
  pointer-events: none;
}

.measureTotalLabel {
  fill: var(--c-primary);
  font-size: 14px;
  font-weight: 800;
  text-anchor: middle;
  dominant-baseline: auto;
  paint-order: stroke;
  stroke: var(--c-surface);
  stroke-width: 4px;
  pointer-events: none;
}
</style>
