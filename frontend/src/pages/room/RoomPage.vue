<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  getRoomById,
  getRoomMembers,
  patchRoom,
  type Room,
  type RoomPatchPayload,
} from "@/infra/api/rooms.api";
import BaseLayout from "@/ui/layout/BaseLayout.vue";
import RoomChatTab from "@/features/room/components/workspace/RoomChatTab.vue";
import type { GameRole, MemberStatus, RoomRole } from "@/features/room/types";
import type { ChatSegment } from "@/features/chat/types";
import { useRoomJoinRequests } from "@/features/room/composables/useRoomJoinRequests";
import { useRoomMemberActions } from "@/features/room/composables/useRoomMemberActions";
import { useRoomRealtimeSession } from "@/features/room/composables/useRoomRealtimeSession";
import type { RoomRealtimeSessionClosed } from "@/infra/realtime/roomRealtime";
import BottomAssetBar from "@/features/table/components/BottomAssetBar.vue";
import FloatingPanel from "@/features/table/components/FloatingPanel.vue";
import GovernanceDock from "@/features/table/components/GovernanceDock.vue";
import InfoPanel from "@/features/table/components/InfoPanel.vue";
import MapViewport from "@/features/table/components/MapViewport.vue";
import ContextMenu from "@/features/table/components/ContextMenu.vue";
import DrawToolStrip from "@/features/table/components/DrawToolStrip.vue";
import PersonalMemo from "@/features/table/components/PersonalMemo.vue";
import TableStage from "@/features/table/components/TableStage.vue";
import TopToolBar from "@/features/table/components/TopToolBar.vue";
import { useDrawingTools } from "@/features/table/composables/useDrawingTools";
import { useTextDrawingEdit } from "@/features/table/composables/useTextDrawingEdit";
import { useGridScale } from "@/features/table/composables/useGridScale";
import { useTabletopSelection } from "@/features/table/composables/useTabletopSelection";
import { useTableToolMode } from "@/features/table/composables/useTableToolMode";
import { useTabletopPointer } from "@/features/table/composables/useTabletopPointer";
import { nextDrawingZIndex } from "@/features/table/drawingTypes";
import { computeMapScaleForViewport } from "@/features/table/utils/mapScale";
import { useMessagesStore } from "@/stores/messages.store";
import { useTabletopStore } from "@/stores/tabletop.store";
import { useEntitiesStore } from "@/stores/entities.store";
import { useAuthStore } from "@/stores/auth.store";
import { useToastsStore } from "@/stores/toasts.store";
import { getBackendErrorMessage } from "@/infra/http/client";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const entitiesStore = useEntitiesStore();
const messagesStore = useMessagesStore();
const tabletopStore = useTabletopStore();
const toasts = useToastsStore();

type RoomRoleState = RoomRole | "unknown";

const room = ref<Room | null>(null);
const isLoading = ref(false);
const error = ref("");
const membersLoading = ref(false);
const membersError = ref("");
const settingsSaving = ref(false);
const currentUserRoomRole = ref<RoomRoleState>("unknown");
const currentUserGameRole = ref<GameRole | "unknown">("unknown");

const roomId = computed(() => {
  const raw = route.params.id;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
});

