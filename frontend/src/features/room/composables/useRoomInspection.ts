import { ref } from "vue";

export type ActiveInspection = {
  kind: "character";
  characterId: number;
  tokenId?: number;
  tokenInstanceName?: string;
} | null;

export function useRoomInspection() {
  const activeInspection = ref<ActiveInspection>(null);

  function setInspection(inspection: ActiveInspection) {
    activeInspection.value = inspection;
  }

  function clearInspection() {
    activeInspection.value = null;
  }

  function inspectCharacter(payload: {
    characterId: number;
    tokenId?: number;
    tokenInstanceName?: string;
  }) {
    activeInspection.value = {
      kind: "character",
      characterId: payload.characterId,
      tokenId: payload.tokenId,
      tokenInstanceName: payload.tokenInstanceName,
    };
  }

  return {
    activeInspection,
    setInspection,
    clearInspection,
    inspectCharacter,
  };
}
