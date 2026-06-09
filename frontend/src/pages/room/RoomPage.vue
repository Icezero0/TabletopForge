<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  getRoomById,
  getRoomMembers,
  patchMyPlayerColor,
  patchRoom,
  type Room,
  type RoomCombatState,
  type RoomPatchPayload,
} from "@/infra/api/rooms.api";
import { patchLibraryResourceGrid, type LibraryResource } from "@/infra/api/library.api";
import BaseLayout from "@/ui/layout/BaseLayout.vue";
import RoomChatTab from "@/features/room/components/workspace/RoomChatTab.vue";
import type { GameRole, MemberStatus, RoomRole } from "@/features/room/types";
import type { ChatSegment } from "@/features/chat/types";
import { useRoomJoinRequests } from "@/features/room/composables/useRoomJoinRequests";
import { useRoomCharacters } from "@/features/room/composables/useRoomCharacters";
import {
  fetchAllMyCharacters,
  mergeSpawnPopoverEntries,
} from "@/features/room/utils/spawnCharacters";
import type { Character } from "@/infra/api/character.api";
import { linkRoomCharacter } from "@/infra/api/roomCharacters.api";
import { useRoomInspection } from "@/features/room/composables/useRoomInspection";
import { useRoomMemberActions } from "@/features/room/composables/useRoomMemberActions";
import { useRoomRealtimeSession } from "@/features/room/composables/useRoomRealtimeSession";
import type { RoomRealtimeSessionClosed } from "@/infra/realtime/roomRealtime";
import {
  sendObjectSelection,
  sendTokenTransformPreview,
  type ObjectSelectionPayload,
} from "@/infra/realtime/tabletopRealtime";
import BottomAssetBar from "@/features/table/components/BottomAssetBar.vue";
import CombatPanel from "@/features/table/components/CombatPanel.vue";
import LibraryMapPickerDialog from "@/features/table/components/LibraryMapPickerDialog.vue";
import MapGridAnnotationDialog from "@/features/table/components/MapGridAnnotationDialog.vue";
import AddRoomCharacterDialog from "@/features/room/components/AddRoomCharacterDialog.vue";
import InGameCharacterList from "@/features/room/components/InGameCharacterList.vue";
import FloatingPanel from "@/features/table/components/FloatingPanel.vue";
import GovernanceDock from "@/features/table/components/GovernanceDock.vue";
import InfoPanel from "@/features/table/components/InfoPanel.vue";
import MapViewport from "@/features/table/components/MapViewport.vue";
import ContextMenu from "@/features/table/components/ContextMenu.vue";
import DrawToolStrip from "@/features/table/components/DrawToolStrip.vue";
import MeasureToolStrip from "@/features/table/components/MeasureToolStrip.vue";
import PersonalMemo from "@/features/table/components/PersonalMemo.vue";
import TableStage from "@/features/table/components/TableStage.vue";
import TopToolBar from "@/features/table/components/TopToolBar.vue";
import { useDrawingTools } from "@/features/table/composables/useDrawingTools";
import { useTextDrawingEdit } from "@/features/table/composables/useTextDrawingEdit";
import { useGridScale } from "@/features/table/composables/useGridScale";
import { useMeasureTool } from "@/features/table/composables/useMeasureTool";
import { useTabletopSelection } from "@/features/table/composables/useTabletopSelection";
import { useTableToolMode } from "@/features/table/composables/useTableToolMode";
import { useTabletopPointer } from "@/features/table/composables/useTabletopPointer";
import { useRealtimePreviewChannel } from "@/features/table/composables/useRealtimePreviewChannel";
import type { ClaimableObjectSelection, RemoteObjectSelection } from "@/features/table/types";
import { nextDrawingZIndex } from "@/features/table/drawingTypes";
import { computeMapScaleForViewport } from "@/features/table/utils/mapScale";
import { canInspectToken, canManageToken } from "@/features/table/utils/tokenDisplay";
import { fitGridFromSamples, circularMeanPhase, type GridSampleRect, type GridSampleLegacy } from "@/features/table/utils/gridFit";
import { useMessagesStore } from "@/stores/messages.store";
import { useDiceStore, type DiceDraft } from "@/stores/dice.store";
import { useTabletopStore } from "@/stores/tabletop.store";
import { useEntitiesStore } from "@/stores/entities.store";
import { useAuthStore } from "@/stores/auth.store";
import { useToastsStore } from "@/stores/toasts.store";
import { getBackendErrorMessage, getBackendErrorReason } from "@/infra/http/client";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const entitiesStore = useEntitiesStore();
const messagesStore = useMessagesStore();
const diceStore = useDiceStore();
const tabletopStore = useTabletopStore();
const toasts = useToastsStore();

type RoomRoleState = RoomRole | "unknown";

const room = ref<Room | null>(null);
const isLoading = ref(false);
const error = ref("");
const membersLoading = ref(false);
const membersError = ref("");
const settingsSaving = ref(false);
const combatSaving = ref(false);
const currentUserRoomRole = ref<RoomRoleState>("unknown");
const currentUserGameRole = ref<GameRole | "unknown">("unknown");

const roomId = computed(() => {
  const raw = route.params.id;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
});

const {
  characters: roomCharacters,
  isLoading: roomCharactersLoading,
  fetchCharacters: fetchRoomCharacters,
  createCharacter: createRoomCharacter,
  upsertEntry: upsertRoomCharacter,
  updateEntryState: updateRoomCharacterState,
  setVisibility: setRoomCharacterVisibility,
  applyVisibilityUpdate: applyRoomCharacterVisibility,
  removeEntry: removeRoomCharacter,
} = useRoomCharacters(roomId);

const { activeInspection, inspectCharacter, clearInspection } = useRoomInspection();