const canManageRoomRequests = computed(() =>
  currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
const canManageRoomSettings = computed(() =>
  currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
const currentUserIsOwner = computed(() => currentUserRoomRole.value === "owner");
const currentUserCanRemoveMembers = computed(() =>
  currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
const memberDangerActionDisabled = computed(() => currentUserRoomRole.value === "unknown");

const canAddMap = computed(() => currentUserGameRole.value === "GM");
const canAddCharacter = computed(() =>
  currentUserGameRole.value === "GM" || currentUserGameRole.value === "PL");
const canEditGrid = computed(() => currentUserGameRole.value === "GM");

const { toolMode, disabledTools } = useTableToolMode(currentUserGameRole);
const {
  gridCellPx,
  gridCellFt,
  scaleBarCells,
  canIncrease: canIncreaseGrid,
  canDecrease: canDecreaseGrid,
  increase: increaseGrid,
  decrease: decreaseGrid,
} = useGridScale(roomId, { canEdit: canEditGrid });

const tabletopMaps = computed(() => tabletopStore.getMaps(roomId.value));
const tabletopDrawings = computed(() => tabletopStore.getDrawings(roomId.value));
const { selection, selectMap, selectDrawing, clearSelection } = useTabletopSelection();
const mapNaturalSizes = ref<Record<number, { w: number; h: number }>>({});
const mapViewportRef = ref<InstanceType<typeof MapViewport> | null>(null);
const mapUploadInput = ref<HTMLInputElement | null>(null);
const mapUploading = ref(false);

const selectedMap = computed(() => {
  if (selection.value?.type !== "map") return null;
  return tabletopMaps.value.find((map) => map.id === selection.value!.id) ?? null;
});

const selectedMapNaturalSize = computed(() => {
  if (selection.value?.type !== "map") return { w: 0, h: 0 };
  return mapNaturalSizes.value[selection.value.id] ?? { w: 0, h: 0 };
});

function fallbackMapId(maps: typeof tabletopMaps.value) {
  if (!maps.length) return null;
  const top = [...maps].sort((a, b) => b.z_index - a.z_index || b.id - a.id)[0];
  return top?.id ?? null;
}

const canDraw = computed(
  () => currentUserGameRole.value === "GM" || currentUserGameRole.value === "PL",
);
const drawingLayerInteractive = computed(() => {
  if (!canDraw.value) return false;
  const mode = toolMode.value;
  return mode === "draw" || mode === "select" || mode === "hand";
});

const {
  subTool,
  strokeColor,
  strokeWidth,
  fontSize,
  preview: drawPreview,
  textPlacement,
  pointerDown: drawPointerDown,
  pointerMove: drawPointerMove,
  pointerUp: drawPointerUp,
  confirmText,
  cancelText,
} = useDrawingTools({
  drawings: tabletopDrawings,
  gridCellPx,
  gridCellFt,
  onCommit: async (payload) => {
    if (!roomId.value) return;
    await tabletopStore.createDrawing(roomId.value, {
      ...payload,
      z_index: nextDrawingZIndex(tabletopDrawings.value),
    });
  },
  onDeleteIds: async (ids) => {
    if (!roomId.value || !ids.length) return;
    await tabletopStore.removeDrawings(roomId.value, ids);
  },
});

const { textEdit, beginEdit: beginTextEdit, cancelEdit: cancelTextEdit, confirmEdit: confirmTextEdit } =
  useTextDrawingEdit({
    drawings: tabletopDrawings,
    onUpdate: (drawingId, payload) => {
      scheduleDrawingPatch(drawingId, payload);
    },
  });

const editingDrawingId = computed(() => textEdit.value?.drawingId ?? null);

watch(textPlacement, (place) => {
  if (place) cancelTextEdit();
});

watch(textEdit, (edit) => {
  if (edit) cancelText();
});

const contextMenuOpen = ref(false);
const contextMenuX = ref(0);
const contextMenuY = ref(0);

watch(tabletopMaps, (maps) => {
  if (!maps.length) {
    clearSelection();
    mapNaturalSizes.value = {};
    return;
  }
  const validIds = new Set(maps.map((m) => m.id));
  const nextSizes: Record<number, { w: number; h: number }> = {};
  for (const id of Object.keys(mapNaturalSizes.value)) {
    const mapId = Number(id);
    if (validIds.has(mapId)) {
      nextSizes[mapId] = mapNaturalSizes.value[mapId]!;
    }
  }
  mapNaturalSizes.value = nextSizes;

  if (selection.value?.type === "map" && !validIds.has(selection.value.id)) {
    const id = fallbackMapId(maps);
    if (id != null) selectMap(id);
    return;
  }
  if (!selection.value) {
    const id = fallbackMapId(maps);
    if (id != null) selectMap(id);
  }
});

let mapPatchTimer: ReturnType<typeof setTimeout> | null = null;
const pendingMapPatch = ref<{
  mapId: number;
  payload: { x?: number; y?: number; scale?: number; locked?: boolean };
} | null>(null);

function scheduleMapPatch(
  mapId: number,
  payload: { x?: number; y?: number; scale?: number; locked?: boolean },
) {
  if (pendingMapPatch.value?.mapId === mapId) {
    pendingMapPatch.value = {
      mapId,
      payload: { ...pendingMapPatch.value.payload, ...payload },
    };
  } else {
    pendingMapPatch.value = { mapId, payload };
  }
  if (mapPatchTimer) clearTimeout(mapPatchTimer);
  mapPatchTimer = setTimeout(() => {
    void flushMapPatch();
  }, 150);
}

async function flushMapPatch() {
  const pending = pendingMapPatch.value;
  pendingMapPatch.value = null;
  mapPatchTimer = null;
  if (!pending || !roomId.value) return;
  try {
    await tabletopStore.updateMap(roomId.value, pending.mapId, pending.payload);
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.uploadFailed"),
      tone: "danger",
    });
    void tabletopStore.loadSnapshot(roomId.value);
  }
}

function handleSelectMap(mapId: number) {
  if (toolMode.value !== "select" && toolMode.value !== "hand") return;
  if (currentUserGameRole.value !== "GM") return;
  selectMap(mapId);
}

function handleMapContextMenu(mapId: number, event: MouseEvent) {
  if (toolMode.value === "draw") return;
  if (currentUserGameRole.value !== "GM") return;
  selectMap(mapId);
  contextMenuX.value = event.clientX;
  contextMenuY.value = event.clientY;
  contextMenuOpen.value = true;
}

function handleSelectDrawing(drawingId: number) {
  if (toolMode.value !== "select" && toolMode.value !== "hand") return;
  if (!canDraw.value) return;
  selectDrawing(drawingId);
}

function handleEditTextDrawing(drawingId: number) {
  if (toolMode.value !== "select" && toolMode.value !== "hand") return;
  if (!canDraw.value) return;
  cancelText();
  beginTextEdit(drawingId);
  selectDrawing(drawingId);
  closeContextMenu();
}

function handleTextPlacementResize(width: number) {
  if (!textPlacement.value) return;
  textPlacement.value = { ...textPlacement.value, width };
}

let drawingPatchTimer: ReturnType<typeof setTimeout> | null = null;
const pendingDrawingPatch = ref<{
  drawingId: number;
  payload: { geometry?: Record<string, unknown>; style?: Record<string, unknown> };
} | null>(null);

function scheduleDrawingPatch(
  drawingId: number,
  payload: { geometry?: Record<string, unknown>; style?: Record<string, unknown> },
) {
  const drawing = tabletopDrawings.value.find((d) => d.id === drawingId);
  if (!drawing || !roomId.value) return;
  tabletopStore.applyDrawingUpdated(roomId.value, {
    ...drawing,
    geometry: payload.geometry ?? drawing.geometry,
    style: payload.style ? { ...drawing.style, ...payload.style } : drawing.style,
  });
  if (pendingDrawingPatch.value?.drawingId === drawingId) {
    pendingDrawingPatch.value = {
      drawingId,
      payload: { ...pendingDrawingPatch.value.payload, ...payload },
    };
  } else {
    pendingDrawingPatch.value = { drawingId, payload };
  }
  if (drawingPatchTimer) clearTimeout(drawingPatchTimer);
  drawingPatchTimer = setTimeout(() => {
    void flushDrawingPatch();
  }, 150);
}

async function flushDrawingPatch() {
  const pending = pendingDrawingPatch.value;
  pendingDrawingPatch.value = null;
  drawingPatchTimer = null;
  if (!pending || !roomId.value) return;
  try {
    await tabletopStore.updateDrawing(roomId.value, pending.drawingId, pending.payload);
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
    void tabletopStore.loadSnapshot(roomId.value);
  }
}

function handlePatchDrawing(
  drawingId: number,
  payload: { geometry?: Record<string, unknown>; style?: Record<string, unknown> },
) {
  scheduleDrawingPatch(drawingId, payload);
}

function handleMapNaturalSize(payload: { mapId: number; w: number; h: number }) {
  mapNaturalSizes.value = {
    ...mapNaturalSizes.value,
    [payload.mapId]: { w: payload.w, h: payload.h },
  };
}

function handleContextMenu(event: MouseEvent) {
  if (toolMode.value === "draw") return;
  if (currentUserGameRole.value !== "GM") return;
  contextMenuX.value = event.clientX;
  contextMenuY.value = event.clientY;
  contextMenuOpen.value = true;
}

function closeContextMenu() {
  contextMenuOpen.value = false;
}

function handleClearSelection() {
  clearSelection();
  closeContextMenu();
}

async function handleContextDeleteMap(mapId: number) {
  if (!roomId.value) return;
  try {
    await tabletopStore.removeMap(roomId.value, mapId);
    clearSelection();
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
  }
}

async function handleContextToggleMapLock(mapId: number, locked: boolean) {
  if (!roomId.value) return;
  try {
    await tabletopStore.updateMap(roomId.value, mapId, { locked });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
  }
}

async function handleContextDeleteDrawing(drawingId: number) {
  if (!roomId.value) return;
  try {
    await tabletopStore.removeDrawings(roomId.value, [drawingId]);
    if (selection.value?.type === "drawing" && selection.value.id === drawingId) {
      clearSelection();
    }
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
  }
}

async function handleContextMapLayer(action: "up" | "down" | "top" | "bottom") {
  const map = selectedMap.value;
  if (!map || !roomId.value || tabletopMaps.value.length <= 1) return;
  const sorted = [...tabletopMaps.value].sort((a, b) => a.z_index - b.z_index);
  const idx = sorted.findIndex((m) => m.id === map.id);
  if (idx < 0) return;
  let target = map.z_index;
  if (action === "up" && idx < sorted.length - 1) {
    target = sorted[idx + 1]!.z_index;
  } else if (action === "down" && idx > 0) {
    target = sorted[idx - 1]!.z_index;
  } else if (action === "top") {
    target = Math.max(...sorted.map((m) => m.z_index)) + 1;
  } else if (action === "bottom") {
    target = Math.min(...sorted.map((m) => m.z_index)) - 1;
  }
  if (target === map.z_index) return;
  try {
    await tabletopStore.updateMap(roomId.value, map.id, { z_index: target });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
  }
}

function handlePatchMap(
  mapId: number,
  payload: { x?: number; y?: number; scale?: number; locked?: boolean },
) {
  const map = tabletopMaps.value.find((m) => m.id === mapId);
  if (!map) return;
  tabletopStore.applyMapUpdated(roomId.value, { ...map, ...payload });
  scheduleMapPatch(mapId, payload);
}

function readImageDimensions(file: File) {
  return new Promise<{ w: number; h: number }>((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve({ w: img.naturalWidth, h: img.naturalHeight });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Failed to read image"));
    };
    img.src = url;
  });
}

