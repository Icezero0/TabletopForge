<script setup lang="ts">
import { computed, useId } from "vue";
const props = withDefaults(
  defineProps<{
    gridCellPx?: number;
    scaleBarCells?: number;
  }>(),
  {
    gridCellPx: 40,
    scaleBarCells: 5,
  },
);

const patternUid = useId().replace(/:/g, "");

const minorPatternId = computed(() => `grid-minor-${patternUid}`);
const majorPatternId = computed(() => `grid-major-${patternUid}`);

const majorCellPx = computed(() => props.gridCellPx * props.scaleBarCells);
</script>

<template>
  <div class="mapViewport">
    <svg
      class="gridLayer"
      aria-hidden="true"
    >
      <defs>
        <pattern
          :id="minorPatternId"
          :width="gridCellPx"
          :height="gridCellPx"
          patternUnits="userSpaceOnUse"
        >
          <path
            :d="`M ${gridCellPx} 0 L 0 0 0 ${gridCellPx}`"
            class="gridLineMinor"
          />
        </pattern>
        <pattern
          :id="majorPatternId"
          :width="majorCellPx"
          :height="majorCellPx"
          patternUnits="userSpaceOnUse"
        >
          <path
            :d="`M ${majorCellPx} 0 L 0 0 0 ${majorCellPx}`"
            class="gridLineMajor"
          />
        </pattern>
      </defs>
      <rect
        width="100%"
        height="100%"
        :fill="`url(#${minorPatternId})`"
      />
      <rect
        width="100%"
        height="100%"
        :fill="`url(#${majorPatternId})`"
      />
    </svg>
  </div>
</template>

<style scoped>
.mapViewport {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  background: color-mix(in srgb, var(--c-surface) 78%, var(--c-bg));
  overflow: hidden;
}

.gridLayer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.gridLineMinor {
  fill: none;
  stroke: color-mix(in srgb, var(--c-text) 32%, transparent);
  stroke-width: 1.25;
  stroke-dasharray: 5 4;
  vector-effect: non-scaling-stroke;
}

.gridLineMajor {
  fill: none;
  stroke: color-mix(in srgb, var(--c-text) 50%, transparent);
  stroke-width: 2;
  stroke-dasharray: 10 6;
  vector-effect: non-scaling-stroke;
}
</style>
