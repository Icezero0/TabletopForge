<script setup lang="ts">
import { computed, onMounted, ref, watch, type Component } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  ChatBubbleLeftRightIcon,
  ClipboardDocumentCheckIcon,
  Cog6ToothIcon,
  Squares2X2Icon,
  UserGroupIcon,
} from "@heroicons/vue/24/outline";
import {
  getRoomById,
  getRoomMembers,
  patchRoom,
  type Room,
  type RoomPatchPayload,
} from "@/infra/api/rooms.api";
import BasePill from "@/ui/base/BasePill.vue";
import AppTabs from "@/ui/layout/AppTabs.vue";
import RoomChatTab from "@/features/room/components/workspace/RoomChatTab.vue";
import RoomMembersTab from "@/features/room/components/workspace/RoomMembersTab.vue";
import RoomRequestsTab from "@/features/room/components/workspace/RoomRequestsTab.vue";
import RoomSettingsTab from "@/features/room/components/workspace/RoomSettingsTab.vue";
import type { MemberStatus, RoomPanelKey, RoomRole } from "@/features/room/types";
import type { ChatSegment } from "@/features/chat/types";
import { useRoomWorkspaceLayout } from "@/features/room/composables/useRoomWorkspaceLayout";
import { useRoomJoinRequests } from "@/features/room/composables/useRoomJoinRequests";
import { useRoomMemberActions } from "@/features/room/composables/useRoomMemberActions";
import { useRoomRealtimeSession } from "@/features/room/composables/useRoomRealtimeSession";
import type { RoomRealtimeSessionClosed } from "@/infra/realtime/roomRealtime";
import { useMessagesStore } from "@/stores/messages.store";
import { useEntitiesStore } from "@/stores/entities.store";
import { useAuthStore } from "@/stores/auth.store";
import { useToastsStore } from "@/stores/toasts.store";
import { getBackendErrorMessage } from "@/infra/http/client";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const entitiesStore = useEntitiesStore();
const messagesStore = useMessagesStore();
const toasts = useToastsStore();

type RoomRoleState = RoomRole | "unknown";

const room = ref<Room | null>(null);
const isLoading = ref(false);
const error = ref("");
const membersLoading = ref(false);
const membersError = ref("");
const settingsSaving = ref(false);
const currentUserRole = ref<RoomRoleState>("unknown");
const activePanel = ref<RoomPanelKey>("chat");

const roomId = computed(() => {
  const raw = route.params.id;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
});

const canManageRoomRequests = computed(() =>
  currentUserRole.value === "owner" || currentUserRole.value === "manager");
const canManageRoomSettings = computed(() =>
  currentUserRole.value === "owner" || currentUserRole.value === "manager");
const currentUserIsOwner = computed(() => currentUserRole.value === "owner");
const currentUserCanRemoveMembers = computed(() =>
  currentUserRole.value === "owner" || currentUserRole.value === "manager");
const memberDangerActionDisabled = computed(() => currentUserRole.value === "unknown");

const allPanelOptions = computed<{ key: RoomPanelKey; label: string; badge?: string; icon?: Component }[]>(() => [
  { key: "chat", label: t("room.tabs.chat"), icon: ChatBubbleLeftRightIcon },
  { key: "members", label: t("room.tabs.members"), icon: UserGroupIcon },
  {
    key: "requests",
    label: t("room.tabs.requests"),
    badge: roomJoinRequests.value.length > 0 ? String(roomJoinRequests.value.length) : undefined,
    icon: ClipboardDocumentCheckIcon,
  },
  { key: "settings", label: t("room.tabs.settings"), icon: Cog6ToothIcon },
]);

const panelOptions = computed(() => {
  if (!canManageRoomRequests.value && !canManageRoomSettings.value) {
    return allPanelOptions.value.filter((panel) =>
      panel.key === "chat" || panel.key === "members");
  }

  return allPanelOptions.value.filter((panel) => {
    if (panel.key === "requests") return canManageRoomRequests.value;
    if (panel.key === "settings") return canManageRoomSettings.value;
    return true;
  });
});

const roomMessagesState = computed(() => messagesStore.getRoomState(roomId.value));
const roomChatMessages = computed(() => messagesStore.getRoomChatMessages(roomId.value));
const entityRoomMembers = computed(() => entitiesStore.getRoomMembers(roomId.value));
const hasOlderMessages = computed(() => roomMessagesState.value.nextBeforeId != null);