function handleAddMapClick() {
  mapUploadInput.value?.click();
}

async function handleMapFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || !roomId.value) return;
  if (!file.type.startsWith("image/")) {
    toasts.push({ message: t("table.assets.uploadInvalidType"), tone: "warning" });
    return;
  }
  mapUploading.value = true;
  try {
    const dims = await readImageDimensions(file);
    const viewportWidth = mapViewportRef.value?.getViewportWidth() ?? window.innerWidth;
    const scale = computeMapScaleForViewport(dims.w, viewportWidth);
    const offset = tabletopMaps.value.length * 24;
    const map = await tabletopStore.uploadMap(roomId.value, file);
    await tabletopStore.updateMap(roomId.value, map.id, {
      scale,
      x: offset,
      y: offset,
    });
    selectMap(map.id);
    toasts.push({ message: t("table.assets.uploadSuccess"), tone: "success" });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.uploadFailed"),
      tone: "danger",
    });
  } finally {
    mapUploading.value = false;
  }
}

const roomMessagesState = computed(() => messagesStore.getRoomState(roomId.value));
const roomChatMessages = computed(() => messagesStore.getRoomChatMessages(roomId.value));
const entityRoomMembers = computed(() => entitiesStore.getRoomMembers(roomId.value));
const hasOlderMessages = computed(() => roomMessagesState.value.nextBeforeId != null);