const characterOwnerById = computed(() => {
  const map = new Map<number, number>();
  for (const entry of roomCharacters.value) {
    map.set(entry.character_id, entry.owner_id);
  }
  return map;
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
const canAddToken = computed(() => currentUserGameRole.value === "GM" || currentUserGameRole.value === "PL");

const tokenSpawnCharacters = computed(() => {
  if (currentUserGameRole.value === "GM") return roomCharacters.value;
  if (currentUserGameRole.value === "PL") {
    return roomCharacters.value.filter((e) => e.owner_id === currentUserId.value);
  }
  return [];
});
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

const measureSubTool = ref<"line" | "route">("line");

const {
  measureState,
  measurePointerDown,
  measurePointerMove,
  measurePointerUp,
  routeClick,
  routeFinish,
  routePointerMove,
  clearMeasure,
} = useMeasureTool({ gridCellPx, gridCellFt });

watch(toolMode, (mode) => {
  if (mode !== "measure") clearMeasure();
});

watch(measureSubTool, clearMeasure);

function handleMeasurePointerMove(x: number, y: number, event: PointerEvent) {
  if (measureSubTool.value === "route") {
    routePointerMove(x, y);
  } else {
    measurePointerMove(x, y, event);
  }
}

const tabletopMaps = computed(() => tabletopStore.getMaps(roomId.value));
const tabletopDrawings = computed(() => tabletopStore.getDrawings(roomId.value));
const tabletopTokens = computed(() => tabletopStore.getTokens(roomId.value));
const tabletopSettings = computed(() => tabletopStore.getSettings(roomId.value));
const currentUserId = computed(() => auth.me?.id ?? null);
const { selection, selectMap, selectDrawing, selectToken, clearSelection } = useTabletopSelection();
const OBJECT_SELECTION_LEASE_MS = 30_000;
const OBJECT_SELECTION_RENEW_MS = 10_000;
const remoteObjectSelectionByKey = ref<Record<string, RemoteObjectSelection>>({});
const objectSelectionNow = ref(Date.now());
let lastClaimedSelection: ClaimableObjectSelection | null = null;
let objectSelectionRenewTimer: ReturnType<typeof window.setInterval> | null = null;
let objectSelectionCleanupTimer: ReturnType<typeof window.setInterval> | null = null;
const mapNaturalSizes = ref<Record<number, { w: number; h: number }>>({});
const mapViewportRef = ref<InstanceType<typeof MapViewport> | null>(null);
const mapUploadInput = ref<HTMLInputElement | null>(null);
const mapUploading = ref(false);
const pendingAnnotationMap = ref<{ id: number; assetId: number; libraryResourceId: number; dims: { w: number; h: number } } | null>(null);
const gridAnnotationOpen = ref(false);

watch(gridAnnotationOpen, (open) => {
  if (!open && pendingAnnotationMap.value) {
    handleAnnotationClose();
  }
});

const addCharacterDialogOpen = ref(false);
const characterPopoverOpen = ref(false);
const mapPopoverOpen = ref(false);
const tokenPopoverOpen = ref(false);
const libraryMapPickerOpen = ref(false);
const libraryCharacters = ref<Character[]>([]);
const libraryLoading = ref(false);

const spawnPopoverEntries = computed(() =>
  mergeSpawnPopoverEntries(
    roomCharacters.value,
    libraryCharacters.value,
    currentUserId.value,
  ),
);

watch(characterPopoverOpen, async (open) => {
  if (!open) return;
  if (currentUserGameRole.value !== "GM" && currentUserGameRole.value !== "PL") return;
  libraryLoading.value = true;
  try {
    libraryCharacters.value = await fetchAllMyCharacters();
    if (currentUserGameRole.value === "GM") {
      await entitiesStore.ensureUsers([
        ...roomCharacters.value.map((entry) => entry.owner_id),
        ...libraryCharacters.value.map((char) => char.owner_id),
      ]);
    }
  } catch {
    libraryCharacters.value = [];
  } finally {
    libraryLoading.value = false;
  }
});

const selectedMapId = computed(() =>
  selection.value?.type === "map" ? selection.value.id : null,
);
const selectedCharacterListId = ref<number | null>(null);
const characterSubmitting = ref(false);

const currentUserDisplayName = computed(
  () => auth.me?.username?.trim() || auth.me?.email?.trim() || "",
);

const selectedToken = computed(() => {
  if (selection.value?.type !== "token") return null;
  return tabletopTokens.value.find((t) => t.id === selection.value!.id) ?? null;
});

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
  undoLastDrawing,
} = useDrawingTools({
  drawings: tabletopDrawings,
  gridCellPx,
  gridCellFt,
  onCommit: async (payload) => {
    if (!roomId.value) return;
    return await tabletopStore.createDrawing(roomId.value, {
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
const chatPanelCollapsed = ref(false);

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

watch(tabletopTokens, (tokens) => {
  if (selection.value?.type === "token") {
    const exists = tokens.some((t) => t.id === selection.value!.id);
    if (!exists) {
      const prevTokenId = selection.value.id;
      clearSelection();
      if (activeInspection.value?.tokenId === prevTokenId) clearInspection();
    }
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

function claimKey(selectionLike: ClaimableObjectSelection) {
  return `${selectionLike.type}:${selectionLike.id}`;
}

function isClaimableSelection(value: typeof selection.value): value is ClaimableObjectSelection {
  return value?.type === "token" || value?.type === "drawing";
}

function remoteClaimFor(selectionLike: ClaimableObjectSelection) {
  const claim = remoteObjectSelectionByKey.value[claimKey(selectionLike)];
  if (!claim || claim.userId === currentUserId.value) return null;
  return claim;
}

function isObjectClaimedByOther(selectionLike: ClaimableObjectSelection) {
  return remoteClaimFor(selectionLike) != null;
}

function releaseLocalObjectSelection() {
  if (!roomId.value || !lastClaimedSelection) return;
  const releasedSelection = lastClaimedSelection;
  lastClaimedSelection = null;
  if (!realtime.isRealtimeActive.value) return;
  sendObjectSelection(roomId.value, {
    object_type: releasedSelection.type,
    object_id: releasedSelection.id,
    active: false,
  });
}

function sendLocalObjectSelectionClaim(selectionLike: ClaimableObjectSelection) {
  if (!roomId.value || !realtime.isRealtimeActive.value) return;
  sendObjectSelection(roomId.value, {
    object_type: selectionLike.type,
    object_id: selectionLike.id,
    active: true,
  });
}

function claimLocalObjectSelection(next: ClaimableObjectSelection) {
  if (!roomId.value) return;
  if (
    lastClaimedSelection &&
    lastClaimedSelection.type === next.type &&
    lastClaimedSelection.id === next.id
  ) {
    sendLocalObjectSelectionClaim(next);
    return;
  }
  releaseLocalObjectSelection();
  lastClaimedSelection = next;
  sendLocalObjectSelectionClaim(next);
}

function handleObjectSelection(payload: ObjectSelectionPayload) {
  if (payload.user_id === currentUserId.value) return;
  const objectType = payload.object_type;
  const objectId = payload.object_id;
  remoteObjectSelectionByKey.value = Object.fromEntries(
    Object.entries(remoteObjectSelectionByKey.value).filter(([, claim]) => claim.userId !== payload.user_id),
  );
  if (!payload.active || objectId == null) return;
  const color = playerColorByUserId.value.get(payload.user_id) ?? null;
  remoteObjectSelectionByKey.value = {
    ...remoteObjectSelectionByKey.value,
    [`${objectType}:${objectId}`]: {
      type: objectType,
      id: objectId,
      userId: payload.user_id,
      color,
      expiresAt: Date.now() + OBJECT_SELECTION_LEASE_MS,
    },
  };
}

watch(selection, (next) => {
  if (isClaimableSelection(next)) {
    claimLocalObjectSelection(next);
    return;
  }
  releaseLocalObjectSelection();
});

onUnmounted(() => {
  releaseLocalObjectSelection();
  if (objectSelectionRenewTimer != null) {
    window.clearInterval(objectSelectionRenewTimer);
    objectSelectionRenewTimer = null;
  }
  if (objectSelectionCleanupTimer != null) {
    window.clearInterval(objectSelectionCleanupTimer);
    objectSelectionCleanupTimer = null;
  }
});

objectSelectionRenewTimer = window.setInterval(() => {
  if (lastClaimedSelection) {
    sendLocalObjectSelectionClaim(lastClaimedSelection);
  }
}, OBJECT_SELECTION_RENEW_MS);

objectSelectionCleanupTimer = window.setInterval(() => {
  const now = Date.now();
  objectSelectionNow.value = now;
  const nextEntries = Object.entries(remoteObjectSelectionByKey.value)
    .filter(([, claim]) => claim.expiresAt == null || claim.expiresAt > now);
  if (nextEntries.length !== Object.keys(remoteObjectSelectionByKey.value).length) {
    remoteObjectSelectionByKey.value = Object.fromEntries(nextEntries);
  }
}, 1_000);

function handleSelectMap(mapId: number) {
  if (toolMode.value !== "select" && toolMode.value !== "hand") return;
  if (currentUserGameRole.value !== "GM") return;
  releaseLocalObjectSelection();
  selectMap(mapId);
  clearInspection();
  selectedCharacterListId.value = null;
}

function handleMapContextMenu(mapId: number, event: MouseEvent) {
  if (toolMode.value === "draw" || toolMode.value === "measure") return;
  if (currentUserGameRole.value !== "GM") return;
  selectMap(mapId);
  clearInspection();
  selectedCharacterListId.value = null;
  contextMenuX.value = event.clientX;
  contextMenuY.value = event.clientY;
  contextMenuOpen.value = true;
}

function handleSelectDrawing(drawingId: number) {
  if (toolMode.value !== "select" && toolMode.value !== "hand") return;
  if (!canDraw.value) return;
  const next = { type: "drawing", id: drawingId } as const;
  if (isObjectClaimedByOther(next)) return;
  selectDrawing(drawingId);
  claimLocalObjectSelection(next);
  clearInspection();
  selectedCharacterListId.value = null;
}

function handleDrawingContextMenu(drawingId: number, event: MouseEvent) {
  if (toolMode.value === "draw" || toolMode.value === "measure") return;
  if (!canDraw.value) return;
  const next = { type: "drawing", id: drawingId } as const;
  if (isObjectClaimedByOther(next)) return;
  selectDrawing(drawingId);
  claimLocalObjectSelection(next);
  clearInspection();
  selectedCharacterListId.value = null;
  contextMenuX.value = event.clientX;
  contextMenuY.value = event.clientY;
  contextMenuOpen.value = true;
}

const selectedDrawing = computed(() => {
  if (selection.value?.type !== "drawing") return null;
  return tabletopDrawings.value.find((d) => d.id === selection.value!.id) ?? null;
});

function tokenCanManage(token: (typeof tabletopTokens.value)[number]) {
  return canManageToken(
    token,
    currentUserGameRole.value,
    currentUserId.value,
    characterOwnerById.value,
  );
}

function tokenCanInteract(token: (typeof tabletopTokens.value)[number]) {
  return canInspectToken(token) || tokenCanManage(token);
}

function selectTokenForInspection(tokenId: number, options: { respectToolMode?: boolean } = {}) {
  if (options.respectToolMode !== false && toolMode.value !== "select" && toolMode.value !== "hand") return;
  const token = tabletopTokens.value.find((t) => t.id === tokenId);
  if (!token || !tokenCanInteract(token)) return;
  const next = { type: "token", id: tokenId } as const;
  if (isObjectClaimedByOther(next)) return;
  selectToken(tokenId);
  claimLocalObjectSelection(next);
  selectedCharacterListId.value = null;
  if (token.linked_character_id != null && canInspectToken(token)) {
    inspectCharacter({
      characterId: token.linked_character_id,
      tokenId: token.id,
      tokenInstanceName: token.name,
    });
  } else {
    clearInspection();
  }
}

function handleSelectToken(tokenId: number) {
  selectTokenForInspection(tokenId);
}

function handleCombatSelectToken(tokenId: number) {
  selectTokenForInspection(tokenId, { respectToolMode: false });
}

function handleCombatFocusToken(tokenId: number) {
  const token = tabletopTokens.value.find((t) => t.id === tokenId);
  if (!token || !tokenCanInteract(token)) return;
  selectTokenForInspection(tokenId, { respectToolMode: false });
  mapViewportRef.value?.centerScenePoint?.({
    x: token.x + token.width / 2,
    y: token.y + token.height / 2,
  });
}

function handleTokenContextMenu(tokenId: number, event: MouseEvent) {
  if (toolMode.value === "draw" || toolMode.value === "measure") return;
  const token = tabletopTokens.value.find((t) => t.id === tokenId);
  if (!token || !tokenCanInteract(token)) return;
  const next = { type: "token", id: tokenId } as const;
  if (isObjectClaimedByOther(next)) return;
  selectToken(tokenId);
  claimLocalObjectSelection(next);
  selectedCharacterListId.value = null;
  contextMenuX.value = event.clientX;
  contextMenuY.value = event.clientY;
  contextMenuOpen.value = true;
}

function handleInspectToken(tokenId: number) {
  const token = tabletopTokens.value.find((t) => t.id === tokenId);
  if (!token?.linked_character_id) return;
  selectedCharacterListId.value = null;
  inspectCharacter({
    characterId: token.linked_character_id,
    tokenId: token.id,
    tokenInstanceName: token.name,
  });
}

function handleCloseInspection() {
  clearInspection();
  clearSelection();
  selectedCharacterListId.value = null;
}

function handleInspectCharacter(payload: { characterId: number }) {
  if (selectedCharacterListId.value === payload.characterId) {
    handleCloseInspection();
    return;
  }
  clearSelection();
  selectedCharacterListId.value = payload.characterId;
  inspectCharacter(payload);
}

async function handleRemoveRoomCharacter(roomCharacterId: number) {
  try {
    await removeRoomCharacter(roomCharacterId);
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.characterList.removeFailed"),
      tone: "danger",
    });
  }
}

async function handleToggleCharacterVisibility(payload: {
  roomCharacterId: number;
  isHidden: boolean;
}) {
  try {
    await setRoomCharacterVisibility(payload.roomCharacterId, payload.isHidden);
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.characterList.visibilityFailed"),
      tone: "danger",
    });
  }
}

function viewportCenterPoint() {
  return mapViewportRef.value?.scenePointFromViewportCenter?.() ?? { x: 0, y: 0 };
}

async function handleLinkRoomCharacter(characterId: number) {
  if (!roomId.value) return;
  try {
    const entry = await linkRoomCharacter(roomId.value, characterId);
    upsertRoomCharacter(entry);
    toasts.push({ message: t("room.characters.linked"), tone: "success" });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("room.characters.linkFailed"),
      tone: "danger",
    });
  }
}

async function handleSpawnCharacter(characterId: number, tokenConfigId?: number) {
  if (!roomId.value) return;
  const inRoom = roomCharacters.value.some((entry) => entry.character_id === characterId);
  if (!inRoom) {
    try {
      const entry = await linkRoomCharacter(roomId.value, characterId);
      upsertRoomCharacter(entry);
    } catch (error) {
      toasts.push({
        message: getBackendErrorMessage(error) || t("room.characters.linkFailed"),
        tone: "danger",
      });
      return;
    }
  }
  const center = viewportCenterPoint();
  try {
    await tabletopStore.spawnCharacterToken(roomId.value, characterId, {
      x: center.x,
      y: center.y,
      token_config_id: tokenConfigId,
    });
    toasts.push({ message: t("table.characterList.spawned"), tone: "success" });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.characterList.spawnFailed"),
      tone: "danger",
    });
  }
}

async function handleSpawnAllTokens(characterId: number) {
  const entry = roomCharacters.value.find((e) => e.character_id === characterId);
  if (!entry || !roomId.value) return;
  const configs = entry.token_configs;
  if (configs.length === 0) return;

  const center = viewportCenterPoint();
  const step = gridCellPx.value;
  const startX = center.x - (configs.length / 2) * step;

  for (let i = 0; i < configs.length; i++) {
    const cfg = configs[i];
    if (!cfg) continue;
    try {
      await tabletopStore.spawnCharacterToken(roomId.value, characterId, {
        x: startX + i * step,
        y: center.y,
        token_config_id: cfg.id,
      });
      toasts.push({ message: t("table.characterList.spawned"), tone: "success" });
    } catch (error) {
      toasts.push({
        message: getBackendErrorMessage(error) || t("table.characterList.spawnFailed"),
        tone: "danger",
      });
    }
  }
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
  if (textPlacement.value.width === width) return;
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
  if (toolMode.value === "draw" || toolMode.value === "measure") return;
  releaseLocalObjectSelection();
  clearSelection();
  clearInspection();
  selectedCharacterListId.value = null;
  contextMenuX.value = event.clientX;
  contextMenuY.value = event.clientY;
  contextMenuOpen.value = true;
}

function closeContextMenu() {
  contextMenuOpen.value = false;
}

function handleOpenDiceRoll(draft: DiceDraft) {
  if (!roomId.value) return;
  chatPanelCollapsed.value = false;
  diceStore.setDraft(roomId.value, draft);
}

async function handleUpdateCombat(state: RoomCombatState | null) {
  if (!roomId.value || combatSaving.value) return;
  combatSaving.value = true;
  try {
    await tabletopStore.updateSettings(roomId.value, { combat_state: state });
  } catch (error) {
    const reason = getBackendErrorReason(error);
    toasts.push({
      message:
        (reason === "room_permission_denied" ? t("room.combat.permissionDenied") : "") ||
        getBackendErrorMessage(error) ||
        t("room.combat.saveFailed"),
      tone: "danger",
    });
  } finally {
    combatSaving.value = false;
  }
}

function handleClearSelection() {
  releaseLocalObjectSelection();
  clearSelection();
  closeContextMenu();
  clearInspection();
  selectedCharacterListId.value = null;
}

async function handleContextAlignMapToGrid(mapId: number) {
  if (!roomId.value) return;
  const map = tabletopMaps.value.find((m) => m.id === mapId);
  if (!map || map.map_grid_size == null) return;
  const cellPx = gridCellPx.value;
  const natural = mapNaturalSizes.value[mapId] ?? { w: 0, h: 0 };
  const effSx = map.scale_x ?? map.scale;
  const effSy = map.scale_y ?? map.scale;
  const centerX = map.x + (natural.w * effSx) / 2;
  const centerY = map.y + (natural.h * effSy) / 2;

  let scaleX: number, scaleY: number, phaseX: number, phaseY: number;

  const calibration = map.map_grid_calibration;
  const firstCalibration = calibration?.[0];
  if (firstCalibration && "width" in firstCalibration) {
    // New format: {x, y, width, height} — use least squares
    const { cellWidth, phaseX: px, cellHeight, phaseY: py } = fitGridFromSamples(calibration as GridSampleRect[]);
    scaleX = cellPx / cellWidth;
    scaleY = cellPx / cellHeight;
    phaseX = ((px * scaleX) % cellPx + cellPx) % cellPx;
    phaseY = ((py * scaleY) % cellPx + cellPx) % cellPx;
  } else if (calibration && calibration.length > 0) {
    // Legacy format: {x, y, size} — use circular mean (uniform scale)
    const legacyScale = cellPx / map.map_grid_size;
    scaleX = legacyScale;
    scaleY = map.map_grid_cell_height != null ? cellPx / map.map_grid_cell_height : legacyScale;
    phaseX = circularMeanPhase(calibration as GridSampleLegacy[], "x", scaleX, cellPx);
    phaseY = circularMeanPhase(calibration as GridSampleLegacy[], "y", scaleY, cellPx);
  } else {
    // No calibration — use stored grid params
    scaleX = cellPx / map.map_grid_size;
    scaleY = map.map_grid_cell_height != null ? cellPx / map.map_grid_cell_height : scaleX;
    phaseX = (((map.map_grid_x ?? 0) * scaleX) % cellPx + cellPx) % cellPx;
    phaseY = (((map.map_grid_y ?? 0) * scaleY) % cellPx + cellPx) % cellPx;
  }

  const idealX = centerX - (natural.w * scaleX) / 2;
  const idealY = centerY - (natural.h * scaleY) / 2;
  const x = Math.round((idealX + phaseX) / cellPx) * cellPx - phaseX;
  const y = Math.round((idealY + phaseY) / cellPx) * cellPx - phaseY;

  const nonSquare = Math.abs(scaleX - scaleY) > 1e-6;
  try {
    if (nonSquare) {
      await tabletopStore.updateMap(roomId.value, mapId, { scale_x: scaleX, scale_y: scaleY, x, y });
    } else {
      await tabletopStore.updateMap(roomId.value, mapId, { scale: scaleX, scale_x: null, scale_y: null, x, y });
    }
  } catch (error) {
    toasts.push({ message: getBackendErrorMessage(error), tone: "danger" });
  }
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

async function handleContextDrawingLayer(action: "up" | "down" | "top" | "bottom") {
  const drawing = selectedDrawing.value;
  if (!drawing || !roomId.value || tabletopDrawings.value.length <= 1) return;
  const sorted = [...tabletopDrawings.value].sort((a, b) => a.z_index - b.z_index);
  const idx = sorted.findIndex((d) => d.id === drawing.id);
  if (idx < 0) return;
  let target = drawing.z_index;
  if (action === "up" && idx < sorted.length - 1) {
    target = sorted[idx + 1]!.z_index;
  } else if (action === "down" && idx > 0) {
    target = sorted[idx - 1]!.z_index;
  } else if (action === "top") {
    target = Math.max(...sorted.map((d) => d.z_index)) + 1;
  } else if (action === "bottom") {
    target = Math.min(...sorted.map((d) => d.z_index)) - 1;
  }
  if (target === drawing.z_index) return;
  try {
    await tabletopStore.updateDrawing(roomId.value, drawing.id, { z_index: target });
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

const TOKEN_PREVIEW_THROTTLE_MS = 33;

type TokenTransformPreview = {
  tokenId: number;
  payload: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
};

const tokenTransformPreview = useRealtimePreviewChannel<TokenTransformPreview>({
  throttleMs: TOKEN_PREVIEW_THROTTLE_MS,
  key: (preview) => preview.tokenId,
  canSend: () => !!roomId.value,
  applyLocal: (preview) => {
    const token = tabletopTokens.value.find((t) => t.id === preview.tokenId);
    if (!token || !roomId.value) return;
    tabletopStore.applyTokenPatch(roomId.value, preview.tokenId, preview.payload);
  },
  merge: (pending, next) => ({
    tokenId: next.tokenId,
    payload: { ...pending.payload, ...next.payload },
  }),
  send: (preview) => {
    if (!roomId.value) return;
    sendTokenTransformPreview(roomId.value, preview.tokenId, preview.payload);
  },
});

async function commitTokenTransform(
  tokenId: number,
  payload: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  },
) {
  if (!roomId.value) return;
  try {
    await tabletopStore.updateToken(roomId.value, tokenId, payload);
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
    void tabletopStore.loadSnapshot(roomId.value);
  }
}

function handlePreviewToken(
  tokenId: number,
  payload: { x?: number; y?: number; width?: number; height?: number },
) {
  tokenTransformPreview.preview({ tokenId, payload });
}

function handleCommitToken(
  tokenId: number,
  payload: { x?: number; y?: number; width?: number; height?: number },
) {
  tokenTransformPreview.cancel();
  void commitTokenTransform(tokenId, payload);
}

async function handleContextDeleteToken(tokenId: number) {
  if (!roomId.value) return;
  try {
    await tabletopStore.removeToken(roomId.value, tokenId);
    if (selection.value?.type === "token" && selection.value.id === tokenId) {
      clearSelection();
    }
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error),
      tone: "danger",
    });
  }
}

