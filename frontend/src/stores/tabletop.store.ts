import { defineStore } from "pinia";
import {
  deleteRoomDrawings,
  deleteRoomMap,
  getRoomTabletop,
  patchRoomDrawing,
  patchRoomMap,
  patchRoomTabletopSettings,
  postRoomDrawing,
  postRoomMap,
  type RoomDrawing,
  type RoomMap,
  type RoomTabletopSettings,
  type RoomTabletopSnapshot,
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
        state.snapshot = { settings, maps: [], drawings: [] };
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

    resetRoom(roomId: number) {
      delete this.rooms[roomId];
    },
  },
});
