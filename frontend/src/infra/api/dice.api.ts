import { http } from "@/infra/http/client";

export type DiceActorType = "user" | "token";
export type DiceVisibility = "public" | "blind";

export type DiceRollDetail = {
  terms: Array<
    | {
        type: "dice";
        sign: number;
        count: number;
        faces: number;
        keep: string | null;
        rolls: { value: number; kept: boolean }[];
        subtotal: number;
      }
    | {
        type: "modifier";
        sign: number;
        value: number;
        total: number;
      }
  >;
};

export type DiceRoll = {
  id: number;
  room_id: number;
  roller_user_id: number;
  actor_type: DiceActorType;
  actor_token_id: number | null;
  actor_display_name: string;
  label: string;
  formula: string;
  visibility: DiceVisibility;
  total: number | null;
  detail: DiceRollDetail | null;
  hidden: boolean;
  created_at: string | null;
};

export type DiceRollCreate = {
  actor_type: DiceActorType;
  actor_token_id?: number | null;
  label?: string;
  formula: string;
  visibility: DiceVisibility;
};

export type DiceRollListResponse = {
  items: DiceRoll[];
  next_before_id: number | null;
};

export async function getRoomDiceRolls(
  roomId: number,
  params?: { before_id?: number | null; limit?: number },
) {
  const { data } = await http.get<DiceRollListResponse>(`/rooms/${roomId}/dice-rolls`, { params });
  return data;
}

export async function createRoomDiceRoll(roomId: number, payload: DiceRollCreate) {
  const { data } = await http.post<DiceRoll>(`/rooms/${roomId}/dice-rolls`, payload);
  return data;
}
