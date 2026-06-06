<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import { buildPathWithReturn } from "@/composables/useNavigationReturn";
import BaseButton from "@/ui/base/BaseButton.vue";
import { useToastsStore } from "@/stores/toasts.store";

type Step = "choose" | "pc" | "additional" | "quick";

const props = defineProps<{
  open: boolean;
  roomId: number;
  gameRole: GameRole | "unknown";
  currentUserDisplayName?: string;
  submitting?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  createPc: [payload: {
    name: string;
    player_name: string;
    max_hp: number | null;
    armor_class: number | null;
    file: File | null;
    spawnAfterCreate?: boolean;
  }];
  createAdditional: [payload: {
    name: string;
    race: string;
    class_name: string;
    backstory: string;
    file: File | null;
    spawnAfterCreate?: boolean;
  }];
  createQuick: [payload: {
    name: string;
    max_hp: number | null;
    armor_class: number | null;
    backstory: string;
    file: File | null;
    spawnAfterCreate?: boolean;
  }];
}>();

const { t } = useI18n();
const router = useRouter();
const toasts = useToastsStore();

const isGm = computed(() => props.gameRole === "GM");

const step = ref<Step>("choose");
const pcName = ref("");
const pcMaxHp = ref("");
const pcAc = ref("");
const pcFile = ref<File | null>(null);

const addName = ref("");
const addRace = ref("");
const addClass = ref("");
const addBackstory = ref("");
const addFile = ref<File | null>(null);

const quickName = ref("");
const quickMaxHp = ref("");
const quickAc = ref("");
const quickBackstory = ref("");
const quickFile = ref<File | null>(null);

const spawnAfterCreate = ref(false);

const importKind = computed(() => (isGm.value ? "npc" : "pc_main"));

const fullEditorKind = computed(() => {
  if (isGm.value) return "npc";
  if (step.value === "additional") return "pc_additional";
  return "pc_main";
});

const title = computed(() => {
  if (step.value === "pc") return t("room.characters.pcQuickTitle");
  if (step.value === "additional") return t("room.characters.additionalTitle");
  if (step.value === "quick") return t("room.characters.gmQuickTitle");
  return t("room.characters.chooseTitle");
});

function resetForm() {
  step.value = "choose";
  pcName.value = "";
  pcMaxHp.value = "";
  pcAc.value = "";
  pcFile.value = null;
  addName.value = "";
  addRace.value = "";
  addClass.value = "";
  addBackstory.value = "";
  addFile.value = null;
  quickName.value = "";
  quickMaxHp.value = "";
  quickAc.value = "";
  quickBackstory.value = "";
  quickFile.value = null;
  spawnAfterCreate.value = false;
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

function onFileChange(event: Event, target: "pc" | "additional" | "quick") {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) return;
  if (target === "pc") pcFile.value = file;
  else if (target === "additional") addFile.value = file;
  else quickFile.value = file;
}

function parseOptionalInt(raw: string | number | null | undefined): number | null {
  if (raw == null) return null;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : null;
  const trimmed = String(raw).trim();
  if (!trimmed) return null;
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

function submitPc() {
  const name = pcName.value.trim();
  if (!name) {
    toasts.push({ message: t("table.assets.nameRequired"), tone: "warning" });
    return;
  }
  emit("createPc", {
    name,
    player_name: props.currentUserDisplayName?.trim() ?? "",
    max_hp: parseOptionalInt(pcMaxHp.value),
    armor_class: parseOptionalInt(pcAc.value),
    file: pcFile.value,
    spawnAfterCreate: spawnAfterCreate.value,
  });
}

function submitAdditional() {
  const name = addName.value.trim();
  if (!name) {
    toasts.push({ message: t("table.assets.nameRequired"), tone: "warning" });
    return;
  }
  emit("createAdditional", {
    name,
    race: addRace.value.trim(),
    class_name: addClass.value.trim(),
    backstory: addBackstory.value.trim(),
    file: addFile.value,
    spawnAfterCreate: spawnAfterCreate.value,
  });
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
    file: quickFile.value,
    spawnAfterCreate: spawnAfterCreate.value,
  });
}

