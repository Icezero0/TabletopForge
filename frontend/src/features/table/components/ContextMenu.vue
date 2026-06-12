<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { RoomDrawing, RoomMap, RoomToken } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TabletopSelection } from "@/features/table/types";
import { canInspectToken, canManageToken } from "@/features/table/utils/tokenDisplay";
import {
  ABILITY_KEYS,
  ABILITY_LABEL_KEYS,
  DND5E_SKILLS,
  abilityMod,
  type AbilityKey,
} from "@/features/character/constants";
import type { DiceDraft } from "@/stores/dice.store";

type DicePreset = {
  id: string;
  name: string;
  formula: string;
  label: string;
  visibility: DiceDraft["visibility"];
};

const props = defineProps<{
  open: boolean;
  clientX: number;
  clientY: number;
  selection: TabletopSelection;
  maps: RoomMap[];
  tokens: RoomToken[];
  drawings: RoomDrawing[];
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
}>();

const emit = defineEmits<{
  close: [];
  deleteMap: [mapId: number];
  deleteDrawing: [drawingId: number];
  deleteToken: [tokenId: number];
  inspectToken: [tokenId: number];
  editTextDrawing: [drawingId: number];
  toggleMapLock: [mapId: number, locked: boolean];
  fillMapFog: [mapId: number];
  alignMapToGrid: [mapId: number];
  mapLayer: [action: "up" | "down" | "top" | "bottom"];
  tokenLayer: [action: "up" | "down" | "top" | "bottom"];
  drawingLayer: [action: "up" | "down" | "top" | "bottom"];
  openDiceRoll: [draft: DiceDraft];
}>();

const { t } = useI18n();

const selectedMap = computed(() => {
  if (props.selection?.type !== "map") return null;
  return props.maps.find((m) => m.id === props.selection!.id) ?? null;
});

const selectedDrawing = computed(() => {
  if (props.selection?.type !== "drawing") return null;
  return props.drawings.find((d) => d.id === props.selection!.id) ?? null;
});

const selectedToken = computed(() => {
  if (props.selection?.type !== "token") return null;
  return props.tokens.find((t) => t.id === props.selection!.id) ?? null;
});

const isGm = computed(() => props.gameRole === "GM");
const canEraseDrawing = computed(
  () => props.gameRole === "GM" || props.gameRole === "PL",
);

const canManageSelectedToken = computed(() => {
  const token = selectedToken.value;
  if (!token) return false;
  return canManageToken(
    token,
    props.gameRole,
    props.currentUserId,
    props.characterOwnerById,
  );
});

const canRollWithSelectedToken = computed(() => canManageSelectedToken.value);

const canInspectSelectedToken = computed(() => {
  const token = selectedToken.value;
  return token != null && canInspectToken(token);
});

const canEditTextDrawing = computed(
  () =>
    canEraseDrawing.value &&
    selectedDrawing.value?.kind === "text" &&
    Number(selectedDrawing.value.geometry.width) > 0 &&
    Number(selectedDrawing.value.geometry.height) > 0,
);

const layerDisabled = computed(() => props.maps.length <= 1);
const tokenLayerDisabled = computed(() => props.tokens.length <= 1);
const drawingLayerDisabled = computed(() => props.drawings.length <= 1);
const diceSubmenuOpen = ref(false);
const tokenLayerSubmenuOpen = ref(false);
const diceBranchOpen = ref<"abilityChecks" | "savingThrows" | "skills" | "presets" | null>(null);
const dicePresets = ref<DicePreset[]>([]);
const viewportHeight = ref(typeof window !== "undefined" ? window.innerHeight : 0);
const submenuDirections = ref<Record<string, "upward" | "downward">>({});

const verticalDirection = computed<"upward" | "downward">(() => {
  const above = props.clientY;
  const below = viewportHeight.value - props.clientY;
  return below < above ? "upward" : "downward";
});

const menuStyle = computed(() => {
  if (verticalDirection.value === "upward") {
    return {
      left: `${props.clientX}px`,
      bottom: `${Math.max(0, viewportHeight.value - props.clientY)}px`,
    };
  }
  return {
    left: `${props.clientX}px`,
    top: `${props.clientY}px`,
  };
});

