<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { ActiveInspection } from "@/features/room/composables/useRoomInspection";
import { getCharacter, type Character } from "@/infra/api/character.api";
import { ABILITY_KEYS, DND5E_SKILLS, fmtMod } from "@/features/character/constants";
import {
  getCharacterState,
  patchCharacterState,
  type CharacterState,
} from "@/infra/api/characterState.api";
import { patchRoomToken } from "@/infra/api/rooms.api";
import { getBackendErrorMessage } from "@/infra/http/client";
import { buildPathWithReturn } from "@/composables/useNavigationReturn";
import PanelSectionHeader from "@/ui/layout/PanelSectionHeader.vue";

const props = defineProps<{
  inspection: ActiveInspection;
  roomId: number;
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
}>();

const emit = defineEmits<{
  close: [];
  statePatched: [characterId: number, state: CharacterState];
  tokenRenamed: [tokenId: number, name: string];
}>();

const { t } = useI18n();
const router = useRouter();

const character = ref<Character | null>(null);
const state = ref<CharacterState | null>(null);
const loading = ref(false);
const saving = ref(false);
const renamingToken = ref(false);
const error = ref("");
const saveError = ref("");
const saveSuccess = ref(false);

const editCurrentHp = ref("");
const editMaxHp = ref("");
const editAc = ref("");
const editInstanceName = ref("");

const canEditState = computed(() => {
  if (!character.value) return false;
  if (props.gameRole === "GM") return true;
  if (props.gameRole === "PL") {
    return props.currentUserId != null && character.value.owner_id === props.currentUserId;
  }
  return false;
});

const canEditInstanceName = computed(
  () => props.gameRole === "GM" && props.inspection?.tokenId != null,
);

const canFullEdit = computed(() => {
  if (!character.value || props.currentUserId == null) return false;
  return character.value.owner_id === props.currentUserId;
});

const isDamageOnlyView = computed(() => {
  const s = state.value;
  if (!s) return false;
  return (
    s.current_hp == null &&
    s.max_hp == null &&
    s.armor_class == null &&
    s.damage_taken != null
  );
});

const displayName = computed(() => {
  if (props.inspection?.tokenInstanceName) return props.inspection.tokenInstanceName;
  return character.value?.name ?? "";
});

const identitySummary = computed(() => {
  const identity = character.value?.identity ?? {};
  const parts: string[] = [];
  const race = identity.race;
  if (typeof race === "string" && race.trim()) parts.push(race);
  const classes = identity.classes;
  if (Array.isArray(classes) && classes.length > 0) {
    const labels = classes
      .map((entry) => {
        if (!entry || typeof entry !== "object") return "";
        const name = (entry as { name?: string }).name ?? "";
        const level = (entry as { level?: number }).level;
        return level ? `${name} ${level}` : name;
      })
      .filter(Boolean);
    if (labels.length) parts.push(labels.join(" / "));
  }
  return parts.join(" · ");
});

const ABILITY_SHORT: Record<string, string> = {
  strength: "STR", dexterity: "DEX", constitution: "CON",
  intelligence: "INT", wisdom: "WIS", charisma: "CHA",
};

const primaryPanel = computed(() =>
  character.value?.token_configs?.find(tc => tc.is_primary)?.panel_initial ?? null
);

const savingThrows = computed(() => {
  const st = primaryPanel.value?.saving_throws as Record<string, number | null> | undefined;
  if (!st) return [];
  return ABILITY_KEYS
    .map(key => ({ key, value: st[key] ?? null }))
    .filter((item): item is { key: string; value: number } => item.value != null);
});

const skillRows = computed(() => {
  const sk = primaryPanel.value?.skills as Record<string, number | null> | undefined;
  if (!sk) return [];
  return DND5E_SKILLS
    .map(s => ({ key: s.key, labelKey: s.labelKey, value: sk[s.key] ?? null }))
    .filter((item): item is { key: string; labelKey: string; value: number } => item.value != null);
});

const inventoryItems = computed(() =>
  (primaryPanel.value?.items ?? []) as { name: string; quantity: number; notes: string }[]
);

const abilityScores = computed(() => {
  const abilities = character.value?.attributes?.abilities;
  if (!abilities || typeof abilities !== "object") return [];
  return Object.entries(abilities as Record<string, unknown>)
    .map(([key, value]) => {
      if (!value || typeof value !== "object") return null;
      const score = (value as { score?: number }).score;
      return score != null ? { key, score } : null;
    })
    .filter((item): item is { key: string; score: number } => item != null);
});

