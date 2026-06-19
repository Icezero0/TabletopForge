<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import {
  CheckIcon,
  PencilSquareIcon,
  PlusIcon,
  TrashIcon,
  XMarkIcon,
} from "@heroicons/vue/24/outline";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import BaseSortableList from "@/ui/base/BaseSortableList.vue";
import {
  buildCommonResourcesFromCharacter,
  normalizeCharacterResource,
  type CharacterResource,
} from "@/features/character/utils/resources";

const props = defineProps<{
  modelValue: CharacterResource[];
  identityBlock: Record<string, unknown>;
  attributesBlock: Record<string, unknown>;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: CharacterResource[]): void;
}>();

const { t } = useI18n();

const resources = computed(() =>
  (props.modelValue ?? [])
    .map((item) => normalizeCharacterResource(item))
    .filter((item): item is CharacterResource => item != null),
);

const editingIndex = ref<number | null>(null);
const editingDraft = ref<CharacterResource | null>(null);

const rows = computed(() => {
  if (editingIndex.value === resources.value.length && editingDraft.value) {
    return [...resources.value, editingDraft.value];
  }
  return resources.value;
});

function push(next: CharacterResource[]) {
  emit("update:modelValue", next);
}

function parseResourceNumber(raw: string) {
  const value = parseInt(raw);
  return Number.isNaN(value) ? 0 : Math.max(0, value);
}

function normalize(resource: CharacterResource): CharacterResource {
  return {
    name: resource.name.trim(),
    max: Math.max(0, Number(resource.max) || 0),
    recovery: resource.recovery.trim(),
    notes: resource.notes.trim(),
  };
}

function addResource() {
  editingIndex.value = resources.value.length;
  editingDraft.value = { name: "", max: 0, recovery: "", notes: "" };
}

function beginEdit(index: number) {
  editingIndex.value = index;
  editingDraft.value = { ...resources.value[index]! };
}

function updateDraft(patch: Partial<CharacterResource>) {
  if (!editingDraft.value) return;
  editingDraft.value = { ...editingDraft.value, ...patch };
}

function commitEdit() {
  const index = editingIndex.value;
  const draft = editingDraft.value;
  if (index == null || !draft) return;
  const normalized = normalize(draft);
  if (index >= resources.value.length) {
    push([...resources.value, normalized]);
  } else {
    push(resources.value.map((item, i) => (i === index ? normalized : item)));
  }
  cancelEdit();
}

function cancelEdit() {
  editingIndex.value = null;
  editingDraft.value = null;
}

function removeResource(index: number) {
  push(resources.value.filter((_, i) => i !== index));
  if (editingIndex.value === index) cancelEdit();
}

function autoCalcCommonResources() {
  cancelEdit();
  push(buildCommonResourcesFromCharacter(props.identityBlock, props.attributesBlock, t));
}

function moveResource(from: number, to: number) {
  if (from === to || from < 0 || to < 0) return;
  const next = [...resources.value];
  const [item] = next.splice(from, 1);
  if (!item) return;
  next.splice(to, 0, item);
  push(next);
}
</script>