function isEditingText() {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  return (el as HTMLElement).isContentEditable;
}

function handleGlobalKeyDown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    if (activeInspection.value) {
      event.preventDefault();
      handleCloseInspection();
      return;
    }
  }
  if ((event.ctrlKey || event.metaKey) && !event.shiftKey && event.key.toLowerCase() === "z") {
    if (isEditingText()) return;
    if (toolMode.value !== "draw") return;
    event.preventDefault();
    void undoLastDrawing();
    return;
  }
  if (event.key !== "Delete") return;
  if (isEditingText()) return;
  if (!selection.value || !roomId.value) return;

  const sel = selection.value;
  if (sel.type === "map") {
    if (currentUserGameRole.value === "GM") {
      void handleContextDeleteMap(sel.id);
    }
  } else if (sel.type === "token") {
    const token = tabletopTokens.value.find((t) => t.id === sel.id);
    if (token && tokenCanManage(token)) {
      void handleContextDeleteToken(sel.id);
    }
  } else if (sel.type === "drawing") {
    if (currentUserGameRole.value === "GM" || currentUserGameRole.value === "PL") {
      void handleContextDeleteDrawing(sel.id);
    }
  }
}

async function handleContextTokenLayer(action: "up" | "down" | "top" | "bottom") {
  const token = selectedToken.value;
  if (!token || !roomId.value || tabletopTokens.value.length <= 1) return;
  const sorted = [...tabletopTokens.value].sort((a, b) => a.z_index - b.z_index);
  const idx = sorted.findIndex((t) => t.id === token.id);
  if (idx < 0) return;
  let target = token.z_index;
  if (action === "up" && idx < sorted.length - 1) {
    target = sorted[idx + 1]!.z_index;
  } else if (action === "down" && idx > 0) {
    target = sorted[idx - 1]!.z_index;
  } else if (action === "top") {
    target = Math.max(...sorted.map((t) => t.z_index)) + 1;
  } else if (action === "bottom") {
    target = Math.min(...sorted.map((t) => t.z_index)) - 1;
  }
  if (target === token.z_index) return;
  try {
    await tabletopStore.updateToken(roomId.value, token.id, { z_index: target });
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

async function handlePickLibraryMap(resource: LibraryResource) {
  if (!roomId.value) return;
  mapUploading.value = true;
  try {
    const map = await tabletopStore.addMapFromResource(roomId.value, resource.id);
    const offset = tabletopMaps.value.length * 24;
    await tabletopStore.updateMap(roomId.value, map.id, { x: offset, y: offset });
    selectMap(map.id);
    toasts.push({ message: t("table.assets.addMapFromLibrarySuccess"), tone: "success" });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.addMapFromLibraryFailed"),
      tone: "danger",
    });
  } finally {
    mapUploading.value = false;
  }
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
    const map = await tabletopStore.uploadMap(roomId.value, file);
    selectMap(map.id);
    pendingAnnotationMap.value = { id: map.id, assetId: map.asset_id ?? 0, libraryResourceId: map.library_resource_id, dims };
    gridAnnotationOpen.value = true;
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.uploadFailed"),
      tone: "danger",
    });
  } finally {
    mapUploading.value = false;
  }
}