async function loadInspection() {
  const inspection = props.inspection;
  if (!inspection || inspection.kind !== "character") {
    character.value = null;
    state.value = null;
    return;
  }
  loading.value = true;
  error.value = "";
  saveError.value = "";
  saveSuccess.value = false;
  try {
    const [char, charState] = await Promise.all([
      getCharacter(inspection.characterId),
      getCharacterState(inspection.characterId),
    ]);
    character.value = char;
    state.value = charState;
    editCurrentHp.value =
      charState.current_hp != null ? String(charState.current_hp) : "";
    editMaxHp.value = charState.max_hp != null ? String(charState.max_hp) : "";
    editAc.value = charState.armor_class != null ? String(charState.armor_class) : "";
    editInstanceName.value = inspection.tokenInstanceName ?? char.name;
  } catch (e) {
    error.value = e instanceof Error ? e.message : t("table.inspector.loadFailed");
    character.value = null;
    state.value = null;
  } finally {
    loading.value = false;
  }
}

watch(() => props.inspection, loadInspection, { immediate: true });

watch([editCurrentHp, editMaxHp, editAc], () => {
  saveSuccess.value = false;
  saveError.value = "";
});

function parseOptionalInt(raw: string | number | null | undefined): number | null {
  if (raw == null) return null;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : null;
  const trimmed = String(raw).trim();
  if (!trimmed) return null;
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

async function saveState() {
  if (!character.value || !canEditState.value) return;
  saving.value = true;
  saveError.value = "";
  saveSuccess.value = false;
  try {
    const updated = await patchCharacterState(character.value.id, {
      current_hp: parseOptionalInt(editCurrentHp.value),
      max_hp: parseOptionalInt(editMaxHp.value),
      armor_class: parseOptionalInt(editAc.value),
    });
    state.value = updated;
    editCurrentHp.value =
      updated.current_hp != null ? String(updated.current_hp) : "";
    editMaxHp.value = updated.max_hp != null ? String(updated.max_hp) : "";
    editAc.value = updated.armor_class != null ? String(updated.armor_class) : "";
    saveSuccess.value = true;
    emit("statePatched", character.value.id, updated);
  } catch (e) {
    saveError.value = getBackendErrorMessage(e) || t("table.inspector.saveFailed");
  } finally {
    saving.value = false;
  }
}

async function saveInstanceName() {
  const tokenId = props.inspection?.tokenId;
  if (!canEditInstanceName.value || tokenId == null) return;
  const trimmed = editInstanceName.value.trim();
  if (!trimmed) return;
  renamingToken.value = true;
  try {
    await patchRoomToken(props.roomId, tokenId, { name: trimmed });
    emit("tokenRenamed", tokenId, trimmed);
  } catch (e) {
    saveError.value = getBackendErrorMessage(e) || t("table.inspector.saveFailed");
  } finally {
    renamingToken.value = false;
  }
}

function openFullEdit() {
  if (!character.value || !canFullEdit.value) return;
  void router.push(
    buildPathWithReturn(
      `/characters/${character.value.id}`,
      `/rooms/${props.roomId}`,
      true,
    ),
  );
}
</script>

<template>
  <section class="infoPanel">
    <div class="panelHead">
      <PanelSectionHeader :title="t('table.inspector.infoTitle')" />
      <button v-if="inspection" type="button" class="linkBtn" @click="emit('close')">
        {{ t("table.inspector.close") }}
      </button>
    </div>

    <p v-if="!inspection" class="empty">{{ t("table.inspector.infoEmpty") }}</p>
    <p v-else-if="loading" class="empty">{{ t("common.loading") }}</p>
    <p v-else-if="error" class="empty">{{ error }}</p>
    <template v-else-if="character">
      <header class="hero">
        <h3 v-if="!canEditInstanceName" class="heroTitle">{{ displayName }}</h3>
        <label v-else class="field instanceField">
          <span>{{ t("room.characters.instanceName") }}</span>
          <div class="inlineRow">
            <input v-model="editInstanceName" type="text" />
            <button
              type="button"
              class="saveBtn small"
              :disabled="renamingToken"
              @click="saveInstanceName"
            >
              {{ t("table.inspector.saveState") }}
            </button>
          </div>
        </label>
        <p v-if="character.player_name" class="heroSub">{{ character.player_name }}</p>
        <p v-if="identitySummary" class="heroSub">{{ identitySummary }}</p>
      </header>

      <div v-if="abilityScores.length" class="section">
        <h4 class="sectionTitle">{{ t("table.inspector.abilities") }}</h4>
        <div class="abilityGrid">
          <span v-for="item in abilityScores" :key="item.key" class="abilityChip">
            {{ item.key.toUpperCase() }} {{ item.score }}
          </span>
        </div>
      </div>

      <div v-if="savingThrows.length" class="section">
        <h4 class="sectionTitle">{{ t("table.inspector.savingThrows") }}</h4>
        <div class="chipRow">
          <span v-for="st in savingThrows" :key="st.key" class="compactChip">
            {{ ABILITY_SHORT[st.key] }} {{ fmtMod(st.value) }}
          </span>
        </div>
      </div>

      <div v-if="skillRows.length" class="section">
        <h4 class="sectionTitle">{{ t("table.inspector.skills") }}</h4>
        <div class="kvList">
          <div v-for="sk in skillRows" :key="sk.key" class="kvRow">
            <span class="kvLabel">{{ t(sk.labelKey) }}</span>
            <span class="kvVal">{{ fmtMod(sk.value) }}</span>
          </div>
        </div>
      </div>

      <div v-if="inventoryItems.length" class="section">
        <h4 class="sectionTitle">{{ t("table.inspector.inventory") }}</h4>
        <div class="kvList">
          <div v-for="(item, i) in inventoryItems" :key="i" class="kvRow">
            <span class="kvLabel">{{ item.name }}</span>
            <span class="kvVal muted">×{{ item.quantity }}</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h4 class="sectionTitle">{{ t("table.inspector.state") }}</h4>
        <div v-if="canEditState" class="stateForm">
          <label class="field">
            <span>{{ t("table.inspector.currentHp") }}</span>
            <input v-model="editCurrentHp" type="number" />
          </label>
          <label class="field">
            <span>{{ t("table.inspector.maxHp") }}</span>
            <input v-model="editMaxHp" type="number" />
          </label>
          <label class="field">
            <span>{{ t("table.inspector.ac") }}</span>
            <input v-model="editAc" type="number" />
          </label>
          <button type="button" class="saveBtn" :disabled="saving" @click="saveState">
            {{ t("table.inspector.saveState") }}
          </button>
          <p v-if="saveSuccess" class="saveHint success">{{ t("table.inspector.stateSaved") }}</p>
          <p v-else-if="saveError" class="saveHint error">{{ saveError }}</p>
        </div>
        <div v-else-if="state && isDamageOnlyView" class="stateReadonly">
          {{ t("room.characters.damageTaken") }}: {{ state.damage_taken }}
        </div>
        <div v-else-if="state" class="stateReadonly">
          HP {{ state.current_hp ?? "?" }}/{{ state.max_hp ?? "?" }} · AC
          {{ state.armor_class ?? "?" }}
        </div>
      </div>

      <button
        v-if="canFullEdit"
        type="button"
        class="fullEditBtn"
        @click="openFullEdit"
      >
        {{ t("table.inspector.fullEdit") }}
      </button>
    </template>
  </section>
</template>

<style scoped>
.infoPanel {
  display: grid;
  gap: 12px;
  min-height: 0;
  color: var(--c-text);
}

.empty {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
  line-height: 1.5;
}

.panelHead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.linkBtn {
  border: none;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 12px;
  cursor: pointer;
}

.heroTitle {
  margin: 0;
  font-size: 16px;
  color: var(--c-text);
}

.heroSub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--c-text-muted);
}

