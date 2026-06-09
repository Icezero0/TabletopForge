import { onBeforeUnmount, onMounted, ref, watch, type Ref } from "vue";
import wsClient, { type WSConnectionStatus } from "@/infra/realtime/wsClient";
import {
  enterRoomRealtime,
  getRoomRealtimePresence,
  leaveRoomRealtime,
  type RoomRealtimePresenceState,
  type RoomRealtimeSessionClosed,
  type RoomRealtimeSnapshot,
} from "@/infra/realtime/roomRealtime";
import type { GameRole } from "@/features/room/types";
import { pickCharacterStateSummaryForRole } from "@/features/table/utils/tokenDisplay";
import type {
  RoomDrawing,
  RoomMap,
  RoomToken,
  RoomTabletopSettings,
  TokenStateSummary,
} from "@/infra/api/rooms.api";
import type { MessageResponse } from "@/infra/api/messages.api";
import type { DiceRoll } from "@/infra/api/dice.api";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import { useAuthStore } from "@/stores/auth.store";
import { useMessagesStore } from "@/stores/messages.store";
import { useDiceStore } from "@/stores/dice.store";
import { useTabletopStore } from "@/stores/tabletop.store";

import type {
  PointerLaserPayload,
  PointerPresencePayload,
  ObjectSelectionPayload,
  TokenTransformPreviewPayload,
} from "@/infra/realtime/tabletopRealtime";

type UseRoomRealtimeSessionOptions = {
  roomId: Ref<number>;
  gameRole: Ref<GameRole | "unknown">;
  refreshRoom: () => void | Promise<void>;
  refreshRoomMembers: () => void | Promise<void>;
  refreshRoomRequests: () => void | Promise<void>;
  refreshRoomCharacters?: () => void | Promise<void>;
  onCharacterStateUpdated?: (characterId: number, summary: TokenStateSummary) => void;
  onRoomCharacterUpdated?: (entry: RoomCharacterEntry) => void;
  onSessionClosed?: (payload: RoomRealtimeSessionClosed) => void;
  onPointerPresence?: (payload: PointerPresencePayload) => void;
  onPointerLaser?: (payload: PointerLaserPayload) => void;
  onObjectSelection?: (payload: ObjectSelectionPayload) => void;
};

function payloadRoomId(payload: unknown) {
  if (!payload || typeof payload !== "object") return null;

  const roomId = (payload as { room_id?: unknown }).room_id;
  return typeof roomId === "number" ? roomId : null;
}

function isCurrentRoomPayload(payload: unknown, roomId: number) {
  const eventRoomId = payloadRoomId(payload);
  return eventRoomId == null || eventRoomId === roomId;
}

function normalizePresentUserIds(snapshot: RoomRealtimeSnapshot) {
  return Array.isArray(snapshot.present_user_ids)
    ? snapshot.present_user_ids.filter((id) => typeof id === "number")
    : [];
}

