import { http } from "@/infra/http/client";
import type { UserResponse } from "@/infra/api/users.api";

export type TextSegmentIn = {
  type: "text";
  text: string;
};

export type MessageSegmentIn = TextSegmentIn;

export type MessageContentIn = {
  segments: MessageSegmentIn[];
};

export type TextSegmentOut = {
  type: "text";
  text: string;
};

export type MessageSegmentOut = TextSegmentOut;

export type MessageContentOut = {
  segments: MessageSegmentOut[];
};

export type MessageCreatePayload = {
  content: MessageContentIn;
};

export type MessageResponse = {
  id: number;
  room_id: number;
  sender_user_id: number | null;
  sender: UserResponse | null;
  content: MessageContentOut;
  created_at: string;
  updated_at: string;
};

export type MessageListResponse = {
  items: MessageResponse[];
  next_before_id?: number | null;
};

export async function getRoomMessages(
  roomId: number,
  params?: {
    before_id?: number | null;
    limit?: number;
  },
) {
  const { data } = await http.get<MessageListResponse>(
    `/rooms/${roomId}/messages`,
    { params },
  );
  return data;
}

export async function createRoomMessage(
  roomId: number,
  payload: MessageCreatePayload,
) {
  const { data } = await http.post<MessageResponse>(
    `/rooms/${roomId}/messages`,
    payload,
  );
  return data;
}
