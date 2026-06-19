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

type ResourceSection = CharacterResource["section"];
type ResourceRow = {
  resource: CharacterResource;
  globalIndex: number | null;
};

const props = defineProps<{
  modelValue: CharacterResource[];
  identityBlock: Record<string, unknown>;
  attributesBlock: Record<string, unknown>;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: CharacterResource[]): void;
}>();

const { t } = useI18n();
const sections: ResourceSection[] = ["common", "special"];

const resources = computed(() =>
  (props.modelValue ?? [])
    .map((item) => normalizeCharacterResource(item))
    .filter((item): item is CharacterResource => item != null),
);

const editingTarget = ref<{ section: ResourceSection; index: number | null } | null>(null);
const editingDraft = ref<CharacterResource | null>(null);

const commonResources = computed(() => resources.value.filter((resource) => resource.section === "common"));
const specialResources = computed(() => resources.value.filter((resource) => resource.section === "special"));

function rowsFor(section: ResourceSection): ResourceRow[] {
  const rows: ResourceRow[] = resources.value
    .map((resource, globalIndex) => ({ resource, globalIndex }))
    .filter((row) => row.resource.section === section);
  if (editingTarget.value?.section === section && editingTarget.value.index == null && editingDraft.value) {
    rows.push({ resource: editingDraft.value, globalIndex: null });
  }
  return rows;
}

function sectionTitle(section: ResourceSection) {
  return t(section === "common" ? "character.resources.commonResources" : "character.resources.specialResources");
}

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
    section: resource.section === "special" ? "special" : "common",
  };
}

function addResource() {
  editingTarget.value = { section: "special", index: null };
  editingDraft.value = { name: "", max: 0, recovery: "", notes: "", section: "special" };
}

function beginEdit(section: ResourceSection, index: number) {
  const row = rowsFor(section)[index];
  if (!row) return;
  editingTarget.value = { section, index };
  editingDraft.value = { ...row.resource };
}

function updateDraft(patch: Partial<CharacterResource>) {
  if (!editingDraft.value) return;
  editingDraft.value = { ...editingDraft.value, ...patch };
}

function commitEdit() {
  const target = editingTarget.value;
  const draft = editingDraft.value;
  if (!target || !draft) return;
  const normalized = normalize({ ...draft, section: target.section });
  const row = target.index == null ? null : rowsFor(target.section)[target.index];
  if (!row || row.globalIndex == null) {
    push([...resources.value, normalized]);
  } else {
    push(resources.value.map((item, i) => (i === row.globalIndex ? normalized : item)));
  }
  cancelEdit();
}

function cancelEdit() {
  editingTarget.value = null;
  editingDraft.value = null;
}

function removeResource(globalIndex: number | null) {
  if (globalIndex == null) {
    cancelEdit();
    return;
  }
  push(resources.value.filter((_, i) => i !== globalIndex));
  cancelEdit();
}

function autoCalcCommonResources() {
  cancelEdit();
  push([
    ...buildCommonResourcesFromCharacter(props.identityBlock, props.attributesBlock, t),
    ...specialResources.value,
  ]);
}

function moveResource(section: ResourceSection, from: number, to: number) {
  if (from === to || from < 0 || to < 0) return;
  const targetResources = section === "common" ? [...commonResources.value] : [...specialResources.value];
  const next = [...targetResources];
  const [item] = next.splice(from, 1);
  if (!item) return;
  next.splice(to, 0, item);
  push(section === "common" ? [...next, ...specialResources.value] : [...commonResources.value, ...next]);
}

function isEditing(section: ResourceSection, index: number) {
  if (editingTarget.value?.section !== section || !editingDraft.value) return false;
  const row = rowsFor(section)[index];
  if (!row) return false;
  return editingTarget.value.index == null
    ? row.globalIndex == null
    : editingTarget.value.index === index;
}
</script>

<template>
  <div class="tab-content">
    <div class="section-header top-actions">
      <BaseButton variant="default" @click="autoCalcCommonResources">
        {{ t("character.resources.autoCalcCommon") }}
      </BaseButton>
    </div>

    <section v-for="section in sections" :key="section" class="resource-section">
      <div class="resource-section-header">
        <h3>{{ sectionTitle(section) }}</h3>
        <BaseButton v-if="section === 'special'" variant="default" @click="addResource">
          <span class="btn-icon-text">
            <AppIcon :icon="PlusIcon" :size="14" />
            {{ t("character.resources.addResource") }}
          </span>
        </BaseButton>
      </div>

      <div v-if="!rowsFor(section).length" class="empty-resource section-empty">—</div>
      <BaseSortableList
        v-else
        :count="rowsFor(section).length"
        :disabled="editingTarget != null"
        :placeholder-min-height="56"
        placeholder-radius="var(--r-1)"
        @reorder="moveResource(section, $event.from, $event.to)"
      >
        <template #default="{ index }">
        <div
          class="resource-row"
          :class="{
            editing: isEditing(section, index),
            draggable: editingTarget == null,
          }"
        >
          <template v-if="isEditing(section, index) && editingDraft">
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
              <span class="resource-display-name">{{ rowsFor(section)[index]?.resource.name || t("character.resources.unnamedResource") }}</span>
              <span v-if="rowsFor(section)[index]?.resource.notes" class="resource-display-notes">{{ rowsFor(section)[index]?.resource.notes }}</span>
            </div>
            <div class="resource-display-limit">
              <span class="resource-limit-label">{{ t("character.resources.resourceMax") }}</span>
              <span class="resource-limit-value">{{ rowsFor(section)[index]?.resource.max }}</span>
            </div>
            <div class="resource-display-recovery">
              <span v-if="rowsFor(section)[index]?.resource.recovery">{{ rowsFor(section)[index]?.resource.recovery }}</span>
              <span v-else class="resource-empty">—</span>
            </div>
            <div class="resource-actions">
              <button class="resource-icon-button" type="button" :title="t('character.resources.editResource')" @click="beginEdit(section, index)">
                <AppIcon :icon="PencilSquareIcon" :size="16" />
              </button>
              <button class="resource-icon-button danger" type="button" :title="t('character.resources.removeResource')" @click="removeResource(rowsFor(section)[index]?.globalIndex ?? null)">
                <AppIcon :icon="TrashIcon" :size="16" />
              </button>
            </div>
          </template>
        </div>
        </template>
      </BaseSortableList>
    </section>
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

.top-actions {
  margin-bottom: -2px;
}

.resource-section {
  display: grid;
  gap: 10px;
}

.resource-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.resource-section-header h3 {
  margin: 0;
  color: var(--c-text);
  font-size: 14px;
  font-weight: 700;
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

.section-empty {
  padding: 4px 0;
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