async function handleAnnotate(payload: { calibration: GridSampleRect[] }) {
  const pending = pendingAnnotationMap.value;
  pendingAnnotationMap.value = null;
  if (!pending || !roomId.value || payload.calibration.length === 0) return;
  const cellPx = gridCellPx.value;
  const { cellWidth, phaseX, cellHeight, phaseY } = fitGridFromSamples(payload.calibration);
  const scaleX = cellPx / cellWidth;
  const scaleY = cellPx / cellHeight;
  const center = viewportCenterPoint();
  const idealX = center.x - (pending.dims.w * scaleX) / 2;
  const idealY = center.y - (pending.dims.h * scaleY) / 2;
  const screenPhaseX = ((phaseX * scaleX) % cellPx + cellPx) % cellPx;
  const screenPhaseY = ((phaseY * scaleY) % cellPx + cellPx) % cellPx;
  const x = Math.round((idealX + screenPhaseX) / cellPx) * cellPx - screenPhaseX;
  const y = Math.round((idealY + screenPhaseY) / cellPx) * cellPx - screenPhaseY;
  const first = payload.calibration[0];
  if (!first) return;
  try {
    await patchLibraryResourceGrid(pending.libraryResourceId, {
      map_grid_x: first.x,
      map_grid_y: first.y,
      map_grid_size: cellWidth,
      map_grid_cell_height: cellHeight,
      map_grid_calibration: payload.calibration,
    });
    await tabletopStore.updateMap(roomId.value, pending.id, { scale_x: scaleX, scale_y: scaleY, x, y });
    toasts.push({ message: t("table.assets.uploadSuccess"), tone: "success" });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.uploadFailed"),
      tone: "danger",
    });
  }
}

