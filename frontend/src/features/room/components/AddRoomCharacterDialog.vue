<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { Character } from "@/infra/api/character.api";
import { buildPathWithReturn } from "@/composables/useNavigationReturn";
import BaseButton from "@/ui/base/BaseButton.vue";
import BaseInput from "@/ui/base/BaseInput.vue";
import BaseNumberInput from "@/ui/base/BaseNumberInput.vue";
import BaseTextarea from "@/ui/base/BaseTextarea.vue";
import CharacterPickerItem from "@/features/room/components/CharacterPickerItem.vue";
import { useToastsStore } from "@/stores/toasts.store";
import { UserCircleIcon } from "@heroicons/vue/24/outline";
import AvatarCropDialog from "@/ui/domain/avatar/AvatarCropDialog.vue";
import AppIcon from "@/ui/base/AppIcon.vue";
import { uploadAsset } from "@/infra/api/assets.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

type Step = "choose" | "quick" | "pick";

const props = defineProps<{
  open: boolean;
  roomId: number;
  gameRole: GameRole | "unknown";
  currentUserDisplayName?: string;
  submitting?: boolean;
  libraryCharacters?: Character[];
  libraryLoading?: boolean;
  inRoomCharacterIds?: Set<number>;
}>();

const emit = defineEmits<{
  close: [];
  createQuick: [payload: {
    name: string;
    max_hp: number | null;
    armor_class: number | null;
    backstory: string;
    portrait_asset_id: number | null;
    spawnAfterCreate?: boolean;
  }];
  linkCharacter: [characterId: number];
}>();

const { t } = useI18n();
const router = useRouter();
const toasts = useToastsStore();

const step = ref<Step>("choose");
const quickName = ref("");
const quickMaxHp = ref("");
const quickAc = ref("");
const quickBackstory = ref("");
const pickSearch = ref("");
const spawnAfterCreate = ref(false);

const avatarAssetId = ref<number | null>(null);
const cropOpen = ref(false);
const pickedFile = ref<File | null>(null);
const uploadingAvatar = ref(false);
const avatarFileInputEl = ref<HTMLInputElement | null>(null);
const { url: avatarUrl } = useAuthenticatedAssetUrl(avatarAssetId);

const title = computed(() => {
  if (step.value === "quick") return t("room.characters.gmQuickTitle");
  if (step.value === "pick") return t("room.characters.pickFromLibrary");
  return t("room.characters.chooseTitle");
});

const filteredLibrary = computed(() => {
  const chars = props.libraryCharacters ?? [];
  const q = pickSearch.value.trim().toLowerCase();
  if (!q) return chars;
  return chars.filter((c) => c.name.toLowerCase().includes(q));
});

function resetForm() {
  step.value = "choose";
  quickName.value = "";
  quickMaxHp.value = "";
  quickAc.value = "";
  quickBackstory.value = "";
  pickSearch.value = "";
  spawnAfterCreate.value = false;
  avatarAssetId.value = null;
  pickedFile.value = null;
}

watch(
  () => props.open,
  (open) => {
    if (!open) resetForm();
  },
);

function close() {
  resetForm();
  emit("close");
}

function openAvatarPicker() {
  avatarFileInputEl.value?.click();
}

function onAvatarPick(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  pickedFile.value = file;
  cropOpen.value = true;
  (e.target as HTMLInputElement).value = "";
}

async function onCropDone(file: File) {
  uploadingAvatar.value = true;
  try {
    const asset = await uploadAsset(file, "image");
    avatarAssetId.value = asset.id;
  } finally {
    uploadingAvatar.value = false;
    pickedFile.value = null;
  }
}

function onCropCancel() {
  pickedFile.value = null;
}

