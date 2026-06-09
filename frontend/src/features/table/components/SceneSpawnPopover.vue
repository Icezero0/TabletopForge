<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { PencilSquareIcon, PlusIcon, TrashIcon } from "@heroicons/vue/24/outline";
import type { RoomScene } from "@/infra/api/rooms.api";

const props = defineProps<{
  open: boolean;
  anchorEl: HTMLElement | null;
  scenes: RoomScene[];
  selectedSceneId?: number | null;
  saving?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  selectScene: [sceneId: number];
  addScene: [];
  editScene: [scene: RoomScene];
  deleteScene: [sceneId: number];
}>();

const popoverStyle = ref<Record<string, string>>({});
let ignoreBackdropUntil = 0;

function syncPosition() {
  const el = props.anchorEl;
  if (!el) {
    popoverStyle.value = { visibility: "hidden" };
    return;
  }
  const rect = el.getBoundingClientRect();
  const margin = 12;
  const left = Math.max(margin, Math.min(rect.left, window.innerWidth - margin));
  const top = Math.min(rect.bottom + 8, window.innerHeight - margin);
  popoverStyle.value = {
    position: "fixed",
    left: `${left}px`,
    top: `${top}px`,
    maxWidth: `${Math.max(120, window.innerWidth - left - margin)}px`,
    maxHeight: `${Math.max(160, window.innerHeight - top - margin)}px`,
    zIndex: "450",
  };
}

function markOpened() {
  ignoreBackdropUntil = Date.now() + 200;
}

function onBackdropPointerDown() {
  if (Date.now() < ignoreBackdropUntil) return;
  emit("close");
}

function onSelect(sceneId: number) {
  emit("selectScene", sceneId);
  emit("close");
}

function onAddScene() {
  emit("addScene");
  emit("close");
}

function onEditScene(scene: RoomScene) {
  emit("editScene", scene);
  emit("close");
}

function onDeleteScene(sceneId: number) {
  emit("deleteScene", sceneId);
  emit("close");
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && props.open) emit("close");
}

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    markOpened();
    syncPosition();
  },
);

watch(
  () => props.anchorEl,
  () => {
    if (props.open) syncPosition();
  },
);

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  window.addEventListener("resize", syncPosition);
  window.addEventListener("scroll", syncPosition, true);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  window.removeEventListener("resize", syncPosition);
  window.removeEventListener("scroll", syncPosition, true);
});

const showPopover = computed(() => props.open && props.anchorEl != null);
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="backdrop" @mousedown="onBackdropPointerDown" />
    <div
      v-show="showPopover"
      class="popover"
      role="menu"
      :style="popoverStyle"
      @mousedown.stop
      @click.stop
    >
      <div class="track">
        <div
          v-for="scene in scenes"
          :key="scene.id"
          class="sceneCard"
          :class="{ active: selectedSceneId === scene.id }"
        >
          <button
            type="button"
            class="sceneMain"
            :disabled="saving || selectedSceneId === scene.id"
            @click="onSelect(scene.id)"
          >
            <span class="sceneName">{{ scene.name }}</span>
            <span v-if="selectedSceneId === scene.id" class="sceneBadge">当前</span>
          </button>
          <span class="sceneActions">
            <button
              type="button"
              class="sceneIconButton"
              :disabled="saving"
              aria-label="编辑场景"
              @click.stop="onEditScene(scene)"
            >
              <PencilSquareIcon class="sceneIcon" aria-hidden="true" />
            </button>
            <button
              type="button"
              class="sceneIconButton danger"
              :disabled="saving || scenes.length <= 1"
              aria-label="删除场景"
              @click.stop="onDeleteScene(scene.id)"
            >
              <TrashIcon class="sceneIcon" aria-hidden="true" />
            </button>
          </span>
        </div>
        <button type="button" class="addCard" :disabled="saving" @click="onAddScene">
          <PlusIcon class="addIcon" aria-hidden="true" />
          <span>添加场景</span>
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 440;
}

.popover {
  max-width: min(90vw, 640px);
  padding: 10px;
  border-radius: 14px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  box-shadow: 0 10px 32px color-mix(in srgb, var(--c-bg) 50%, transparent);
}

.track {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.sceneCard,
.addCard {
  flex: 0 0 112px;
  min-height: 84px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: 12px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 84%, transparent);
  color: var(--c-text);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
}

.sceneCard {
  cursor: default;
}

.sceneMain {
  width: 100%;
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.sceneMain:disabled {
  cursor: default;
}

.sceneCard:hover,
.addCard:hover:not(:disabled) {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-accent) 6%, transparent);
}

.addCard:disabled {
  cursor: default;
  opacity: 0.68;
}

.sceneCard.active {
  border-color: color-mix(in srgb, var(--c-primary) 70%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 18%, var(--c-surface));
}

.sceneName {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
  font-weight: 700;
}

.sceneBadge {
  color: var(--c-primary);
  font-size: 11px;
}

.sceneActions {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.sceneIconButton {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 70%, transparent);
  color: var(--c-text-muted);
  cursor: pointer;
}

.sceneIconButton:hover:not(:disabled) {
  color: var(--c-text);
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
}

.sceneIconButton.danger:hover:not(:disabled) {
  color: var(--c-danger, #ff7a7a);
}

.sceneIconButton:disabled {
  cursor: default;
  opacity: 0.45;
}

.sceneIcon {
  width: 17px;
  height: 17px;
}

.addCard {
  border-style: dashed;
  background: transparent;
  color: var(--c-text-muted);
}

.addIcon {
  width: 22px;
  height: 22px;
}
</style>
