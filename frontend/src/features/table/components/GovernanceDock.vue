<script setup lang="ts">
import { computed, ref, watch, type Component } from "vue";
import { useI18n } from "vue-i18n";
import {
  ClipboardDocumentCheckIcon,
  Cog6ToothIcon,
  UserGroupIcon,
} from "@heroicons/vue/24/outline";
import AppTabs from "@/ui/layout/AppTabs.vue";
import FloatingPanel from "@/features/table/components/FloatingPanel.vue";
import RoomMembersTab from "@/features/room/components/workspace/RoomMembersTab.vue";
import RoomRequestsTab from "@/features/room/components/workspace/RoomRequestsTab.vue";
import RoomSettingsTab from "@/features/room/components/workspace/RoomSettingsTab.vue";
import type { GameRole, GovernancePanelKey, MemberStatus, RoomRole } from "@/features/room/types";
// GovernancePanelKey in room/types
import type { Room, RoomPatchPayload } from "@/infra/api/rooms.api";

const props = defineProps<{
  roomId: number;
  room: Room;
  members: Array<{
    id: number;
    name: string;
    email?: string | null;
    avatarUrl?: string | null;
    room_role: RoomRole;
    game_role: GameRole;
    status: MemberStatus;
  }>;
  membersLoading?: boolean;
  membersError?: string;
  canManageRequests?: boolean;
  canManageSettings?: boolean;
  requestsBadge?: string;
  requestsLoading?: boolean;
  requestsError?: string | null;
  requestItems: Array<{
    id: number;
    user: string;
    note: string;
    time: string;
  }>;
  isRequestActionLoading: (requestId: number) => boolean;
  settingsSaving?: boolean;
  isOwner?: boolean;
  canRemoveMembers?: boolean;
  actionDisabled?: boolean;
  leaving?: boolean;
  disbanding?: boolean;
  pendingJoinRequests?: Array<{
    userId: number;
    source: "apply" | "invite" | "member_invite";
  }>;
  settingManagerUserIds?: number[];
  settingGameRoleUserIds?: number[];
  removingMemberUserIds?: number[];
}>();

const emit = defineEmits<{
  inviteUser: [userId: number];
  leaveRoom: [];
  disbandRoom: [];
  setManager: [userId: number];
  unsetManager: [userId: number];
  setGameRole: [userId: number, gameRole: GameRole];
  removeMember: [userId: number];
  approveRequest: [requestId: number];
  rejectRequest: [requestId: number];
  saveSettings: [payload: RoomPatchPayload];
  openRequests: [];
}>();

const { t } = useI18n();
const activePanel = ref<GovernancePanelKey>("members");

const panelOptions = computed<{ key: GovernancePanelKey; label: string; badge?: string; icon?: Component }[]>(() => {
  const items: { key: GovernancePanelKey; label: string; badge?: string; icon?: Component }[] = [
    { key: "members", label: t("room.tabs.members"), icon: UserGroupIcon },
  ];

  if (props.canManageRequests) {
    items.push({
      key: "requests",
      label: t("room.tabs.requests"),
      badge: props.requestsBadge,
      icon: ClipboardDocumentCheckIcon,
    });
  }

  if (props.canManageSettings) {
    items.push({
      key: "settings",
      label: t("room.tabs.settings"),
      icon: Cog6ToothIcon,
    });
  }

  return items;
});

watch(panelOptions, (panels) => {
  if (!panels.some((p) => p.key === activePanel.value)) {
    activePanel.value = panels[0]?.key ?? "members";
  }
});

watch(activePanel, (panel) => {
  if (panel === "requests") {
    emit("openRequests");
  }
});
</script>

<template>
  <FloatingPanel
    :title="t('table.governance.title')"
    anchor="top-left"
    collapse-to="top-left"
    variant="governance"
    :storage-key="`room-${roomId}-governance`"
  >
    <AppTabs
      v-model="activePanel"
      :items="panelOptions"
    />

    <div class="govContent">
    <RoomMembersTab
      v-show="activePanel === 'members'"
      :members="members"
      :search-placeholder="t('room.members.searchPlaceholder')"
      :invite-label="t('room.members.invite')"
      :leave-room-label="t('room.members.leaveRoom')"
      :disband-room-label="t('room.members.disbandRoom')"
      :is-owner="isOwner"
      :can-remove-members="canRemoveMembers"
      :can-manage-game-role="canRemoveMembers"
      :setting-game-role-user-ids="settingGameRoleUserIds"
      :action-disabled="actionDisabled"
      :leaving="leaving"
      :disbanding="disbanding"
      :pending-join-requests="pendingJoinRequests"
      :setting-manager-user-ids="settingManagerUserIds"
      :removing-member-user-ids="removingMemberUserIds"
      :loading="membersLoading"
      :loading-label="t('common.loading')"
      :empty-label="membersError || t('room.membersEmpty')"
      @leave-room="emit('leaveRoom')"
      @disband-room="emit('disbandRoom')"
      @invite-user="emit('inviteUser', $event)"
      @set-manager="emit('setManager', $event)"
      @unset-manager="emit('unsetManager', $event)"
      @set-game-role="(userId, gameRole) => emit('setGameRole', userId, gameRole)"
      @remove-member="emit('removeMember', $event)"
    />

    <RoomRequestsTab
      v-show="activePanel === 'requests' && canManageRequests"
      :loading="requestsLoading"
      :error="requestsError"
      :empty-label="t('room.requestsEmpty')"
      :items="requestItems"
      :is-request-action-loading="isRequestActionLoading"
      @approve="emit('approveRequest', $event)"
      @reject="emit('rejectRequest', $event)"
    />

    <RoomSettingsTab
      v-if="canManageSettings"
      v-show="activePanel === 'settings'"
      :room="room"
      :saving="settingsSaving"
      @save="emit('saveSettings', $event)"
    />
    </div>
  </FloatingPanel>
</template>

<style scoped>
:deep(.tabs) {
  border-bottom: 1px solid color-mix(in srgb, var(--c-border) 65%, transparent);
}

.govContent {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

:deep(.govContent .panelBody) {
  min-height: 0;
  overflow: auto;
}
</style>
