import { computed, ref, type ComputedRef, type Ref } from "vue";
import type { Router } from "vue-router";
import {
  getRoomMembers,
  patchMyPlayerColor,
  patchRoom,
  type Room,
  type RoomPatchPayload,
} from "@/infra/api/rooms.api";
import { useAuthStore } from "@/stores/auth.store";
import { useEntitiesStore } from "@/stores/entities.store";
import { useToastsStore } from "@/stores/toasts.store";
import { getBackendErrorMessage } from "@/infra/http/client";
import type { GameRole, MemberStatus, RoomRole } from "@/features/room/types";
import { useRoomJoinRequests } from "@/features/room/composables/useRoomJoinRequests";
import { useRoomMemberActions } from "@/features/room/composables/useRoomMemberActions";

type RoomRoleState = RoomRole | "unknown";

type UseRoomGovernanceOptions = {
  roomId: ComputedRef<number>;
  room: Ref<Room | null>;
  router: Router;
  presentUserIds?: ComputedRef<Set<number>>;
  hasPresenceSnapshot?: ComputedRef<boolean>;
  t: (key: string, named?: Record<string, unknown>) => string;
  onRoomUpdated?: (room: Room) => void;
  onPlayerColorUpdated?: (color: string) => void;
};

export function useRoomGovernance(options: UseRoomGovernanceOptions) {
  const auth = useAuthStore();
  const entitiesStore = useEntitiesStore();
  const toasts = useToastsStore();

  const membersLoading = ref(false);
  const membersError = ref("");
  const settingsSaving = ref(false);
  const playerColorSaving = ref(false);
  const currentUserRoomRole = ref<RoomRoleState>("unknown");
  const currentUserGameRole = ref<GameRole | "unknown">("unknown");

  const currentUserId = computed(() => auth.me?.id ?? null);
  const entityRoomMembers = computed(() => entitiesStore.getRoomMembers(options.roomId.value));

  const canManageRoomRequests = computed(() =>
    currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
  const canManageRoomSettings = computed(() =>
    currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
  const currentUserIsOwner = computed(() => currentUserRoomRole.value === "owner");
  const currentUserCanRemoveMembers = computed(() =>
    currentUserRoomRole.value === "owner" || currentUserRoomRole.value === "manager");
  const memberDangerActionDisabled = computed(() => currentUserRoomRole.value === "unknown");

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

    if (options.room.value?.owner_id === meId) {
      currentUserRoomRole.value = "owner";
      currentUserGameRole.value = "unknown";
      return;
    }

    currentUserRoomRole.value = "unknown";
    currentUserGameRole.value = "unknown";
  }

  const memberActions = useRoomMemberActions({
    roomId: options.roomId,
    router: options.router,
    t: options.t,
    syncCurrentUserRoles,
    fetchRoomRequests: (fetchOptions) => fetchRoomRequests(fetchOptions),
  });

  const {
    isLeavingRoom,
    isDisbandingRoom,
    invitingMemberUserIds,
    settingManagerUserIds,
    settingGameRoleUserIds,
    removingMemberUserIds,
    handleLeaveRoom,
    handleDisbandRoom,
    handleInviteUser,
    handleSetMemberManager,
    handleUnsetMemberManager,
    handleSetMemberGameRole,
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
    roomId: options.roomId,
    canManageRoomRequests,
    optimisticInviteUserIds: invitingMemberUserIds,
    t: options.t,
  });

  async function fetchRoomMembers() {
    if (!options.roomId.value) {
      membersError.value = options.t("room.invalidId");
      return;
    }

    membersLoading.value = true;
    membersError.value = "";

    try {
      const response = await getRoomMembers(options.roomId.value);
      entitiesStore.upsertRoomMembers(response.items);
      syncCurrentUserRoles();
      await fetchRoomRequests({ force: true });
    } catch (e: any) {
      membersError.value =
        getBackendErrorMessage(e) ||
        options.t("room.membersLoadFailed");
    } finally {
      membersLoading.value = false;
    }
  }

  async function handleSaveRoomSettings(payload: RoomPatchPayload) {
    if (!options.roomId.value || settingsSaving.value) return;

    settingsSaving.value = true;

    try {
      const updatedRoom = await patchRoom(options.roomId.value, payload);
      options.room.value = updatedRoom;
      entitiesStore.upsertRoom(updatedRoom);
      options.onRoomUpdated?.(updatedRoom);
      toasts.push({
        message: options.t("room.settings.saved"),
        tone: "success",
      });
    } catch (error) {
      toasts.push({
        message: getBackendErrorMessage(error) || options.t("room.settings.saveFailed"),
        tone: "danger",
      });
    } finally {
      settingsSaving.value = false;
    }
  }

  const playerColorByUserId = computed(() => {
    const map = new Map<number, string>();
    for (const member of entityRoomMembers.value) {
      if (member.player_color) {
        map.set(member.user_id, member.player_color);
      }
    }
    return map;
  });

  const selfPlayerColor = computed(() => {
    const meId = currentUserId.value;
    if (!meId) return null;
    return playerColorByUserId.value.get(meId) ?? null;
  });

  const takenPlayerColors = computed(() => {
    const meId = currentUserId.value;
    const taken = new Set<string>();
    for (const member of entityRoomMembers.value) {
      if (member.player_color && member.user_id !== meId) {
        taken.add(member.player_color);
      }
    }
    return taken;
  });

  async function updatePlayerColor(color: string) {
    if (!options.roomId.value || playerColorSaving.value) return;
    playerColorSaving.value = true;
    try {
      const updated = await patchMyPlayerColor(options.roomId.value, color);
      entitiesStore.upsertRoomMember(updated);
      options.onPlayerColorUpdated?.(color);
    } catch (e) {
      toasts.push({
        message: getBackendErrorMessage(e) || options.t("room.playerColor.saveFailed"),
        tone: "danger",
      });
    } finally {
      playerColorSaving.value = false;
    }
  }

  const roomMemberItems = computed(() => entityRoomMembers.value.map((member) => {
    const user = entitiesStore.getUser(member.user_id);
    const memberStatus: MemberStatus =
      options.hasPresenceSnapshot?.value && options.presentUserIds?.value.has(member.user_id)
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
      player_color: member.player_color ?? null,
      status: memberStatus,
    };
  }));

  const roomMemberStatusByUserId = computed<Map<number, MemberStatus>>(() =>
    new Map(roomMemberItems.value.map((member) => [member.id, member.status])));

  const ownerNameByUserId = computed(() =>
    new Map(roomMemberItems.value.map((member) => [member.id, member.name])));

  function resetRoomGovernanceState() {
    currentUserRoomRole.value = "unknown";
    currentUserGameRole.value = "unknown";
    membersError.value = "";
    resetMemberActionState();
    resetRoomRequestsState();
  }

  return {
    membersLoading,
    membersError,
    settingsSaving,
    playerColorSaving,
    currentUserId,
    currentUserRoomRole,
    currentUserGameRole,
    canManageRoomRequests,
    canManageRoomSettings,
    currentUserIsOwner,
    currentUserCanRemoveMembers,
    memberDangerActionDisabled,
    entityRoomMembers,
    roomMemberItems,
    roomMemberStatusByUserId,
    ownerNameByUserId,
    playerColorByUserId,
    selfPlayerColor,
    takenPlayerColors,
    requestsLoading,
    requestsError,
    roomJoinRequests,
    roomRequestItems,
    pendingMemberInviteStates,
    fetchRoomMembers,
    fetchRoomRequests,
    isRequestActionLoading,
    approveRequest,
    rejectRequest,
    isLeavingRoom,
    isDisbandingRoom,
    settingManagerUserIds,
    settingGameRoleUserIds,
    removingMemberUserIds,
    handleLeaveRoom,
    handleDisbandRoom,
    handleInviteUser,
    handleSetMemberManager,
    handleUnsetMemberManager,
    handleSetMemberGameRole,
    handleRemoveRoomMember,
    handleSaveRoomSettings,
    updatePlayerColor,
    syncCurrentUserRoles,
    resetRoomGovernanceState,
  };
}
