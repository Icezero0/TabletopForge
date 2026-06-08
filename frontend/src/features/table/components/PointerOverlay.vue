<script setup lang="ts">
import { computed } from "vue";
import type { RemoteCursor, RemoteLaser } from "@/features/table/composables/useTabletopPointer";

const props = defineProps<{
  cursors: RemoteCursor[];
  lasers: RemoteLaser[];
  colorByUserId?: Map<number, string>;
}>();

function cursorColor(userId: number): string {
  return props.colorByUserId?.get(userId) ?? `hsl(${(userId * 47) % 360} 85% 55%)`;
}

const cursorItems = computed(() =>
  props.cursors.map((c) => ({
    ...c,
    color: cursorColor(c.userId),
    style: {
      transform: `translate(${c.x}px, ${c.y}px)`,
    },
  })),
);

const laserItems = computed(() =>
  props.lasers.map((l) => {
    const color = cursorColor(l.userId);
    const segments = l.trail.slice(1).map((point, index) => {
      const prev = l.trail[index]!;
      const dx = point.x - prev.x;
      const dy = point.y - prev.y;
      const length = Math.max(1, Math.hypot(dx, dy));
      const angle = Math.atan2(dy, dx);
      return {
        id: point.id,
        style: {
          width: `${length}px`,
          opacity: point.opacity,
          transform: `translate(${prev.x}px, ${prev.y}px) rotate(${angle}rad)`,
          "--laser-color": color,
        },
      };
    });
    return {
      ...l,
      color,
      style: {
        transform: `translate(${l.x}px, ${l.y}px)`,
        "--laser-color": color,
      },
      segments,
    };
  }),
);
</script>

<template>
  <div class="pointerOverlay" aria-hidden="true">
    <template v-for="laser in laserItems" :key="`laser-${laser.userId}`">
      <span
        v-for="segment in laser.segments"
        :key="`laser-trail-${laser.userId}-${segment.id}`"
        class="laserTrailSegment"
        :style="segment.style"
      />
      <span
        v-if="laser.active"
        class="laserSpot"
        :style="laser.style"
      />
    </template>
    <div
      v-for="cursor in cursorItems"
      :key="cursor.userId"
      class="remoteCursor"
      :style="cursor.style"
    >
      <span
        class="cursorDot"
        :style="{ background: cursor.color }"
      />
      <span
        class="cursorLabel"
        :style="{
          background: `color-mix(in srgb, ${cursor.color} 22%, var(--c-surface))`,
          borderColor: cursor.color,
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
  transition: transform 60ms linear;
}

.laserSpot,
.laserTrailSegment {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
  transform-origin: 0 50%;
}

.laserSpot {
  width: 16px;
  height: 16px;
  margin: -8px 0 0 -8px;
  background: color-mix(in srgb, var(--laser-color) 70%, white);
  box-shadow:
    0 0 0 2px color-mix(in srgb, var(--laser-color) 30%, transparent),
    0 0 10px 3px var(--laser-color),
    0 0 22px 7px color-mix(in srgb, var(--laser-color) 40%, transparent);
}

.laserTrailSegment {
  height: 8px;
  margin-top: -4px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--laser-color) 10%, transparent),
    var(--laser-color)
  );
  box-shadow:
    0 0 8px 2px color-mix(in srgb, var(--laser-color) 70%, transparent),
    0 0 16px 4px color-mix(in srgb, var(--laser-color) 35%, transparent);
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