function parseOptionalInt(raw: string | number | null | undefined): number | null {
  if (raw == null) return null;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : null;
  const trimmed = String(raw).trim();
  if (!trimmed) return null;
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

function submitQuick() {
  const name = quickName.value.trim();
  if (!name) {
    toasts.push({ message: t("table.assets.nameRequired"), tone: "warning" });
    return;
  }
  emit("createQuick", {
    name,
    max_hp: parseOptionalInt(quickMaxHp.value),
    armor_class: parseOptionalInt(quickAc.value),
    backstory: quickBackstory.value.trim(),
    portrait_asset_id: avatarAssetId.value,
    spawnAfterCreate: spawnAfterCreate.value,
  });
}

function pickCharacter(char: Character) {
  const alreadyIn = props.inRoomCharacterIds?.has(char.id) ?? false;
  if (alreadyIn) return;
  emit("linkCharacter", char.id);
  close();
}

function openFullEditor() {
  const base = buildPathWithReturn(
    "/characters/new",
    `/rooms/${props.roomId}`,
    true,
  );
  const query =
    typeof base === "object"
      ? {
          ...base.query,
          roomId: String(props.roomId),
          openCharacterPopover: "1",
        }
      : {
          roomId: String(props.roomId),
          openCharacterPopover: "1",
        };
  void router.push({ path: "/characters/new", query });
  close();
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="backdrop" @click="step === 'choose' || step === 'pick' ? close() : undefined">
      <div class="dialog" @click.stop>
        <h3 class="title">{{ title }}</h3>

        <div v-if="step === 'choose'" class="chooseGrid">
          <button type="button" class="choiceCard" @click="step = 'pick'">
            <span class="choiceTitle">{{ t("room.characters.pickFromLibrary") }}</span>
            <span class="choiceHint">{{ t("room.characters.pickFromLibraryHint") }}</span>
          </button>
          <button type="button" class="choiceCard" @click="step = 'quick'">
            <span class="choiceTitle">{{ t("room.characters.gmQuick") }}</span>
            <span class="choiceHint">{{ t("room.characters.gmQuickHint") }}</span>
          </button>
          <button type="button" class="choiceCard" @click="openFullEditor">
            <span class="choiceTitle">{{ t("room.characters.gmFull") }}</span>
            <span class="choiceHint">{{ t("room.characters.gmFullHint") }}</span>
          </button>
        </div>

        <form v-else-if="step === 'quick'" class="form" @submit.prevent="submitQuick">
          <div class="nameRow">
            <div class="avatarArea" @click="openAvatarPicker">
              <div class="avatarCircle" :class="{ uploading: uploadingAvatar }">
                <img v-if="avatarUrl" :src="avatarUrl" class="avatarImg" alt="" />
                <AppIcon v-else :icon="UserCircleIcon" :size="36" class="avatarEmpty" />
              </div>
            </div>
            <label class="field">
              <span>{{ t("room.characters.nameLabel") }}</span>
              <BaseInput v-model="quickName" />
            </label>
          </div>
          <div class="row">
            <label class="field">
              <span>{{ t("room.characters.maxHpLabel") }}</span>
              <BaseNumberInput v-model="quickMaxHp" :min="0" />
            </label>
            <label class="field">
              <span>{{ t("room.characters.acLabel") }}</span>
              <BaseNumberInput v-model="quickAc" :min="0" />
            </label>
          </div>
          <label class="field">
            <span>{{ t("room.characters.backstoryLabel") }}</span>
            <BaseTextarea v-model="quickBackstory" :rows="4" min-height="80px" />
          </label>
          <label class="toggleField">
            <span>{{ t("table.assets.spawnAfterCreate") }}</span>
            <span class="toggle" :class="{ on: spawnAfterCreate }" @click="spawnAfterCreate = !spawnAfterCreate">
              <span class="toggleThumb" />
            </span>
          </label>
          <div class="actions">
            <BaseButton type="button" variant="default" @click="step = 'choose'">
              {{ t("common.back") }}
            </BaseButton>
            <BaseButton
              type="button"
              variant="primary"
              :disabled="submitting"
              :loading="submitting"
              @click="submitQuick"
            >
              {{ t("room.characters.create") }}
            </BaseButton>
          </div>
        </form>

        <div v-else-if="step === 'pick'" class="pickStep">
          <BaseInput
            v-model="pickSearch"
            :placeholder="t('room.characters.searchPlaceholder')"
          />
          <p v-if="libraryLoading" class="muted">{{ t("common.loading") }}</p>
          <p v-else-if="filteredLibrary.length === 0" class="muted">
            {{ t("room.characters.pickEmpty") }}
          </p>
          <ul v-else class="pickList">
            <CharacterPickerItem
              v-for="char in filteredLibrary"
              :key="char.id"
              :character="char"
              :in-room="inRoomCharacterIds?.has(char.id)"
              :in-room-label="t('room.characters.alreadyInRoom')"
              @pick="pickCharacter"
            />
          </ul>
          <div class="actions">
            <BaseButton type="button" variant="default" @click="step = 'choose'">
              {{ t("common.back") }}
            </BaseButton>
          </div>
        </div>

        <input
          ref="avatarFileInputEl"
          type="file"
          accept="image/*"
          style="display: none"
          @change="onAvatarPick"
        />
      </div>
    </div>
  </Teleport>

  <AvatarCropDialog
    v-model="cropOpen"
    :file="pickedFile"
    :title="t('profile.crop.title')"
    :output-size="512"
    :z-index="500"
    @done="onCropDone"
    @cancel="onCropCancel"
  />
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 460;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--c-bg) 55%, transparent);
}

.dialog {
  width: min(420px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  overflow: auto;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  box-shadow: 0 12px 40px color-mix(in srgb, var(--c-bg) 50%, transparent);
}

.title {
  margin: 0 0 16px;
  font-size: 16px;
  color: var(--c-text);
}

.chooseGrid {
  display: grid;
  gap: 10px;
}

.choiceCard {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  color: var(--c-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.choiceCard:hover {
  border-color: var(--c-accent);
}

.choiceTitle {
  font-size: 14px;
  font-weight: 600;
}

.choiceHint {
  font-size: 12px;
  color: var(--c-text-muted);
  line-height: 1.4;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nameRow {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nameRow .field {
  flex: 1;
  min-width: 0;
}

.avatarArea {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  flex-shrink: 0;
}

.avatarCircle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  border: 2px solid var(--c-border);
  transition: border-color 0.15s, opacity 0.15s;
}

.avatarArea:hover .avatarCircle {
  border-color: var(--c-accent);
}

.avatarCircle.uploading {
  opacity: 0.5;
}

.avatarImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatarEmpty {
  color: var(--c-text-muted);
  opacity: 0.4;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--c-text);
  min-width: 0;
}

.toggleField {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--c-text);
  cursor: pointer;
  user-select: none;
}

.toggle {
  width: 36px;
  height: 20px;
  border-radius: 999px;
  background: var(--c-border);
  position: relative;
  flex-shrink: 0;
  transition: background 0.2s;
  cursor: pointer;
}

.toggle.on {
  background: var(--c-accent, var(--c-primary));
}

.toggleThumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle.on .toggleThumb {
  transform: translateX(16px);
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.pickStep {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.muted {
  font-size: 13px;
  color: var(--c-text-muted);
  margin: 0;
}

.pickList {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 320px;
  overflow-y: auto;
}
</style>
