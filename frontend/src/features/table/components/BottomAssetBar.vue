<script setup lang="ts">
import { useI18n } from "vue-i18n";
import BaseButton from "@/ui/base/BaseButton.vue";

defineProps<{
  canAddMap?: boolean;
  canAddCharacter?: boolean;
}>();

const emit = defineEmits<{
  addMap: [];
  addCharacter: [];
}>();

const { t } = useI18n();
</script>

<template>
  <div class="bottomAssetBar">
    <BaseButton
      v-if="canAddMap"
      variant="primary"
      @click="emit('addMap')"
    >
      {{ t("table.assets.addMap") }}
    </BaseButton>
    <BaseButton
      v-if="canAddCharacter"
      variant="default"
      @click="emit('addCharacter')"
    >
      {{ t("table.assets.addCharacter") }}
    </BaseButton>
  </div>
</template>

<style scoped>
.bottomAssetBar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 4px 8px;
}
</style>
