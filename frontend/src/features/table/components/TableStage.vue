<script setup lang="ts">
// Full-bleed map stage with overlay slot for floating panels.
</script>

<template>
  <div class="tableStage">
    <div class="mapLayer">
      <slot name="map" />
    </div>
    <div class="overlays">
      <slot name="overlays" />
    </div>
  </div>
</template>

<style scoped>
.tableStage {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.mapLayer {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.overlays {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.rightStack {
  position: absolute;
  top: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 10px;
  pointer-events: none;
  z-index: 2;
}

.rightStack > * {
  pointer-events: auto;
  flex-shrink: 0;
}

.rightStack > .memoPanel {
  margin-top: auto;
}
</style>
