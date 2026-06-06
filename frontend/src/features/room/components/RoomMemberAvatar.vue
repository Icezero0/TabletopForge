<script setup lang="ts">
import { computed } from "vue";
import type { MemberStatus, RoomRole } from "@/features/room/types";

const props = withDefaults(
  defineProps<{
    name: string;
    src?: string | null;
    role: RoomRole;
    status: MemberStatus;
    playerColor?: string | null;
    size?: number;
  }>(),
  {
    size: 42,
  },
);

const avatarBorderColor = computed(() => {
  if (props.playerColor) return props.playerColor;
  if (props.role === "owner") return "#f2c14d";
  if (props.role === "manager") return "#3dc0b3";
  return "color-mix(in srgb, var(--c-border) 75%, white)";
});

function memberInitial(name: string) {
  return name.slice(0, 1).toUpperCase();
}
</script>

<template>
  <div
    class="avatar"
    :data-role="role"
    :style="{ width: `${props.size}px`, height: `${props.size}px` }"
  >
    <BaseAvatar
      class="avatarInner"
      :src="src || undefined"
      :name="name"
      :alt="name"
      shape="circle"
      fit="cover"
      :style="{
        width: `${props.size}px`,
        height: `${props.size}px`,
        borderColor: avatarBorderColor,
      }"
    >
      <template #fallback>
        <span>{{ memberInitial(name) }}</span>
      </template>
    </BaseAvatar>
    <span class="statusDot" :data-status="status" />
  </div>
</template>

<style scoped>
.avatar {
  position: relative;
  display: grid;
  place-items: center;
}

.avatarInner {
  border-radius: 999px;
  font-size: 13px;
  border: 2px solid var(--c-border);
  user-select: none;
}

.statusDot {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 11px;
  height: 11px;
  border-radius: 999px;
  border: 2px solid white;
}

.statusDot[data-status="idle"],
.statusDot[data-status="ready"] {
  background: #2fb46e;
}

.statusDot[data-status="stalling"] {
  background: #dfad3f;
}

.statusDot[data-status="offline"] {
  background: transparent;
  border-color: #9aa8b8;
}

.statusDot[data-status="error"] {
  background: #dc4f4f;
}
</style>
