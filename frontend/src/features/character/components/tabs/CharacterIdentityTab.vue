<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import { useI18n } from "vue-i18n";
import { MagnifyingGlassPlusIcon, PlusIcon, TrashIcon, UserCircleIcon } from "@heroicons/vue/24/outline";
import { DND5E_ALIGNMENT_OPTIONS, DND5E_CLASSES } from "@/features/character/constants";
import { uploadAsset } from "@/infra/api/assets.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import AvatarCropDialog from "@/ui/domain/avatar/AvatarCropDialog.vue";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseNumberInput from "@/ui/base/BaseNumberInput.vue";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";
import BaseSelect from "@/ui/base/BaseSelect.vue";
import BaseButton from "@/ui/base/BaseButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{
  modelValue: Record<string, unknown>;
  flavor: Record<string, unknown>;
  portraitAssetId: number | null;
}>();
const emit = defineEmits<{
  (e: "update:modelValue", v: Record<string, unknown>): void;
  (e: "update:flavor", v: Record<string, unknown>): void;
  (e: "update:portraitAssetId", v: number | null): void;
}>();

const { t } = useI18n();

function update(key: string, value: unknown) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}
function updateFlavor(key: string, value: string) {
  emit("update:flavor", { ...props.flavor, [key]: value });
}

const classes = computed(
  () => (props.modelValue.classes as { name: string; level: number; subclass: string }[]) ?? [],
);
function updateClass(i: number, field: string, value: unknown) {
  const next = classes.value.map((c, idx) => idx === i ? { ...c, [field]: value } : c);
  update("classes", next);
}
function addClass() {
  update("classes", [...classes.value, { name: "", level: 1, subclass: "" }]);
}

// Available class options for a given row — excludes classes already picked in other rows
function classSelectOptions(currentIdx: number) {
  const takenByOthers = new Set(
    classes.value.filter((_, i) => i !== currentIdx).map(c => c.name).filter(Boolean),
  );
  return DND5E_CLASSES
    .filter(c => !takenByOthers.has(c))
    .map(c => ({ value: c, label: t(`character.classes.${c}`) }));
}
const canAddClass = computed(() => classes.value.length < DND5E_CLASSES.length);
function removeClass(i: number) {
  update("classes", classes.value.filter((_, idx) => idx !== i));
}

const alignmentOptions = computed(() =>
  DND5E_ALIGNMENT_OPTIONS.map((a) => ({ value: a.value, label: t(a.labelKey) })),
);

// ── Portrait (cropped square) ──────────────────────────────────────────────
const portraitIdRef = toRef(() => props.portraitAssetId);
const { url: portraitUrl } = useAuthenticatedAssetUrl(portraitIdRef);
const portraitInputRef = ref<HTMLInputElement | null>(null);
const cropOpen = ref(false);
const pickedFile = ref<File | null>(null);
const uploadingPortrait = ref(false);

function onPortraitPick(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  pickedFile.value = file;
  cropOpen.value = true;
  (e.target as HTMLInputElement).value = "";
}
async function onCropDone(file: File) {
  uploadingPortrait.value = true;
  try {
    const asset = await uploadAsset(file, "image");
    emit("update:portraitAssetId", asset.id);
  } finally {
    uploadingPortrait.value = false;
    pickedFile.value = null;
  }
}
function onCropCancel() { pickedFile.value = null; }

// ── Gallery (up to 3 full-size images) ────────────────────────────────────
const galleryIds = computed(() => {
  const raw = (props.modelValue.gallery_asset_ids as (number | null)[]) ?? [];
  return [raw[0] ?? null, raw[1] ?? null, raw[2] ?? null];
});

const gRef0 = toRef(() => galleryIds.value[0]);
const gRef1 = toRef(() => galleryIds.value[1]);
const gRef2 = toRef(() => galleryIds.value[2]);
const { url: gUrl0 } = useAuthenticatedAssetUrl(gRef0);
const { url: gUrl1 } = useAuthenticatedAssetUrl(gRef1);
const { url: gUrl2 } = useAuthenticatedAssetUrl(gRef2);
const galleryUrls = computed(() => [gUrl0.value, gUrl1.value, gUrl2.value]);