function updateViewportHeight() {
  viewportHeight.value = window.innerHeight;
}

function isDicePreset(value: unknown): value is DicePreset {
  if (!value || typeof value !== "object") return false;
  const preset = value as Partial<DicePreset>;
  return (
    typeof preset.id === "string" &&
    typeof preset.name === "string" &&
    typeof preset.formula === "string" &&
    typeof preset.label === "string" &&
    (preset.visibility === "public" || preset.visibility === "blind")
  );
}

function loadDicePresets() {
  try {
    const raw = localStorage.getItem(`tabletopforge:dice-presets:${props.currentUserId ?? "guest"}`);
    const parsed = raw ? JSON.parse(raw) : [];
    dicePresets.value = Array.isArray(parsed) ? parsed.filter(isDicePreset) : [];
  } catch {
    dicePresets.value = [];
  }
}

function panelNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function formatD20Formula(bonus: number | null) {
  const value = bonus ?? 0;
  return `1d20${value > 0 ? `+${value}` : value < 0 ? `${value}` : ""}`;
}

function tokenPanel(token: RoomToken) {
  return token.panel as Record<string, unknown> | null | undefined;
}

function tokenAbilityScore(token: RoomToken, key: AbilityKey) {
  const scores = tokenPanel(token)?.ability_scores as Record<string, unknown> | undefined;
  return panelNumber(scores?.[key]) ?? 10;
}

function tokenProfBonus(token: RoomToken): number {
  return panelNumber(tokenPanel(token)?.proficiency_bonus) ?? 2;
}

function tokenSpellAttackBonus(token: RoomToken): number | null {
  const panel = tokenPanel(token);
  const raw = panel?.spell_attack_bonus;
  if (raw && typeof raw === "object") {
    return panelNumber((raw as { value?: unknown }).value);
  }
  return panelNumber(raw);
}

function tokenSavingThrowBonus(token: RoomToken, key: AbilityKey): number {
  const panel = tokenPanel(token);
  const saves = panel?.saving_throws as Record<string, unknown> | undefined;
  const override = panelNumber(saves?.[key]);
  if (override != null) return override;

  const profs = panel?.saving_throw_profs as Record<string, boolean> | undefined;
  return abilityMod(tokenAbilityScore(token, key)) + (profs?.[key] ? tokenProfBonus(token) : 0);
}

function tokenSkillBonus(token: RoomToken, key: string, ability: AbilityKey): number {
  const panel = tokenPanel(token);
  const skills = panel?.skills as Record<string, unknown> | undefined;
  const override = panelNumber(skills?.[key]);
  if (override != null) return override;

  const profs = panel?.skill_profs as Record<string, string> | undefined;
  const prof = profs?.[key] ?? "none";
  const multiplier = prof === "proficient" ? 1 : (prof === "expert" || prof === "expertise") ? 2 : 0;
  return abilityMod(tokenAbilityScore(token, ability)) + tokenProfBonus(token) * multiplier;
}

function userDiceDraft(): DiceDraft {
  return {
    actorType: "user",
    actorTokenId: null,
    actorDisplayName: "",
    label: "",
    formula: "1d20",
    visibility: "public",
  };
}

function tokenDiceDraft(
  token: RoomToken,
  label: string,
  formula: string,
  visibility: DiceDraft["visibility"] = "public",
): DiceDraft {
  return {
    actorType: "token",
    actorTokenId: token.id,
    actorDisplayName: token.name,
    label,
    formula,
    visibility,
  };
}

const tokenPrimaryDiceScenes = computed(() => {
  const token = selectedToken.value;
  if (!token) return [];
  return [
    { label: "攻击投掷", draft: tokenDiceDraft(token, "攻击投掷", "1d20") },
    {
      label: "法术攻击投掷",
      draft: tokenDiceDraft(
        token,
        "法术攻击投掷",
        formatD20Formula(tokenSpellAttackBonus(token)),
      ),
    },
  ];
});

const tokenUtilityDiceScenes = computed(() => {
  const token = selectedToken.value;
  if (!token) return [];
  return [
    { label: "数值投掷", draft: tokenDiceDraft(token, "数值投掷", "1d6") },
    { label: "自定义", draft: tokenDiceDraft(token, "", "1d20") },
  ];
});

