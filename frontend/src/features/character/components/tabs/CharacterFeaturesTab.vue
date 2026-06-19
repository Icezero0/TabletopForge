<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon, TrashIcon, PencilIcon, CheckIcon, XMarkIcon } from "@heroicons/vue/24/outline";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseListItem from "@/ui/base/BaseListItem.vue";
import BaseSortableList from "@/ui/base/BaseSortableList.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{
  modelValue: Record<string, unknown>;
  identityBlock: Record<string, unknown>;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

function syncReplicatedValue(e: Event) {
  const textarea = e.target as HTMLTextAreaElement;
  textarea.parentElement?.setAttribute("data-replicated-value", textarea.value);
}

function moveArrayItem<T>(items: T[], from: number, to: number) {
  if (from === to || from < 0 || to < 0) return items;
  const next = [...items];
  const [item] = next.splice(from, 1);
  if (!item) return items;
  next.splice(to, 0, item);
  return next;
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
const editingFeats = ref(new Set<number>());
const editingFeatures = ref(new Set<number>());
type DragSection = "trait" | "feature" | "feat" | "pair";
const editingPairs = ref(new Set<number>());

function sectionIsEditing(section: DragSection) {
  if (section === "trait") return editingTraits.value.size > 0;
  if (section === "feature") return editingFeatures.value.size > 0;
  if (section === "feat") return editingFeats.value.size > 0;
  return editingPairs.value.size > 0;
}

function moveSectionRow(section: DragSection, from: number, to: number) {
  if (sectionIsEditing(section)) return;
  if (section === "trait") {
    localTraits.value = moveArrayItem(localTraits.value, from, to);
    update("racial_traits", localTraits.value);
  } else if (section === "feature") {
    localFeatures.value = moveArrayItem(localFeatures.value, from, to);
    update("class_features", localFeatures.value);
  } else if (section === "feat") {
    localFeats.value = moveArrayItem(localFeats.value, from, to);
    update("feats", localFeats.value);
  } else {
    localPairs.value = moveArrayItem(localPairs.value, from, to);
    emitCustomFields(localPairs.value);
  }
}

function rowDragClasses(section: DragSection) {
  return {
    draggableCard: true,
    canDrag: !sectionIsEditing(section),
  };
}

// ── Racial traits ─────────────────────────────────────────────────────────────
type RacialTrait = { name: string; notes: string };
type TraitDraft = { data: RacialTrait; isNew: boolean };

const localTraits = ref<RacialTrait[]>([...(props.modelValue.racial_traits as RacialTrait[] ?? [])]);
const traitDrafts = ref(new Map<number, TraitDraft>());

watch(
  () => props.modelValue.racial_traits,
  (newVal) => {
    if (editingTraits.value.size > 0) return;
    const fromParent = (newVal as RacialTrait[]) ?? [];
    if (JSON.stringify(fromParent) !== JSON.stringify(localTraits.value)) {
      localTraits.value = [...fromParent];
      editingTraits.value = new Set();
      traitDrafts.value = new Map();
    }
  },
  { deep: true },
);

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

// ── Feats ─────────────────────────────────────────────────────────────────────
type Feat = { name: string; notes: string };
type FeatDraft = { data: Feat; isNew: boolean };

const localFeats = ref<Feat[]>([...(props.modelValue.feats as Feat[] ?? [])]);
const featDrafts = ref(new Map<number, FeatDraft>());

watch(
  () => props.modelValue.feats,
  (newVal) => {
    if (editingFeats.value.size > 0) return;
    const fromParent = (newVal as Feat[]) ?? [];
    if (JSON.stringify(fromParent) !== JSON.stringify(localFeats.value)) {
      localFeats.value = [...fromParent];
      editingFeats.value = new Set();
      featDrafts.value = new Map();
    }
  },
  { deep: true },
);

function updateFeat(i: number, field: string, v: string) {
  localFeats.value = localFeats.value.map((feat, idx) => idx === i ? { ...feat, [field]: v } : feat);
  if (!isNew(featDrafts.value, i)) update("feats", localFeats.value);
}
function addFeat() {
  const idx = localFeats.value.length;
  localFeats.value = [...localFeats.value, { name: "", notes: "" }];
  featDrafts.value = new Map([...featDrafts.value, [idx, { data: { name: "", notes: "" }, isNew: true }]]);
  editingFeats.value = new Set([...editingFeats.value, idx]);
}
function removeFeat(i: number) {
  const wasNew = isNew(featDrafts.value, i);
  localFeats.value = localFeats.value.filter((_, idx) => idx !== i);
  editingFeats.value = shiftEditSet(editingFeats.value, i);
  featDrafts.value = shiftDraftMap(featDrafts.value, i);
  if (!wasNew) update("feats", localFeats.value);
}
function startEditFeat(i: number) {
  const current = localFeats.value[i];
  if (!current) return;
  featDrafts.value = new Map([...featDrafts.value, [i, { data: { ...current }, isNew: false }]]);
  editingFeats.value = new Set([...editingFeats.value, i]);
}
function confirmFeat(i: number) {
  if (!localFeats.value[i]?.name.trim()) return;
  update("feats", localFeats.value);
  editingFeats.value = new Set([...editingFeats.value].filter(idx => idx !== i));
  const d = new Map(featDrafts.value); d.delete(i); featDrafts.value = d;
}
function cancelFeat(i: number) {
  const draft = featDrafts.value.get(i);
  if (!draft) return;
  if (draft.isNew) {
    localFeats.value = localFeats.value.filter((_, idx) => idx !== i);
    editingFeats.value = shiftEditSet(editingFeats.value, i);
    featDrafts.value = shiftDraftMap(featDrafts.value, i);
  } else {
    localFeats.value = localFeats.value.map((feat, idx) => idx === i ? { ...draft.data } : feat);
    update("feats", localFeats.value);
    editingFeats.value = new Set([...editingFeats.value].filter(idx => idx !== i));
    const d = new Map(featDrafts.value); d.delete(i); featDrafts.value = d;
  }
}

// ── Class source options ──────────────────────────────────────────────────────
const classSourceOptions = computed(() =>
  ((props.identityBlock.classes as { name?: string }[] | undefined) ?? [])
    .map((cls) => cls.name?.trim())
    .filter((name): name is string => Boolean(name))
    .map((name) => ({ value: name, label: t(`character.classes.${name}`, name) })),
);

// ── Class features ────────────────────────────────────────────────────────────
type ClassFeature = { name: string; source: string; notes: string };
type FeatureDraft = { data: ClassFeature; isNew: boolean };

const localFeatures = ref<ClassFeature[]>([...(props.modelValue.class_features as ClassFeature[] ?? [])]);
const featureDrafts = ref(new Map<number, FeatureDraft>());

watch(
  () => props.modelValue.class_features,
  (newVal) => {
    if (editingFeatures.value.size > 0) return;
    const fromParent = (newVal as ClassFeature[]) ?? [];
    if (JSON.stringify(fromParent) !== JSON.stringify(localFeatures.value)) {
      localFeatures.value = [...fromParent];
      editingFeatures.value = new Set();
      featureDrafts.value = new Map();
    }
  },
  { deep: true },
);

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
    if (editingPairs.value.size > 0) return;
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
      <BaseSortableList
        :count="localTraits.length"
        :disabled="sectionIsEditing('trait')"
        :placeholder-min-height="50"
        :placeholder-radius="14"
        @reorder="moveSectionRow('trait', $event.from, $event.to)"
      >
        <template #default="{ index }">
      <BaseListItem
        dense
        :class="rowDragClasses('trait')"
      >
        <div class="feature-row">
          <template v-if="!editingTraits.has(index)">
            <div class="display-content">
              <span class="display-name">{{ localTraits[index]?.name || "—" }}</span>
              <span v-if="localTraits[index]?.notes" class="display-notes">{{ localTraits[index]?.notes }}</span>
            </div>
            <button class="action-btn" @click="startEditTrait(index)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeTrait(index)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <BaseInput :model-value="localTraits[index]?.name ?? ''" :placeholder="t('character.features.traitName')" @update:model-value="updateTrait(index, 'name', $event)" />
              <div class="notes-grow-wrap" :data-replicated-value="localTraits[index]?.notes">
                <textarea
                  :placeholder="t('character.features.traitNotes')"
                  :value="localTraits[index]?.notes"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateTrait(index, 'notes', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!localTraits[index]?.name.trim()" @click="confirmTrait(index)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelTrait(index)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
        </template>
      </BaseSortableList>
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
      <BaseSortableList
        :count="localFeatures.length"
        :disabled="sectionIsEditing('feature')"
        :placeholder-min-height="50"
        :placeholder-radius="14"
        @reorder="moveSectionRow('feature', $event.from, $event.to)"
      >
        <template #default="{ index }">
      <BaseListItem
        dense
        :class="rowDragClasses('feature')"
      >
        <div class="feature-row">
          <template v-if="!editingFeatures.has(index)">
            <div class="display-content">
              <div class="display-primary">
                <span class="display-name">{{ localFeatures[index]?.name || "—" }}</span>
                <span v-if="localFeatures[index]?.source" class="source-tag">{{ t(`character.classes.${localFeatures[index]?.source}`, localFeatures[index]?.source) }}</span>
              </div>
              <span v-if="localFeatures[index]?.notes" class="display-notes">{{ localFeatures[index]?.notes }}</span>
            </div>
            <button class="action-btn" @click="startEditFeature(index)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeFeature(index)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <div class="feature-edit-main">
                <BaseInput :model-value="localFeatures[index]?.name ?? ''" :placeholder="t('character.features.featureName')" @update:model-value="updateFeature(index, 'name', $event)" style="flex: 1" />
                <BaseSelect :model-value="localFeatures[index]?.source ?? ''" :options="classSourceOptions" :placeholder="t('character.features.featureSource')" :width="140" @update:model-value="updateFeature(index, 'source', $event)" />
              </div>
              <div class="notes-grow-wrap" :data-replicated-value="localFeatures[index]?.notes">
                <textarea
                  :placeholder="t('character.features.featureNotes')"
                  :value="localFeatures[index]?.notes"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateFeature(index, 'notes', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!localFeatures[index]?.name.trim() || !localFeatures[index]?.source" @click="confirmFeature(index)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelFeature(index)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
        </template>
      </BaseSortableList>
    </div>

    <!-- Feats -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.features.feats") }}</span>
        <BaseButton variant="default" @click="addFeat">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.features.addFeat") }}</span>
        </BaseButton>
      </div>
      <div v-if="!localFeats.length" class="empty-hint">—</div>
      <BaseSortableList
        :count="localFeats.length"
        :disabled="sectionIsEditing('feat')"
        :placeholder-min-height="50"
        :placeholder-radius="14"
        @reorder="moveSectionRow('feat', $event.from, $event.to)"
      >
        <template #default="{ index }">
      <BaseListItem
        dense
        :class="rowDragClasses('feat')"
      >
        <div class="feature-row">
          <template v-if="!editingFeats.has(index)">
            <div class="display-content">
              <span class="display-name">{{ localFeats[index]?.name || "—" }}</span>
              <span v-if="localFeats[index]?.notes" class="display-notes">{{ localFeats[index]?.notes }}</span>
            </div>
            <button class="action-btn" @click="startEditFeat(index)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeFeat(index)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <BaseInput :model-value="localFeats[index]?.name ?? ''" :placeholder="t('character.features.featName')" @update:model-value="updateFeat(index, 'name', $event)" />
              <div class="notes-grow-wrap" :data-replicated-value="localFeats[index]?.notes">
                <textarea
                  :placeholder="t('character.features.featNotes')"
                  :value="localFeats[index]?.notes"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateFeat(index, 'notes', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!localFeats[index]?.name.trim()" @click="confirmFeat(index)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelFeat(index)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
        </template>
      </BaseSortableList>
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
      <BaseSortableList
        :count="localPairs.length"
        :disabled="sectionIsEditing('pair')"
        :placeholder-min-height="50"
        :placeholder-radius="14"
        @reorder="moveSectionRow('pair', $event.from, $event.to)"
      >
        <template #default="{ index }">
      <BaseListItem
        dense
        :class="rowDragClasses('pair')"
      >
        <div class="feature-row">
          <template v-if="!editingPairs.has(index)">
            <div class="display-content">
              <span class="display-name">{{ localPairs[index]?.key || "—" }}</span>
              <span v-if="localPairs[index]?.value" class="display-notes">{{ localPairs[index]?.value }}</span>
            </div>
            <button class="action-btn" @click="startEditPair(index)"><AppIcon :icon="PencilIcon" :size="14" /></button>
            <button class="del-btn" @click="removeCustomField(index)"><AppIcon :icon="TrashIcon" :size="14" /></button>
          </template>
          <template v-else>
            <div class="feature-edit">
              <BaseInput :model-value="localPairs[index]?.key ?? ''" :placeholder="t('character.features.customKey')" @update:model-value="updateCustomField(index, 'key', $event)" />
              <div class="notes-grow-wrap" :data-replicated-value="localPairs[index]?.value">
                <textarea
                  :placeholder="t('character.features.customValue')"
                  :value="localPairs[index]?.value"
                  rows="1"
                  @input="(e) => { syncReplicatedValue(e); updateCustomField(index, 'value', (e.target as HTMLTextAreaElement).value); }"
                />
              </div>
            </div>
            <button class="action-btn confirm-btn" :disabled="!localPairs[index]?.key.trim()" @click="confirmCustomField(index)"><AppIcon :icon="CheckIcon" :size="14" /></button>
            <button class="action-btn cancel-btn" @click="cancelCustomField(index)"><AppIcon :icon="XMarkIcon" :size="14" /></button>
          </template>
        </div>
      </BaseListItem>
        </template>
      </BaseSortableList>
    </div>

  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 28px; }
.section { display: grid; gap: 6px; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.empty-hint { font-size: 13px; color: var(--c-text-muted); }
.draggableCard {
  transition:
    opacity 140ms ease,
    transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

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
