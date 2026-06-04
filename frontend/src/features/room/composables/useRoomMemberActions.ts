import { ref, type ComputedRef } from "vue";
import type { Router } from "vue-router";
import {
  deleteRoom,
  inviteRoomJoinRequest,
  leaveRoom,
  patchRoomMemberGameRole,
  removeRoomMember,
  setRoomMemberManager,
  unsetRoomMemberManager,
  type GameRole,
} from "@/infra/api/rooms.api";
import { useEntitiesStore } from "@/stores/entities.store";
import { useToastsStore } from "@/stores/toasts.store";
import { getBackendErrorMessage } from "@/infra/http/client";

type UseRoomMemberActionsOptions = {
  roomId: ComputedRef<number>;
  router: Router;
  t: (key: string) => string;
  syncCurrentUserRoles: () => void;
  fetchRoomRequests: (options?: { force?: boolean }) => Promise<void>;
};

function extractErrorMessage(error: any, fallback: string) {
  return getBackendErrorMessage(error) || fallback;
}

function setMemberActionLoading(actionIds: { value: number[] }, userId: number, loading: boolean) {
  actionIds.value = loading
    ? [...new Set([...actionIds.value, userId])]
    : actionIds.value.filter((id) => id !== userId);
}

export function useRoomMemberActions(options: UseRoomMemberActionsOptions) {
  const entitiesStore = useEntitiesStore();
  const toasts = useToastsStore();

  const isLeavingRoom = ref(false);
  const isDisbandingRoom = ref(false);
  const invitingMemberUserIds = ref<number[]>([]);
  const settingManagerUserIds = ref<number[]>([]);
  const settingGameRoleUserIds = ref<number[]>([]);
  const removingMemberUserIds = ref<number[]>([]);

  async function handleLeaveRoom() {
    if (!options.roomId.value || isLeavingRoom.value) return;

    isLeavingRoom.value = true;

    try {
      await leaveRoom(options.roomId.value);
      toasts.push({
        message: options.t("room.members.leaveSuccess"),
        tone: "success",
      });
      await options.router.push("/");
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.leaveFailed")),
        tone: "danger",
      });
    } finally {
      isLeavingRoom.value = false;
    }
  }

  async function handleDisbandRoom() {
    if (!options.roomId.value || isDisbandingRoom.value) return;

    isDisbandingRoom.value = true;

    try {
      await deleteRoom(options.roomId.value);
      toasts.push({
        message: options.t("room.members.disbandSuccess"),
        tone: "success",
      });
      await options.router.push("/");
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.disbandFailed")),
        tone: "danger",
      });
    } finally {
      isDisbandingRoom.value = false;
    }
  }

  async function handleInviteUser(userId: number) {
    if (!options.roomId.value || invitingMemberUserIds.value.includes(userId)) return;

    setMemberActionLoading(invitingMemberUserIds, userId, true);

    try {
      await inviteRoomJoinRequest(options.roomId.value, { target_user_id: userId });
      await options.fetchRoomRequests({ force: true });
      toasts.push({
        message: options.t("room.members.inviteSuccess"),
        tone: "success",
      });
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.inviteFailed")),
        tone: "danger",
      });
    } finally {
      setMemberActionLoading(invitingMemberUserIds, userId, false);
    }
  }

  async function handleSetMemberManager(userId: number) {
    if (!options.roomId.value || settingManagerUserIds.value.includes(userId)) return;

    setMemberActionLoading(settingManagerUserIds, userId, true);

    try {
      const member = await setRoomMemberManager(options.roomId.value, userId);
      entitiesStore.upsertRoomMember(member);
      options.syncCurrentUserRoles();
      toasts.push({
        message: options.t("room.members.setManagerSuccess"),
        tone: "success",
      });
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.setManagerFailed")),
        tone: "danger",
      });
    } finally {
      setMemberActionLoading(settingManagerUserIds, userId, false);
    }
  }

  async function handleUnsetMemberManager(userId: number) {
    if (!options.roomId.value || settingManagerUserIds.value.includes(userId)) return;

    setMemberActionLoading(settingManagerUserIds, userId, true);

    try {
      const member = await unsetRoomMemberManager(options.roomId.value, userId);
      entitiesStore.upsertRoomMember(member);
      options.syncCurrentUserRoles();
      toasts.push({
        message: options.t("room.members.unsetManagerSuccess"),
        tone: "success",
      });
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.unsetManagerFailed")),
        tone: "danger",
      });
    } finally {
      setMemberActionLoading(settingManagerUserIds, userId, false);
    }
  }

  async function handleSetMemberGameRole(userId: number, gameRole: GameRole) {
    if (!options.roomId.value || settingGameRoleUserIds.value.includes(userId)) return;

    setMemberActionLoading(settingGameRoleUserIds, userId, true);

    try {
      const member = await patchRoomMemberGameRole(options.roomId.value, userId, {
        game_role: gameRole,
      });
      entitiesStore.upsertRoomMember(member);
      options.syncCurrentUserRoles();
      toasts.push({
        message: options.t("room.members.setGameRoleSuccess"),
        tone: "success",
      });
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.setGameRoleFailed")),
        tone: "danger",
      });
    } finally {
      setMemberActionLoading(settingGameRoleUserIds, userId, false);
    }
  }

  async function handleRemoveRoomMember(userId: number) {
    if (!options.roomId.value || removingMemberUserIds.value.includes(userId)) return;

    setMemberActionLoading(removingMemberUserIds, userId, true);

    try {
      await removeRoomMember(options.roomId.value, userId);
      entitiesStore.removeRoomMember(options.roomId.value, userId);
      options.syncCurrentUserRoles();
      toasts.push({
        message: options.t("room.members.removeSuccess"),
        tone: "success",
      });
    } catch (e: any) {
      toasts.push({
        message: extractErrorMessage(e, options.t("room.members.removeFailed")),
        tone: "danger",
      });
    } finally {
      setMemberActionLoading(removingMemberUserIds, userId, false);
    }
  }

  function resetMemberActionState() {
    invitingMemberUserIds.value = [];
    settingManagerUserIds.value = [];
    settingGameRoleUserIds.value = [];
    removingMemberUserIds.value = [];
  }

  return {
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
  };
}
