import { defineStore } from "pinia";
import {
  deleteRoomDrawings,
  deleteRoomMap,
  deleteRoomToken,
  getRoomTabletop,
  patchRoomDrawing,
  patchRoomMap,
  patchRoomToken,
  patchRoomTabletopSettings,
  postRoomDrawing,
  postRoomMap,
  postRoomMapFromResource,
  postRoomToken,
  spawnRoomCharacterToken,
  type RoomDrawing,
  type RoomMap,
  type RoomToken,
  type RoomTabletopSettings,
  type RoomTabletopSnapshot,
  type TokenStateSummary,
} from "@/infra/api/rooms.api";

type RoomTabletopState = {
  snapshot: RoomTabletopSnapshot | null;
  isLoading: boolean;
  error: string | null;
};

type State = {
  rooms: Record<number, RoomTabletopState>;
};

function emptyRoomState(): RoomTabletopState {
  return {
    snapshot: null,
    isLoading: false,
    error: null,
  };
}

function extractErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail[0] && typeof detail[0] === "object" && "msg" in detail[0]) {
    return String((detail[0] as { msg: string }).msg);
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export const useTabletopStore = defineStore("tabletop", {
  state: (): State => ({
    rooms: {},
  }),

  getters: {
    getRoomState: (state) => (roomId: number) => state.rooms[roomId] ?? emptyRoomState(),
    getSettings: (state) => (roomId: number) => state.rooms[roomId]?.snapshot?.settings ?? null,
    getMaps: (state) => (roomId: number) => state.rooms[roomId]?.snapshot?.maps ?? [],
    getDrawings: (state) => (roomId: number) => state.rooms[roomId]?.snapshot?.drawings ?? [],
    getTokens: (state) => (roomId: number) => state.rooms[roomId]?.snapshot?.tokens ?? [],
  },

  actions: {
    ensureRoom(roomId: number): RoomTabletopState {
      if (!this.rooms[roomId]) {
        this.rooms[roomId] = emptyRoomState();
      }
      return this.rooms[roomId];
    },

    setSnapshot(roomId: number, snapshot: RoomTabletopSnapshot) {
      const state = this.ensureRoom(roomId);
      state.snapshot = snapshot;
      state.error = null;
    },

    applySettings(roomId: number, settings: RoomTabletopSettings) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) {
        state.snapshot = { settings, maps: [], drawings: [], tokens: [] };
        return;
      }
      state.snapshot.settings = settings;
    },

    applyMapCreated(roomId: number, map: RoomMap) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      const maps = state.snapshot.maps.filter((m) => m.id !== map.id);
      maps.push(map);
      state.snapshot.maps = maps.sort((a, b) => a.z_index - b.z_index || a.id - b.id);
    },

    applyMapUpdated(roomId: number, map: RoomMap) {
      this.applyMapCreated(roomId, map);
    },

    applyMapDeleted(roomId: number, mapId: number) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      state.snapshot.maps = state.snapshot.maps.filter((m) => m.id !== mapId);
    },

    applyDrawingCreated(roomId: number, drawing: RoomDrawing) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      const drawings = state.snapshot.drawings.filter((d) => d.id !== drawing.id);
      drawings.push(drawing);
      state.snapshot.drawings = drawings.sort(
        (a, b) => a.z_index - b.z_index || a.id - b.id,
      );
    },

    applyDrawingUpdated(roomId: number, drawing: RoomDrawing) {
      this.applyDrawingCreated(roomId, drawing);
    },

    applyDrawingsDeleted(roomId: number, drawingIds: number[]) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      const idSet = new Set(drawingIds);
      state.snapshot.drawings = state.snapshot.drawings.filter((d) => !idSet.has(d.id));
    },

    applyTokenCreated(roomId: number, token: RoomToken) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      const tokens = state.snapshot.tokens.filter((t) => t.id !== token.id);
      tokens.push(token);
      state.snapshot.tokens = tokens.sort((a, b) => a.z_index - b.z_index || a.id - b.id);
    },

    applyTokenUpdated(roomId: number, token: RoomToken) {
      this.applyTokenCreated(roomId, token);
    },

    applyTokenDeleted(roomId: number, tokenId: number) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      state.snapshot.tokens = state.snapshot.tokens.filter((t) => t.id !== tokenId);
    },

    applyCharacterStateUpdated(
      roomId: number,
      characterId: number,
      summary: TokenStateSummary,
    ) {
      const state = this.ensureRoom(roomId);
      if (!state.snapshot) return;
      state.snapshot = {
        ...state.snapshot,
        tokens: state.snapshot.tokens.map((token) => {
          if (token.linked_character_id !== characterId) return token;
          return { ...token, state_summary: summary };
        }),
      };
    },

    async loadSnapshot(roomId: number) {
      if (!roomId) return;
      const state = this.ensureRoom(roomId);
      state.isLoading = true;
      state.error = null;
      try {
        const snapshot = await getRoomTabletop(roomId);
        this.setSnapshot(roomId, snapshot);
      } catch (error) {
        state.error = extractErrorMessage(error, "Failed to load tabletop");
      } finally {
        state.isLoading = false;
      }
    },

    async uploadMap(roomId: number, file: File) {
      const map = await postRoomMap(roomId, file);
      this.applyMapCreated(roomId, map);
      return map;
    },

    async addMapFromResource(
      roomId: number,
      resourceId: number,
      opts?: Parameters<typeof postRoomMapFromResource>[2],
    ) {
      const map = await postRoomMapFromResource(roomId, resourceId, opts);
      this.applyMapCreated(roomId, map);
      return map;
    },

    async updateMap(
      roomId: number,
      mapId: number,
      payload: Parameters<typeof patchRoomMap>[2],
    ) {
      const map = await patchRoomMap(roomId, mapId, payload);
      this.applyMapUpdated(roomId, map);
      return map;
    },

    async removeMap(roomId: number, mapId: number) {
      await deleteRoomMap(roomId, mapId);
      this.applyMapDeleted(roomId, mapId);
    },

    async updateSettings(
      roomId: number,
      payload: Parameters<typeof patchRoomTabletopSettings>[1],
    ) {
      const settings = await patchRoomTabletopSettings(roomId, payload);
      this.applySettings(roomId, settings);
      return settings;
    },

    async createDrawing(
      roomId: number,
      payload: Parameters<typeof postRoomDrawing>[1],
    ) {
      const drawing = await postRoomDrawing(roomId, payload);
      this.applyDrawingCreated(roomId, drawing);
      return drawing;
    },

    async updateDrawing(
      roomId: number,
      drawingId: number,
      payload: Parameters<typeof patchRoomDrawing>[2],
    ) {
      const drawing = await patchRoomDrawing(roomId, drawingId, payload);
      this.applyDrawingUpdated(roomId, drawing);
      return drawing;
    },

    async removeDrawings(roomId: number, ids: number[]) {
      await deleteRoomDrawings(roomId, ids);
      this.applyDrawingsDeleted(roomId, ids);
    },

    async createToken(
      roomId: number,
      payload: Parameters<typeof postRoomToken>[1],
    ) {
      const token = await postRoomToken(roomId, payload);
      this.applyTokenCreated(roomId, token);
      return token;
    },

    async spawnCharacterToken(
      roomId: number,
      characterId: number,
      payload?: { x?: number; y?: number; name?: string },
    ) {
      const token = await spawnRoomCharacterToken(roomId, characterId, payload);
      this.applyTokenCreated(roomId, token);
      return token;
    },

    async updateToken(
      roomId: number,
      tokenId: number,
      payload: Parameters<typeof patchRoomToken>[2],
    ) {
      const token = await patchRoomToken(roomId, tokenId, payload);
      this.applyTokenUpdated(roomId, token);
      return token;
    },

    async removeToken(roomId: number, tokenId: number) {
      await deleteRoomToken(roomId, tokenId);
      this.applyTokenDeleted(roomId, tokenId);
    },

    resetRoom(roomId: number) {
      delete this.rooms[roomId];
    },
  },
});
