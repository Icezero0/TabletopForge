<script setup lang="ts">
import { computed } from "vue";
import type { RemoteCursor, RemoteLaser } from "@/features/table/composables/useTabletopPointer";

const props = defineProps<{
  cursors: RemoteCursor[];
  lasers: RemoteLaser[];
}>();

const cursorHue = (userId: number) => (userId * 47) % 360;

const cursorItems = computed(() =>
  props.cursors.map((c) => ({
    ...c,
    hue: cursorHue(c.userId),
    style: {
      transform: `translate(${c.x}px, ${c.y}px)`,
    },
  })),
);

const laserItems = computed(() =>
  props.lasers.map((l) => {
    const hue = cursorHue(l.userId);
    return {
      ...l,
      hue,
      x: Math.min(l.x1, l.x2),
      y: Math.min(l.y1, l.y2),
      width: Math.max(2, Math.abs(l.x2 - l.x1)),
      height: Math.max(2, Math.abs(l.y2 - l.y1)),
    };
  }),
);
</script>

<template>
  <div class="pointerOverlay" aria-hidden="true">
    <svg class="laserLayer">
      <line
        v-for="laser in laserItems"
        :key="`laser-${laser.userId}`"
        :x1="laser.x1"
        :y1="laser.y1"
        :x2="laser.x2"
        :y2="laser.y2"
        class="laserLine"
        :style="{ stroke: `hsl(${laser.hue} 85% 55%)` }"
      />
    </svg>
    <div
      v-for="cursor in cursorItems"
      :key="cursor.userId"
      class="remoteCursor"
      :style="cursor.style"
    >
      <span
        class="cursorDot"
        :style="{ background: `hsl(${cursor.hue} 85% 55%)` }"
      />
      <span
        class="cursorLabel"
        :style="{
          background: `color-mix(in srgb, hsl(${cursor.hue} 85% 55%) 22%, var(--c-surface))`,
          borderColor: `hsl(${cursor.hue} 70% 45%)`,
        }"
      >
        {{ cursor.displayName }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.pointerOverlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: visible;
  z-index: 210;
}

.laserLayer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.laserLine {
  stroke-width: 3;
  stroke-linecap: round;
  opacity: 0.85;
  filter: drop-shadow(0 0 4px currentColor);
}

.remoteCursor {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.cursorDot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--c-surface);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--c-text) 25%, transparent);
}

.cursorLabel {
  margin-left: 12px;
  margin-top: -6px;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text);
  white-space: nowrap;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