<template>
  <div class="tab-content">
    <div class="section-header">
      <BaseButton variant="default" @click="autoCalcCommonResources">
        {{ t("character.resources.autoCalcCommon") }}
      </BaseButton>
      <BaseButton variant="default" @click="addResource">
        <span class="btn-icon-text">
          <AppIcon :icon="PlusIcon" :size="14" />
          {{ t("character.resources.addResource") }}
        </span>
      </BaseButton>
    </div>

    <div v-if="!rows.length" class="empty-resource">{{ t("character.resources.noResources") }}</div>
    <BaseSortableList
      v-else
      :count="rows.length"
      :disabled="editingIndex != null"
      :placeholder-min-height="56"
      placeholder-radius="var(--r-1)"
      @reorder="moveResource($event.from, $event.to)"
    >
      <template #default="{ index }">
      <div
        class="resource-row"
        :class="{
          editing: editingIndex === index && editingDraft,
          draggable: editingIndex == null,
        }"
      >
        <template v-if="editingIndex === index && editingDraft">
          <label class="resource-name">
            <span class="resource-label">{{ t("character.resources.resourceName") }}</span>
            <input
              class="resource-input"
              type="text"
              :value="editingDraft.name"
              :placeholder="t('character.resources.resourceNamePlaceholder')"
              @input="updateDraft({ name: ($event.target as HTMLInputElement).value })"
            />
          </label>
          <label class="resource-notes">
            <span class="resource-label">{{ t("character.resources.resourceNotes") }}</span>
            <input
              class="resource-input"
              type="text"
              :value="editingDraft.notes"
              :placeholder="t('character.resources.resourceNotesPlaceholder')"
              @input="updateDraft({ notes: ($event.target as HTMLInputElement).value })"
            />
          </label>
          <label class="resource-number">
            <span class="resource-label">{{ t("character.resources.resourceMax") }}</span>
            <input
              class="resource-input no-spin"
              type="number"
              min="0"
              :value="editingDraft.max"
              @change="updateDraft({ max: parseResourceNumber(($event.target as HTMLInputElement).value) })"
            />
          </label>
          <label class="resource-recovery">
            <span class="resource-label">{{ t("character.resources.resourceRecovery") }}</span>
            <input
              class="resource-input"
              type="text"
              :value="editingDraft.recovery"
              :placeholder="t('character.resources.resourceRecoveryPlaceholder')"
              @input="updateDraft({ recovery: ($event.target as HTMLInputElement).value })"
            />
          </label>
          <div class="resource-actions">
            <button class="resource-icon-button confirm" type="button" :title="t('common.save')" @click="commitEdit">
              <AppIcon :icon="CheckIcon" :size="16" />
            </button>
            <button class="resource-icon-button" type="button" :title="t('common.cancel')" @click="cancelEdit">
              <AppIcon :icon="XMarkIcon" :size="16" />
            </button>
          </div>
        </template>
        <template v-else>
          <div class="resource-display">
            <span class="resource-display-name">{{ rows[index]?.name || t("character.resources.unnamedResource") }}</span>
            <span v-if="rows[index]?.notes" class="resource-display-notes">{{ rows[index]?.notes }}</span>
          </div>
          <div class="resource-display-limit">
            <span class="resource-limit-label">{{ t("character.resources.resourceMax") }}</span>
            <span class="resource-limit-value">{{ rows[index]?.max }}</span>
          </div>
          <div class="resource-display-recovery">
            <span v-if="rows[index]?.recovery">{{ rows[index]?.recovery }}</span>
            <span v-else class="resource-empty">—</span>
          </div>
          <div class="resource-actions">
            <button class="resource-icon-button" type="button" :title="t('character.resources.editResource')" @click="beginEdit(index)">
              <AppIcon :icon="PencilSquareIcon" :size="16" />
            </button>
            <button class="resource-icon-button danger" type="button" :title="t('character.resources.removeResource')" @click="removeResource(index)">
              <AppIcon :icon="TrashIcon" :size="16" />
            </button>
          </div>
        </template>
      </div>
      </template>
    </BaseSortableList>
  </div>
</template>

<style scoped>
.tab-content {
  display: grid;
  gap: 14px;
}

.section-header {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-icon-text {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.empty-resource {
  color: var(--c-text-muted);
  font-size: 13px;
}

.resource-row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) max-content max-content auto;
  gap: 14px;
  align-items: center;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface-raised);
  transition:
    background 140ms ease,
    border-color 140ms ease,
    box-shadow 140ms ease,
    opacity 140ms ease,
    transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.resource-row.editing {
  grid-template-columns: minmax(150px, 0.9fr) minmax(180px, 1.1fr) 86px minmax(120px, 0.7fr) auto;
  gap: 10px;
}

.resource-row.draggable {
  cursor: grab;
}

.resource-row.draggable:active {
  cursor: grabbing;
}

.resource-row:not(.editing):hover {
  background: color-mix(in srgb, var(--c-hover) 55%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-border) 65%, var(--c-text));
  box-shadow: 0 10px 22px rgb(0 0 0 / 0.08);
}

.resource-display {
  min-width: 0;
  display: grid;
  gap: 2px;
}


.resource-display-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text);
  font-size: 14px;
  font-weight: 600;
}

.resource-display-notes {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text-muted);
  font-size: 12px;
}

.resource-display-limit {
  justify-self: start;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
}

.resource-limit-label {
  color: var(--c-text-muted);
  font-size: 10px;
  font-weight: 700;
}

.resource-limit-value {
  color: var(--c-text);
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.resource-display-recovery {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 7px;
  border: 1px solid var(--c-border);
  border-radius: 999px;
  background: var(--c-surface);
  color: var(--c-text-muted);
  font-size: 11px;
  font-weight: 600;
}

.resource-empty {
  color: var(--c-text-muted);
}

.resource-name,
.resource-number,
.resource-recovery,
.resource-notes {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.resource-label {
  color: var(--c-text-muted);
  font-size: 11px;
  font-weight: 600;
}

.resource-input {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text);
  padding: 6px 8px;
  font: inherit;
  font-size: 13px;
  outline: none;
}

.resource-input:focus {
  border-color: var(--c-accent);
}

.resource-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.resource-icon-button {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text-muted);
  cursor: pointer;
}

.resource-icon-button:hover {
  color: var(--c-text);
  border-color: var(--c-accent);
}

.resource-icon-button.confirm:hover {
  color: var(--c-success, #3aa675);
}

.resource-icon-button.danger:hover {
  color: var(--c-danger);
}

.no-spin {
  -moz-appearance: textfield;
}

.no-spin::-webkit-inner-spin-button,
.no-spin::-webkit-outer-spin-button {
  -webkit-appearance: none;
}

@media (max-width: 720px) {
  .section-header,
  .resource-row,
  .resource-row.editing {
    grid-template-columns: 1fr;
  }
}
</style>
