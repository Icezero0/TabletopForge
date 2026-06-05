import { http } from "@/infra/http/client";

export type Character = {
  id: number;
  owner_id: number;
  name: string;
  player_name: string;
  portrait_asset_id: number | null;
  system: string;
  identity: Record<string, unknown>;
  flavor: Record<string, unknown>;
  attributes: Record<string, unknown>;
  features: Record<string, unknown>;
  spells: Record<string, unknown> | null;
  equipment: Record<string, unknown>;
  extras: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
};

export type CharacterListResponse = {
  items: Character[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CharacterPayload = {
  name: string;
  player_name?: string;
  system?: string;
  portrait_asset_id?: number | null;
  identity?: Record<string, unknown>;
  flavor?: Record<string, unknown>;
  attributes?: Record<string, unknown>;
  features?: Record<string, unknown>;
  spells?: Record<string, unknown> | null;
  equipment?: Record<string, unknown>;
  extras?: Record<string, unknown>;
};

export async function getCharacters(params?: { page?: number; page_size?: number }) {
  const { data } = await http.get<CharacterListResponse>("/characters", { params });
  return data;
}

export async function getCharacter(id: number) {
  const { data } = await http.get<Character>(`/characters/${id}`);
  return data;
}

export async function createCharacter(payload: CharacterPayload) {
  const { data } = await http.post<Character>("/characters", payload);
  return data;
}

export async function patchCharacter(id: number, payload: Partial<CharacterPayload>) {
  const { data } = await http.patch<Character>(`/characters/${id}`, payload);
  return data;
}

export async function deleteCharacter(id: number) {
  await http.delete(`/characters/${id}`);
}
