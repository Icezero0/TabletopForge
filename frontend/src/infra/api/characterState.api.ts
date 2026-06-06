import { http } from "@/infra/http/client";

export type CharacterStateConditions = {
  [key: string]: unknown;
};

export type CharacterState = {
  character_id: number;
  current_hp: number | null;
  max_hp: number | null;
  temp_hp: number;
  armor_class: number | null;
  conditions: CharacterStateConditions;
  damage_taken: number;
  updated_at: string;
};

export type CharacterStatePatch = {
  current_hp?: number | null;
  max_hp?: number | null;
  temp_hp?: number | null;
  armor_class?: number | null;
  conditions?: CharacterStateConditions;
};

export async function getCharacterState(characterId: number) {
  const { data } = await http.get<CharacterState>(`/characters/${characterId}/state`);
  return data;
}

export async function patchCharacterState(characterId: number, payload: CharacterStatePatch) {
  const { data } = await http.patch<CharacterState>(
    `/characters/${characterId}/state`,
    payload,
  );
  return data;
}
