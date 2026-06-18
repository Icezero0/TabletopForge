<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import { getRoomById, type Room } from "@/infra/api/rooms.api";
import BaseLayout from "@/ui/layout/BaseLayout.vue";
import Dnd5eRoomMode from "@/pages/room/Dnd5eRoomMode.vue";
import ThunderStoneRoomMode from "@/pages/room/ThunderStoneRoomMode.vue";

const { t } = useI18n();
const route = useRoute();

const room = ref<Room | null>(null);
const isLoading = ref(false);
const error = ref("");

const roomId = computed(() => {
  const raw = route.params.id;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
});

async function loadRoom() {
  if (!roomId.value) {
    room.value = null;
    error.value = t("room.invalidId");
    return;
  }

  isLoading.value = true;
  error.value = "";

  try {
    room.value = await getRoomById(roomId.value);
  } catch {
    room.value = null;
    error.value = t("room.loadFailed");
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  void loadRoom();
});

watch(roomId, () => {
  void loadRoom();
});
</script>

<template>
  <Dnd5eRoomMode v-if="room?.type === 'DND5E'" />
  <ThunderStoneRoomMode v-else-if="room?.type === 'ThunderStone'" :room="room" />

  <div v-else class="roomPageWrap">
    <BaseLayout :max-width="10000">
      <div class="roomShell">
        <div v-if="isLoading" class="state">{{ t("common.loading") }}</div>
        <div v-else-if="error" class="state error">{{ error }}</div>
        <div v-else class="state error">{{ t("room.unsupportedType") }}</div>
      </div>
    </BaseLayout>
  </div>
</template>

<style scoped>
.roomPageWrap {
  width: 100%;
  min-height: 100%;
}

.roomShell {
  position: relative;
  height: calc(100dvh - 68px);
  min-height: 560px;
  overflow: hidden;
}

.state {
  padding: 32px;
  color: var(--c-text-muted);
}

.state.error {
  color: var(--c-danger);
}

@media (max-width: 720px) {
  .roomShell {
    height: calc(100dvh - 52px);
  }
}
</style>
