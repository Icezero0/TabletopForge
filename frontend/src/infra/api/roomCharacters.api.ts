import { http } from "@/infra/http/client";

export type CharacterStateSummary = {
  current_hp: number | null;
  max_hp: number | null;
  armor_class: number | null;
  damage_taken?: number | null;
};

export type RoomCharacterTokenConfig = {
  id: number;
  is_primary: boolean;
  name: string;
  asset_id: number | null;
};

export type RoomCharacterEntry = {
  room_character_id: number;
  character_id: number;
  owner_id: number;
  name: string;
  player_name: string;
  token_image_asset_id: number | null;
  token_configs: RoomCharacterTokenConfig[];
  state: CharacterStateSummary;
  is_hidden: boolean;
};

export type SpawnPopoverEntry = RoomCharacterEntry & {
  inRoom: boolean;
};

export type RoomCharacterStateInput = {
  current_hp?: number | null;
  max_hp?: number | null;
  temp_hp?: number;
  armor_class?: number | null;
  conditions?: Record<string, unknown>;
};

export type RoomCharacterCreatePayload = {
  name: string;
  player_name?: string;
  system?: string;
  portrait_asset_id?: number | null;
  token_image_asset_id?: number | null;
  identity?: Record<string, unknown>;
  flavor?: Record<string, unknown>;
  attributes?: Record<string, unknown>;
  features?: Record<string, unknown>;
  spells?: Record<string, unknown> | null;
  equipment?: Record<string, unknown>;
  extras?: Record<string, unknown>;
  state?: RoomCharacterStateInput;
  file?: File;
};

export async function getRoomCharacters(roomId: number) {
  const { data } = await http.get<RoomCharacterEntry[]>(`/rooms/${roomId}/characters`);
  return data;
}

export async function linkRoomCharacter(roomId: number, characterId: number) {
  const { data } = await http.post<RoomCharacterEntry>(
    `/rooms/${roomId}/characters/link`,
    { character_id: characterId },
  );
  return data;
}

export async function deleteRoomCharacter(roomId: number, roomCharacterId: number) {
  await http.delete(`/rooms/${roomId}/characters/${roomCharacterId}`);
}

export async function patchRoomCharacterVisibility(
  roomId: number,
  roomCharacterId: number,
  isHidden: boolean,
) {
  const { data } = await http.patch<RoomCharacterEntry>(
    `/rooms/${roomId}/characters/${roomCharacterId}/visibility`,
    { is_hidden: isHidden },
  );
  return data;
}

export async function postRoomCharacter(roomId: number, payload: RoomCharacterCreatePayload) {
  const form = new FormData();
  form.append("name", payload.name);
  if (payload.player_name != null) form.append("player_name", payload.player_name);
  if (payload.system != null) form.append("system", payload.system);
  if (payload.portrait_asset_id != null) {
    form.append("portrait_asset_id", String(payload.portrait_asset_id));
  }
  if (payload.token_image_asset_id != null) {
    form.append("token_image_asset_id", String(payload.token_image_asset_id));
  }
  if (payload.identity && Object.keys(payload.identity).length > 0) {
    form.append("identity_json", JSON.stringify(payload.identity));
  }
  if (payload.flavor && Object.keys(payload.flavor).length > 0) {
    form.append("flavor_json", JSON.stringify(payload.flavor));
  }
  if (payload.attributes && Object.keys(payload.attributes).length > 0) {
    form.append("attributes_json", JSON.stringify(payload.attributes));
  }
  if (payload.features && Object.keys(payload.features).length > 0) {
    form.append("features_json", JSON.stringify(payload.features));
  }
  if (payload.spells != null) {
    form.append("spells_json", JSON.stringify(payload.spells));
  }
  if (payload.equipment && Object.keys(payload.equipment).length > 0) {
    form.append("equipment_json", JSON.stringify(payload.equipment));
  }
  if (payload.extras && Object.keys(payload.extras).length > 0) {
    form.append("extras_json", JSON.stringify(payload.extras));
  }
  if (payload.state) {
    const hasState = Object.values(payload.state).some(
      (value) => value != null && (typeof value !== "object" || Object.keys(value).length > 0),
    );
    if (hasState) {
      form.append("state_json", JSON.stringify(payload.state));
    }
  }
  if (payload.file) {
    form.append("file", payload.file);
  }

  const { data } = await http.post<RoomCharacterEntry>(
    `/rooms/${roomId}/characters`,
    form,
  );
  return data;
}
