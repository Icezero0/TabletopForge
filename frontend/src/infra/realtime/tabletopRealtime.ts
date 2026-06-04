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
  x1: number;
  y1: number;
  x2?: number;
  y2?: number;
};

export function sendPointerPresence(roomId: number, x: number, y: number) {
  wsClient.sendCommand("pointer_presence", { room_id: roomId, x, y });
}

export function sendPointerLaser(
  roomId: number,
  payload: {
    active: boolean;
    x1: number;
    y1: number;
    x2?: number;
    y2?: number;
  },
) {
  wsClient.sendCommand("pointer_laser", { room_id: roomId, ...payload });
}