const tokenSavingThrowScenes = computed(() => {
  const token = selectedToken.value;
  if (!token) return [];
  return ABILITY_KEYS.map((key) => {
    const label = `${t(ABILITY_LABEL_KEYS[key])}豁免`;
    return {
      label,
      draft: tokenDiceDraft(token, label, formatD20Formula(tokenSavingThrowBonus(token, key))),
    };
  });
});

const tokenAbilityCheckScenes = computed(() => {
  const token = selectedToken.value;
  if (!token) return [];
  return ABILITY_KEYS.map((key) => {
    const label = `${t(ABILITY_LABEL_KEYS[key])}检定`;
    return {
      label,
      draft: tokenDiceDraft(token, label, formatD20Formula(abilityMod(tokenAbilityScore(token, key)))),
    };
  });
});

const tokenSkillScenes = computed(() => {
  const token = selectedToken.value;
  if (!token) return [];
  return DND5E_SKILLS.map((skill) => {
    const label = `${t(skill.labelKey)}检定`;
    return {
      label,
      draft: tokenDiceDraft(
        token,
        label,
        formatD20Formula(tokenSkillBonus(token, skill.key, skill.ability)),
      ),
    };
  });
});

const tokenPresetDiceScenes = computed(() => {
  const token = selectedToken.value;
  if (!token) return [];
  return dicePresets.value.map((preset) => ({
    label: preset.name,
    formula: preset.formula,
    draft: tokenDiceDraft(token, preset.label, preset.formula, preset.visibility),
  }));
});

function directionForHost(host: Element | null): "upward" | "downward" {
  if (!host) return verticalDirection.value;
  const rect = host.getBoundingClientRect();
  const anchorY = rect.top + rect.height / 2;
  const above = anchorY;
  const below = viewportHeight.value - anchorY;
  return below < above ? "upward" : "downward";
}

function updateSubmenuDirection(key: string, event: MouseEvent) {
  submenuDirections.value = {
    ...submenuDirections.value,
    [key]: directionForHost((event.currentTarget as HTMLElement).closest(".submenuHost")),
  };
}

function submenuDirectionClass(key: string) {
  return submenuDirections.value[key] ?? verticalDirection.value;
}

function toggleDiceSubmenu(event: MouseEvent) {
  updateSubmenuDirection("dice", event);
  diceSubmenuOpen.value = !diceSubmenuOpen.value;
  if (diceSubmenuOpen.value) tokenLayerSubmenuOpen.value = false;
}

function toggleTokenLayerSubmenu(event: MouseEvent) {
  updateSubmenuDirection("tokenLayer", event);
  tokenLayerSubmenuOpen.value = !tokenLayerSubmenuOpen.value;
  if (tokenLayerSubmenuOpen.value) {
    diceSubmenuOpen.value = false;
    diceBranchOpen.value = null;
  }
}

function toggleDiceBranch(branch: "abilityChecks" | "savingThrows" | "skills" | "presets", event: MouseEvent) {
  updateSubmenuDirection(branch, event);
  diceBranchOpen.value = diceBranchOpen.value === branch ? null : branch;
}

function onAction(fn: () => void) {
  fn();
  diceSubmenuOpen.value = false;
  tokenLayerSubmenuOpen.value = false;
  diceBranchOpen.value = null;
  emit("close");
}

watch(
  () => props.open,
  (open) => {
    if (open) loadDicePresets();
    if (!open) diceSubmenuOpen.value = false;
    if (!open) tokenLayerSubmenuOpen.value = false;
    if (!open) diceBranchOpen.value = null;
    if (!open) submenuDirections.value = {};
  },
);

watch(
  () => props.selection,
  () => {
    diceSubmenuOpen.value = false;
    tokenLayerSubmenuOpen.value = false;
    diceBranchOpen.value = null;
    submenuDirections.value = {};
  },
);

onMounted(() => {
  updateViewportHeight();
  loadDicePresets();
  window.addEventListener("resize", updateViewportHeight);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateViewportHeight);
});
</script>