const memberActions = useRoomMemberActions({
  roomId,
  router,
  t,
  syncCurrentUserRole,
  fetchRoomRequests: (options) => fetchRoomRequests(options),
});
const {
  isLeavingRoom,
  isDisbandingRoom,
  invitingMemberUserIds,
  settingManagerUserIds,
  removingMemberUserIds,
  handleLeaveRoom,
  handleDisbandRoom,
  handleInviteUser,
  handleSetMemberManager,
  handleUnsetMemberManager,
  handleRemoveRoomMember,
  resetMemberActionState,
} = memberActions;

const {
  requestsLoading,
  requestsError,
  roomJoinRequests,
  roomRequestItems,
  pendingMemberInviteStates,
  fetchRoomRequests,
  isRequestActionLoading,
  approveRequest,
  rejectRequest,
  resetRoomRequestsState,
} = useRoomJoinRequests({
  roomId,
  canManageRoomRequests,
  optimisticInviteUserIds: invitingMemberUserIds,
  t,
});

const layout = useRoomWorkspaceLayout({
  activePanel,
  roomId: computed(() => room.value?.id),
  isLoading,
});
const mainGridStyle = computed(() => layout.mainGridStyle.value);
const workspaceCardStyle = computed(() => layout.workspaceCardStyle.value);

const realtime = useRoomRealtimeSession({
  roomId,
  refreshRoom: () => fetchRoom({ silent: true }),
  refreshRoomMembers: fetchRoomMembers,
  refreshRoomRequests: () => fetchRoomRequests({ force: true }),
  onSessionClosed: handleRealtimeSessionClosed,
});

const presentUserIds = computed(() => new Set(realtime.presentUserIds.value));
const roomMemberItems = computed(() => entityRoomMembers.value.map((member) => {
  const user = entitiesStore.getUser(member.user_id);
  const memberStatus: MemberStatus =
    realtime.hasPresenceSnapshot.value && presentUserIds.value.has(member.user_id)
      ? "idle"
      : "offline";

  return {
    id: member.user_id,
    name:
      user?.username ||
      user?.email ||
      `User #${member.user_id}`,
    email: user?.email ?? null,
    avatarUrl: user?.avatar_url ?? null,
    role: member.role,
    status: memberStatus,
  };
}));
const roomMemberStatusByUserId = computed<Map<number, MemberStatus>>(() =>
  new Map(roomMemberItems.value.map((member) => [member.id, member.status])));

const roomVisibilityLabel = computed(() =>
  room.value?.visibility === "public" ? "Public" : "Private");
const roomRoleLabel = computed(() =>
  currentUserRole.value === "unknown" ? "Unknown" : currentUserRole.value);

function syncCurrentUserRole() {
  const meId = auth.me?.id;
  if (!meId) {
    currentUserRole.value = "unknown";
    return;
  }

  if (room.value?.owner_id === meId) {
    currentUserRole.value = "owner";
    return;
  }

  const selfMember = entityRoomMembers.value.find((member) => member.user_id === meId);
  if (selfMember) {
    currentUserRole.value = selfMember.role;
    return;
  }

  currentUserRole.value = "unknown";
}

async function fetchRoom(options?: { silent?: boolean }) {
  if (!roomId.value) {
    error.value = t("room.invalidId");
    return;
  }

  const shouldShowLoading = !options?.silent && !room.value;
  if (shouldShowLoading) {
    isLoading.value = true;
  }
  error.value = "";

  try {
    room.value = await getRoomById(roomId.value);
    entitiesStore.upsertRoom(room.value);
    syncCurrentUserRole();
  } catch (e: any) {
    if (!options?.silent) {
      room.value = null;
    }
    error.value =
      getBackendErrorMessage(e) ||
      t("room.loadFailed");
  } finally {
    if (shouldShowLoading) {
      isLoading.value = false;
    }
  }
}

async function fetchRoomMembers() {
  if (!roomId.value) {
    membersError.value = t("room.invalidId");
    return;
  }

  membersLoading.value = true;
  membersError.value = "";

  try {
    const response = await getRoomMembers(roomId.value);
    entitiesStore.upsertRoomMembers(response.items);
    syncCurrentUserRole();
    await fetchRoomRequests({ force: true });
  } catch (e: any) {
    membersError.value =
      getBackendErrorMessage(e) ||
      t("room.membersLoadFailed");
  } finally {
    membersLoading.value = false;
  }
}

async function fetchRoomMessages() {
  if (!roomId.value) return;

  try {
    await messagesStore.refreshRoomMessages(roomId.value, 20);
  } catch {
    // messages.store already keeps the error state for the panel
  }
}

