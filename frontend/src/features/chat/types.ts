import type { MemberStatus, RoomRole } from "@/features/room/types";

export type ChatSegment = { id: number | string; type: "text"; content: string };

export type ChatMessage = {
  id: number | string;
  author: string;
  authorUserId?: number | null;
  avatarUrl?: string | null;
  segments: ChatSegment[];
  self?: boolean;
  avatarVariant?: "default" | "room";
  role?: RoomRole;
  status?: MemberStatus;
};