const memberActions = useRoomMemberActions({
  roomId,
  router,
  t,
  syncCurrentUserRoles,
  fetchRoomRequests: (options) => fetchRoomRequests(options),
});
const {
  isLeavingRoom,
  isDisbandingRoom,
  invitingMemberUserIds,
  settingManagerUserIds,
  removingMemberUserIds,
  handleLeaveRoom,
  handleDisbandRoom,
  handleInviteUser,
  handleSetMemberManager,
  handleUnsetMemberManager,
  handleSetMemberGameRole,
  handleRemoveRoomMember,
  settingGameRoleUserIds,
  resetMemberActionState,
} = memberActions;

const {
  requestsLoading,
  requestsError,
  roomJoinRequests,
  roomRequestItems,
  pendingMemberInviteStates,
  fetchRoomRequests,
  isRequestActionLoading,
  approveRequest,
  rejectRequest,
  resetRoomRequestsState,
} = useRoomJoinRequests({
  roomId,
  canManageRoomRequests,
  optimisticInviteUserIds: invitingMemberUserIds,
  t,
});

const selfUserId = computed(() => auth.me?.id ?? null);

const {
  remoteCursors,
  remoteLasers,
  handlePointerPresence,
  handlePointerLaser,
  onViewportPointerMove: sendPointerMove,
  onViewportPointerDown: sendPointerDown,
  onViewportPointerUp: sendPointerUp,
} = useTabletopPointer({
  roomId,
  selfUserId,
  canSend: canDraw,
});

