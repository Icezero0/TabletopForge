import type { Character } from "@/infra/api/character.api";
import { getCharacters } from "@/infra/api/character.api";
import type { RoomCharacterEntry, SpawnPopoverEntry } from "@/infra/api/roomCharacters.api";
import type { GameRole } from "@/features/room/types";

function characterToPopoverEntry(char: Character): SpawnPopoverEntry {
  return {
    room_character_id: 0,
    character_id: char.id,
    owner_id: char.owner_id,
    name: char.name,
    player_name: char.player_name,
    token_image_asset_id: char.token_image_asset_id ?? char.portrait_asset_id,
    state: {
      current_hp: null,
      max_hp: null,
      armor_class: null,
      damage_taken: null,
    },
    inRoom: false,
  };
}

export function mergeSpawnPopoverEntries(
  roomEntries: RoomCharacterEntry[],
  libraryCharacters: Character[],
  gameRole: GameRole | "unknown",
  currentUserId: number | null | undefined,
): SpawnPopoverEntry[] {
  const roomIds = new Set(roomEntries.map((entry) => entry.character_id));
  const inRoom: SpawnPopoverEntry[] = roomEntries.map((entry) => ({
    ...entry,
    inRoom: true,
  }));
  const libraryOnly = libraryCharacters
    .filter((char) => currentUserId != null && char.owner_id === currentUserId)
    .filter((char) => !roomIds.has(char.id))
    .map(characterToPopoverEntry);
  return [...inRoom, ...libraryOnly];
}

export async function fetchAllMyCharacters() {
  const pageSize = 100;
  const items: Character[] = [];
  let page = 1;
  let totalPages = 1;
  while (page <= totalPages) {
    const response = await getCharacters({ page, page_size: pageSize });
    items.push(...response.items);
    totalPages = response.total_pages;
    page += 1;
  }
  return items;
}
