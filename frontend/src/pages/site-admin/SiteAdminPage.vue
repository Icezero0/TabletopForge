<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import {
  MagnifyingGlassIcon,
  ShieldCheckIcon,
} from "@heroicons/vue/24/outline";
import {
  getUsers,
  patchUserSiteRole,
  type SiteRole,
  type UserResponse,
} from "@/infra/api/users.api";
import { getBackendErrorMessage } from "@/infra/http/client";
import { resolveMediaUrl } from "@/infra/media";
import { useAuthStore } from "@/stores/auth.store";
import { useToastsStore } from "@/stores/toasts.store";
import AppIcon from "@/ui/base/AppIcon.vue";

const { t } = useI18n();
const router = useRouter();
const auth = useAuthStore();
const toasts = useToastsStore();

const adminUsers = ref<UserResponse[]>([]);
const isLoading = ref(false);
const error = ref("");
const updatingUserIds = ref<number[]>([]);
const addDialogOpen = ref(false);
const addKeyword = ref("");
const addResults = ref<UserResponse[]>([]);
const addLoading = ref(false);
const addError = ref("");
const hasSearchedAddUsers = ref(false);

const filteredAddResults = computed(() =>
  addResults.value.filter((user) => user.site_role !== "admin" && !isSelf(user)),
);

function userDisplayName(user: UserResponse) {
  return user.username || user.email || `User #${user.id}`;
}

function userAvatarUrl(user: UserResponse) {
  return resolveMediaUrl(user.avatar_url);
}

function isSelf(user: UserResponse) {
  return auth.me?.id === user.id;
}

function isUpdating(userId: number) {
  return updatingUserIds.value.includes(userId);
}

function roleLabel(role: SiteRole) {
  return t(`siteAdmin.roles.${role}`);
}

function sortedUsers(users: UserResponse[]) {
  return [...users].sort((a, b) => a.id - b.id);
}

async function fetchAdmins() {
  if (!auth.canManageSiteRoles) {
    await router.replace("/");
    return;
  }

  isLoading.value = true;
  error.value = "";

  try {
    const admins: UserResponse[] = [];
    let page = 1;
    let totalPages = 1;

    do {
      const data = await getUsers({
        page,
        page_size: 100,
      });

      admins.push(...data.items.filter((user) => user.site_role === "admin"));
      totalPages = data.total_pages;
      page += 1;
    } while (page <= totalPages);

    adminUsers.value = sortedUsers(admins);
  } catch (err) {
    error.value = getBackendErrorMessage(err) || t("siteAdmin.loadFailed");
  } finally {
    isLoading.value = false;
  }
}

function openAddDialog() {
  addDialogOpen.value = true;
}

function closeAddDialog() {
  addDialogOpen.value = false;
  addError.value = "";
}

async function searchAddUsers() {
  const keyword = addKeyword.value.trim();

  if (!keyword) {
    addResults.value = [];
    addError.value = "";
    hasSearchedAddUsers.value = false;
    return;
  }

  addLoading.value = true;
  addError.value = "";
  hasSearchedAddUsers.value = true;

  try {
    const data = await getUsers({
      page: 1,
      page_size: 20,
      username: keyword,
      email: keyword,
    });

    addResults.value = data.items;
  } catch (err) {
    addError.value = getBackendErrorMessage(err) || t("siteAdmin.addSearchFailed");
  } finally {
    addLoading.value = false;
  }
}

async function setSiteRole(user: UserResponse, siteRole: SiteRole) {
  if (isSelf(user) || user.site_role === siteRole || isUpdating(user.id)) return;

  updatingUserIds.value = [...updatingUserIds.value, user.id];

  try {
    const updated = await patchUserSiteRole(user.id, siteRole);

    if (updated.site_role === "admin") {
      adminUsers.value = sortedUsers([
        ...adminUsers.value.filter((entry) => entry.id !== updated.id),
        updated,
      ]);
      addResults.value = addResults.value.filter((entry) => entry.id !== updated.id);
    } else {
      adminUsers.value = adminUsers.value.filter((entry) => entry.id !== updated.id);
      addResults.value = addResults.value.map((entry) =>
        entry.id === updated.id ? { ...entry, ...updated } : entry,
      );
    }

    toasts.push({
      message: t("siteAdmin.saved"),
      tone: "success",
    });
  } catch (err) {
    toasts.push({
      message: getBackendErrorMessage(err) || t("siteAdmin.saveFailed"),
      tone: "danger",
    });
  } finally {
    updatingUserIds.value = updatingUserIds.value.filter((id) => id !== user.id);
  }
}

onMounted(fetchAdmins);
</script>

