<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { PlusIcon, TrashIcon } from "@heroicons/vue/24/outline";
import { DND5E_CLASSES } from "@/features/character/constants";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{ modelValue: Record<string, unknown> }>();
const emit = defineEmits<{ (e: "update:modelValue", v: Record<string, unknown>): void }>();
const { t } = useI18n();

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

// Custom fields (local pair state to allow empty-key rows while editing)
const localPairs = ref<{ key: string; value: string }[]>(
  Object.entries((props.modelValue.custom_fields as Record<string, string>) ?? {}).map(([k, v]) => ({ key: k, value: v })),
);
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
function emitCustomFields(pairs: { key: string; value: string }[]) {
  const obj: Record<string, string> = {};
  for (const { key, value } of pairs) if (key.trim()) obj[key.trim()] = value;
  update("custom_fields", obj);
}
function addCustomField() { localPairs.value = [...localPairs.value, { key: "", value: "" }]; }
function updateCustomField(i: number, field: "key" | "value", v: string) {
  localPairs.value = localPairs.value.map((p, idx) => (idx === i ? { ...p, [field]: v } : p));
  emitCustomFields(localPairs.value);
}
function removeCustomField(i: number) {
  localPairs.value = localPairs.value.filter((_, idx) => idx !== i);
  emitCustomFields(localPairs.value);
}

// Racial traits
type RacialTrait = { name: string; notes: string };
const racialTraits = computed(() => (props.modelValue.racial_traits as RacialTrait[]) ?? []);
function updateTrait(i: number, field: string, v: string) {
  update("racial_traits", racialTraits.value.map((t, idx) => idx === i ? { ...t, [field]: v } : t));
}
function addTrait() { update("racial_traits", [...racialTraits.value, { name: "", notes: "" }]); }
function removeTrait(i: number) { update("racial_traits", racialTraits.value.filter((_, idx) => idx !== i)); }

// Class source options — all DnD 5e classes
const classSourceOptions = computed(() =>
  DND5E_CLASSES.map(c => ({ value: c, label: t(`character.classes.${c}`) })),
);

// Class features
type ClassFeature = { name: string; source: string; notes: string };
const classFeatures = computed(() => (props.modelValue.class_features as ClassFeature[]) ?? []);
function updateFeature(i: number, field: string, v: string) {
  update("class_features", classFeatures.value.map((f, idx) => idx === i ? { ...f, [field]: v } : f));
}
function addFeature() { update("class_features", [...classFeatures.value, { name: "", source: "", notes: "" }]); }
function removeFeature(i: number) { update("class_features", classFeatures.value.filter((_, idx) => idx !== i)); }

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
      <div v-if="!racialTraits.length" class="empty-hint">—</div>
      <div v-for="(trait, i) in racialTraits" :key="i" class="feature-row">
        <div class="feature-fields">
          <BaseInput :model-value="trait.name" :placeholder="t('character.features.traitName')" @update:model-value="updateTrait(i, 'name', $event)" style="flex: 0 0 180px" />
          <input class="notes-input" type="text" :placeholder="t('character.features.traitNotes')" :value="trait.notes" @input="updateTrait(i, 'notes', ($event.target as HTMLInputElement).value)" />
        </div>
        <button class="del-btn" @click="removeTrait(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
      </div>
    </div>

    <!-- Class features -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.features.classFeatures") }}</span>
        <BaseButton variant="default" @click="addFeature">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.features.addClassFeature") }}</span>
        </BaseButton>
      </div>
      <div v-if="!classFeatures.length" class="empty-hint">—</div>
      <div v-for="(feat, i) in classFeatures" :key="i" class="feature-row">
        <div class="feature-fields">
          <BaseInput :model-value="feat.name" :placeholder="t('character.features.featureName')" @update:model-value="updateFeature(i, 'name', $event)" style="flex: 0 0 180px" />
          <BaseSelect :model-value="feat.source" :options="classSourceOptions" :placeholder="t('character.features.featureSource')" :width="140" @update:model-value="updateFeature(i, 'source', $event)" />
          <input class="notes-input" type="text" :placeholder="t('character.features.featureNotes')" :value="feat.notes" @input="updateFeature(i, 'notes', ($event.target as HTMLInputElement).value)" />
        </div>
        <button class="del-btn" @click="removeFeature(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
      </div>
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
      <div v-for="(pair, i) in localPairs" :key="i" class="feature-row">
        <BaseInput
          :model-value="pair.key"
          :placeholder="t('character.features.customKey')"
          style="flex: 0 0 180px"
          @update:model-value="updateCustomField(i, 'key', $event)"
        />
        <input
          class="notes-input"
          type="text"
          :placeholder="t('character.features.customValue')"
          :value="pair.value"
          @input="updateCustomField(i, 'value', ($event.target as HTMLInputElement).value)"
        />
        <button class="del-btn" @click="removeCustomField(i)">
          <AppIcon :icon="TrashIcon" :size="14" />
        </button>
      </div>
    </div>

  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 28px; }
.section { display: grid; gap: 12px; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }
.empty-hint { font-size: 13px; color: var(--c-text-muted); }
.feature-row { display: flex; align-items: center; gap: 8px; }
.feature-fields { display: flex; gap: 8px; flex: 1; }
.notes-input {
  flex: 1; border: 1px solid var(--c-border); border-radius: var(--r-1);
  background: var(--c-surface); color: var(--c-text); padding: 6px 10px;
  font-size: 13px; font-family: inherit; outline: none; min-width: 0;
}
.notes-input:focus { border-color: var(--c-accent); }
.notes-input::placeholder { color: var(--c-text-muted); }
.del-btn {
  background: none; border: none; cursor: pointer; color: var(--c-text-muted);
  padding: 4px; border-radius: var(--r-1); display: flex; align-items: center;
  transition: color 0.12s; flex-shrink: 0;
}
.del-btn:hover { color: var(--c-danger, #e53e3e); }
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }
</style>