const realtime = useRoomRealtimeSession({
  roomId,
  refreshRoom: () => fetchRoom({ silent: true }),
  refreshRoomMembers: fetchRoomMembers,
  refreshRoomRequests: () => fetchRoomRequests({ force: true }),
  onSessionClosed: handleRealtimeSessionClosed,
  onPointerPresence: handlePointerPresence,
  onPointerLaser: handlePointerLaser,
});

function scenePointFromViewport(clientX: number, clientY: number) {
  return mapViewportRef.value?.scenePointFromClient(clientX, clientY) ?? { x: 0, y: 0 };
}

function onViewportPointerMove(event: PointerEvent) {
  sendPointerMove(event.clientX, event.clientY, scenePointFromViewport);
}

function onViewportPointerDown(event: PointerEvent) {
  sendPointerDown(event.clientX, event.clientY, scenePointFromViewport);
}

function onViewportPointerUp(event: PointerEvent) {
  sendPointerUp(event.clientX, event.clientY, scenePointFromViewport);
}

const presentUserIds = computed(() => new Set(realtime.presentUserIds.value));
const roomMemberItems = computed(() => entityRoomMembers.value.map((member) => {
  const user = entitiesStore.getUser(member.user_id);
  const memberStatus: MemberStatus =
    realtime.hasPresenceSnapshot.value && presentUserIds.value.has(member.user_id)
      ? "idle"
      : "offline";

  return {
    id: member.user_id,
    name:
      user?.username ||
      user?.email ||
      `User #${member.user_id}`,
    email: user?.email ?? null,
    avatarUrl: user?.avatar_url ?? null,
    room_role: member.room_role,
    game_role: member.game_role,
    status: memberStatus,
  };
}));
const roomMemberStatusByUserId = computed<Map<number, MemberStatus>>(() =>
  new Map(roomMemberItems.value.map((member) => [member.id, member.status])));

function syncCurrentUserRoles() {
  const meId = auth.me?.id;
  if (!meId) {
    currentUserRoomRole.value = "unknown";
    currentUserGameRole.value = "unknown";
    return;
  }

  const selfMember = entityRoomMembers.value.find((member) => member.user_id === meId);
  if (selfMember) {
    currentUserRoomRole.value = selfMember.room_role;
    currentUserGameRole.value = selfMember.game_role;
    return;
  }

  if (room.value?.owner_id === meId) {
    currentUserRoomRole.value = "owner";
    currentUserGameRole.value = "unknown";
    return;
  }

  currentUserRoomRole.value = "unknown";
  currentUserGameRole.value = "unknown";
}

async function fetchRoom(options?: { silent?: boolean }) {
  if (!roomId.value) {
    error.value = t("room.invalidId");
    return;
  }

  const shouldShowLoading = !options?.silent && !room.value;
  if (shouldShowLoading) {
    isLoading.value = true;
  }
  error.value = "";

  try {
    room.value = await getRoomById(roomId.value);
    entitiesStore.upsertRoom(room.value);
    syncCurrentUserRoles();
  } catch (e: any) {
    if (!options?.silent) {
      room.value = null;
    }
    error.value =
      getBackendErrorMessage(e) ||
      t("room.loadFailed");
  } finally {
    if (shouldShowLoading) {
      isLoading.value = false;
    }
  }
}

