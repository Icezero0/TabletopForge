<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();
</script>

<template>
  <div class="inGameCharacterList">
    <p class="hint">{{ t("table.characterList.hint") }}</p>
    <p class="empty">{{ t("table.characterList.empty") }}</p>
  </div>
</template>

<style scoped>
.inGameCharacterList {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--c-text-muted);
}

.empty {
  margin: 0;
  padding: 12px;
  border-radius: 10px;
  border: 1px dashed color-mix(in srgb, var(--c-border) 70%, transparent);
  font-size: 13px;
  line-height: 1.5;
  color: var(--c-text-muted);
  text-align: center;
}
</style>
