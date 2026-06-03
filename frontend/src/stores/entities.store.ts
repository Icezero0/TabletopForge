import { defineStore } from "pinia";
import { getUserById, type UserResponse } from "@/infra/api/users.api";
import {
  getRoomById,
  type Room,
  type RoomBrief,
  type RoomJoinRequest,
  type RoomMember,
  type RoomUserBrief,
} from "@/infra/api/rooms.api";
import type { UserBrief as NotificationUserBrief } from "@/infra/api/notifications.api";
type EntityUser = {
  id: number;
  email?: string | null;
  username?: string | null;
  avatar_asset_id?: number | null;
  avatar_url?: string | null;
};

type EntityRoom = {
  id: number;
  name?: string;
  owner_id?: number;
  owner_name?: string | null;
  owner_avatar_url?: string | null;
  visibility?: Room["visibility"];
  my_role?: Room["my_role"];
  join_audit_mode?: Room["join_audit_mode"];
};

type EntityRoomMember = {
  room_id: number;
  user_id: number;
  joined_at?: string | null;
  role: RoomMember["role"];
};

type State = {
  usersById: Record<number, EntityUser>;
  roomsById: Record<number, EntityRoom>;
  roomMembersByRoomId: Record<number, EntityRoomMember[]>;
  loadingUsers: Record<number, boolean>;
  loadingRooms: Record<number, boolean>;
};

type UserSummaryInput =
  | UserResponse
  | RoomUserBrief
  | NotificationUserBrief
  | {
      id: number;
      email?: string | null;
      username?: string | null;
      avatar_asset_id?: number | null;
      avatar_url?: string | null;
    };
type RoomSummaryInput = Room | RoomBrief;

function mergeDefined<T extends Record<string, any>>(base: T | undefined, patch: Partial<T>): T {
  const next = { ...(base ?? {}) } as T;

  for (const [key, value] of Object.entries(patch)) {
    if (value !== undefined) {
      (next as any)[key] = value;
    }
  }

  return next;
}

function normalizeUser(user: UserSummaryInput): EntityUser {
  return {
    id: user.id,
    email: user.email,
    username: user.username,
    avatar_asset_id: "avatar_asset_id" in user ? user.avatar_asset_id : undefined,
    avatar_url: user.avatar_url,
  };
}

function normalizeRoom(room: RoomSummaryInput): EntityRoom {
  return {
    id: room.id,
    name: room.name,
    owner_id: room.owner_id,
    visibility: room.visibility,
    owner_name: "owner_name" in room ? room.owner_name : undefined,
    owner_avatar_url: "owner_avatar_url" in room ? room.owner_avatar_url : undefined,
    my_role: "my_role" in room ? room.my_role : undefined,
    join_audit_mode:
      "join_audit_mode" in room ? room.join_audit_mode : undefined,
  };
}

function normalizeRoomMember(member: RoomMember): EntityRoomMember {
  return {
    room_id: member.room_id,
    user_id: member.user_id,
    joined_at: member.joined_at,
    role: member.role,
  };
}