<template>
  <AppPageShell :title="t('siteAdmin.title')" :max-width="980">
    <BaseCard class="adminCard">
      <div class="cardHeader">
        <div class="cardTitle">{{ t("siteAdmin.adminList") }}</div>

        <BaseButton variant="primary" @click="openAddDialog">
          {{ t("siteAdmin.add") }}
        </BaseButton>
      </div>

      <div class="adminScroll">
        <div v-if="isLoading" class="state">{{ t("common.loading") }}</div>
        <div v-else-if="error" class="state error">{{ error }}</div>
        <div v-else-if="adminUsers.length === 0" class="empty">
          <div class="emptyTitle">{{ t("siteAdmin.empty.title") }}</div>
          <div class="emptyHint">{{ t("siteAdmin.empty.hint") }}</div>
        </div>

        <div v-else class="userList">
          <RowListItem v-for="user in adminUsers" :key="user.id" class="userItem">
            <div class="userMain">
              <BaseAvatar
                size="sm"
                :src="userAvatarUrl(user)"
                :name="userDisplayName(user)"
              />

              <div class="userText">
                <div class="userName">{{ userDisplayName(user) }}</div>
                <div class="userMeta">
                  <span>#{{ user.id }}</span>
                  <span>{{ user.email }}</span>
                </div>
              </div>
            </div>

            <template #right>
              <div class="roleArea">
                <span class="rolePill" data-role="admin">
                  <AppIcon :icon="ShieldCheckIcon" :size="16" />
                  {{ roleLabel(user.site_role) }}
                </span>

                <BaseButton
                  variant="danger"
                  :disabled="isSelf(user)"
                  :loading="isUpdating(user.id)"
                  @click="setSiteRole(user, 'user')"
                >
                  {{ t("siteAdmin.actions.setUser") }}
                </BaseButton>
              </div>
            </template>
          </RowListItem>
        </div>
      </div>
    </BaseCard>

    <BaseDialog
      v-model="addDialogOpen"
      :aria-label="t('siteAdmin.addDialogTitle')"
      :max-width="520"
      @close="closeAddDialog"
    >
      <BaseCard class="addDialogCard">
        <form class="addSearchBar" @submit.prevent="searchAddUsers">
          <input
            v-model="addKeyword"
            class="addSearchInput"
            :aria-label="t('siteAdmin.searchLabel')"
            :placeholder="t('siteAdmin.addSearchPlaceholder')"
            :disabled="addLoading"
            autocomplete="off"
          >
          <BaseIconButton
            class="addSearchButton"
            type="submit"
            :aria-label="t('siteAdmin.search')"
            :disabled="addLoading"
          >
            <AppIcon :icon="MagnifyingGlassIcon" :size="17" />
          </BaseIconButton>
        </form>

        <div v-if="addError" class="dialogState error">{{ addError }}</div>
        <div v-else-if="addLoading" class="dialogState">
          {{ t("common.loading") }}
        </div>
        <div v-else-if="hasSearchedAddUsers && filteredAddResults.length === 0" class="dialogState">
          {{ t("siteAdmin.addSearchEmpty") }}
        </div>
        <div v-else class="dialogResults">
          <div
            v-for="user in filteredAddResults"
            :key="user.id"
            class="dialogUserItem"
          >
            <BaseAvatar
              size="sm"
              :src="userAvatarUrl(user)"
              :name="userDisplayName(user)"
            />
            <div class="dialogUserMeta">
              <div class="dialogUserName">{{ userDisplayName(user) }}</div>
              <div class="dialogUserEmail">{{ user.email }}</div>
            </div>
            <BaseButton
              class="dialogUserAction"
              variant="primary"
              :loading="isUpdating(user.id)"
              @click="setSiteRole(user, 'admin')"
            >
              {{ t("siteAdmin.actions.setAdmin") }}
            </BaseButton>
          </div>
        </div>
      </BaseCard>
    </BaseDialog>
  </AppPageShell>
</template>

<style scoped>
.adminCard {
  max-height: calc(100dvh - 140px);
  min-height: 0;
  padding: 22px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 16px;
  overflow: hidden;
}

.cardHeader {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.cardTitle {
  height: 40px;
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  line-height: 1;
  color: var(--c-text);
  font-size: inherit;
  font-weight: 500;
}

.adminScroll {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
  padding-right: 4px;
}

.state,
.empty {
  padding: 18px 6px;
  color: var(--c-text-muted);
}

.state.error,
.dialogState.error {
  color: var(--c-danger);
}

.empty {
  text-align: center;
}

.emptyTitle {
  margin-bottom: 6px;
  color: var(--c-text);
  font-size: 14px;
}

.emptyHint {
  font-size: 12px;
}

.userList {
  display: grid;
  gap: 10px;
}

.userMain {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.userText {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.userName {
  min-width: 0;
  color: var(--c-text);
  font-size: 14px;
  font-weight: 650;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.userMeta {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--c-text-muted);
  font-size: 12px;
}

.roleArea {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.rolePill {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-primary) 14%, var(--c-surface));
  color: var(--c-primary);
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.addDialogCard {
  padding: 12px;
  display: grid;
  gap: 12px;
}

.addSearchBar {
  min-height: 46px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 0 6px 0 14px;
  border: 1px solid var(--c-border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--c-surface) 86%, var(--c-bg));
}

.addSearchInput {
  width: 100%;
  min-width: 0;
  height: 42px;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 14px;
}

.addSearchButton {
  width: 34px;
  height: 34px;
}

.dialogState {
  min-height: 56px;
  display: grid;
  place-items: center;
  color: var(--c-text-muted);
  font-size: 13px;
  text-align: center;
}

.dialogResults {
  display: grid;
  gap: 8px;
  max-height: min(320px, 48dvh);
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.dialogUserItem {
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--c-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--c-surface) 78%, var(--c-bg));
}

.dialogUserMeta {
  flex: 1;
  min-width: 0;
}

.dialogUserName {
  font-size: 13px;
  color: var(--c-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dialogUserEmail {
  margin-top: 3px;
  color: var(--c-text-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dialogUserAction {
  flex: 0 0 auto;
}

@media (max-width: 720px) {
  .adminCard {
    max-height: calc(100dvh - 112px);
    padding: 14px;
  }

  .userItem :deep(.rowListItemInner),
  .roleArea {
    align-items: stretch;
  }

  .roleArea {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr;
  }

  .dialogUserItem {
    align-items: stretch;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
  }

  .dialogUserAction {
    grid-column: 1 / -1;
    width: 100%;
  }
}
</style>