function handleAnnotationClose() {
  const pending = pendingAnnotationMap.value;
  pendingAnnotationMap.value = null;
  if (!pending || !roomId.value) return;
  const viewportWidth = mapViewportRef.value?.getViewportWidth() ?? window.innerWidth;
  const scale = computeMapScaleForViewport(pending.dims.w, viewportWidth);
  const offset = (tabletopMaps.value.length - 1) * 24;
  void tabletopStore.updateMap(roomId.value, pending.id, { scale, x: offset, y: offset }).then(() => {
    toasts.push({ message: t("table.assets.uploadSuccess"), tone: "success" });
  }).catch((error: unknown) => {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.uploadFailed"),
      tone: "danger",
    });
  });
}

async function handleCancelAnnotation() {
  const pending = pendingAnnotationMap.value;
  pendingAnnotationMap.value = null; // clear before watch fires to skip handleAnnotationClose
  if (!pending || !roomId.value) return;
  clearSelection();
  try {
    await tabletopStore.removeMap(roomId.value, pending.id);
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("table.assets.uploadFailed"),
      tone: "danger",
    });
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
  selfDisplayName: currentUserDisplayName,
  canSend: canDraw,
});

const realtime = useRoomRealtimeSession({
  roomId,
  gameRole: currentUserGameRole,
  refreshRoom: () => fetchRoom({ silent: true }),
  refreshRoomMembers: fetchRoomMembers,
  refreshRoomRequests: () => fetchRoomRequests({ force: true }),
  refreshRoomCharacters: fetchRoomCharacters,
  onCharacterStateUpdated: (characterId, summary) => {
    updateRoomCharacterState(characterId, summary);
  },
  onRoomCharacterUpdated: (entry) => {
    applyRoomCharacterVisibility(entry);
    tabletopStore.applyCharacterVisibilityChanged(roomId.value, entry.character_id, entry.is_hidden);
  },
  onSessionClosed: handleRealtimeSessionClosed,
  onPointerPresence: handlePointerPresence,
  onPointerLaser: handlePointerLaser,
  onObjectSelection: handleObjectSelection,
});

