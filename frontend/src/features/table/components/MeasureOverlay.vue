<script setup lang="ts">
import { computed } from "vue";
import type { MeasureState } from "@/features/table/composables/useMeasureTool";

const props = defineProps<{
  state: MeasureState | null;
}>();

const midpoint = computed(() => {
  if (!props.state) return { x: 0, y: 0 };
  const { x1, y1, x2, y2 } = props.state;
  return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 };
});
</script>

<template>
  <svg
    v-if="state"
    class="measureOverlay"
    aria-hidden="true"
  >
    <line
      :x1="state.x1"
      :y1="state.y1"
      :x2="state.x2"
      :y2="state.y2"
      class="measureLine"
    />
    <circle
      :cx="state.x1"
      :cy="state.y1"
      r="3"
      class="measureAnchor"
    />
    <circle
      :cx="state.x2"
      :cy="state.y2"
      r="3"
      class="measureAnchor"
    />
    <text
      :x="midpoint.x"
      :y="midpoint.y"
      class="measureLabel"
    >
      {{ state.labelFt }} ft
    </text>
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
  z-index: 7;
}

.measureLine {
  stroke: var(--c-primary);
  stroke-width: 5;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 2px color-mix(in srgb, var(--c-bg) 80%, transparent));
}

.measureAnchor {
  fill: var(--c-primary);
  stroke: var(--c-surface);
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
</style>
