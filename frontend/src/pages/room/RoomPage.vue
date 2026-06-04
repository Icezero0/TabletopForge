<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  getRoomById,
  getRoomMembers,
  patchRoom,
  type Room,
  type RoomPatchPayload,
} from "@/infra/api/rooms.api";
import BaseLayout from "@/ui/layout/BaseLayout.vue";
import RoomChatTab from "@/features/room/components/workspace/RoomChatTab.vue";
import type { GameRole, MemberStatus, RoomRole } from "@/features/room/types";
import type { ChatSegment } from "@/features/chat/types";
import { useRoomJoinRequests } from "@/features/room/composables/useRoomJoinRequests";
import { useRoomMemberActions } from "@/features/room/composables/useRoomMemberActions";
import { useRoomRealtimeSession } from "@/features/room/composables/useRoomRealtimeSession";
import type { RoomRealtimeSessionClosed } from "@/infra/realtime/roomRealtime";
import BottomAssetBar from "@/features/table/components/BottomAssetBar.vue";
import FloatingPanel from "@/features/table/components/FloatingPanel.vue";
import GovernanceDock from "@/features/table/components/GovernanceDock.vue";
import InfoPanel from "@/features/table/components/InfoPanel.vue";
import MapViewport from "@/features/table/components/MapViewport.vue";
import PersonalMemo from "@/features/table/components/PersonalMemo.vue";
import TableStage from "@/features/table/components/TableStage.vue";
import TopToolBar from "@/features/table/components/TopToolBar.vue";
import { useGridScale } from "@/features/table/composables/useGridScale";
import { useTableToolMode } from "@/features/table/composables/useTableToolMode";
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
const currentUserRoomRole = ref<RoomRoleState>("unknown");
const currentUserGameRole = ref<GameRole | "unknown">("unknown");

const roomId = computed(() => {
  const raw = route.params.id;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
});

