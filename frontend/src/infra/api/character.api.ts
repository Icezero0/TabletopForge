import { http } from "@/infra/http/client";

export type TokenPanelInitial = {
  ability_scores?: Partial<Record<string, number>>;
  ac?: number | null;
  hp_current?: number | null;
  hp_max?: number | null;
  hide_data?: boolean;
  hide_hp?: boolean;
  speed?: number | null;
  pp?: number | null;
  proficiency_bonus?: number | null;
  saving_throws?: Record<string, number | null>;
  saving_throw_profs?: Record<string, boolean>;
  skills?: Record<string, number | null>;
  skill_profs?: Record<string, string>;
  items?: { name: string; quantity: number; notes: string }[];
  weapons?: unknown[];
  armor?: unknown[];
  spellcasting_ability?: string;
  spell_save_dc?: { value: number; breakdown?: string };
  spell_attack_bonus?: { value: number; breakdown?: string };
  spellbook?: Record<string, string[]>;
  resources?: { name: string; max: number; current?: number; recovery: string }[];
  inherit_items_from_character?: boolean;
};

export type TokenConfig = {
  id: number;
  character_id: number;
  is_primary: boolean;
  name: string;
  asset_id: number | null;
  library_resource_id?: number | null;
  panel_initial: TokenPanelInitial;
  sort_order: number;
};

export type TokenConfigUpsert = {
  id?: number;
  is_primary: boolean;
  name: string;
  asset_id: number | null;
  library_resource_id?: number | null;
  panel_initial: TokenPanelInitial;
  sort_order: number;
};

export type Character = {
  id: number;
  owner_id: number;
  name: string;
  player_name: string;
  portrait_asset_id: number | null;
  token_image_asset_id: number | null;
  system: string;
  identity: Record<string, unknown>;
  flavor: Record<string, unknown>;
  attributes: Record<string, unknown>;
  features: Record<string, unknown>;
  spells: Record<string, unknown> | null;
  equipment: Record<string, unknown>;
  extras: Record<string, unknown>;
  token_configs: TokenConfig[];
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

export type CharacterImportPreview = CharacterPayload & {
  state?: {
    current_hp?: number | null;
    max_hp?: number | null;
    temp_hp?: number;
    armor_class?: number | null;
    conditions?: Record<string, unknown>;
  } | null;
};

export type CharacterPayload = {
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
  token_configs?: TokenConfigUpsert[];
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

const IMPORT_PREVIEW_TIMEOUT_MS = 6 * 60_000;

export async function importCharacterPreview(rawText: string) {
  const { data } = await http.post<CharacterImportPreview>(
    "/characters/import-preview",
    { raw_text: rawText },
    { timeout: IMPORT_PREVIEW_TIMEOUT_MS },
  );
  return data;
}
