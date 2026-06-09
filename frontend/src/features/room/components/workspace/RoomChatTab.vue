<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import ChatPanel from "@/features/chat/components/ChatPanel.vue";
import DiceRollPanel from "@/features/room/components/workspace/DiceRollPanel.vue";
import { useDiceStore } from "@/stores/dice.store";
import type { ChatMessage, ChatSegment } from "@/features/chat/types";
import type { GameRole, MemberStatus } from "@/features/room/types";

const props = defineProps<{
  roomKey: number;
  active?: boolean;
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
  characterOwnerById: Map<number, number>;
  messages: ChatMessage[];
  sendLabel: string;
  loading?: boolean;
  sending?: boolean;
  loadingHistory?: boolean;
  hasOlder?: boolean;
  error?: string | null;
  loadingLabel: string;
  emptyLabel: string;
  sendMessage?: (segments: ChatSegment[]) => Promise<void> | void;
  memberStatusByUserId?: Map<number, MemberStatus>;
}>();

const emit = defineEmits<{
  send: [segments: ChatSegment[]];
  loadOlder: [];
}>();

const { t } = useI18n();
const diceStore = useDiceStore();
const activeTab = ref<"chat" | "adventureLog" | "dice">("chat");

watch(
  () => diceStore.getRoomState(props.roomKey).draft,
  (draft) => {
    if (draft) activeTab.value = "dice";
  },
);
</script>

<template>
  <div class="panelBody chatPanelBody">
    <div class="workspaceTabs" role="tablist" aria-label="Room communication">
      <button
        type="button"
        class="workspaceTab"
        :class="{ active: activeTab === 'chat' }"
        role="tab"
        :aria-selected="activeTab === 'chat'"
        @click="activeTab = 'chat'"
      >{{ t("room.workspace.chatTab") }}</button>
      <button
        type="button"
        class="workspaceTab"
        :class="{ active: activeTab === 'adventureLog' }"
        role="tab"
        :aria-selected="activeTab === 'adventureLog'"
        @click="activeTab = 'adventureLog'"
      >{{ t("room.workspace.adventureLogTab") }}</button>
      <button
        type="button"
        class="workspaceTab"
        :class="{ active: activeTab === 'dice' }"
        role="tab"
        :aria-selected="activeTab === 'dice'"
        @click="activeTab = 'dice'"
      >{{ t("room.workspace.diceLogTab") }}</button>
    </div>

    <ChatPanel
      v-show="activeTab === 'chat'"
      class="chatPanelFill chatPanelWithDivider"
      :room-key="roomKey"
      :active="active && activeTab === 'chat'"
      :messages="messages"
      :send-label="sendLabel"
      :loading="loading"
      :sending="sending"
      :loading-history="loadingHistory"
      :has-older="hasOlder"
      :error="error"
      :loading-label="loadingLabel"
      :empty-label="emptyLabel"
      :send-message="sendMessage"
      :member-status-by-user-id="memberStatusByUserId"
      @send="emit('send', $event)"
      @load-older="emit('loadOlder')"
    />
    <div
      v-show="activeTab === 'adventureLog'"
      class="adventureLogPane"
      role="tabpanel"
      :aria-label="t('room.workspace.adventureLogTab')"
    >
      <span class="adventureLogPlaceholder">{{ t("common.comingSoon") }}</span>
    </div>
    <DiceRollPanel
      v-show="activeTab === 'dice'"
      :room-id="roomKey"
      :active="active && activeTab === 'dice'"
      :game-role="gameRole"
      :current-user-id="currentUserId"
      :character-owner-by-id="characterOwnerById"
    />
  </div>
</template>

<style scoped>
.panelBody {
  display: grid;
  gap: 14px;
  min-height: 0;
  overflow: auto;
}

.chatPanelBody {
  grid-template-rows: auto minmax(0, 1fr);
  padding: 0 14px 14px;
  overflow: hidden;
}

.workspaceTabs {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-width: 0;
  padding: 2px;
  border: 1px solid color-mix(in srgb, var(--c-border) 82%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-bg-subtle) 72%, transparent);
}

.workspaceTab {
  min-width: 64px;
  height: 26px;
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.workspaceTab.active {
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
  color: var(--c-text);
}

:deep(.chatPanelFill) {
  height: 100%;
  min-height: 0;
}

:deep(.chatPanelWithDivider) {
  border-top: 0;
  padding-top: 0;
}

:deep(.chatPanelWithDivider .timeline) {
  border-top: 1px solid color-mix(in srgb, var(--c-border) 78%, transparent);
  padding-top: 0;
}

.adventureLogPane {
  min-height: 0;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--c-border) 76%, transparent);
  border-radius: 10px;
  background: color-mix(in srgb, var(--c-surface) 82%, var(--c-bg));
}

.adventureLogPlaceholder {
  color: var(--c-text-muted);
  font-size: 13px;
}

@media (max-width: 720px) {
  .chatPanelBody {
    min-height: 0;
    height: 100%;
  }

  :deep(.chatPanelFill) {
    min-height: 100%;
  }
}
</style>