function openImportDialog() {
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
          kind: importKind.value,
          openCharacterPopover: "1",
          openImport: "1",
        }
      : {
          roomId: String(props.roomId),
          kind: importKind.value,
          openCharacterPopover: "1",
          openImport: "1",
        };
  void router.push({ path: "/characters/new", query });
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
          kind: fullEditorKind.value,
          openCharacterPopover: "1",
        }
      : {
          roomId: String(props.roomId),
          kind: fullEditorKind.value,
          openCharacterPopover: "1",
        };
  void router.push({ path: "/characters/new", query });
  close();
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="backdrop" @click="close">
      <div class="dialog" @click.stop>
      <h3 class="title">{{ title }}</h3>

      <div v-if="step === 'choose'" class="chooseGrid">
        <template v-if="isGm">
          <button type="button" class="choiceCard" @click="openFullEditor">
            <span class="choiceTitle">{{ t("room.characters.gmFull") }}</span>
            <span class="choiceHint">{{ t("room.characters.gmFullHint") }}</span>
          </button>
          <button type="button" class="choiceCard" @click="step = 'quick'">
            <span class="choiceTitle">{{ t("room.characters.gmQuick") }}</span>
            <span class="choiceHint">{{ t("room.characters.gmQuickHint") }}</span>
          </button>
        </template>
        <template v-else>
          <button type="button" class="choiceCard" @click="step = 'pc'">
            <span class="choiceTitle">{{ t("room.characters.kindPc") }}</span>
            <span class="choiceHint">{{ t("room.characters.kindPcHint") }}</span>
          </button>
          <button type="button" class="choiceCard" @click="step = 'additional'">
            <span class="choiceTitle">{{ t("room.characters.kindAdditional") }}</span>
            <span class="choiceHint">{{ t("room.characters.kindAdditionalHint") }}</span>
          </button>
        </template>
        <button type="button" class="choiceCard importCard" @click="openImportDialog">
          <span class="choiceTitle">{{ t("character.import.fromRoom") }}</span>
          <span class="choiceHint">{{ t("character.import.hint") }}</span>
        </button>
      </div>

      <form v-else-if="step === 'pc'" class="form" @submit.prevent="submitPc">
        <label class="field">
          <span>{{ t("room.characters.nameLabel") }}</span>
          <input v-model="pcName" type="text" required />
        </label>
        <label class="field">
          <span>{{ t("room.characters.boundPlayer") }}</span>
          <input
            type="text"
            :value="currentUserDisplayName ?? ''"
            readonly
            class="readonlyInput"
          />
        </label>
        <div class="row">
          <label class="field">
            <span>{{ t("room.characters.maxHpLabel") }}</span>
            <input v-model="pcMaxHp" type="text" inputmode="numeric" />
          </label>
          <label class="field">
            <span>{{ t("room.characters.acLabel") }}</span>
            <input v-model="pcAc" type="text" inputmode="numeric" />
          </label>
        </div>
        <label class="field">
          <span>{{ t("room.characters.tokenImageLabel") }}</span>
          <input type="file" accept="image/*" @change="onFileChange($event, 'pc')" />
        </label>
        <label class="checkboxField">
          <input v-model="spawnAfterCreate" type="checkbox" />
          <span>{{ t("table.assets.spawnAfterCreate") }}</span>
        </label>
        <BaseButton type="button" variant="default" @click="openFullEditor">
          {{ t("room.characters.fullEditor") }}
        </BaseButton>
        <div class="actions">
          <BaseButton type="button" variant="default" @click="step = 'choose'">
            {{ t("common.back") }}
          </BaseButton>
          <BaseButton
            type="button"
            variant="primary"
            :disabled="submitting"
            :loading="submitting"
            @click="submitPc"
          >
            {{ t("room.characters.create") }}
          </BaseButton>
        </div>
      </form>

      <form v-else-if="step === 'quick'" class="form" @submit.prevent="submitQuick">
        <label class="field">
          <span>{{ t("room.characters.nameLabel") }}</span>
          <input v-model="quickName" type="text" required />
        </label>
        <div class="row">
          <label class="field">
            <span>{{ t("room.characters.maxHpLabel") }}</span>
            <input v-model="quickMaxHp" type="text" inputmode="numeric" />
          </label>
          <label class="field">
            <span>{{ t("room.characters.acLabel") }}</span>
            <input v-model="quickAc" type="text" inputmode="numeric" />
          </label>
        </div>
        <label class="field">
          <span>{{ t("room.characters.backstoryLabel") }}</span>
          <textarea v-model="quickBackstory" rows="4" />
        </label>
        <label class="field">
          <span>{{ t("room.characters.tokenImageLabel") }}</span>
          <input type="file" accept="image/*" @change="onFileChange($event, 'quick')" />
        </label>
        <label class="checkboxField">
          <input v-model="spawnAfterCreate" type="checkbox" />
          <span>{{ t("table.assets.spawnAfterCreate") }}</span>
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

      <form v-else class="form" @submit.prevent="submitAdditional">
        <label class="field">
          <span>{{ t("room.characters.nameLabel") }}</span>
          <input v-model="addName" type="text" required />
        </label>
        <div class="row">
          <label class="field">
            <span>{{ t("room.characters.raceLabel") }}</span>
            <input v-model="addRace" type="text" />
          </label>
          <label class="field">
            <span>{{ t("room.characters.classLabel") }}</span>
            <input v-model="addClass" type="text" />
          </label>
        </div>
        <label class="field">
          <span>{{ t("room.characters.backstoryLabel") }}</span>
          <textarea v-model="addBackstory" rows="4" />
        </label>
        <label class="field">
          <span>{{ t("room.characters.tokenImageLabel") }}</span>
          <input type="file" accept="image/*" @change="onFileChange($event, 'additional')" />
        </label>
        <label class="checkboxField">
          <input v-model="spawnAfterCreate" type="checkbox" />
          <span>{{ t("table.assets.spawnAfterCreate") }}</span>
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
            @click="submitAdditional"
          >
            {{ t("room.characters.create") }}
          </BaseButton>
        </div>
      </form>
      </div>
    </div>
  </Teleport>
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

.importCard {
  margin-top: 4px;
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

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--c-text);
}

.checkboxField {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text);
}

.field input,
.field textarea,
.readonlyInput {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg);
  color: var(--c-text);
}

.readonlyInput {
  opacity: 0.85;
  cursor: default;
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
</style>