<template>
  <div
    v-if="open"
    class="contextMenuBackdrop"
    @click="emit('close')"
    @contextmenu.prevent="emit('close')"
  >
    <menu
      class="contextMenu"
      :class="verticalDirection"
      :style="menuStyle"
      @click.stop
    >
      <template v-if="selection?.type === 'map' && selectedMap && isGm">
        <button
          type="button"
          class="menuItem"
          @click="onAction(() => emit('fillMapFog', selectedMap!.id))"
        >
          填充战争迷雾
        </button>
        <div class="menuDivider" />
        <button
          v-if="selectedMap.map_grid_size != null"
          type="button"
          class="menuItem"
          @click="onAction(() => emit('alignMapToGrid', selectedMap!.id))"
        >
          {{ t("table.menu.alignMapToGrid") }}
        </button>
        <button
          type="button"
          class="menuItem"
          @click="onAction(() => emit('toggleMapLock', selectedMap!.id, !selectedMap!.locked))"
        >
          {{ selectedMap.locked ? t("table.tools.mapUnlock") : t("table.tools.mapLock") }}
        </button>
        <button
          type="button"
          class="menuItem danger"
          @click="onAction(() => emit('deleteMap', selectedMap!.id))"
        >
          {{ t("table.menu.deleteMap") }}
        </button>
        <div class="menuDivider" />
        <button
          type="button"
          class="menuItem"
          :disabled="layerDisabled"
          :title="layerDisabled ? t('table.menu.layerSingleMap') : undefined"
          @click="onAction(() => emit('mapLayer', 'up'))"
        >
          {{ t("table.menu.layerUp") }}
        </button>
        <button
          type="button"
          class="menuItem"
          :disabled="layerDisabled"
          :title="layerDisabled ? t('table.menu.layerSingleMap') : undefined"
          @click="onAction(() => emit('mapLayer', 'down'))"
        >
          {{ t("table.menu.layerDown") }}
        </button>
      </template>
      <template v-else-if="selection?.type === 'token' && selectedToken">
        <div
          v-if="canRollWithSelectedToken"
          class="submenuHost"
          :class="submenuDirectionClass('dice')"
        >
          <button
            type="button"
            class="menuItem submenuTrigger"
            :class="{ active: diceSubmenuOpen }"
            @click.stop="toggleDiceSubmenu"
          >
            <span>掷骰</span>
            <span class="submenuArrow">›</span>
          </button>
          <div v-if="diceSubmenuOpen" class="submenu" @click.stop>
            <div
              class="submenuHost"
              :class="submenuDirectionClass('presets')"
            >
              <button
                type="button"
                class="menuItem submenuTrigger"
                :class="{ active: diceBranchOpen === 'presets' }"
                @click.stop="toggleDiceBranch('presets', $event)"
              >
                <span>使用预设</span>
                <span class="submenuArrow">›</span>
              </button>
              <div
                v-if="diceBranchOpen === 'presets'"
                class="submenu nestedSubmenu compactSubmenu presetSubmenu"
                @click.stop
              >
                <button
                  v-for="scene in tokenPresetDiceScenes"
                  :key="scene.label"
                  type="button"
                  class="menuItem presetMenuItem"
                  @click="onAction(() => emit('openDiceRoll', scene.draft))"
                >
                  <span class="presetName">{{ scene.label }}</span>
                  <span class="presetFormula">{{ scene.formula }}</span>
                </button>
                <button v-if="tokenPresetDiceScenes.length === 0" type="button" class="menuItem" disabled>
                  暂无预设
                </button>
              </div>
            </div>
            <button
              v-for="scene in tokenPrimaryDiceScenes"
              :key="scene.label"
              type="button"
              class="menuItem"
              @click="onAction(() => emit('openDiceRoll', scene.draft))"
            >
              {{ scene.label }}
            </button>
            <div
              class="submenuHost"
              :class="submenuDirectionClass('savingThrows')"
            >
              <button
                type="button"
                class="menuItem submenuTrigger"
                :class="{ active: diceBranchOpen === 'savingThrows' }"
                @click.stop="toggleDiceBranch('savingThrows', $event)"
              >
                <span>豁免检定</span>
                <span class="submenuArrow">›</span>
              </button>
              <div
                v-if="diceBranchOpen === 'savingThrows'"
                class="submenu nestedSubmenu compactSubmenu"
                @click.stop
              >
                <button
                  v-for="scene in tokenSavingThrowScenes"
                  :key="scene.label"
                  type="button"
                  class="menuItem"
                  @click="onAction(() => emit('openDiceRoll', scene.draft))"
                >
                  {{ scene.label }}
                </button>
              </div>
            </div>
            <div
              class="submenuHost"
              :class="submenuDirectionClass('abilityChecks')"
            >
              <button
                type="button"
                class="menuItem submenuTrigger"
                :class="{ active: diceBranchOpen === 'abilityChecks' }"
                @click.stop="toggleDiceBranch('abilityChecks', $event)"
              >
                <span>六维检定</span>
                <span class="submenuArrow">›</span>
              </button>
              <div
                v-if="diceBranchOpen === 'abilityChecks'"
                class="submenu nestedSubmenu compactSubmenu"
                @click.stop
              >
                <button
                  v-for="scene in tokenAbilityCheckScenes"
                  :key="scene.label"
                  type="button"
                  class="menuItem"
                  @click="onAction(() => emit('openDiceRoll', scene.draft))"
                >
                  {{ scene.label }}
                </button>
              </div>
            </div>
            <div
              class="submenuHost"
              :class="submenuDirectionClass('skills')"
            >
              <button
                type="button"
                class="menuItem submenuTrigger"
                :class="{ active: diceBranchOpen === 'skills' }"
                @click.stop="toggleDiceBranch('skills', $event)"
              >
                <span>技能检定</span>
                <span class="submenuArrow">›</span>
              </button>
              <div
                v-if="diceBranchOpen === 'skills'"
                class="submenu nestedSubmenu compactSubmenu"
                @click.stop
              >
                <button
                  v-for="scene in tokenSkillScenes"
                  :key="scene.label"
                  type="button"
                  class="menuItem"
                  @click="onAction(() => emit('openDiceRoll', scene.draft))"
                >
                  {{ scene.label }}
                </button>
              </div>
            </div>
            <button
              v-for="scene in tokenUtilityDiceScenes"
              :key="scene.label"
              type="button"
              class="menuItem"
              @click="onAction(() => emit('openDiceRoll', scene.draft))"
            >
              {{ scene.label }}
            </button>
          </div>
        </div>
        <div v-if="canRollWithSelectedToken" class="menuDivider" />
        <button
          v-if="canInspectSelectedToken"
          type="button"
          class="menuItem"
          @click="onAction(() => emit('inspectToken', selectedToken!.id))"
        >
          {{ t("table.menu.inspectInfo") }}
        </button>
        <template v-if="canManageSelectedToken">
          <button
            type="button"
            class="menuItem danger"
            @click="onAction(() => emit('deleteToken', selectedToken!.id))"
          >
            {{ t("table.menu.deleteToken") }}
          </button>
          <div class="menuDivider" />
          <div
            class="submenuHost"
            :class="submenuDirectionClass('tokenLayer')"
          >
            <button
              type="button"
              class="menuItem submenuTrigger"
              :class="{ active: tokenLayerSubmenuOpen }"
              :disabled="tokenLayerDisabled"
              :title="tokenLayerDisabled ? t('table.menu.layerSingleToken') : undefined"
              @click.stop="toggleTokenLayerSubmenu"
            >
              <span>{{ t("table.menu.layer") }}</span>
              <span class="submenuArrow">›</span>
            </button>
            <div v-if="tokenLayerSubmenuOpen" class="submenu" @click.stop>
              <button
                type="button"
                class="menuItem"
                @click="onAction(() => emit('tokenLayer', 'up'))"
              >
                {{ t("table.menu.layerUp") }}
              </button>
              <button
                type="button"
                class="menuItem"
                @click="onAction(() => emit('tokenLayer', 'down'))"
              >
                {{ t("table.menu.layerDown") }}
              </button>
              <button
                type="button"
                class="menuItem"
                @click="onAction(() => emit('tokenLayer', 'top'))"
              >
                {{ t("table.menu.layerTop") }}
              </button>
              <button
                type="button"
                class="menuItem"
                @click="onAction(() => emit('tokenLayer', 'bottom'))"
              >
                {{ t("table.menu.layerBottom") }}
              </button>
            </div>
          </div>
        </template>
      </template>
      <template v-else-if="!selection">
        <button
          type="button"
          class="menuItem"
          @click="onAction(() => emit('openDiceRoll', userDiceDraft()))"
        >
          掷骰
        </button>
      </template>
      <template v-else-if="selection?.type === 'drawing' && canEraseDrawing">
        <button
          v-if="canEditTextDrawing"
          type="button"
          class="menuItem"
          @click="onAction(() => emit('editTextDrawing', selection!.id))"
        >
          {{ t("table.menu.editTextDrawing") }}
        </button>
        <button
          type="button"
          class="menuItem danger"
          @click="onAction(() => emit('deleteDrawing', selection!.id))"
        >
          {{ t("table.menu.deleteDrawing") }}
        </button>
        <div class="menuDivider" />
        <button
          type="button"
          class="menuItem"
          :disabled="drawingLayerDisabled"
          :title="drawingLayerDisabled ? t('table.menu.layerSingleDrawing') : undefined"
          @click="onAction(() => emit('drawingLayer', 'up'))"
        >
          {{ t("table.menu.layerUp") }}
        </button>
        <button
          type="button"
          class="menuItem"
          :disabled="drawingLayerDisabled"
          :title="drawingLayerDisabled ? t('table.menu.layerSingleDrawing') : undefined"
          @click="onAction(() => emit('drawingLayer', 'down'))"
        >
          {{ t("table.menu.layerDown") }}
        </button>
        <button
          type="button"
          class="menuItem"
          :disabled="drawingLayerDisabled"
          :title="drawingLayerDisabled ? t('table.menu.layerSingleDrawing') : undefined"
          @click="onAction(() => emit('drawingLayer', 'top'))"
        >
          {{ t("table.menu.layerTop") }}
        </button>
        <button
          type="button"
          class="menuItem"
          :disabled="drawingLayerDisabled"
          :title="drawingLayerDisabled ? t('table.menu.layerSingleDrawing') : undefined"
          @click="onAction(() => emit('drawingLayer', 'bottom'))"
        >
          {{ t("table.menu.layerBottom") }}
        </button>
      </template>
    </menu>
  </div>
