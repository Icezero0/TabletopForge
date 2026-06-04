<script setup lang="ts">
import { useI18n } from "vue-i18n";
import PanelSectionHeader from "@/ui/layout/PanelSectionHeader.vue";

const { t } = useI18n();
</script>

<template>
  <section class="infoPanel">
    <PanelSectionHeader :title="t('table.inspector.infoTitle')" />
    <p class="empty">{{ t("table.inspector.infoEmpty") }}</p>
  </section>
</template>

<style scoped>
.infoPanel {
  display: grid;
  gap: 10px;
  min-height: 0;
}

.empty {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
  line-height: 1.5;
}
</style>
