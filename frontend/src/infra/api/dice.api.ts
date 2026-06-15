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
  scene_id: number;
  roller_user_id: number;
  actor_type: DiceActorType;
  actor_token_id: number | null;
  actor_display_name: string;
  actor_asset_id: number | null;
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

export type DicePresetKind = "folder" | "preset";

export type DicePreset = {
  id: number;
  owner_id: number;
  parent_id: number | null;
  kind: DicePresetKind;
  name: string;
  formula: string;
  label: string;
  visibility: DiceVisibility;
  sort_order: number;
  created_at: string | null;
  updated_at: string | null;
};

export type DicePresetCreate = {
  parent_id?: number | null;
  kind: DicePresetKind;
  name: string;
  formula?: string;
  label?: string;
  visibility?: DiceVisibility;
  sort_order?: number;
};

export type DicePresetPatch = Partial<DicePresetCreate>;

export type DiceRollListResponse = {
  items: DiceRoll[];
  next_before_id: number | null;
};

export type DicePresetListResponse = {
  items: DicePreset[];
};

export async function getRoomDiceRolls(
  roomId: number,
  params?: { before_id?: number | null; limit?: number; scene_id?: number | null },
) {
  const { data } = await http.get<DiceRollListResponse>(`/rooms/${roomId}/dice-rolls`, { params });
  return data;
}

export async function createRoomDiceRoll(roomId: number, payload: DiceRollCreate) {
  const { data } = await http.post<DiceRoll>(`/rooms/${roomId}/dice-rolls`, payload);
  return data;
}

export async function getDicePresets() {
  const { data } = await http.get<DicePresetListResponse>("/dice-presets");
  return data;
}

export async function createDicePreset(payload: DicePresetCreate) {
  const { data } = await http.post<DicePreset>("/dice-presets", payload);
  return data;
}

export async function patchDicePreset(presetId: number, payload: DicePresetPatch) {
  const { data } = await http.patch<DicePreset>(`/dice-presets/${presetId}`, payload);
  return data;
}

export async function deleteDicePreset(presetId: number) {
  await http.delete(`/dice-presets/${presetId}`);
}
