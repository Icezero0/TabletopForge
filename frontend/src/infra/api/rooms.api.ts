import { http } from "@/infra/http/client";

export type RoomVisibility = "public" | "private";
export type RoomJoinAuditMode =
  | "auto_approve"
  | "manual_review"
  | "auto_reject";
export type Room = {
  id: number;
  name: string;
  owner_id: number;
  owner_name?: string | null;
  owner_avatar_url?: string | null;
  visibility: RoomVisibility;
  my_room_role?: RoomRole | null;
  my_game_role?: GameRole | null;
  join_audit_mode?: RoomJoinAuditMode | null;
};

export type RoomListResponse = {
  items: Room[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type GameRole = "GM" | "PL" | "OB";

export type RoomCreatePayload = {
  name: string;
  visibility?: RoomVisibility;
  join_audit_mode?: RoomJoinAuditMode;
  creator_game_role?: GameRole;
};

export type RoomPatchPayload = {
  name?: string | null;
  visibility?: RoomVisibility | null;
  join_audit_mode?: RoomJoinAuditMode | null;
};

export type RoomRole = "owner" | "manager" | "member";

export type RoomUserBrief = {
  id: number;
  email: string;
  username: string | null;
  avatar_asset_id?: number | null;
  avatar_url: string | null;
};

export type RoomMember = {
  room_id: number;
  user_id: number;
  joined_at: string | null;
  room_role: RoomRole;
  game_role: GameRole;
  user: RoomUserBrief | null;
};

export type RoomMemberListResponse = {
  items: RoomMember[];
  total: number;
};

export type RoomJoinRequestSource = "apply" | "invite" | "member_invite";
export type RoomJoinRequestStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "cancelled";
export type RoomJoinRequestAction = "pending" | "approved" | "rejected";

export type RoomJoinRequest = {
  id: number;
  room_id: number;
  initiator_user_id: number;
  target_user_id: number;
  source: RoomJoinRequestSource;
  status: RoomJoinRequestStatus;
  room_action: RoomJoinRequestAction;
  target_action: RoomJoinRequestAction;
  room_action_by_user_id: number | null;
  created_at: string | null;
  updated_at: string | null;
  room?: RoomBrief | null;
  initiator: RoomUserBrief | null;
  target: RoomUserBrief | null;
  room_action_by: RoomUserBrief | null;
};

export type RoomJoinRequestListResponse = {
  items: RoomJoinRequest[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

type RoomResponse = {
  id: number;
  name: string;
  owner_id: number;
  visibility: RoomVisibility;
  join_audit_mode: RoomJoinAuditMode;
};

export type RoomBrief = {
  id: number;
  name: string;
  owner_id: number;
  visibility: RoomVisibility;
};

type UserRoomSummaryResponse = {
  id: number;
  name: string;
  owner_id: number;
  owner: RoomUserBrief;
  my_room_role: RoomRole;
  my_game_role: GameRole | null;
  is_public: boolean;
};

type UserRoomSummaryListResponse = {
  items: UserRoomSummaryResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

function mapRoomResponse(room: RoomResponse): Room {
  return {
    id: room.id,
    name: room.name,
    owner_id: room.owner_id,
    visibility: room.visibility,
    join_audit_mode: room.join_audit_mode,
  };
}

function mapUserRoomSummary(room: UserRoomSummaryResponse): Room {
  return {
    id: room.id,
    name: room.name,
    owner_id: room.owner_id,
    owner_name: room.owner?.username || room.owner?.email || null,
    owner_avatar_url: room.owner?.avatar_url || null,
    visibility: room.is_public ? "public" : "private",
    my_room_role: room.my_room_role,
    my_game_role: room.my_game_role,
  };
}

export async function getRooms(params?: {
  page?: number;
  page_size?: number;
  name?: string | null;
  owner_username?: string | null;
  owner_email?: string | null;
}) {
  // Backend currently defaults this endpoint to public rooms only.
  const { data } = await http.get<{
    items: RoomResponse[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }>("/rooms", { params });

  return {
    ...data,
    items: data.items.map(mapRoomResponse),
  } satisfies RoomListResponse;
}

export async function getMyRooms(params?: {
  page?: number;
  page_size?: number;
  role?: RoomRole | null;
}) {
  const { data } = await http.get<UserRoomSummaryListResponse>("/users/me/rooms", {
    params,
  });

  return {
    ...data,
    items: data.items.map(mapUserRoomSummary),
  } satisfies RoomListResponse;
}

export async function getMyOwnedRooms(params?: {
  page?: number;
  page_size?: number;
}) {
  const { data } = await http.get<UserRoomSummaryListResponse>("/users/me/owned-rooms", {
    params,
  });

  return {
    ...data,
    items: data.items.map(mapUserRoomSummary),
  } satisfies RoomListResponse;
}

export async function createRoom(payload: RoomCreatePayload) {
  const { data } = await http.post<RoomResponse>("/rooms", payload);
  return mapRoomResponse(data);
}

export async function getRoomById(roomId: number) {
  const { data } = await http.get<RoomResponse>(`/rooms/${roomId}`);
  return mapRoomResponse(data);
}

export async function patchRoom(roomId: number, payload: RoomPatchPayload) {
  const { data } = await http.patch<RoomResponse>(`/rooms/${roomId}`, payload);
  return mapRoomResponse(data);
}

export async function deleteRoom(roomId: number) {
  await http.delete(`/rooms/${roomId}`);
}

export async function getRoomMembers(roomId: number) {
  const { data } = await http.get<RoomMemberListResponse>(
    `/rooms/${roomId}/members`,
  );
  return data;
}

export async function getRoomJoinRequests(
  roomId: number,
  params?: {
    page?: number;
    page_size?: number;
    status?: RoomJoinRequestStatus | null;
    source?: RoomJoinRequestSource | null;
  },
) {
  const { data } = await http.get<RoomJoinRequestListResponse>(
    `/rooms/${roomId}/join-requests`,
    { params },
  );
  return data;
}

export async function applyRoomJoinRequest(roomId: number) {
  await http.post(`/rooms/${roomId}/join-requests/apply`);
}

export async function inviteRoomJoinRequest(
  roomId: number,
  payload: { target_user_id: number },
) {
  await http.post(`/rooms/${roomId}/join-requests/invite`, payload);
}

export async function removeRoomMember(roomId: number, targetUserId: number) {
  await http.delete(`/rooms/${roomId}/members/${targetUserId}`);
}

export async function leaveRoom(roomId: number) {
  await http.delete(`/rooms/${roomId}/members/me`);
}

export async function setRoomMemberManager(roomId: number, targetUserId: number) {
  const { data } = await http.put<RoomMember>(
    `/rooms/${roomId}/members/${targetUserId}/manager`,
  );
  return data;
}

export async function unsetRoomMemberManager(roomId: number, targetUserId: number) {
  const { data } = await http.delete<RoomMember>(
    `/rooms/${roomId}/members/${targetUserId}/manager`,
  );
  return data;
}

export async function patchRoomMemberGameRole(
  roomId: number,
  targetUserId: number,
  payload: { game_role: GameRole },
) {
  const { data } = await http.patch<RoomMember>(
    `/rooms/${roomId}/members/${targetUserId}/game-role`,
    payload,
  );
  return data;
}

export type RoomPersonalMemo = {
  content: string;
  updated_at: string | null;
};

export async function getRoomPersonalMemo(roomId: number) {
  const { data } = await http.get<RoomPersonalMemo>(
    `/rooms/${roomId}/personal-memo`,
  );
  return data;
}

export async function putRoomPersonalMemo(
  roomId: number,
  payload: { content: string },
) {
  const { data } = await http.put<RoomPersonalMemo>(
    `/rooms/${roomId}/personal-memo`,
    payload,
  );
  return data;
}

export type DrawingKind = "brush" | "line" | "rect" | "ellipse" | "text";

export type RoomTabletopSettings = {
  grid_cell_ft: number;
  grid_cell_px: number;
  updated_at: string | null;
};

export type RoomMap = {
  id: number;
  room_id: number;
  asset_id: number;
  x: number;
  y: number;
  scale: number;
  locked: boolean;
  z_index: number;
  created_at: string | null;
  updated_at: string | null;
};

export type RoomDrawing = {
  id: number;
  room_id: number;
  kind: DrawingKind;
  geometry: Record<string, unknown>;
  style: Record<string, unknown>;
  z_index: number;
  created_by_user_id: number;
  created_at: string | null;
  updated_at: string | null;
};

export type RoomTabletopSnapshot = {
  settings: RoomTabletopSettings;
  maps: RoomMap[];
  drawings: RoomDrawing[];
  tokens: RoomToken[];
};

export type TokenStateSummary = {
  current_hp: number | null;
  max_hp: number | null;
  ac: number | null;
  pp: number | null;
  damage_taken?: number | null;
};

export type RoomToken = {
  id: number;
  room_id: number;
  asset_id: number | null;
  linked_character_id: number | null;
  name: string;
  token_type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  z_index: number;
  visible: boolean;
  locked: boolean;
  owner_user_id: number;
  linked_character_owner_id?: number | null;
  state_summary: TokenStateSummary | null;
  created_at: string | null;
  updated_at: string | null;
};

export function assetContentUrl(assetId: number) {
  return `/assets/${assetId}/content`;
}

export async function getRoomTabletop(roomId: number) {
  const { data } = await http.get<RoomTabletopSnapshot>(`/rooms/${roomId}/tabletop`);
  return data;
}

export async function patchRoomTabletopSettings(
  roomId: number,
  payload: { grid_cell_ft?: number; grid_cell_px?: number },
) {
  const { data } = await http.patch<RoomTabletopSettings>(
    `/rooms/${roomId}/tabletop/settings`,
    payload,
  );
  return data;
}

export async function postRoomMap(roomId: number, file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await http.post<RoomMap>(`/rooms/${roomId}/maps`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function patchRoomMap(
  roomId: number,
  mapId: number,
  payload: {
    x?: number;
    y?: number;
    scale?: number;
    locked?: boolean;
    z_index?: number;
  },
) {
  const { data } = await http.patch<RoomMap>(
    `/rooms/${roomId}/maps/${mapId}`,
    payload,
  );
  return data;
}

export async function deleteRoomMap(roomId: number, mapId: number) {
  await http.delete(`/rooms/${roomId}/maps/${mapId}`);
}

export async function postRoomDrawing(
  roomId: number,
  payload: {
    kind: DrawingKind;
    geometry: Record<string, unknown>;
    style?: Record<string, unknown>;
    z_index?: number;
  },
) {
  const { data } = await http.post<RoomDrawing>(`/rooms/${roomId}/drawings`, payload);
  return data;
}

export async function patchRoomDrawing(
  roomId: number,
  drawingId: number,
  payload: {
    geometry?: Record<string, unknown>;
    style?: Record<string, unknown>;
    z_index?: number;
  },
) {
  const { data } = await http.patch<RoomDrawing>(
    `/rooms/${roomId}/drawings/${drawingId}`,
    payload,
  );
  return data;
}

export async function deleteRoomDrawings(roomId: number, ids: number[]) {
  await http.delete(`/rooms/${roomId}/drawings`, { data: { ids } });
}

export async function postRoomToken(
  roomId: number,
  payload: {
    name: string;
    x: number;
    y: number;
    file?: File;
    linked_character_id?: number | null;
  },
) {
  const form = new FormData();
  form.append("name", payload.name);
  form.append("x", String(payload.x));
  form.append("y", String(payload.y));
  if (payload.linked_character_id != null) {
    form.append("linked_character_id", String(payload.linked_character_id));
  }
  if (payload.file) {
    form.append("file", payload.file);
  }
  const { data } = await http.post<RoomToken>(`/rooms/${roomId}/tokens`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function spawnRoomCharacterToken(
  roomId: number,
  characterId: number,
  payload?: { x?: number; y?: number; name?: string },
) {
  const { data } = await http.post<RoomToken>(
    `/rooms/${roomId}/characters/${characterId}/spawn-token`,
    payload ?? {},
  );
  return data;
}

export async function patchRoomToken(
  roomId: number,
  tokenId: number,
  payload: {
    name?: string;
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    rotation?: number;
    z_index?: number;
    visible?: boolean;
    locked?: boolean;
    linked_character_id?: number | null;
  },
) {
  const { data } = await http.patch<RoomToken>(
    `/rooms/${roomId}/tokens/${tokenId}`,
    payload,
  );
  return data;
}

export async function deleteRoomToken(roomId: number, tokenId: number) {
  await http.delete(`/rooms/${roomId}/tokens/${tokenId}`);
}
