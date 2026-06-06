<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon, TrashIcon, PencilIcon, CheckIcon, XMarkIcon } from "@heroicons/vue/24/outline";
import { DND5E_CLASSES } from "@/features/character/constants";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseListItem from "@/ui/base/BaseListItem.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{ modelValue: Record<string, unknown> }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

function syncReplicatedValue(e: Event) {
  const textarea = e.target as HTMLTextAreaElement;
  textarea.parentElement?.setAttribute("data-replicated-value", textarea.value);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function shiftEditSet(s: Set<number>, removedIdx: number): Set<number> {
  const result = new Set<number>();
  for (const idx of s) {
    if (idx < removedIdx) result.add(idx);
    else if (idx > removedIdx) result.add(idx - 1);
  }
  return result;
}
function shiftDraftMap<T>(m: Map<number, T>, removedIdx: number): Map<number, T> {
  const result = new Map<number, T>();
  for (const [idx, val] of m) {
    if (idx < removedIdx) result.set(idx, val);
    else if (idx > removedIdx) result.set(idx - 1, val);
  }
  return result;
}
function isNew(drafts: Map<number, { isNew: boolean }>, i: number) {
  return drafts.get(i)?.isNew ?? false;
}

// ── Edit state ────────────────────────────────────────────────────────────────
const editingTraits = ref(new Set<number>());
const editingFeatures = ref(new Set<number>());
const editingPairs = ref(new Set<number>());

// ── Racial traits ─────────────────────────────────────────────────────────────
type RacialTrait = { name: string; notes: string };
type TraitDraft = { data: RacialTrait; isNew: boolean };

const localTraits = ref<RacialTrait[]>([...(props.modelValue.racial_traits as RacialTrait[] ?? [])]);
const traitDrafts = ref(new Map<number, TraitDraft>());

function updateTrait(i: number, field: string, v: string) {
  localTraits.value = localTraits.value.map((tr, idx) => idx === i ? { ...tr, [field]: v } : tr);
  if (!isNew(traitDrafts.value, i)) update("racial_traits", localTraits.value);
}
function addTrait() {
  const idx = localTraits.value.length;
  localTraits.value = [...localTraits.value, { name: "", notes: "" }];
  traitDrafts.value = new Map([...traitDrafts.value, [idx, { data: { name: "", notes: "" }, isNew: true }]]);
  editingTraits.value = new Set([...editingTraits.value, idx]);
}
function removeTrait(i: number) {
  const wasNew = isNew(traitDrafts.value, i);
  localTraits.value = localTraits.value.filter((_, idx) => idx !== i);
  editingTraits.value = shiftEditSet(editingTraits.value, i);
  traitDrafts.value = shiftDraftMap(traitDrafts.value, i);
  if (!wasNew) update("racial_traits", localTraits.value);
}
function startEditTrait(i: number) {
  const current = localTraits.value[i];
  if (!current) return;
  traitDrafts.value = new Map([...traitDrafts.value, [i, { data: { ...current }, isNew: false }]]);
  editingTraits.value = new Set([...editingTraits.value, i]);
}
function confirmTrait(i: number) {
  if (!localTraits.value[i]?.name.trim()) return;
  update("racial_traits", localTraits.value);
  editingTraits.value = new Set([...editingTraits.value].filter(idx => idx !== i));
  const d = new Map(traitDrafts.value); d.delete(i); traitDrafts.value = d;
}
function cancelTrait(i: number) {
  const draft = traitDrafts.value.get(i);
  if (!draft) return;
  if (draft.isNew) {
    localTraits.value = localTraits.value.filter((_, idx) => idx !== i);
    editingTraits.value = shiftEditSet(editingTraits.value, i);
    traitDrafts.value = shiftDraftMap(traitDrafts.value, i);
  } else {
    localTraits.value = localTraits.value.map((tr, idx) => idx === i ? { ...draft.data } : tr);
    update("racial_traits", localTraits.value);
    editingTraits.value = new Set([...editingTraits.value].filter(idx => idx !== i));
    const d = new Map(traitDrafts.value); d.delete(i); traitDrafts.value = d;
  }
}

// ── Class source options ──────────────────────────────────────────────────────
const classSourceOptions = computed(() =>
  DND5E_CLASSES.map(c => ({ value: c, label: t(`character.classes.${c}`) })),
);

// ── Class features ────────────────────────────────────────────────────────────
type ClassFeature = { name: string; source: string; notes: string };
type FeatureDraft = { data: ClassFeature; isNew: boolean };

const localFeatures = ref<ClassFeature[]>([...(props.modelValue.class_features as ClassFeature[] ?? [])]);
const featureDrafts = ref(new Map<number, FeatureDraft>());

function updateFeature(i: number, field: string, v: string) {
  localFeatures.value = localFeatures.value.map((f, idx) => idx === i ? { ...f, [field]: v } : f);
  if (!isNew(featureDrafts.value, i)) update("class_features", localFeatures.value);
}
function addFeature() {
  const idx = localFeatures.value.length;
  localFeatures.value = [...localFeatures.value, { name: "", source: "", notes: "" }];
  featureDrafts.value = new Map([...featureDrafts.value, [idx, { data: { name: "", source: "", notes: "" }, isNew: true }]]);
  editingFeatures.value = new Set([...editingFeatures.value, idx]);
}
function removeFeature(i: number) {
  const wasNew = isNew(featureDrafts.value, i);
  localFeatures.value = localFeatures.value.filter((_, idx) => idx !== i);
  editingFeatures.value = shiftEditSet(editingFeatures.value, i);
  featureDrafts.value = shiftDraftMap(featureDrafts.value, i);
  if (!wasNew) update("class_features", localFeatures.value);
}
function startEditFeature(i: number) {
  const current = localFeatures.value[i];
  if (!current) return;
  featureDrafts.value = new Map([...featureDrafts.value, [i, { data: { ...current }, isNew: false }]]);
  editingFeatures.value = new Set([...editingFeatures.value, i]);
}
function confirmFeature(i: number) {
  const feat = localFeatures.value[i];
  if (!feat?.name.trim() || !feat?.source) return;
  update("class_features", localFeatures.value);
  editingFeatures.value = new Set([...editingFeatures.value].filter(idx => idx !== i));
  const d = new Map(featureDrafts.value); d.delete(i); featureDrafts.value = d;
}
function cancelFeature(i: number) {
  const draft = featureDrafts.value.get(i);
  if (!draft) return;
  if (draft.isNew) {
    localFeatures.value = localFeatures.value.filter((_, idx) => idx !== i);
    editingFeatures.value = shiftEditSet(editingFeatures.value, i);
    featureDrafts.value = shiftDraftMap(featureDrafts.value, i);
  } else {
    localFeatures.value = localFeatures.value.map((f, idx) => idx === i ? { ...draft.data } : f);
    update("class_features", localFeatures.value);
    editingFeatures.value = new Set([...editingFeatures.value].filter(idx => idx !== i));
    const d = new Map(featureDrafts.value); d.delete(i); featureDrafts.value = d;
  }
}

// ── Custom fields ─────────────────────────────────────────────────────────────
type PairData = { key: string; value: string };
type PairDraft = { data: PairData; isNew: boolean };

const localPairs = ref<PairData[]>(
  Object.entries((props.modelValue.custom_fields as Record<string, string>) ?? {}).map(([k, v]) => ({ key: k, value: v })),
);
const pairDrafts = ref(new Map<number, PairDraft>());

watch(
  () => props.modelValue.custom_fields,
  (newVal) => {
    const fromParent = Object.entries((newVal as Record<string, string>) ?? {}).map(([k, v]) => ({ key: k, value: v }));
    const localNonEmpty = localPairs.value.filter((p) => p.key.trim());
    if (JSON.stringify(fromParent) !== JSON.stringify(localNonEmpty)) {
      localPairs.value = fromParent;
    }
  },
  { deep: true },
);
function emitCustomFields(pairs: PairData[]) {
  const obj: Record<string, string> = {};
  for (const { key, value } of pairs) if (key.trim()) obj[key.trim()] = value;
  update("custom_fields", obj);
}
function addCustomField() {
  const idx = localPairs.value.length;
  localPairs.value = [...localPairs.value, { key: "", value: "" }];
  pairDrafts.value = new Map([...pairDrafts.value, [idx, { data: { key: "", value: "" }, isNew: true }]]);
  editingPairs.value = new Set([...editingPairs.value, idx]);
}
function updateCustomField(i: number, field: "key" | "value", v: string) {
  localPairs.value = localPairs.value.map((p, idx) => (idx === i ? { ...p, [field]: v } : p));
  emitCustomFields(localPairs.value);
}
function removeCustomField(i: number) {
  localPairs.value = localPairs.value.filter((_, idx) => idx !== i);
  emitCustomFields(localPairs.value);
  editingPairs.value = shiftEditSet(editingPairs.value, i);
  pairDrafts.value = shiftDraftMap(pairDrafts.value, i);
}
function startEditPair(i: number) {
  const current = localPairs.value[i];
  if (!current) return;
  pairDrafts.value = new Map([...pairDrafts.value, [i, { data: { ...current }, isNew: false }]]);
  editingPairs.value = new Set([...editingPairs.value, i]);
}
function confirmCustomField(i: number) {
  if (!localPairs.value[i]?.key.trim()) return;
  emitCustomFields(localPairs.value);
  editingPairs.value = new Set([...editingPairs.value].filter(idx => idx !== i));
  const d = new Map(pairDrafts.value); d.delete(i); pairDrafts.value = d;
}
function cancelCustomField(i: number) {
  const draft = pairDrafts.value.get(i);
  if (!draft) return;
  if (draft.isNew) {
    localPairs.value = localPairs.value.filter((_, idx) => idx !== i);
    emitCustomFields(localPairs.value);
    editingPairs.value = shiftEditSet(editingPairs.value, i);
    pairDrafts.value = shiftDraftMap(pairDrafts.value, i);
  } else {
    localPairs.value = localPairs.value.map((p, idx) => idx === i ? { ...draft.data } : p);
    emitCustomFields(localPairs.value);
    editingPairs.value = new Set([...editingPairs.value].filter(idx => idx !== i));
    const d = new Map(pairDrafts.value); d.delete(i); pairDrafts.value = d;
  }
}
</script>

<template>
  <div class="tab-content">

    <!-- Racial traits -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.features.racialTraits") }}</span>
        <BaseButton variant="default" @click="addTrait">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.features.addRacialTrait") }}</span>
        </BaseButton>
      </div>
      <div v-if="!localTraits.length" class="empty-hint">—</div>
      <BaseListItem v-for="(trait, i) in localTraits" :key="i" dense>
        <div class="feature-row">
          <template v-if="!editingTraits.has(i)">
            <div class="display-content">
              <span class="display-name">{{ trait.name || "—" }}</span>
              <span v-if="trait.notes" class="display-notes">{{ trait.notes }}</span>
            </div>
            <button class="action-btn" @click="startEditTrait(i)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeTrait(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <BaseInput :model-value="trait.name" :placeholder="t('character.features.traitName')" @update:model-value="updateTrait(i, 'name', $event)" />
              <div class="notes-grow-wrap" :data-replicated-value="trait.notes">
                <textarea
                  :placeholder="t('character.features.traitNotes')"
                  :value="trait.notes"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateTrait(i, 'notes', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!trait.name.trim()" @click="confirmTrait(i)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelTrait(i)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
    </div>

    <!-- Class features -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.features.classFeatures") }}</span>
        <BaseButton variant="default" @click="addFeature">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.features.addClassFeature") }}</span>
        </BaseButton>
      </div>
      <div v-if="!localFeatures.length" class="empty-hint">—</div>
      <BaseListItem v-for="(feat, i) in localFeatures" :key="i" dense>
        <div class="feature-row">
          <template v-if="!editingFeatures.has(i)">
            <div class="display-content">
              <div class="display-primary">
                <span class="display-name">{{ feat.name || "—" }}</span>
                <span v-if="feat.source" class="source-tag">{{ t(`character.classes.${feat.source}`, feat.source) }}</span>
              </div>
              <span v-if="feat.notes" class="display-notes">{{ feat.notes }}</span>
            </div>
            <button class="action-btn" @click="startEditFeature(i)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeFeature(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <div class="feature-edit-main">
                <BaseInput :model-value="feat.name" :placeholder="t('character.features.featureName')" @update:model-value="updateFeature(i, 'name', $event)" style="flex: 1" />
                <BaseSelect :model-value="feat.source" :options="classSourceOptions" :placeholder="t('character.features.featureSource')" :width="140" @update:model-value="updateFeature(i, 'source', $event)" />
              </div>
              <div class="notes-grow-wrap" :data-replicated-value="feat.notes">
                <textarea
                  :placeholder="t('character.features.featureNotes')"
                  :value="feat.notes"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateFeature(i, 'notes', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!feat.name.trim() || !feat.source" @click="confirmFeature(i)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelFeature(i)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
    </div>

    <!-- Custom fields -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.features.customFields") }}</span>
        <BaseButton variant="default" @click="addCustomField">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.features.addCustomField") }}</span>
        </BaseButton>
      </div>
      <div v-if="!localPairs.length" class="empty-hint">—</div>
      <BaseListItem v-for="(pair, i) in localPairs" :key="i" dense>
        <div class="feature-row">
          <template v-if="!editingPairs.has(i)">
            <div class="display-content">
              <span class="display-name">{{ pair.key || "—" }}</span>
              <span v-if="pair.value" class="display-notes">{{ pair.value }}</span>
            </div>
            <button class="action-btn" @click="startEditPair(i)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeCustomField(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <BaseInput :model-value="pair.key" :placeholder="t('character.features.customKey')" @update:model-value="updateCustomField(i, 'key', $event)" />
              <div class="notes-grow-wrap" :data-replicated-value="pair.value">
                <textarea
                  :placeholder="t('character.features.customValue')"
                  :value="pair.value"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateCustomField(i, 'value', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!pair.key.trim()" @click="confirmCustomField(i)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelCustomField(i)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
    </div>

  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 28px; }
.section { display: grid; gap: 6px; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.empty-hint { font-size: 13px; color: var(--c-text-muted); }

/* Row shell */
.feature-row { display: flex; align-items: flex-start; gap: 8px; }

/* ── Display state ───────────────────────────────────────────── */
.display-content { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.display-primary { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.display-name { font-size: 13px; font-weight: 500; color: var(--c-text); word-break: break-word; }
.display-notes { font-size: 13px; color: var(--c-text-muted); white-space: pre-wrap; word-break: break-word; }
.source-tag {
  font-size: 11px; padding: 1px 7px; border-radius: 10px;
  background: var(--c-surface-raised); border: 1px solid var(--c-border);
  color: var(--c-text-muted); white-space: nowrap; flex-shrink: 0;
}

/* ── Edit state ─────────────────────────────────────────────── */
.feature-edit { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.feature-edit-main { display: flex; gap: 8px; }

/* Auto-grow textarea */
.notes-grow-wrap { display: grid; }
.notes-grow-wrap::after {
  content: attr(data-replicated-value) " ";
  white-space: pre-wrap; word-break: break-word;
  visibility: hidden; grid-area: 1 / 1 / 2 / 2;
  font-size: 13px; font-family: inherit;
  padding: 6px 10px; border: 1px solid transparent;
  min-height: 34px; box-sizing: border-box;
}
.notes-grow-wrap > textarea {
  grid-area: 1 / 1 / 2 / 2;
  resize: none; overflow: hidden; width: 100%; box-sizing: border-box;
  border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text);
  padding: 6px 10px; font-size: 13px; font-family: inherit; outline: none;
}
.notes-grow-wrap > textarea:focus { border-color: var(--c-accent); }
.notes-grow-wrap > textarea::placeholder { color: var(--c-text-muted); }

/* ── Buttons ────────────────────────────────────────────────── */
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
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }
</style>
