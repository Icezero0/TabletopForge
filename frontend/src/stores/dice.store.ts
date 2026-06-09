import { defineStore } from "pinia";
import {
  createRoomDiceRoll,
  getRoomDiceRolls,
  type DiceActorType,
  type DiceRoll,
  type DiceRollCreate,
  type DiceVisibility,
} from "@/infra/api/dice.api";
import { i18n } from "@/infra/i18n";

export type DiceDraft = {
  actorType: DiceActorType;
  actorTokenId: number | null;
  actorDisplayName: string;
  label: string;
  formula: string;
  visibility: DiceVisibility;
};

type RoomDiceState = {
  items: DiceRoll[];
  nextBeforeId: number | null;
  hasLoaded: boolean;
  isLoading: boolean;
  isLoadingHistory: boolean;
  isRolling: boolean;
  error: string | null;
  draft: DiceDraft | null;
};

type State = {
  rooms: Record<number, RoomDiceState>;
};

function createEmptyRoomState(): RoomDiceState {
  return {
    items: [],
    nextBeforeId: null,
    hasLoaded: false,
    isLoading: false,
    isLoadingHistory: false,
    isRolling: false,
    error: null,
    draft: null,
  };
}

function translateDiceErrorMessage(message: string) {
  const keyByMessage: Record<string, string> = {
    "Dice formula is empty": "room.dice.errors.emptyFormula",
    "Unsupported dice formula": "room.dice.errors.unsupportedFormula",
    "Dice formula is out of range": "room.dice.errors.formulaOutOfRange",
    "Dice roller returned out-of-range value": "room.dice.errors.rollOutOfRange",
  };
  const key = keyByMessage[message];
  return key ? i18n.global.t(key) : message;
}

function extractErrorMessage(error: any, fallback: string) {
  const detail = error?.response?.data?.error?.message ?? error?.response?.data?.detail;
  if (typeof detail === "string" && detail) return translateDiceErrorMessage(detail);
  if (typeof error?.message === "string" && error.message) return translateDiceErrorMessage(error.message);
  return fallback;
}

function normalizeRolls(rolls: DiceRoll[]) {
  const map = new Map<number, DiceRoll>();
  rolls.forEach((roll) => map.set(roll.id, roll));
  return Array.from(map.values()).sort((a, b) => a.id - b.id);
}

function mergeRolls(existing: DiceRoll[], incoming: DiceRoll[], mode: "replace" | "append" | "prepend") {
  if (mode === "replace") return normalizeRolls(incoming);
  if (mode === "append") return normalizeRolls([...existing, ...incoming]);
  return normalizeRolls([...incoming, ...existing]);
}

export const useDiceStore = defineStore("dice", {
  state: (): State => ({
    rooms: {},
  }),

  getters: {
    getRoomState: (state) => {
      return (roomId: number | null | undefined) =>
        typeof roomId === "number" && roomId > 0
          ? state.rooms[roomId] ?? createEmptyRoomState()
          : createEmptyRoomState();
    },
  },

  actions: {
    ensureRoomState(roomId: number) {
      this.rooms[roomId] = this.rooms[roomId] ?? createEmptyRoomState();
      return this.rooms[roomId];
    },

    setRoomRolls(roomId: number, rolls: DiceRoll[], mode: "replace" | "append" | "prepend" = "replace") {
      const roomState = this.ensureRoomState(roomId);
      roomState.items = mergeRolls(roomState.items, rolls, mode);
      roomState.hasLoaded = true;
    },

    async refreshRoomRolls(roomId: number, limit = 30) {
      const roomState = this.ensureRoomState(roomId);
      roomState.isLoading = true;
      roomState.error = null;
      try {
        const response = await getRoomDiceRolls(roomId, { limit });
        this.setRoomRolls(roomId, response.items, "replace");
        roomState.nextBeforeId = response.next_before_id ?? null;
        return response;
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to load dice rolls");
        roomState.error = message;
        throw new Error(message);
      } finally {
        roomState.isLoading = false;
      }
    },

    async loadOlderRolls(roomId: number, limit = 30) {
      const roomState = this.ensureRoomState(roomId);
      if (roomState.isLoadingHistory || roomState.nextBeforeId == null) return roomState;
      roomState.isLoadingHistory = true;
      roomState.error = null;
      try {
        const response = await getRoomDiceRolls(roomId, {
          before_id: roomState.nextBeforeId,
          limit,
        });
        this.setRoomRolls(roomId, response.items, "prepend");
        roomState.nextBeforeId = response.next_before_id ?? null;
        return response;
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to load dice history");
        roomState.error = message;
        throw new Error(message);
      } finally {
        roomState.isLoadingHistory = false;
      }
    },

    async roll(roomId: number, payload: DiceRollCreate) {
      const roomState = this.ensureRoomState(roomId);
      roomState.isRolling = true;
      roomState.error = null;
      try {
        const created = await createRoomDiceRoll(roomId, payload);
        if (!(created.visibility === "blind" && created.hidden)) {
          this.setRoomRolls(roomId, [created], "append");
        }
        return created;
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to roll dice");
        roomState.error = message;
        throw new Error(message);
      } finally {
        roomState.isRolling = false;
      }
    },

    appendRealtimeRoll(roll: DiceRoll) {
      this.setRoomRolls(roll.room_id, [roll], "append");
    },

    setDraft(roomId: number, draft: DiceDraft) {
      this.ensureRoomState(roomId).draft = draft;
    },

    clearRoom(roomId: number) {
      delete this.rooms[roomId];
    },
  },
});
