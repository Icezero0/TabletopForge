<script setup lang="ts">
import RoomMemberAvatar from "@/features/room/components/RoomMemberAvatar.vue";
import type { ChatSegment } from "@/features/chat/types";
import type { MemberStatus } from "@/features/room/types";

defineProps<{
  author: string;
  avatarUrl?: string | null;
  segments: ChatSegment[];
  self?: boolean;
  showAvatar?: boolean;
  showAuthor?: boolean;
  avatarVariant?: "default" | "room";
  role?: "owner" | "manager" | "member";
  status?: MemberStatus;
}>();
</script>

<template>
  <div class="messageRow" :class="{ self, compact: showAvatar === false }">
    <RoomMemberAvatar
      v-if="showAvatar !== false && avatarVariant === 'room'"
      class="avatar"
      :name="author"
      :src="avatarUrl"
      :role="role ?? 'member'"
      :status="status ?? 'idle'"
      :size="32"
    />
    <BaseAvatar
      v-else-if="showAvatar !== false"
      class="avatar"
      size="sm"
      :src="avatarUrl || undefined"
      :name="author"
    />
    <div v-else class="avatarSpacer" aria-hidden="true" />

    <div class="content" :class="{ compact: showAuthor === false }">
      <div v-if="showAuthor !== false" class="author">{{ author }}</div>

      <div class="bubble">
        <span
          v-for="segment in segments"
          :key="segment.id"
          class="segment"
        >
          {{ segment.content }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.messageRow {
  --avatar-size: 32px;
  --avatar-gap: 10px;
  display: flex;
  gap: var(--avatar-gap);
  align-items: start;
}

.messageRow.self {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.messageRow.self .content {
  align-items: end;
}

.messageRow.self .author {
  text-align: right;
}

.messageRow.self .bubble {
  background: color-mix(in srgb, var(--c-primary) 9%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 24%, var(--c-border));
}

.avatar {
  flex: 0 0 auto;
}

.avatarSpacer {
  flex: 0 0 auto;
  width: var(--avatar-size);
  height: 1px;
}

.content {
  flex: 0 1 auto;
  display: grid;
  gap: 6px;
  max-width: min(calc(100% - ((var(--avatar-size) * 2) + var(--avatar-gap))), 520px);
  align-items: start;
  justify-items: start;
}

.content.compact {
  gap: 0;
}

.messageRow.self .content {
  justify-items: end;
}

.author {
  font-size: 12px;
  line-height: 1.2;
  color: var(--c-text-muted);
  padding: 0 2px;
  user-select: none;
}

.bubble {
  box-sizing: border-box;
  width: fit-content;
  max-width: 100%;
  padding: 9px 11px;
  border-radius: 16px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 74%, var(--c-bg));
  line-height: 1.6;
  justify-self: start;
}

.messageRow.self .bubble {
  justify-self: end;
}

.segment {
  display: block;
  font-size: 13px;
  color: var(--c-text);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