async function loadOlderRoomMessages() {
  if (!roomId.value) return;

  try {
    await messagesStore.loadOlderMessages(roomId.value, 20);
  } catch {
    // messages.store already keeps the error state for the panel
  }
}

async function handleSend(segments: ChatSegment[]) {
  if (!roomId.value) return;

  try {
    await messagesStore.sendSegments(roomId.value, segments);
  } catch (error) {
    toasts.push({
      message: t("room.chatSendFailed"),
      tone: "danger",
    });
    throw error;
  }
}

async function handleSaveRoomSettings(payload: RoomPatchPayload) {
  if (!roomId.value || settingsSaving.value) return;

  settingsSaving.value = true;

  try {
    const updatedRoom = await patchRoom(roomId.value, payload);
    room.value = updatedRoom;
    entitiesStore.upsertRoom(updatedRoom);
    toasts.push({
      message: t("room.settings.saved"),
      tone: "success",
    });
  } catch (error) {
    toasts.push({
      message: getBackendErrorMessage(error) || t("room.settings.saveFailed"),
      tone: "danger",
    });
  } finally {
    settingsSaving.value = false;
  }
}

function handleRealtimeSessionClosed(payload: RoomRealtimeSessionClosed) {
  toasts.push({
    message: t(`room.realtime.sessionClosed.${payload.reason}`),
    tone: "warning",
  });

  if (payload.reason === "removed_from_room" || payload.reason === "room_deleted") {
    void router.push("/");
  }
}

onMounted(() => {
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomMembers();
});

watch(roomId, () => {
  currentUserRole.value = "unknown";
  resetRoomRequestsState();
  resetMemberActionState();
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomMembers();
});
watch(panelOptions, (nextPanels) => {
  if (!nextPanels.some((panel) => panel.key === activePanel.value)) {
    activePanel.value = nextPanels[0]?.key ?? "chat";
  }
});
watch(() => auth.me?.id, () => {
  syncCurrentUserRole();
});
watch([roomId, currentUserRole], () => {
  void fetchRoomRequests();
});
watch(activePanel, (panel) => {
  if (panel === "requests") {
    void fetchRoomRequests();
  }
});
</script>

<template>
  <BaseLayout :max-width="1320">
    <div class="roomShell">
      <div v-if="isLoading" class="state">{{ t("common.loading") }}</div>

      <div v-else-if="error" class="state error">{{ error }}</div>

      <template v-else-if="room">
        <BaseCard class="topStrip">
          <div class="roomIntro">
            <h2 class="roomName">{{ room.name }}</h2>
          </div>

          <div class="statusBar">
            <BasePill tone="default">{{ roomVisibilityLabel }}</BasePill>
            <BasePill tone="default">{{ roomRoleLabel }}</BasePill>
          </div>
        </BaseCard>

        <div
          class="mainGrid"
          :style="mainGridStyle"
        >
          <section
            :ref="(el) => { layout.setStageColumnEl(el as HTMLElement | null); }"
            class="stageColumn"
          >
            <BaseCard class="stageCard">
              <div class="tabletopStage">
                <Squares2X2Icon class="stageIcon" aria-hidden="true" />
                <div class="stageCopy">
                  <h3>Tabletop</h3>
                  <p>地图、Token 和角色状态将在后续业务阶段接入。</p>
                </div>
              </div>
            </BaseCard>
          </section>

          <aside
            :ref="(el) => { layout.setWorkspaceColumnEl(el as HTMLElement | null); }"
            class="workspaceColumn"
          >
            <BaseCard
              class="workspaceCard"
              :style="workspaceCardStyle"
            >
              <AppTabs
                v-model="activePanel"
                :items="panelOptions"
              />

              <RoomChatTab
                v-show="activePanel === 'chat'"
                :room-key="roomId"
                :active="activePanel === 'chat'"
                :messages="roomChatMessages"
                :member-status-by-user-id="roomMemberStatusByUserId"
                :send-label="t('room.chat.send')"
                :loading="roomMessagesState.isLoading"
                :sending="roomMessagesState.isSending"
                :loading-history="roomMessagesState.isLoadingHistory"
                :has-older="hasOlderMessages"
                :error="roomMessagesState.error"
                :loading-label="t('common.loading')"
                :empty-label="t('room.chatEmpty')"
                :send-message="handleSend"
                @load-older="loadOlderRoomMessages"
              />

              <RoomMembersTab
                v-show="activePanel === 'members'"
                :members="roomMemberItems"
                :search-placeholder="t('room.members.searchPlaceholder')"
                :invite-label="t('room.members.invite')"
                :leave-room-label="t('room.members.leaveRoom')"
                :disband-room-label="t('room.members.disbandRoom')"
                :is-owner="currentUserIsOwner"
                :can-remove-members="currentUserCanRemoveMembers"
                :action-disabled="memberDangerActionDisabled"
                :leaving="isLeavingRoom"
                :disbanding="isDisbandingRoom"
                :pending-join-requests="pendingMemberInviteStates"
                :setting-manager-user-ids="settingManagerUserIds"
                :removing-member-user-ids="removingMemberUserIds"
                :loading="membersLoading"
                :loading-label="t('common.loading')"
                :empty-label="membersError || t('room.membersEmpty')"
                @leave-room="handleLeaveRoom"
                @disband-room="handleDisbandRoom"
                @invite-user="handleInviteUser"
                @set-manager="handleSetMemberManager"
                @unset-manager="handleUnsetMemberManager"
                @remove-member="handleRemoveRoomMember"
              />

              <RoomRequestsTab
                v-show="activePanel === 'requests'"
                :loading="requestsLoading"
                :error="requestsError"
                :empty-label="t('room.requestsEmpty')"
                :items="roomRequestItems"
                :is-request-action-loading="isRequestActionLoading"
                @approve="approveRequest"
                @reject="rejectRequest"
              />

              <RoomSettingsTab
                v-if="canManageRoomSettings"
                v-show="activePanel === 'settings'"
                :room="room"
                :saving="settingsSaving"
                @save="handleSaveRoomSettings"
              />
            </BaseCard>
          </aside>
        </div>
      </template>
    </div>
  </BaseLayout>