watch(
  () => realtime.isRealtimeActive.value,
  (active) => {
    if (active && lastClaimedSelection) {
      sendLocalObjectSelectionClaim(lastClaimedSelection);
    }
  },
);

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

const playerColorByUserId = computed(() => {
  const map = new Map<number, string>();
  for (const member of entityRoomMembers.value) {
    if (member.player_color) {
      map.set(member.user_id, member.player_color);
    }
  }
  return map;
});

const selfPlayerColor = computed(() => {
  const meId = currentUserId.value;
  if (!meId) return null;
  return playerColorByUserId.value.get(meId) ?? null;
});

const takenPlayerColors = computed(() => {
  const meId = currentUserId.value;
  const taken = new Set<string>();
  for (const member of entityRoomMembers.value) {
    if (member.player_color && member.user_id !== meId) {
      taken.add(member.player_color);
    }
  }
  return taken;
});

const playerColorSaving = ref(false);

async function updatePlayerColor(color: string) {
  if (!roomId.value || playerColorSaving.value) return;
  playerColorSaving.value = true;
  try {
    const updated = await patchMyPlayerColor(roomId.value, color);
    entitiesStore.upsertRoomMember(updated);
    strokeColor.value = color;
  } catch (e) {
    toasts.push({
      message: getBackendErrorMessage(e) || t("room.playerColor.saveFailed"),
      tone: "danger",
    });
  } finally {
    playerColorSaving.value = false;
  }
}