.section {
  display: grid;
  gap: 8px;
}

.sectionTitle {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--c-text-muted);
}

.abilityGrid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.abilityChip {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 8px;
  background: var(--c-bg-subtle);
  border: 1px solid var(--c-border);
  color: var(--c-text);
}

.stateForm {
  display: grid;
  gap: 8px;
}

.field {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--c-text);
}

.field input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
}

.inlineRow {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.inlineRow input {
  flex: 1;
  min-width: 80px;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
}

.saveBtn,
.fullEditBtn {
  justify-self: start;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  color: var(--c-text);
  cursor: pointer;
  font-size: 13px;
  font: inherit;
}

.saveBtn.small {
  padding: 4px 10px;
  font-size: 12px;
}

.saveBtn:hover:not(:disabled),
.fullEditBtn:hover {
  background: color-mix(in srgb, var(--c-primary) 12%, var(--c-bg-subtle));
}

.saveBtn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.saveHint {
  margin: 0;
  font-size: 12px;
}

.saveHint.success {
  color: var(--c-success, #16a34a);
}

.saveHint.error {
  color: var(--c-danger);
}

.stateReadonly {
  font-size: 13px;
  color: var(--c-text-muted);
}

.chipRow {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.compactChip {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 6px;
  background: var(--c-bg-subtle);
  border: 1px solid var(--c-border);
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
}

.kvList {
  display: grid;
  gap: 1px;
}

.kvRow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  padding: 2px 0;
  gap: 8px;
}

.kvLabel {
  color: var(--c-text-muted);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kvVal {
  font-weight: 500;
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.kvVal.muted {
  font-weight: 400;
  color: var(--c-text-muted);
}

.instanceField {
  margin-top: 0;
}
</style>
