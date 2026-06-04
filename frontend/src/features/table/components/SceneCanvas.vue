<script setup lang="ts">
defineProps<{
  transform: string;
  interactive?: boolean;
}>();
</script>

<template>
  <div
    class="sceneCanvas"
    :class="{ interactive }"
    :style="{ transform }"
  >
    <slot />
  </div>
</template>

<style scoped>
.sceneCanvas {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  will-change: transform;
  overflow: visible;
}

.sceneCanvas.interactive {
  cursor: grab;
}

.sceneCanvas.interactive:active {
  cursor: grabbing;
}
</style>