watch(selfPlayerColor, (color) => {
  if (color) strokeColor.value = color;
}, { immediate: true });

const presentUserIds = computed(() => new Set(realtime.presentUserIds.value));
const remoteObjectSelections = computed<RemoteObjectSelection[]>(() =>
  Object.values(remoteObjectSelectionByKey.value)
    .filter((claim) => claim.userId !== currentUserId.value)
    .filter((claim) => claim.expiresAt == null || claim.expiresAt > objectSelectionNow.value)
    .filter((claim) => !realtime.hasPresenceSnapshot.value || presentUserIds.value.has(claim.userId))
    .map((claim) => ({
      ...claim,
      color: claim.color ?? playerColorByUserId.value.get(claim.userId) ?? null,
    })),
);
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
    player_color: member.player_color ?? null,
    status: memberStatus,
  };
}));
const roomMemberStatusByUserId = computed<Map<number, MemberStatus>>(() =>
  new Map(roomMemberItems.value.map((member) => [member.id, member.status])));

const inRoomCharacterIds = computed(
  () => new Set(roomCharacters.value.map((e) => e.character_id)),
);

const ownerNameByUserId = computed(() => {
  const map = new Map(roomMemberItems.value.map((member) => [member.id, member.name]));
  for (const entry of spawnPopoverEntries.value) {
    if (map.has(entry.owner_id)) continue;
    const user = entitiesStore.getUser(entry.owner_id);
    const name = user?.username?.trim() || user?.email?.trim();
    if (name) map.set(entry.owner_id, name);
  }
  return map;
});

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

async function fetchRoomDiceRolls() {
  if (!roomId.value) return;
  try {
    await diceStore.refreshRoomRolls(roomId.value, 30);
  } catch {
    // dice.store keeps the panel error state
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

function openAddCharacterDialog() {
  characterPopoverOpen.value = true;
  addCharacterDialogOpen.value = true;
}

function closeAddCharacterDialog() {
  addCharacterDialogOpen.value = false;
}

const OPEN_CHARACTER_POPOVER_QUERY = "openCharacterPopover";

function applyOpenCharacterPopoverFromQuery() {
  if (route.query[OPEN_CHARACTER_POPOVER_QUERY] !== "1") return;
  characterPopoverOpen.value = true;
  void fetchRoomCharacters();
  const nextQuery = { ...route.query };
  delete nextQuery[OPEN_CHARACTER_POPOVER_QUERY];
  void router.replace({ query: nextQuery });
}

async function handleCreateRoomQuick(payload: {
  name: string;
  max_hp: number | null;
  armor_class: number | null;
  backstory: string;
  portrait_asset_id: number | null;
  spawnAfterCreate?: boolean;
}) {
  if (!roomId.value) {
    toasts.push({ message: t("room.invalidId"), tone: "danger" });
    return;
  }
  if (characterSubmitting.value) return;
  characterSubmitting.value = true;
  try {
    const hasState = payload.max_hp != null || payload.armor_class != null;
    const flavor: Record<string, unknown> = {};
    if (payload.backstory) flavor.backstory = payload.backstory;

    const entry = await createRoomCharacter({
      name: payload.name,
      flavor,
      state: hasState
        ? {
            max_hp: payload.max_hp,
            current_hp: payload.max_hp,
            armor_class: payload.armor_class,
          }
        : undefined,
      portrait_asset_id: payload.portrait_asset_id ?? undefined,
    });
    closeAddCharacterDialog();
    characterPopoverOpen.value = true;
    toasts.push({ message: t("room.characters.created"), tone: "success" });
    if (payload.spawnAfterCreate) {
      await handleSpawnCharacter(entry.character_id);
    }
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("room.characters.createFailed"),
      tone: "danger",
    });
  } finally {
    characterSubmitting.value = false;
  }
}

onMounted(() => {
  applyOpenCharacterPopoverFromQuery();
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomDiceRolls();
  void fetchRoomMembers();
  if (roomId.value) {
    void tabletopStore.loadSnapshot(roomId.value);
    void fetchRoomCharacters();
  }
  window.addEventListener("keydown", handleGlobalKeyDown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleGlobalKeyDown);
});