</template>

<style scoped>
.contextMenuBackdrop {
  position: fixed;
  inset: 0;
  z-index: 920;
}

.contextMenu {
  position: fixed;
  min-width: 160px;
  margin: 0;
  padding: 6px;
  list-style: none;
  border-radius: 10px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  box-shadow: 0 8px 28px color-mix(in srgb, var(--c-bg) 45%, transparent);
}

.menuItem {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text);
  font-size: 13px;
  cursor: pointer;
}

.menuItem:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 12%, transparent);
}

.menuItem:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.menuItem.danger {
  color: var(--c-danger, #dc2626);
}

.submenuHost {
  position: relative;
}

.submenuTrigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.submenuTrigger.active {
  background: color-mix(in srgb, var(--c-primary) 14%, transparent);
}

.submenuArrow {
  color: var(--c-text-muted);
  font-size: 16px;
  line-height: 1;
}

.submenu {
  position: absolute;
  top: 0;
  left: calc(100% + 6px);
  min-width: 150px;
  padding: 6px;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  background: var(--c-surface);
  box-shadow: 0 8px 28px color-mix(in srgb, var(--c-bg) 45%, transparent);
}

.submenuHost.upward > .submenu {
  top: auto;
  bottom: 0;
}

.nestedSubmenu {
  top: -6px;
}

.submenuHost.upward > .nestedSubmenu {
  top: auto;
  bottom: -6px;
}

.compactSubmenu {
  max-height: min(360px, calc(100vh - 48px));
  overflow-y: auto;
}

.compactSubmenu .menuItem {
  padding-block: 7px;
}

.presetSubmenu {
  min-width: 180px;
}

.presetMenuItem {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 2px;
}

.presetName,
.presetFormula {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.presetName {
  font-weight: 700;
}

.presetFormula {
  color: var(--c-text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}

.menuDivider {
  height: 1px;
  margin: 4px 6px;
  background: var(--c-border);
}
</style>
