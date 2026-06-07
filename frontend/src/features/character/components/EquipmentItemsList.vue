<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon, TrashIcon, PencilIcon, CheckIcon, XMarkIcon } from "@heroicons/vue/24/outline";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseListItem from "@/ui/base/BaseListItem.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

type Item = { name: string; quantity: number; notes: string };
type ItemDraft = { data: Item; isNew: boolean };

const props = defineProps<{ modelValue: Item[]; readonly?: boolean }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Item[]): void }>();
const { t } = useI18n();

function shiftSet(s: Set<number>, idx: number): Set<number> {
  const r = new Set<number>();
  for (const i of s) { if (i < idx) r.add(i); else if (i > idx) r.add(i - 1); }
  return r;
}
function shiftMap<T>(m: Map<number, T>, idx: number): Map<number, T> {
  const r = new Map<number, T>();
  for (const [i, v] of m) { if (i < idx) r.set(i, v); else if (i > idx) r.set(i - 1, v); }
  return r;
}

const localItems = ref<Item[]>([...props.modelValue]);
const editingItems = ref(new Set<number>());
const itemDrafts = ref(new Map<number, ItemDraft>());

watch(
  () => props.modelValue,
  (val) => {
    const from = (val as Item[]) ?? [];
    if (JSON.stringify(from) !== JSON.stringify(localItems.value)) {
      localItems.value = [...from];
      editingItems.value = new Set();
      itemDrafts.value = new Map();
    }
  },
  { deep: true },
);

function addItem() {
  const idx = localItems.value.length;
  localItems.value = [...localItems.value, { name: "", quantity: 1, notes: "" }];
  itemDrafts.value = new Map([...itemDrafts.value, [idx, { data: { name: "", quantity: 1, notes: "" }, isNew: true }]]);
  editingItems.value = new Set([...editingItems.value, idx]);
}
function removeItem(i: number) {
  const wasNew = itemDrafts.value.get(i)?.isNew ?? false;
  localItems.value = localItems.value.filter((_, idx) => idx !== i);
  editingItems.value = shiftSet(editingItems.value, i);
  itemDrafts.value = shiftMap(itemDrafts.value, i);
  if (!wasNew) emit("update:modelValue", localItems.value);
}
function updateItem(i: number, field: keyof Item, value: unknown) {
  localItems.value = localItems.value.map((item, idx) => idx === i ? { ...item, [field]: value } : item);
  if (!itemDrafts.value.get(i)?.isNew) emit("update:modelValue", localItems.value);
}
function changeQty(i: number, delta: number) {
  updateItem(i, "quantity", Math.max(0, (localItems.value[i]?.quantity ?? 1) + delta));
}
function startEditItem(i: number) {
  const current = localItems.value[i];
  if (!current) return;
  itemDrafts.value = new Map([...itemDrafts.value, [i, { data: { ...current }, isNew: false }]]);
  editingItems.value = new Set([...editingItems.value, i]);
}
function confirmItem(i: number) {
  if (!localItems.value[i]?.name.trim()) return;
  emit("update:modelValue", localItems.value);
  editingItems.value = new Set([...editingItems.value].filter(idx => idx !== i));
  const d = new Map(itemDrafts.value); d.delete(i); itemDrafts.value = d;
}
function cancelItem(i: number) {
  const draft = itemDrafts.value.get(i);
  if (!draft) return;
  if (draft.isNew) {
    localItems.value = localItems.value.filter((_, idx) => idx !== i);
    editingItems.value = shiftSet(editingItems.value, i);
    itemDrafts.value = shiftMap(itemDrafts.value, i);
  } else {
    localItems.value = localItems.value.map((item, idx) => idx === i ? { ...draft.data } : item);
    emit("update:modelValue", localItems.value);
    editingItems.value = new Set([...editingItems.value].filter(idx => idx !== i));
    const d = new Map(itemDrafts.value); d.delete(i); itemDrafts.value = d;
  }
}
function syncReplicatedValue(e: Event) {
  const textarea = e.target as HTMLTextAreaElement;
  textarea.parentElement?.setAttribute("data-replicated-value", textarea.value);
}
</script>