watch(roomId, (newId, oldId) => {
  closeAddCharacterDialog();
  characterPopoverOpen.value = false;
  currentUserRoomRole.value = "unknown";
  currentUserGameRole.value = "unknown";
  resetRoomRequestsState();
  resetMemberActionState();
  if (oldId) {
    tabletopStore.resetRoom(oldId);
  }
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomDiceRolls();
  void fetchRoomMembers();
  if (newId) {
    void tabletopStore.loadSnapshot(newId);
    void fetchRoomCharacters();
  }
});
watch(() => auth.me?.id, () => {
  syncCurrentUserRoles();
});
watch([roomId, currentUserRoomRole], () => {
  void fetchRoomRequests();
});
watch(
  () => route.query[OPEN_CHARACTER_POPOVER_QUERY],
  () => applyOpenCharacterPopoverFromQuery(),
);
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
            :room-id="roomId"
            :maps="tabletopMaps"
            :tokens="tabletopTokens"
            :drawings="tabletopDrawings"
            :combat-state="tabletopSettings?.combat_state ?? null"
            :grid-cell-px="gridCellPx"
            :grid-cell-ft="gridCellFt"
            :scale-bar-cells="scaleBarCells"
            :tool-mode="toolMode"
            :game-role="currentUserGameRole"
            :current-user-id="currentUserId"
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
            :remote-object-selections="remoteObjectSelections"
            :player-color-by-user-id="playerColorByUserId"
            :measure-state="measureState"
            :character-owner-by-id="characterOwnerById"
            @select-map="handleSelectMap"
            @map-context-menu="handleMapContextMenu"
            @select-token="handleSelectToken"
            @token-context-menu="handleTokenContextMenu"
            @select-drawing="handleSelectDrawing"
            @drawing-context-menu="handleDrawingContextMenu"
            @text-placement-resize="handleTextPlacementResize"
            @patch-map="handlePatchMap"
            @preview-token="handlePreviewToken"
            @commit-token="handleCommitToken"
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
            :measure-sub-tool="measureSubTool"
            @measure-pointer-down="measurePointerDown"
            @measure-pointer-move="handleMeasurePointerMove"
            @measure-pointer-up="measurePointerUp"
            @measure-route-click="routeClick"
            @measure-route-finish="routeFinish"
          />
          <ContextMenu
            :open="contextMenuOpen"
            :client-x="contextMenuX"
            :client-y="contextMenuY"
            :selection="selection"
            :maps="tabletopMaps"
            :tokens="tabletopTokens"
            :drawings="tabletopDrawings"
            :game-role="currentUserGameRole"
            :current-user-id="currentUserId"
            :character-owner-by-id="characterOwnerById"
            @close="closeContextMenu"
            @align-map-to-grid="handleContextAlignMapToGrid"
            @delete-map="handleContextDeleteMap"
            @delete-drawing="handleContextDeleteDrawing"
            @delete-token="handleContextDeleteToken"
            @inspect-token="handleInspectToken"
            @edit-text-drawing="handleEditTextDrawing"
            @toggle-map-lock="handleContextToggleMapLock"
            @map-layer="handleContextMapLayer"
            @token-layer="handleContextTokenLayer"
            @drawing-layer="handleContextDrawingLayer"
            @open-dice-roll="handleOpenDiceRoll"
          />
          <AddRoomCharacterDialog
            :open="addCharacterDialogOpen"
            :room-id="roomId"
            :game-role="currentUserGameRole"
            :current-user-display-name="currentUserDisplayName"
            :submitting="characterSubmitting"
            :library-characters="libraryCharacters"
            :library-loading="libraryLoading"
            :in-room-character-ids="inRoomCharacterIds"
            @close="closeAddCharacterDialog"
            @create-quick="handleCreateRoomQuick"
            @link-character="handleLinkRoomCharacter"
          />
          <LibraryMapPickerDialog
            v-model="libraryMapPickerOpen"
            @pick="handlePickLibraryMap"
          />
          <MapGridAnnotationDialog
            v-model="gridAnnotationOpen"
            :asset-id="pendingAnnotationMap?.assetId ?? null"
            @annotate="handleAnnotate"
            @cancel="handleCancelAnnotation"
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
            :current-user-id="currentUserId"
            :taken-player-colors="takenPlayerColors"
            :player-color-saving="playerColorSaving"
            @update-player-color="updatePlayerColor"
          />
          <InGameCharacterList
            :room-id="roomId"
            :entries="roomCharacters"
            :owner-name-by-user-id="ownerNameByUserId"
            :current-user-id="currentUserId ?? undefined"
            :loading="roomCharactersLoading"
            :game-role="currentUserGameRole"
            :selected-character-id="selectedCharacterListId"
            @inspect="handleInspectCharacter"
            @toggle-visibility="handleToggleCharacterVisibility"
            @remove="handleRemoveRoomCharacter"
          />

          <FloatingPanel
            :title="t('table.assets.barTitle')"
            inline
            collapse-to="top-left"
            variant="assets"
            :storage-key="`room-${roomId}-assets`"
          >
            <BottomAssetBar
              v-model:map-popover-open="mapPopoverOpen"
              v-model:token-popover-open="tokenPopoverOpen"
              :can-add-map="canAddMap"
              :can-add-token="canAddToken"
              :maps="tabletopMaps"
              :selected-map-id="selectedMapId"
              :characters="tokenSpawnCharacters"
              @add-map="handleAddMapClick"
              @select-map="selectMap"
              @open-library-picker="libraryMapPickerOpen = true"
              @spawn-token="(cid, cfgId) => handleSpawnCharacter(cid, cfgId)"
              @spawn-all="(cid) => handleSpawnAllTokens(cid)"
              @add-character="openAddCharacterDialog"
            />
          </FloatingPanel>

          </div>

          <FloatingPanel
            v-model:collapsed="chatPanelCollapsed"
            :title="t('table.chat.title')"
            anchor="bottom-left"
            collapse-to="bottom-left"
            variant="chat"
            :storage-key="`room-${roomId}-chat`"
          >
            <RoomChatTab
              :room-key="roomId"
              :active="true"
              :game-role="currentUserGameRole"
              :current-user-id="currentUserId"
              :character-owner-by-id="characterOwnerById"
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
            title="战斗"
            anchor="bottom-center"
            collapse-to="bottom"
            variant="combat"
            :storage-key="`room-${roomId}-combat`"
          >
            <CombatPanel
              :room-id="roomId"
              :tokens="tabletopTokens"
              :members="entityRoomMembers"
              :combat-state="tabletopSettings?.combat_state ?? null"
              :game-role="currentUserGameRole"
              :current-user-id="currentUserId"
              :saving="combatSaving"
              @update-combat="handleUpdateCombat"
              @select-token="handleCombatSelectToken"
              @focus-token="handleCombatFocusToken"
              @error="(message) => toasts.push({ message, tone: 'danger' })"
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
              @reset-viewport="mapViewportRef?.resetViewport()"
            />
            <DrawToolStrip
              v-if="toolMode === 'draw' && canDraw"
              v-model:sub-tool="subTool"
              v-model:stroke-color="strokeColor"
              v-model:stroke-width="strokeWidth"
              v-model:font-size="fontSize"
            />
            <MeasureToolStrip
              v-if="toolMode === 'measure'"
              v-model:sub-tool="measureSubTool"
            />
          </FloatingPanel>

          <div class="rightStack">
            <Transition name="infoPanel">
              <InfoPanel
                v-if="activeInspection"
                :inspection="activeInspection"
                :room-id="roomId"
                :game-role="currentUserGameRole"
                :current-user-id="currentUserId"
                @close="handleCloseInspection"
              />
            </Transition>

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

.infoPanel-enter-active,
.infoPanel-leave-active {
  transition: opacity 0.15s ease;
}

.infoPanel-enter-from,
.infoPanel-leave-to {
  opacity: 0;
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