async function fetchRoomMembers() {
  if (!roomId.value) {
    membersError.value = t("room.invalidId");
    return;
  }

  membersLoading.value = true;
  membersError.value = "";

  try {
    const response = await getRoomMembers(roomId.value);
    entitiesStore.upsertRoomMembers(response.items);
    syncCurrentUserRoles();
    await fetchRoomRequests({ force: true });
  } catch (e: any) {
    membersError.value =
      getBackendErrorMessage(e) ||
      t("room.membersLoadFailed");
  } finally {
    membersLoading.value = false;
  }
}

async function fetchRoomMessages() {
  if (!roomId.value) return;

  try {
    await messagesStore.refreshRoomMessages(roomId.value, 20);
  } catch {
    // messages.store already keeps the error state for the panel
  }
}

async function loadOlderRoomMessages() {
  if (!roomId.value) return;

  try {
    await messagesStore.loadOlderMessages(roomId.value, 20);
  } catch {
    // messages.store already keeps the error state for the panel
  }
}

async function handleSend(segments: ChatSegment[]) {
  if (!roomId.value) return;

  try {
    await messagesStore.sendSegments(roomId.value, segments);
  } catch (error) {
    toasts.push({
      message: t("room.chatSendFailed"),
      tone: "danger",
    });
    throw error;
  }
}

async function handleSaveRoomSettings(payload: RoomPatchPayload) {
  if (!roomId.value || settingsSaving.value) return;

  settingsSaving.value = true;

  try {
    const updatedRoom = await patchRoom(roomId.value, payload);
    room.value = updatedRoom;
    entitiesStore.upsertRoom(updatedRoom);
    toasts.push({
      message: t("room.settings.saved"),
      tone: "success",
    });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("room.settings.saveFailed"),
      tone: "danger",
    });
  } finally {
    settingsSaving.value = false;
  }
}

function handleRealtimeSessionClosed(payload: RoomRealtimeSessionClosed) {
  toasts.push({
    message: t(`room.realtime.sessionClosed.${payload.reason}`),
    tone: "warning",
  });

  if (payload.reason === "removed_from_room" || payload.reason === "room_deleted") {
    void router.push("/");
  }
}

function handleAssetPlaceholder() {
  toasts.push({
    message: t("table.assets.comingSoon"),
    tone: "default",
  });
}

onMounted(() => {
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomMembers();
  if (roomId.value) {
    void tabletopStore.loadSnapshot(roomId.value);
  }
});

watch(roomId, (newId, oldId) => {
  currentUserRoomRole.value = "unknown";
  currentUserGameRole.value = "unknown";
  resetRoomRequestsState();
  resetMemberActionState();
  if (oldId) {
    tabletopStore.resetRoom(oldId);
  }
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomMembers();
  if (newId) {
    void tabletopStore.loadSnapshot(newId);
  }
});
watch(() => auth.me?.id, () => {
  syncCurrentUserRoles();
});
watch([roomId, currentUserRoomRole], () => {
  void fetchRoomRequests();
});
</script>