export const useEntitiesStore = defineStore("entities", {
  state: (): State => ({
    usersById: {},
    roomsById: {},
    roomMembersByRoomId: {},
    loadingUsers: {},
    loadingRooms: {},
  }),

  getters: {
    getUser: (state) => {
      return (userId: number | null | undefined) =>
        userId ? state.usersById[userId] ?? null : null;
    },
    getRoom: (state) => {
      return (roomId: number | null | undefined) =>
        roomId ? state.roomsById[roomId] ?? null : null;
    },
    getRoomMembers: (state) => {
      return (roomId: number | null | undefined) =>
        roomId ? state.roomMembersByRoomId[roomId] ?? [] : [];
    },
    getRoomMember: (state) => {
      return (roomId: number | null | undefined, userId: number | null | undefined) => {
        if (!roomId || !userId) return null;
        return state.roomMembersByRoomId[roomId]?.find((member) => member.user_id === userId) ?? null;
      };
    },
  },

  actions: {
    upsertUser(user: UserSummaryInput | null | undefined) {
      if (!user?.id) return;

      const normalized = normalizeUser(user);
      this.usersById[user.id] = mergeDefined(this.usersById[user.id], normalized);
    },

    upsertUsers(users: Array<UserSummaryInput | null | undefined>) {
      users.forEach((user) => this.upsertUser(user));
    },

    upsertRoom(room: RoomSummaryInput | null | undefined) {
      if (!room?.id) return;

      const normalized = normalizeRoom(room);
      this.roomsById[room.id] = mergeDefined(this.roomsById[room.id], normalized);
    },

    upsertRooms(rooms: Array<RoomSummaryInput | null | undefined>) {
      rooms.forEach((room) => this.upsertRoom(room));
    },

    upsertRoomMembers(members: Array<RoomMember | null | undefined>) {
      const groupedMembers: Record<number, EntityRoomMember[]> = {};

      members.forEach((member) => {
        if (!member) return;
        this.upsertUser(member.user);
        const roomMembers = groupedMembers[member.room_id] ?? [];
        groupedMembers[member.room_id] = roomMembers;
        roomMembers.push(normalizeRoomMember(member));
      });

      Object.entries(groupedMembers).forEach(([roomId, roomMembers]) => {
        const numericRoomId = Number(roomId);
        this.roomMembersByRoomId[numericRoomId] = roomMembers;
      });
    },

    upsertRoomMember(member: RoomMember | null | undefined) {
      if (!member) return;

      this.upsertUser(member.user);

      const existingMembers = this.roomMembersByRoomId[member.room_id] ?? [];
      const nextMember = normalizeRoomMember(member);
      const existingIndex = existingMembers.findIndex(
        (item) => item.user_id === member.user_id,
      );

      if (existingIndex === -1) {
        this.roomMembersByRoomId[member.room_id] = [...existingMembers, nextMember];
        return;
      }

      this.roomMembersByRoomId[member.room_id] = existingMembers.map((item, index) =>
        index === existingIndex ? nextMember : item,
      );
    },

    removeRoomMember(roomId: number, userId: number) {
      const roomMembers = this.roomMembersByRoomId[roomId];
      if (!roomMembers) return;

      this.roomMembersByRoomId[roomId] = roomMembers.filter(
        (member) => member.user_id !== userId,
      );
    },

    upsertJoinRequests(requests: Array<RoomJoinRequest | null | undefined>) {
      requests.forEach((request) => {
        if (!request) return;
        this.upsertRoom(request.room);
        this.upsertUsers([
          request.initiator,
          request.target,
          request.room_action_by,
        ]);
      });
    },

    async ensureUsers(userIds: Array<number | null | undefined>) {
      const ids = Array.from(
        new Set(
          userIds.filter((value): value is number => typeof value === "number" && value > 0),
        ),
      );

      const toFetch = ids.filter(
        (id) => !this.usersById[id] && !this.loadingUsers[id],
      );

      if (toFetch.length === 0) return;

      await Promise.all(
        toFetch.map(async (id) => {
          this.loadingUsers[id] = true;

          try {
            const user = await getUserById(id);
            this.upsertUser(user);
          } finally {
            this.loadingUsers[id] = false;
          }
        }),
      );
    },

    async ensureRooms(roomIds: Array<number | null | undefined>) {
      const ids = Array.from(
        new Set(
          roomIds.filter((value): value is number => typeof value === "number" && value > 0),
        ),
      );

      const toFetch = ids.filter(
        (id) => !this.roomsById[id] && !this.loadingRooms[id],
      );

      if (toFetch.length === 0) return;

      await Promise.all(
        toFetch.map(async (id) => {
          this.loadingRooms[id] = true;

          try {
            const room = await getRoomById(id);
            this.upsertRoom(room);
          } finally {
            this.loadingRooms[id] = false;
          }
        }),
      );
    },

    clear() {
      this.usersById = {};
      this.roomsById = {};
      this.roomMembersByRoomId = {};
      this.loadingUsers = {};
      this.loadingRooms = {};
    },
  },
});