</template>

<style scoped>
.roomShell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 16px;
  padding-top: 6px;
  min-height: 0;
}

.state {
  color: var(--c-text-muted);
  font-size: 14px;
}

.state.error {
  color: var(--c-danger);
}

.topStrip {
  padding: 18px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  background:
    radial-gradient(circle at top right, rgb(210 233 255 / 0.75), transparent 28%),
    linear-gradient(180deg, color-mix(in srgb, var(--c-surface) 92%, white), color-mix(in srgb, var(--c-surface) 88%, var(--c-bg)));
}

.roomIntro {
  min-width: 0;
}

.roomName {
  margin: 0;
  font-size: 24px;
  color: var(--c-text);
}

.statusBar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mainGrid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 380px);
  gap: 16px;
  align-items: start;
}

.stageColumn,
.workspaceColumn {
  min-width: 0;
}

.workspaceColumn {
  align-self: start;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
}

.stageCard {
  min-height: 420px;
  padding: 16px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--c-surface) 92%, white), color-mix(in srgb, var(--c-surface) 86%, var(--c-bg)));
  overflow: hidden;
}

.tabletopStage {
  min-height: 388px;
  display: grid;
  place-items: center;
  gap: 16px;
  align-content: center;
  border: 1px dashed color-mix(in srgb, var(--c-border) 80%, var(--c-primary));
  border-radius: 14px;
  background:
    linear-gradient(color-mix(in srgb, var(--c-border) 24%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--c-border) 24%, transparent) 1px, transparent 1px),
    color-mix(in srgb, var(--c-surface) 78%, var(--c-bg));
  background-size: 32px 32px;
  color: var(--c-text-muted);
  text-align: center;
  padding: 24px;
}

.stageIcon {
  width: 48px;
  height: 48px;
  color: color-mix(in srgb, var(--c-primary) 68%, var(--c-text-muted));
}

.stageCopy {
  display: grid;
  gap: 6px;
}

.stageCopy h3 {
  margin: 0;
  color: var(--c-text);
  font-size: 18px;
}

.stageCopy p {
  margin: 0;
  font-size: 13px;
}

.workspaceCard {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 0;
  height: 100%;
  overflow: hidden;
  max-height: 100%;
}

:deep(.workspaceCard.card) {
  padding: 0;
}

@media (max-width: 720px) {
  :deep(.page) {
    height: calc(100dvh - 56px);
    padding: 8px;
    overflow: hidden;
    box-sizing: border-box;
  }

  :deep(.container) {
    height: 100%;
  }

  .roomShell {
    height: 100%;
    overflow: hidden;
  }

  .mainGrid {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    height: 100%;
    min-height: 0;
  }

  .workspaceCard {
    min-height: 0;
  }

  .workspaceColumn {
    min-height: 0;
    overflow: hidden;
  }
}

@media (max-width: 640px) {
  .topStrip,
  .stageCard {
    padding: 12px;
  }

  .roomName {
    font-size: 20px;
  }
}
</style>