const canManageRoomRequests = computed(() =>
  currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
const canManageRoomSettings = computed(() =>
  currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
const currentUserIsOwner = computed(() => currentUserRoomRole.value === "owner");
const currentUserCanRemoveMembers = computed(() =>
  currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
const memberDangerActionDisabled = computed(() => currentUserRoomRole.value === "unknown");

const canAddMap = computed(() => currentUserGameRole.value === "GM");
const canAddCharacter = computed(() =>
  currentUserGameRole.value === "GM" || currentUserGameRole.value === "PL");

const { toolMode, disabledTools } = useTableToolMode(currentUserGameRole);
const {
  gridCellPx,
  gridCellFt,
  scaleBarCells,
  canIncrease: canIncreaseGrid,
  canDecrease: canDecreaseGrid,
  increase: increaseGrid,
  decrease: decreaseGrid,
} = useGridScale(roomId);

const roomMessagesState = computed(() => messagesStore.getRoomState(roomId.value));
const roomChatMessages = computed(() => messagesStore.getRoomChatMessages(roomId.value));
const entityRoomMembers = computed(() => entitiesStore.getRoomMembers(roomId.value));
const hasOlderMessages = computed(() => roomMessagesState.value.nextBeforeId != null);

const memberActions = useRoomMemberActions({
  roomId,
  router,
  t,
  syncCurrentUserRoles,
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
  handleSetMemberGameRole,
  handleRemoveRoomMember,
  settingGameRoleUserIds,
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
    room_role: member.room_role,
    game_role: member.game_role,
    status: memberStatus,
  };
}));
const roomMemberStatusByUserId = computed<Map<number, MemberStatus>>(() =>
  new Map(roomMemberItems.value.map((member) => [member.id, member.status])));

function syncCurrentUserRoles() {
  const meId = auth.me?.id;
  if (!meId) {
    currentUserRoomRole.value = "unknown";
    currentUserGameRole.value = "unknown";
    return;
  }

  const selfMember = entityRoomMembers.value.find((member) => member.user_id === meId);
  if (selfMember) {
    currentUserRoomRole.value = selfMember.room_role;
    currentUserGameRole.value = selfMember.game_role;
    return;
  }

  if (room.value?.owner_id === meId) {
    currentUserRoomRole.value = "owner";
    currentUserGameRole.value = "unknown";
    return;
  }

  currentUserRoomRole.value = "unknown";
  currentUserGameRole.value = "unknown";
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
    syncCurrentUserRoles();
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
    syncCurrentUserRoles();
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

function handleAssetPlaceholder() {
  toasts.push({
    message: t("table.assets.comingSoon"),
    tone: "default",
  });
}

onMounted(() => {
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomMembers();
});

watch(roomId, () => {
  currentUserRoomRole.value = "unknown";
  currentUserGameRole.value = "unknown";
  resetRoomRequestsState();
  resetMemberActionState();
  void fetchRoom();
  void fetchRoomMessages();
  void fetchRoomMembers();
});
watch(() => auth.me?.id, () => {
  syncCurrentUserRoles();
});
watch([roomId, currentUserRoomRole], () => {
  void fetchRoomRequests();
});
</script>

<template>
  <div class="roomPageWrap">
  <BaseLayout :max-width="10000">
    <div class="roomShell">
      <div v-if="isLoading" class="state">{{ t("common.loading") }}</div>

      <div v-else-if="error" class="state error">{{ error }}</div>

      <TableStage v-else-if="room">
        <template #map>
          <MapViewport
            :grid-cell-px="gridCellPx"
            :scale-bar-cells="scaleBarCells"
          />
        </template>

        <template #overlays>
          <GovernanceDock
            :room-id="roomId"
            :room="room"
            :members="roomMemberItems"
            :members-loading="membersLoading"
            :members-error="membersError"
            :can-manage-requests="canManageRoomRequests"
            :can-manage-settings="canManageRoomSettings"
            :requests-badge="roomJoinRequests.length > 0 ? String(roomJoinRequests.length) : undefined"
            :requests-loading="requestsLoading"
            :requests-error="requestsError"
            :request-items="roomRequestItems"
            :is-request-action-loading="isRequestActionLoading"
            :settings-saving="settingsSaving"
            :is-owner="currentUserIsOwner"
            :can-remove-members="currentUserCanRemoveMembers"
            :action-disabled="memberDangerActionDisabled"
            :leaving="isLeavingRoom"
            :disbanding="isDisbandingRoom"
            :pending-join-requests="pendingMemberInviteStates"
            :setting-manager-user-ids="settingManagerUserIds"
            :setting-game-role-user-ids="settingGameRoleUserIds"
            :removing-member-user-ids="removingMemberUserIds"
            @invite-user="handleInviteUser"
            @leave-room="handleLeaveRoom"
            @disband-room="handleDisbandRoom"
            @set-manager="handleSetMemberManager"
            @unset-manager="handleUnsetMemberManager"
            @set-game-role="(userId, gameRole) => handleSetMemberGameRole(userId, gameRole)"
            @remove-member="handleRemoveRoomMember"
            @approve-request="approveRequest"
            @reject-request="rejectRequest"
            @save-settings="handleSaveRoomSettings"
            @open-requests="fetchRoomRequests({ force: true })"
          />

          <FloatingPanel
            :title="t('table.chat.title')"
            anchor="bottom-left"
            collapse-to="bottom-left"
            variant="chat"
            :storage-key="`room-${roomId}-chat`"
          >
            <RoomChatTab
              :room-key="roomId"
              :active="true"
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
          </FloatingPanel>

          <FloatingPanel
            :title="t('table.tools.toolbar')"
            anchor="top-center"
            collapse-to="top"
            variant="tools"
            :storage-key="`room-${roomId}-tools`"
          >
            <TopToolBar
              v-model="toolMode"
              :disabled-tools="disabledTools"
              :grid-cell-px="gridCellPx"
              :grid-cell-ft="gridCellFt"
              :can-increase-grid="canIncreaseGrid"
              :can-decrease-grid="canDecreaseGrid"
              @increase-grid="increaseGrid"
              @decrease-grid="decreaseGrid"
            />
          </FloatingPanel>

          <FloatingPanel
            :title="t('table.assets.barTitle')"
            anchor="bottom-center"
            collapse-to="bottom"
            variant="assets"
            :storage-key="`room-${roomId}-assets`"
          >
            <BottomAssetBar
              :can-add-map="canAddMap"
              :can-add-character="canAddCharacter"
              @add-map="handleAssetPlaceholder"
              @add-character="handleAssetPlaceholder"
            />
          </FloatingPanel>

          <div class="rightStack">
            <FloatingPanel
              :title="t('table.inspector.infoTitle')"
              inline
              collapse-to="right"
              variant="info"
              :storage-key="`room-${roomId}-info`"
            >
              <InfoPanel />
            </FloatingPanel>

            <FloatingPanel
              class="memoPanel"
              :title="t('table.inspector.memoTitle')"
              inline
              collapse-to="right"
              variant="memo"
              :storage-key="`room-${roomId}-memo`"
            >
              <PersonalMemo :room-id="roomId" />
            </FloatingPanel>
          </div>
        </template>
      </TableStage>
    </div>
  </BaseLayout>
  </div>
</template>

<style scoped>
.roomPageWrap {
  height: calc(100dvh - 56px);
  min-height: 0;
}

.roomPageWrap :deep(.page) {
  padding: 0;
  min-height: 0;
  height: 100%;
}

.roomPageWrap :deep(.container) {
  max-width: 100% !important;
  height: 100%;
  margin: 0;
}

.roomShell {
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.state {
  padding: 16px;
  color: var(--c-text-muted);
  font-size: 14px;
}

.state.error {
  color: var(--c-danger);
}

.rightStack {
  position: absolute;
  top: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  pointer-events: none;
  z-index: 2;
  max-width: min(300px, calc(100vw - 24px));
}

.rightStack > * {
  pointer-events: auto;
}

.rightStack > .memoPanel {
  margin-top: auto;
}

@media (max-width: 720px) {
  .roomShell {
    height: calc(100dvh - 52px);
  }

  .rightStack {
    max-width: calc(100vw - 24px);
  }
}
</style>