<template>
  <div class="roomPageWrap">
  <BaseLayout :max-width="10000">
    <div class="roomShell">
      <div v-if="isLoading" class="state">{{ t("common.loading") }}</div>

      <div v-else-if="error" class="state error">{{ error }}</div>

      <TableStage
        v-else-if="room"
        class="roomTableStage"
        :class="{ drawPassthrough: toolMode === 'draw' }"
      >
        <template #map>
          <input
            ref="mapUploadInput"
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            class="mapUploadInput"
            @change="handleMapFileChange"
          />
          <MapViewport
            ref="mapViewportRef"
            :maps="tabletopMaps"
            :drawings="tabletopDrawings"
            :grid-cell-px="gridCellPx"
            :scale-bar-cells="scaleBarCells"
            :tool-mode="toolMode"
            :game-role="currentUserGameRole"
            :selection="selection"
            :draw-preview="drawPreview"
            :map-natural-size="selectedMapNaturalSize"
            :draw-interactive="drawingLayerInteractive"
            :draw-sub-tool="subTool"
            :text-placement="textPlacement"
            :text-edit="textEdit"
            :editing-drawing-id="editingDrawingId"
            :draw-font-size="fontSize"
            :remote-cursors="remoteCursors"
            :remote-lasers="remoteLasers"
            @select-map="handleSelectMap"
            @map-context-menu="handleMapContextMenu"
            @select-drawing="handleSelectDrawing"
            @text-placement-resize="handleTextPlacementResize"
            @patch-map="handlePatchMap"
            @patch-drawing="handlePatchDrawing"
            @confirm-text="confirmText"
            @cancel-text="cancelText"
            @confirm-text-edit="confirmTextEdit"
            @cancel-text-edit="cancelTextEdit"
            @edit-text="handleEditTextDrawing"
            @map-natural-size="handleMapNaturalSize"
            @draw-pointer-down="drawPointerDown"
            @draw-pointer-move="drawPointerMove"
            @draw-pointer-up="drawPointerUp"
            @context-menu="handleContextMenu"
            @clear-selection="handleClearSelection"
            @viewport-pointer-move="onViewportPointerMove"
            @viewport-pointer-down="onViewportPointerDown"
            @viewport-pointer-up="onViewportPointerUp"
          />
          <ContextMenu
            :open="contextMenuOpen"
            :client-x="contextMenuX"
            :client-y="contextMenuY"
            :selection="selection"
            :maps="tabletopMaps"
            :drawings="tabletopDrawings"
            :game-role="currentUserGameRole"
            @close="closeContextMenu"
            @delete-map="handleContextDeleteMap"
            @delete-drawing="handleContextDeleteDrawing"
            @edit-text-drawing="handleEditTextDrawing"
            @toggle-map-lock="handleContextToggleMapLock"
            @map-layer="handleContextMapLayer"
          />
        </template>

        <template #overlays>
          <div class="leftStack">
          <GovernanceDock
            :room-id="roomId"
            :room="room"
            :members="roomMemberItems"
            :members-loading="membersLoading"
            :members-error="membersError"
            :can-manage-requests="canManageRoomRequests"
            :can-manage-settings="canManageRoomSettings"
            :requests-badge="roomJoinRequests.length > 0 ? String(roomJoinRequests.length) : undefined"
            :requests-loading="requestsLoading"
            :requests-error="requestsError"
            :request-items="roomRequestItems"
            :is-request-action-loading="isRequestActionLoading"
            :settings-saving="settingsSaving"
            :is-owner="currentUserIsOwner"
            :can-remove-members="currentUserCanRemoveMembers"
            :action-disabled="memberDangerActionDisabled"
            :leaving="isLeavingRoom"
            :disbanding="isDisbandingRoom"
            :pending-join-requests="pendingMemberInviteStates"
            :setting-manager-user-ids="settingManagerUserIds"
            :setting-game-role-user-ids="settingGameRoleUserIds"
            :removing-member-user-ids="removingMemberUserIds"
            @invite-user="handleInviteUser"
            @leave-room="handleLeaveRoom"
            @disband-room="handleDisbandRoom"
            @set-manager="handleSetMemberManager"
            @unset-manager="handleUnsetMemberManager"
            @set-game-role="(userId, gameRole) => handleSetMemberGameRole(userId, gameRole)"
            @remove-member="handleRemoveRoomMember"
            @approve-request="approveRequest"
            @reject-request="rejectRequest"
            @save-settings="handleSaveRoomSettings"
            @open-requests="fetchRoomRequests({ force: true })"
          />
          </div>

          <FloatingPanel
            :title="t('table.chat.title')"
            anchor="bottom-left"
            collapse-to="bottom-left"
            variant="chat"
            :storage-key="`room-${roomId}-chat`"
          >
            <RoomChatTab
              :room-key="roomId"
              :active="true"
              :messages="roomChatMessages"
              :member-status-by-user-id="roomMemberStatusByUserId"
              :send-label="t('room.chat.send')"
              :loading="roomMessagesState.isLoading"
              :sending="roomMessagesState.isSending"
              :loading-history="roomMessagesState.isLoadingHistory"
              :has-older="hasOlderMessages"
              :error="roomMessagesState.error"
              :loading-label="t('common.loading')"
              :empty-label="t('room.chatEmpty')"
              :send-message="handleSend"
              @load-older="loadOlderRoomMessages"
            />
          </FloatingPanel>

          <FloatingPanel
            :title="t('table.tools.toolbar')"
            anchor="top-center"
            collapse-to="top"
            variant="tools"
            :storage-key="`room-${roomId}-tools`"
          >
            <TopToolBar
              v-model="toolMode"
              :disabled-tools="disabledTools"
              :grid-cell-px="gridCellPx"
              :grid-cell-ft="gridCellFt"
              :can-increase-grid="canIncreaseGrid"
              :can-decrease-grid="canDecreaseGrid"
              @increase-grid="increaseGrid"
              @decrease-grid="decreaseGrid"
            />
            <DrawToolStrip
              v-if="toolMode === 'draw' && canDraw"
              v-model:sub-tool="subTool"
              v-model:stroke-color="strokeColor"
              v-model:stroke-width="strokeWidth"
              v-model:font-size="fontSize"
            />
          </FloatingPanel>

          <FloatingPanel
            :title="t('table.assets.barTitle')"
            anchor="bottom-center"
            collapse-to="bottom"
            variant="assets"
            :storage-key="`room-${roomId}-assets`"
          >
            <BottomAssetBar
              :can-add-map="canAddMap"
              :can-add-character="canAddCharacter"
              @add-map="handleAddMapClick"
              @add-character="handleAssetPlaceholder"
            />
          </FloatingPanel>

          <div class="rightStack">
            <FloatingPanel
              :title="t('table.inspector.infoTitle')"
              inline
              collapse-to="right"
              variant="info"
              :storage-key="`room-${roomId}-info`"
            >
              <InfoPanel />
            </FloatingPanel>

            <FloatingPanel
              class="memoPanel"
              :title="t('table.inspector.memoTitle')"
              inline
              collapse-to="right"
              variant="memo"
              :storage-key="`room-${roomId}-memo`"
            >
              <PersonalMemo :room-id="roomId" />
            </FloatingPanel>
          </div>
        </template>
      </TableStage>
    </div>
  </BaseLayout>
  </div>
