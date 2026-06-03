import wsClient from "@/infra/realtime/wsClient";

export type RoomRealtimePresenceState = {
  room_id: number;
  present_user_ids: number[];
};

export type RoomRealtimeSnapshot = {
  room_id: number;
  present_user_ids: number[];
};

export type RoomRealtimeSessionClosed = {
  room_id: number;
  reason: "entered_elsewhere" | "left_room" | "removed_from_room" | "room_deleted";
};

export type RoomRealtimePresenceGetResponse = {
  presence?: RoomRealtimePresenceState | null;
};

export function enterRoomRealtime(roomId: number) {
  return wsClient.command<RoomRealtimeSnapshot>("room_enter", {
    room_id: roomId,
  });
}

export function leaveRoomRealtime(roomId: number) {
  return wsClient.command<void>("room_leave", {
    room_id: roomId,
  });
}

export function getRoomRealtimePresence() {
  return wsClient.command<RoomRealtimePresenceGetResponse, null>("room_presence_get", null);
}