const galleryInputRef = ref<HTMLInputElement | null>(null);
const editingSlot = ref<number>(-1);
const uploadingSlot = ref<number>(-1);

function openGalleryPick(slot: number) {
  editingSlot.value = slot;
  galleryInputRef.value?.click();
}
async function onGalleryPick(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file || editingSlot.value < 0) return;
  const slot = editingSlot.value;
  uploadingSlot.value = slot;
  (e.target as HTMLInputElement).value = "";
  try {
    const asset = await uploadAsset(file, "image");
    const next: (number | null)[] = [...galleryIds.value];
    next[slot] = asset.id;
    update("gallery_asset_ids", next);
  } finally {
    uploadingSlot.value = -1;
    editingSlot.value = -1;
  }
}
function removeGalleryImage(slot: number) {
  const next: (number | null)[] = [...galleryIds.value];
  next[slot] = null;
  update("gallery_asset_ids", next);
}

// ── Fullscreen image viewer ────────────────────────────────────────────────
const viewingUrl = ref<string | null>(null);

function viewImage(url: string) { viewingUrl.value = url; }
function closeViewer() { viewingUrl.value = null; }
</script>

<template>
  <div class="tab-content">
    <!-- Crop dialog -->
    <AvatarCropDialog
      v-model="cropOpen"
      :file="pickedFile"
      :title="t('profile.crop.title')"
      :output-size="512"
      @done="onCropDone"
      @cancel="onCropCancel"
    />

    <!-- Fullscreen viewer -->
    <Teleport to="body">
      <div v-if="viewingUrl" class="image-viewer" @click="closeViewer">
        <img :src="viewingUrl" class="viewer-img" />
      </div>
    </Teleport>

    <!-- Portrait + Gallery row -->
    <div class="section">
      <div class="media-row">
        <!-- Portrait -->
        <div class="media-col">
          <div class="media-label">{{ t("character.identity.portrait") }}</div>
          <div class="portrait-box" @click="portraitInputRef?.click()">
            <img v-if="portraitUrl" :src="portraitUrl" class="slot-img" />
            <div v-else class="slot-empty">
              <AppIcon :icon="UserCircleIcon" :size="44" />
            </div>
            <div class="slot-overlay"><span class="overlay-text">{{ t("character.identity.uploadPortrait") }}</span></div>
          </div>
          <input ref="portraitInputRef" type="file" accept="image/*" class="hidden" @change="onPortraitPick" />
          <button v-if="portraitAssetId" class="remove-link" @click="emit('update:portraitAssetId', null)">
            {{ t("character.identity.removePortrait") }}
          </button>
        </div>

        <!-- Gallery -->
        <div class="media-col gallery-col">
          <div class="media-label">{{ t("character.identity.gallery") }}</div>
          <div class="gallery-slots">
            <div
              v-for="slot in 3"
              :key="slot"
              class="gallery-slot"
              :class="{ loading: uploadingSlot === slot - 1 }"
            >
              <template v-if="galleryIds[slot - 1] !== null && galleryUrls[slot - 1]">
                <img :src="galleryUrls[slot - 1]!" class="slot-img" />
                <div class="slot-actions">
                  <button class="action-btn" @click.stop="viewImage(galleryUrls[slot - 1]!)">
                    <AppIcon :icon="MagnifyingGlassPlusIcon" :size="14" />
                  </button>
                  <button class="action-btn danger" @click.stop="removeGalleryImage(slot - 1)">×</button>
                </div>
              </template>
              <template v-else-if="galleryIds[slot - 1] !== null">
                <!-- ID exists but URL not loaded yet -->
                <div class="slot-empty"><AppIcon :icon="UserCircleIcon" :size="24" /></div>
              </template>
              <template v-else>
                <button class="gallery-add" @click="openGalleryPick(slot - 1)">
                  <AppIcon :icon="PlusIcon" :size="22" />
                </button>
              </template>
            </div>
          </div>
          <input ref="galleryInputRef" type="file" accept="image/*" class="hidden" @change="onGalleryPick" />
        </div>
      </div>
    </div>

    <!-- Basic info (uniform 3-col grid) -->
    <div class="section">
      <div class="section-title">{{ t("character.identity.basicInfo") }}</div>
      <div class="info-grid">
        <div class="field">
          <label class="label">{{ t("character.identity.name") }}<span class="required">*</span></label>
          <BaseInput :model-value="(modelValue.name as string) ?? ''" @update:model-value="update('name', $event)" />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.gender") }}</label>
          <BaseInput :model-value="(modelValue.gender as string) ?? ''" @update:model-value="update('gender', $event)" />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.age") }}</label>
          <BaseInput :model-value="(modelValue.age as string) ?? ''" @update:model-value="update('age', $event)" />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.race") }}</label>
          <BaseInput :model-value="(modelValue.race as string) ?? ''" @update:model-value="update('race', $event)" />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.alignment") }}</label>
          <BaseSelect
            :model-value="(modelValue.alignment as string) ?? ''"
            :options="alignmentOptions"
            @update:model-value="update('alignment', $event)"
          />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.background") }}</label>
          <BaseInput :model-value="(modelValue.background as string) ?? ''" @update:model-value="update('background', $event)" />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.height") }}</label>
          <BaseInput :model-value="(modelValue.height as string) ?? ''" @update:model-value="update('height', $event)" />
        </div>
        <div class="field">
          <label class="label">{{ t("character.identity.weight") }}</label>
          <BaseInput :model-value="(modelValue.weight as string) ?? ''" @update:model-value="update('weight', $event)" />
        </div>
      </div>
      <div class="field">
        <label class="label">{{ t("character.identity.appearance") }}</label>
        <BaseTextarea
          :rows="3"
          :model-value="(modelValue.appearance as string) ?? ''"
          @update:model-value="update('appearance', $event)"
        />
      </div>
    </div>

    <!-- Classes -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">{{ t("character.identity.classes") }}</span>
        <BaseButton variant="default" :disabled="!canAddClass" @click="addClass">
          <span class="btn-icon-text"><AppIcon :icon="PlusIcon" :size="14" />{{ t("character.identity.addClass") }}</span>
        </BaseButton>
      </div>
      <div v-if="!classes.length" class="empty-hint">{{ t("character.identity.noClasses") }}</div>
      <div v-for="(cls, i) in classes" :key="i" class="class-row">
        <div class="class-fields">
          <BaseSelect
            :model-value="cls.name"
            :options="classSelectOptions(i)"
            :placeholder="t('character.identity.className')"
            :width="140"
            @update:model-value="updateClass(i, 'name', $event)"
          />
          <div class="level-wrap">
            <BaseNumberInput
              compact
              :model-value="String(cls.level)"
              :min="1"
              :max="20"
              @update:model-value="updateClass(i, 'level', Math.max(1, Math.min(20, parseInt($event, 10) || 1)))"
            />
          </div>
          <BaseInput :model-value="cls.subclass" :placeholder="t('character.identity.classSubclass')" @update:model-value="updateClass(i, 'subclass', $event)" />
        </div>
        <button class="del-btn" @click="removeClass(i)"><AppIcon :icon="TrashIcon" :size="14" /></button>
      </div>
    </div>

    <!-- Personality (flavor merged) -->
    <div class="section">
      <div class="section-title">{{ t("character.flavor.section") }}</div>
      <div v-for="field in ['personality', 'ideals', 'bonds', 'flaws']" :key="field" class="field">
        <label class="label">{{ t(`character.flavor.${field}`) }}</label>
        <BaseTextarea
          :rows="3"
          :placeholder="t(`character.flavor.${field}Placeholder`)"
          :model-value="(flavor[field] as string) ?? ''"
          @update:model-value="updateFlavor(field, $event)"
        />
      </div>
      <div class="field">
        <label class="label">{{ t("character.flavor.backstory") }}</label>
        <BaseTextarea
          :rows="8"
          min-height="160px"
          :placeholder="t('character.flavor.backstoryPlaceholder')"
          :model-value="(flavor.backstory as string) ?? ''"
          @update:model-value="updateFlavor('backstory', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-content { display: grid; gap: 28px; }