<template>
  <div class="items-list">
    <div v-if="!readonly" class="list-toolbar">
      <BaseButton variant="default" @click="addItem">
        <span class="btn-icon-text">
          <AppIcon :icon="PlusIcon" :size="14" />{{ t("character.equipment.addItem") }}
        </span>
      </BaseButton>
    </div>
    <div v-if="!localItems.length" class="empty-hint">—</div>
    <BaseListItem v-for="(item, i) in localItems" :key="i" dense>
      <div class="item-row">
        <template v-if="!editingItems.has(i)">
          <div class="item-display-content">
            <div class="item-display-main">
              <span class="item-display-name">{{ item.name || "—" }}</span>
              <span class="item-qty-badge">×{{ item.quantity }}</span>
            </div>
            <span v-if="item.notes" class="display-notes">{{ item.notes }}</span>
          </div>
          <button v-if="!readonly" class="action-btn" @click="startEditItem(i)"><AppIcon :icon="PencilIcon" :size="14" /></button>
          <button v-if="!readonly" class="del-btn" @click="removeItem(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
        </template>
        <template v-else>
          <div class="item-edit">
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
            </div>
            <div class="notes-grow-wrap" :data-replicated-value="item.notes">
              <textarea
                :placeholder="t('character.equipment.itemNotes')"
                :value="item.notes"
                rows="1"
                @input="(e) => { syncReplicatedValue(e); updateItem(i, 'notes', (e.target as HTMLTextAreaElement).value); }"
              />
            </div>
          </div>
          <div class="item-actions">
            <button class="action-btn confirm-btn" :disabled="!item.name.trim()" @click="confirmItem(i)">
              <AppIcon :icon="CheckIcon" :size="14" />
            </button>
            <button class="action-btn cancel-btn" @click="cancelItem(i)">
              <AppIcon :icon="XMarkIcon" :size="14" />
            </button>
          </div>
        </template>
      </div>
    </BaseListItem>
  </div>
</template>

<style scoped>
.items-list { display: grid; gap: 6px; }
.list-toolbar { display: flex; justify-content: flex-end; }
.empty-hint { font-size: 13px; color: var(--c-text-muted); }
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }

.item-row { display: flex; align-items: flex-start; gap: 8px; }

.item-display-content { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.item-display-main { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.item-display-name { font-size: 13px; font-weight: 500; color: var(--c-text); word-break: break-word; }
.item-qty-badge {
  font-size: 12px; color: var(--c-text-muted); flex-shrink: 0;
  padding: 1px 6px; border-radius: 10px;
  background: var(--c-surface-raised); border: 1px solid var(--c-border);
}
.display-notes { font-size: 13px; color: var(--c-text-muted); white-space: pre-wrap; word-break: break-word; }

.item-edit { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.item-main { display: flex; gap: 8px; align-items: center; }
.item-actions { display: flex; flex-direction: row; gap: 2px; flex-shrink: 0; align-items: flex-start; }

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
  width: 40px; text-align: center;
  border-top: 1px solid var(--c-border); border-bottom: 1px solid var(--c-border);
  border-left: none; border-right: none;
  background: var(--c-surface); color: var(--c-text); padding: 3px 2px;
  font-size: 13px; font-family: inherit; outline: none; height: 30px; box-sizing: border-box;
}
.qty-input:focus { background: var(--c-surface-raised); }
.no-spin::-webkit-outer-spin-button,
.no-spin::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.no-spin { -moz-appearance: textfield; }

.notes-grow-wrap { display: grid; }
.notes-grow-wrap::after {
  content: attr(data-replicated-value) " ";
  white-space: pre-wrap; word-break: break-word;
  visibility: hidden; grid-area: 1 / 1 / 2 / 2;
  font-size: 13px; font-family: inherit; padding: 5px 8px;
  border: 1px solid transparent; min-height: 32px; box-sizing: border-box;
}
.notes-grow-wrap > textarea {
  grid-area: 1 / 1 / 2 / 2; resize: none; overflow: hidden;
  width: 100%; box-sizing: border-box;
  border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text-muted);
  padding: 5px 8px; font-size: 13px; font-family: inherit; outline: none;
}
.notes-grow-wrap > textarea:focus { border-color: var(--c-accent); }
.notes-grow-wrap > textarea::placeholder { color: var(--c-text-muted); opacity: 0.6; }

.action-btn {
  background: none; border: none; cursor: pointer; color: var(--c-text-muted);
  padding: 4px; border-radius: var(--r-1); display: flex; align-items: center;
  transition: color 0.12s; flex-shrink: 0;
}
.action-btn:hover:not(:disabled) { color: var(--c-text); }
.confirm-btn:not(:disabled) { color: var(--c-accent); }
.confirm-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.del-btn {
  background: none; border: none; cursor: pointer; color: var(--c-text-muted);
  padding: 4px; border-radius: var(--r-1); display: flex; align-items: center;
  transition: color 0.12s; flex-shrink: 0;
}
.del-btn:hover { color: var(--c-danger, #e53e3e); }
</style>
