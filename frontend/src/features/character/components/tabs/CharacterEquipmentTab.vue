<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import EquipmentItemsList from "@/features/character/components/EquipmentItemsList.vue";

type Item = { name: string; quantity: number; notes: string };

const props = defineProps<{ modelValue: Record<string, unknown> }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

const items = computed(() => (props.modelValue.items as Item[]) ?? []);
function updateItems(v: Item[]) {
  emit("update:modelValue", { ...props.modelValue, items: v });
}
</script>

<template>
  <div class="tab-content">
    <div class="section">
      <div class="section-title">{{ t("character.equipment.items") }}</div>
      <EquipmentItemsList :model-value="items" @update:model-value="updateItems" />
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 16px; }
.section { display: grid; gap: 6px; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
</style>
