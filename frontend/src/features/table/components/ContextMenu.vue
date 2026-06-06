<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { RoomDrawing, RoomMap, RoomToken } from "@/infra/api/rooms.api";
import type { GameRole } from "@/features/room/types";
import type { TabletopSelection } from "@/features/table/types";
import { canInspectToken, canManageToken } from "@/features/table/utils/tokenDisplay";

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
  mapLayer: [action: "up" | "down" | "top" | "bottom"];
  tokenLayer: [action: "up" | "down" | "top" | "bottom"];
  drawingLayer: [action: "up" | "down" | "top" | "bottom"];
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

function onAction(fn: () => void) {
  fn();
  emit("close");
}
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
      :style="{ left: `${clientX}px`, top: `${clientY}px` }"
      @click.stop
    >
      <template v-if="selection?.type === 'map' && selectedMap && isGm">
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
          <button
            type="button"
            class="menuItem"
            :disabled="tokenLayerDisabled"
            :title="tokenLayerDisabled ? t('table.menu.layerSingleToken') : undefined"
            @click="onAction(() => emit('tokenLayer', 'up'))"
          >
            {{ t("table.menu.layerUp") }}
          </button>
          <button
            type="button"
            class="menuItem"
            :disabled="tokenLayerDisabled"
            :title="tokenLayerDisabled ? t('table.menu.layerSingleToken') : undefined"
            @click="onAction(() => emit('tokenLayer', 'down'))"
          >
            {{ t("table.menu.layerDown") }}
          </button>
          <button
            type="button"
            class="menuItem"
            :disabled="tokenLayerDisabled"
            :title="tokenLayerDisabled ? t('table.menu.layerSingleToken') : undefined"
            @click="onAction(() => emit('tokenLayer', 'top'))"
          >
            {{ t("table.menu.layerTop") }}
          </button>
          <button
            type="button"
            class="menuItem"
            :disabled="tokenLayerDisabled"
            :title="tokenLayerDisabled ? t('table.menu.layerSingleToken') : undefined"
            @click="onAction(() => emit('tokenLayer', 'bottom'))"
          >
            {{ t("table.menu.layerBottom") }}
          </button>
        </template>
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
  z-index: 300;
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

.menuDivider {
  height: 1px;
  margin: 4px 6px;
  background: var(--c-border);
}
</style>