.section { display: grid; gap: 12px; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 14px; font-weight: 600; color: var(--c-text); }

/* ── Media row ─────────────────────────────────────────────────────────── */
.media-row { display: flex; gap: 24px; align-items: flex-start; }

.media-col { display: flex; flex-direction: column; gap: 6px; align-items: center; flex-shrink: 0; }
.gallery-col { align-items: center; flex: 1; }

.media-label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }

.portrait-box {
  width: 120px; height: 120px; border-radius: var(--r-2); border: 1px solid var(--c-border);
  background: var(--c-surface-raised); overflow: hidden; display: flex;
  align-items: center; justify-content: center; cursor: pointer; position: relative;
}
.portrait-box:hover .slot-overlay { opacity: 1; }

.slot-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.slot-empty { color: var(--c-text-muted); opacity: 0.35; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
.slot-overlay {
  position: absolute; inset: 0; background: rgb(0 0 0 / 0.4);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.16s;
}
.overlay-text { color: #fff; font-size: 11px; font-weight: 500; text-align: center; padding: 0 6px; }

.remove-link {
  background: none; border: none; cursor: pointer; font-size: 11px;
  color: var(--c-text-muted); padding: 0; text-decoration: underline; text-underline-offset: 2px;
}
.remove-link:hover { color: var(--c-danger, #e53e3e); }

/* Gallery slots */
.gallery-slots { display: flex; gap: 8px; }
.gallery-slot {
  width: 120px; height: 120px; border-radius: var(--r-2); border: 1px solid var(--c-border);
  background: var(--c-surface-raised); overflow: hidden; position: relative; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}

/* Slot action buttons (appear on hover) */
.slot-actions {
  position: absolute; top: 5px; right: 5px;
  display: flex; gap: 3px; opacity: 0; transition: opacity 0.15s;
  background: rgba(0, 0, 0, 0.5); border-radius: var(--r-1); padding: 2px;
}
.gallery-slot:hover .slot-actions { opacity: 1; }
.action-btn {
  background: none; border: none; cursor: pointer; color: #fff;
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  border-radius: 3px; font-size: 13px; line-height: 1;
  transition: background 0.1s;
}
.action-btn:hover { background: rgba(255, 255, 255, 0.2); }
.action-btn.danger:hover { background: rgba(220, 50, 50, 0.6); }

.gallery-add {
  width: 100%; height: 100%; background: none; border: none; cursor: pointer;
  color: var(--c-text-muted); display: flex; align-items: center; justify-content: center;
  opacity: 0.4; transition: opacity 0.14s;
}
.gallery-add:hover { opacity: 0.85; }

/* ── Basic info grid (uniform 3-col) ───────────────────────────────────── */
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 10px; }
.field { display: grid; gap: 4px; }
.label { font-size: 12px; font-weight: 500; color: var(--c-text-muted); }
.required { margin-left: 3px; color: var(--c-danger, #e53e3e); }

/* ── Classes ────────────────────────────────────────────────────────────── */
.empty-hint { font-size: 13px; color: var(--c-text-muted); }
.class-row { display: flex; align-items: center; gap: 8px; }
.class-fields { display: flex; gap: 8px; flex: 1; align-items: center; }

.level-wrap { width: 100px; flex-shrink: 0; }

.del-btn {
  background: none; border: none; cursor: pointer; color: var(--c-text-muted);
  padding: 4px; border-radius: var(--r-1); display: flex; align-items: center; transition: color 0.12s;
}
.del-btn:hover { color: var(--c-danger, #e53e3e); }
.btn-icon-text { display: inline-flex; align-items: center; gap: 5px; }


/* ── Fullscreen viewer ──────────────────────────────────────────────────── */
.hidden { display: none; }
</style>

<!-- Fullscreen viewer uses Teleport to body so it's not clipped by overflow:hidden parents -->
<style>
.image-viewer {
  position: fixed; inset: 0; z-index: 9999;
  background: rgb(0 0 0 / 0.82);
  display: flex; align-items: center; justify-content: center;
  cursor: zoom-out;
  animation: viewer-in 0.18s ease;
}
@keyframes viewer-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.viewer-img {
  max-width: 90vw; max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 24px 64px rgb(0 0 0 / 0.6);
  cursor: zoom-out;
}
</style>
