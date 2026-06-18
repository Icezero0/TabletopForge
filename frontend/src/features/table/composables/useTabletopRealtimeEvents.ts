import { onBeforeUnmount, onMounted, type Ref } from "vue";
import wsClient from "@/infra/realtime/wsClient";
import type { GameRole } from "@/features/room/types";
import { pickCharacterStateSummaryForRole } from "@/features/table/utils/tokenDisplay";
import type {
  RoomDrawing,
  RoomMap,
  RoomToken,
  RoomTabletopSettings,
  TokenStateSummary,
} from "@/infra/api/rooms.api";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import { useTabletopStore } from "@/stores/tabletop.store";
import type {
  PointerLaserPayload,
  PointerPresencePayload,
  ObjectSelectionPayload,
  TokenTransformPreviewPayload,
} from "@/infra/realtime/tabletopRealtime";

type UseTabletopRealtimeEventsOptions = {
  roomId: Ref<number>;
  gameRole: Ref<GameRole | "unknown">;
  refreshRoomCharacters?: () => void | Promise<void>;
  refreshRoomScenes?: () => void | Promise<void>;
  onCharacterStateUpdated?: (characterId: number, summary: TokenStateSummary) => void;
  onRoomCharacterUpdated?: (entry: RoomCharacterEntry) => void;
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

export function useTabletopRealtimeEvents(options: UseTabletopRealtimeEventsOptions) {
  const tabletopStore = useTabletopStore();
  let stopEventSubscriptions: Array<() => void> = [];

  function bindEvents() {
    stopEventSubscriptions = [
      wsClient.onEvent("room_characters", (payload) => {
        if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
        void options.refreshRoomCharacters?.();
        void tabletopStore.loadSnapshot(options.roomId.value);
      }),
      wsClient.onEvent<{ room_id: number; settings: RoomTabletopSettings }>(
        "tabletop_settings_updated",
        (payload) => {
          if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
          tabletopStore.applySettings(options.roomId.value, payload.settings);
        },
      ),
      wsClient.onEvent<{ room_id: number; scene_id: number }>(
        "tabletop_snapshot_replaced",
        (payload) => {
          if (!isCurrentRoomPayload(payload, options.roomId.value)) return;
          void tabletopStore.loadSnapshot(options.roomId.value);
          void options.refreshRoomCharacters?.();
          void options.refreshRoomScenes?.();
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

  onMounted(bindEvents);

  onBeforeUnmount(() => {
    stopEventSubscriptions.forEach((stop) => stop());
    stopEventSubscriptions = [];
  });
}
