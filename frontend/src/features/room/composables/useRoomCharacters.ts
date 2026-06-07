import { ref, type Ref } from "vue";
import {
  deleteRoomCharacter,
  getRoomCharacters,
  patchRoomCharacterVisibility,
  postRoomCharacter,
  type CharacterStateSummary,
  type RoomCharacterCreatePayload,
  type RoomCharacterEntry,
} from "@/infra/api/roomCharacters.api";
import type { TokenStateSummary } from "@/infra/api/rooms.api";

export function useRoomCharacters(roomId: Ref<number | null>) {
  const characters = ref<RoomCharacterEntry[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  async function fetchCharacters() {
    const id = roomId.value;
    if (!id) return;
    isLoading.value = true;
    error.value = null;
    try {
      characters.value = await getRoomCharacters(id);
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to load room characters";
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function createCharacter(payload: RoomCharacterCreatePayload) {
    const id = roomId.value;
    if (!id) throw new Error("Missing room id");
    const entry = await postRoomCharacter(id, payload);
    characters.value = [...characters.value, entry];
    return entry;
  }

  function upsertEntry(entry: RoomCharacterEntry) {
    const index = characters.value.findIndex(
      (item) => item.character_id === entry.character_id,
    );
    if (index >= 0) {
      characters.value = characters.value.map((item, i) =>
        i === index ? entry : item,
      );
    } else {
      characters.value = [...characters.value, entry];
    }
  }

  function updateEntryState(characterId: number, summary: TokenStateSummary | CharacterStateSummary) {
    characters.value = characters.value.map((entry) => {
      if (entry.character_id !== characterId) return entry;
      return {
        ...entry,
        state: {
          current_hp: summary.current_hp,
          max_hp: summary.max_hp,
          armor_class: "ac" in summary ? summary.ac : summary.armor_class,
          damage_taken: summary.damage_taken ?? entry.state.damage_taken,
        },
      };
    });
  }

  async function removeEntry(roomCharacterId: number) {
    const id = roomId.value;
    if (!id) throw new Error("Missing room id");
    await deleteRoomCharacter(id, roomCharacterId);
    characters.value = characters.value.filter(
      (e) => e.room_character_id !== roomCharacterId,
    );
  }

  async function setVisibility(roomCharacterId: number, isHidden: boolean) {
    const id = roomId.value;
    if (!id) throw new Error("Missing room id");
    const updated = await patchRoomCharacterVisibility(id, roomCharacterId, isHidden);
    upsertEntry(updated);
    return updated;
  }

  return {
    characters,
    isLoading,
    error,
    fetchCharacters,
    createCharacter,
    upsertEntry,
    updateEntryState,
    removeEntry,
    setVisibility,
    refresh: fetchCharacters,
  };
}