export function useRoomRealtimeSession(options: UseRoomRealtimeSessionOptions) {
  const auth = useAuthStore();
  const messagesStore = useMessagesStore();
  const diceStore = useDiceStore();
  const tabletopStore = useTabletopStore();
  const presentUserIds = ref<number[]>([]);
  const hasPresenceSnapshot = ref(false);
  const isRealtimeActive = ref(false);
  const realtimeStatus = ref<WSConnectionStatus>(wsClient.connectionStatus);
  const realtimeError = ref("");

  let stopStatusSubscription: (() => void) | null = null;
  let stopEventSubscriptions: Array<() => void> = [];
  let enteredRoomId: number | null = null;
  let enteringRoomId: number | null = null;
  let enterAttempt = 0;

  async function ensureConnectionReady() {
    auth.syncTokensFromStorage();

    if (!auth.isLoggedIn || !auth.accessToken) {
      throw new Error("Realtime connection requires an authenticated user");
    }

    await wsClient.connect(auth.accessToken);
  }

  async function enterCurrentRoom() {
    const roomId = options.roomId.value;
    auth.syncTokensFromStorage();
    if (!roomId || !auth.isLoggedIn || !auth.accessToken) return;
    if (enteredRoomId === roomId || enteringRoomId === roomId) return;

    const attempt = ++enterAttempt;
    enteringRoomId = roomId;
    realtimeError.value = "";

    try {
      await ensureConnectionReady();
      if (attempt !== enterAttempt || roomId !== options.roomId.value) return;

      const snapshot = await enterRoomRealtime(roomId);
      if (attempt !== enterAttempt || roomId !== options.roomId.value) return;

      enteredRoomId = roomId;
      isRealtimeActive.value = true;
      presentUserIds.value = normalizePresentUserIds(snapshot);
      hasPresenceSnapshot.value = true;
    } catch (error) {
      if (attempt !== enterAttempt) return;
      isRealtimeActive.value = false;
      realtimeError.value =
        error instanceof Error ? error.message : "Failed to enter realtime room";
    } finally {
      if (enteringRoomId === roomId) {
        enteringRoomId = null;
      }
    }
  }

  async function leaveEnteredRoom(roomId = enteredRoomId) {
    if (!roomId) return;

    enteredRoomId = null;
    enteringRoomId = null;
    isRealtimeActive.value = false;
    presentUserIds.value = [];
    hasPresenceSnapshot.value = false;

    if (wsClient.connectionStatus !== "ready") return;

    try {
      await leaveRoomRealtime(roomId);
    } catch {
      // Leaving is best-effort; the server also cleans up on disconnect.
    }
  }

  function refreshIfCurrentRoom(payload: unknown, refresh: () => void | Promise<void>) {
    const roomId = options.roomId.value;
    if (!roomId || !isCurrentRoomPayload(payload, roomId)) return;
    void refresh();
  }

  function handlePresence(payload: RoomRealtimePresenceState) {
    if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
    presentUserIds.value = Array.isArray(payload.present_user_ids)
      ? payload.present_user_ids.filter((id) => typeof id === "number")
      : [];
    hasPresenceSnapshot.value = true;
  }

  function handleMessage(payload: MessageResponse) {
    if (!payload?.room_id || payload.room_id !== options.roomId.value) return;
    messagesStore.appendRealtimeMessage(payload);
  }

  function handleDiceRoll(payload: DiceRoll) {
    if (!payload?.room_id || payload.room_id !== options.roomId.value) return;
    diceStore.appendRealtimeRoll(payload);
  }

  async function fetchPresenceSnapshot() {
    const response = await getRoomRealtimePresence();
    const presence = response.presence;
    if (!presence || !isCurrentRoomPayload(presence, options.roomId.value)) return;

    handlePresence(presence);
  }

  function handleSessionClosed(payload: RoomRealtimeSessionClosed) {
    if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
    enteredRoomId = null;
    isRealtimeActive.value = false;
    presentUserIds.value = [];
    hasPresenceSnapshot.value = true;
    options.onSessionClosed?.(payload);
  }

  function bindEvents() {
    stopEventSubscriptions = [
      wsClient.onEvent("room_info", (payload) => {
        refreshIfCurrentRoom(payload, options.refreshRoom);
      }),
      wsClient.onEvent("room_members", (payload) => {
        refreshIfCurrentRoom(payload, () => {
          void options.refreshRoomMembers();
          void options.refreshRoomRequests();
        });
      }),
      wsClient.onEvent("room_characters", (payload) => {
        refreshIfCurrentRoom(payload, () => {
          void options.refreshRoomCharacters?.();
          void tabletopStore.loadSnapshot(options.roomId.value);
        });
      }),
      wsClient.onEvent<RoomRealtimePresenceState>("room_user_presence", handlePresence),
      wsClient.onEvent<MessageResponse>("message", handleMessage),
      wsClient.onEvent<DiceRoll>("dice_roll", handleDiceRoll),
      wsClient.onEvent<RoomRealtimeSessionClosed>("session_closed", handleSessionClosed),
      wsClient.onEvent<{ room_id: number; settings: RoomTabletopSettings }>(
        "tabletop_settings_updated",
        (payload) => {
          if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
          tabletopStore.applySettings(options.roomId.value, payload.settings);
        },
      ),
      wsClient.onEvent<{ room_id: number; map: RoomMap }>("map_created", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyMapCreated(options.roomId.value, payload.map);
      }),
      wsClient.onEvent<{ room_id: number; map: RoomMap }>("map_updated", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyMapUpdated(options.roomId.value, payload.map);
      }),
      wsClient.onEvent<{ room_id: number; map_id: number }>("map_deleted", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyMapDeleted(options.roomId.value, payload.map_id);
      }),
      wsClient.onEvent<{ room_id: number; drawing: RoomDrawing }>("drawing_created", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyDrawingCreated(options.roomId.value, payload.drawing);
      }),
      wsClient.onEvent<{ room_id: number; drawing: RoomDrawing }>("drawing_updated", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyDrawingUpdated(options.roomId.value, payload.drawing);
      }),
      wsClient.onEvent<{ room_id: number; drawing_ids: number[] }>("drawing_deleted", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyDrawingsDeleted(options.roomId.value, payload.drawing_ids);
      }),
      wsClient.onEvent<{ room_id: number; token: RoomToken }>("token_created", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyTokenCreated(options.roomId.value, payload.token);
      }),
      wsClient.onEvent<{ room_id: number; token: RoomToken }>("token_updated", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyTokenUpdated(options.roomId.value, payload.token);
      }),
      wsClient.onEvent<{ room_id: number; token_id: number }>("token_deleted", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        tabletopStore.applyTokenDeleted(options.roomId.value, payload.token_id);
      }),
      wsClient.onEvent<TokenTransformPreviewPayload>(
        "token_transform_preview",
        (payload) => {
          if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
          tabletopStore.applyTokenPatch(
            options.roomId.value,
            payload.token_id,
            payload.transform,
          );
        },
      ),
      wsClient.onEvent<{
        room_id: number;
        character_id: number;
        state_summary: TokenStateSummary;
        state_summary_public?: TokenStateSummary;
      }>("character_state_updated", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        const summary = pickCharacterStateSummaryForRole(
          payload,
          options.gameRole.value,
        );
        tabletopStore.applyCharacterStateUpdated(
          options.roomId.value,
          payload.character_id,
          summary,
        );
        options.onCharacterStateUpdated?.(payload.character_id, summary);
      }),
      wsClient.onEvent<{ room_id: number; entry: RoomCharacterEntry }>(
        "room_character_updated",
        (payload) => {
          if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
          options.onRoomCharacterUpdated?.(payload.entry);
          void tabletopStore.loadSnapshot(options.roomId.value);
        },
      ),
      wsClient.onEvent<PointerPresencePayload>("pointer_presence", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        options.onPointerPresence?.(payload);
      }),
      wsClient.onEvent<PointerLaserPayload>("pointer_laser", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        options.onPointerLaser?.(payload);
      }),
      wsClient.onEvent<ObjectSelectionPayload>("object_selection", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        options.onObjectSelection?.(payload);
      }),
    ];
  }

  onMounted(() => {
    bindEvents();
    stopStatusSubscription = wsClient.onStatusChange((status) => {
      realtimeStatus.value = status;
      if (
        status === "ready" &&
        enteredRoomId !== options.roomId.value &&
        enteringRoomId !== options.roomId.value
      ) {
        void enterCurrentRoom();
      }
    });
    void enterCurrentRoom();
  });

  watch(
    () => options.roomId.value,
    async (roomId, previousRoomId) => {
      enterAttempt += 1;
      if (previousRoomId) {
        await leaveEnteredRoom(previousRoomId);
      }
      if (roomId) {
        void enterCurrentRoom();
      }
    },
  );

  watch(
    () => [auth.isLoggedIn, auth.accessToken] as const,
    ([isLoggedIn, accessToken]) => {
      if (!isLoggedIn || !accessToken) {
        enterAttempt += 1;
        void leaveEnteredRoom();
        return;
      }
      void enterCurrentRoom();
    },
  );

  onBeforeUnmount(() => {
    enterAttempt += 1;
    stopStatusSubscription?.();
    stopEventSubscriptions.forEach((stop) => stop());
    stopEventSubscriptions = [];
    void leaveEnteredRoom();
  });

  return {
    presentUserIds,
    hasPresenceSnapshot,
    isRealtimeActive,
    realtimeStatus,
    realtimeError,
    enterCurrentRoom,
    fetchPresenceSnapshot,
  };
}
