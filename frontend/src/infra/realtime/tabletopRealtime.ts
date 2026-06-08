import wsClient from "@/infra/realtime/wsClient";

export type PointerPresencePayload = {
  room_id: number;
  user_id: number;
  display_name: string;
  x: number;
  y: number;
};

export type PointerLaserPayload = {
  room_id: number;
  user_id: number;
  display_name: string;
  active: boolean;
  x: number;
  y: number;
};

export type TokenTransformPreviewPayload = {
  room_id: number;
  token_id: number;
  user_id: number;
  transform: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
};

export type ObjectSelectionPayload = {
  room_id: number;
  user_id: number;
  object_type: "token" | "drawing";
  object_id: number | null;
  active: boolean;
};

export function sendPointerPresence(roomId: number, x: number, y: number) {
  wsClient.sendCommand("pointer_presence", { room_id: roomId, x, y });
}

export function sendPointerLaser(
  roomId: number,
  payload: {
    active: boolean;
    x: number;
    y: number;
  },
) {
  wsClient.sendCommand("pointer_laser", { room_id: roomId, ...payload });
}

export function sendTokenTransformPreview(
  roomId: number,
  tokenId: number,
  transform: TokenTransformPreviewPayload["transform"],
) {
  wsClient.sendCommand("token_transform_preview", {
    room_id: roomId,
    token_id: tokenId,
    ...transform,
  });
}

export function sendObjectSelection(
  roomId: number,
  payload: {
    object_type: ObjectSelectionPayload["object_type"];
    object_id: number | null;
    active: boolean;
  },
) {
  wsClient.sendCommand("object_selection", {
    room_id: roomId,
    ...payload,
  });
}