</template>

<style scoped>
.mapUploadInput {
  display: none;
}

.roomPageWrap {
  height: calc(100dvh - 56px);
  min-height: 0;
}

.roomPageWrap :deep(.page) {
  padding: 0;
  min-height: 0;
  height: 100%;
}

.roomPageWrap :deep(.container) {
  max-width: 100% !important;
  height: 100%;
  margin: 0;
}

.roomShell {
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.state {
  padding: 16px;
  color: var(--c-text-muted);
  font-size: 14px;
}

.state.error {
  color: var(--c-danger);
}

.rightStack {
  position: absolute;
  top: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  pointer-events: none;
  z-index: 2;
  max-width: min(300px, calc(100vw - 24px));
}

.rightStack > * {
  pointer-events: auto;
}

.rightStack > .memoPanel {
  margin-top: auto;
}

.leftStack {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  max-height: calc(100% - 24px);
  pointer-events: none;
}

.leftStack > * {
  pointer-events: auto;
  flex-shrink: 0;
}

.leftStack :deep(.floatingPanel.governance) {
  position: relative;
  top: auto;
  left: auto;
  width: min(320px, calc(100vw - 24px));
  max-height: min(52vh, 420px);
}

.roomTableStage.drawPassthrough :deep(.leftStack > *),
.roomTableStage.drawPassthrough :deep(.rightStack > *) {
  pointer-events: none;
}

.roomTableStage.drawPassthrough :deep(.overlays > .floatingPanel:not(.tools)) {
  pointer-events: none;
}

.roomTableStage.drawPassthrough :deep(.overlays > .floatingPanel.tools) {
  z-index: 10;
  pointer-events: none;
}

.roomTableStage.drawPassthrough :deep(.overlays > .floatingPanel.tools .panelHeader),
.roomTableStage.drawPassthrough :deep(.overlays > .floatingPanel.tools .panelBody) {
  pointer-events: auto;
}

@media (max-width: 720px) {
  .roomShell {
    height: calc(100dvh - 52px);
  }

  .rightStack {
    max-width: calc(100vw - 24px);
  }
}
</style>
