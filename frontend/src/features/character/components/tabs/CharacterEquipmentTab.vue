<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon, TrashIcon } from "@heroicons/vue/24/outline";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

type Item = { name: string; quantity: number; notes: string };

const props = defineProps<{ modelValue: Record<string, unknown> }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

const items = computed(() => (props.modelValue.items as Item[]) ?? []);

function addItem() {
  update("items", [...items.value, { name: "", quantity: 1, notes: "" }]);
}
function removeItem(i: number) {
  update("items", items.value.filter((_, idx) => idx !== i));
}
function updateItem(i: number, field: keyof Item, value: unknown) {
  update("items", items.value.map((item, idx) => idx === i ? { ...item, [field]: value } : item));
}
function changeQty(i: number, delta: number) {
  updateItem(i, "quantity", Math.max(0, (items.value[i].quantity ?? 1) + delta));
}
</script>

<template>
  <div class="tab-content">
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.equipment.items") }}</span>
        <BaseButton variant="default" @click="addItem">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.equipment.addItem") }}</span>
        </BaseButton>
      </div>
      <div v-if="!items.length" class="empty-hint">—</div>
      <div v-for="(item, i) in items" :key="i" class="item-row">
        <div class="item-main">
          <input
            class="item-name"
            type="text"
            :placeholder="t('character.equipment.itemName')"
            :value="item.name"
            @input="updateItem(i, 'name', ($event.target as HTMLInputElement).value)"
          />
          <div class="qty-stepper">
            <button class="qty-btn" @click="changeQty(i, -1)">−</button>
            <input
              type="number"
              class="qty-input no-spin"
              :value="item.quantity"
              @change="updateItem(i, 'quantity', Math.max(0, parseInt(($event.target as HTMLInputElement).value) || 0))"
            />
            <button class="qty-btn" @click="changeQty(i, 1)">+</button>
          </div>
          <button class="del-btn" @click="removeItem(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
        </div>
        <input
          class="item-notes"
          type="text"
          :placeholder="t('character.equipment.itemNotes')"
          :value="item.notes"
          @input="updateItem(i, 'notes', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 16px; }
.section { display: grid; gap: 10px; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.empty-hint { font-size: 13px; color: var(--c-text-muted); }

.item-row { display: grid; gap: 6px; border: 1px solid var(--c-border); border-radius: var(--r-1); padding: 10px; }
.item-main { display: flex; gap: 8px; align-items: center; }

.item-name {
  flex: 1; min-width: 120px; border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text); padding: 5px 8px; font-size: 13px;
  font-family: inherit; outline: none;
}
.item-name:focus { border-color: var(--c-accent); }
.item-name::placeholder { color: var(--c-text-muted); }

.qty-stepper { display: flex; align-items: center; flex-shrink: 0; }
.qty-btn {
  background: var(--c-surface-raised); border: 1px solid var(--c-border);
  border-radius: var(--r-1); color: var(--c-text-muted); cursor: pointer;
  font-size: 13px; font-weight: 600; padding: 3px 7px; height: 30px;
  transition: background 0.12s, color 0.12s;
}
.qty-btn:hover { background: var(--c-hover); color: var(--c-text); }
.qty-input {
  width: 40px; text-align: center; border-top: 1px solid var(--c-border);
  border-bottom: 1px solid var(--c-border); border-left: none; border-right: none;
  background: var(--c-surface); color: var(--c-text); padding: 3px 2px;
  font-size: 13px; font-family: inherit; outline: none; height: 30px; box-sizing: border-box;
}
.qty-input:focus { background: var(--c-surface-raised); }
.no-spin::-webkit-outer-spin-button,
.no-spin::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.no-spin { -moz-appearance: textfield; }

.item-notes {
  width: 100%; box-sizing: border-box; border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text-muted); padding: 5px 8px; font-size: 12px;
  font-family: inherit; outline: none;
}
.item-notes:focus { border-color: var(--c-accent); }
.item-notes::placeholder { color: var(--c-text-muted); opacity: 0.6; }

.del-btn {
  background: none; border: none; cursor: pointer; color: var(--c-text-muted);
  padding: 4px; border-radius: var(--r-1); display: flex; align-items: center;
  margin-left: auto; transition: color 0.12s;
}
.del-btn:hover { color: var(--c-danger, #e53e3e); }
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }
</style>
