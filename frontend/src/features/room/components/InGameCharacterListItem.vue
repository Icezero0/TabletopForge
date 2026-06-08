<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, toRef } from "vue";
import { useI18n } from "vue-i18n";
import { EyeIcon, EyeSlashIcon, TrashIcon } from "@heroicons/vue/24/outline";
import type { GameRole } from "@/features/room/types";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import { tokenInitial } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  entry: RoomCharacterEntry;
  ownerLabel: string;
  gameRole?: GameRole | "unknown";
  currentUserId?: number;
  selected?: boolean;
}>();

const emit = defineEmits<{
  inspect: [payload: { characterId: number }];
  toggleVisibility: [payload: { roomCharacterId: number; isHidden: boolean }];
  remove: [roomCharacterId: number];
}>();

const { t } = useI18n();

const assetId = toRef(() => props.entry.token_image_asset_id ?? null);
const { url: tokenUrl } = useAuthenticatedAssetUrl(assetId);

const isGm = computed(() => props.gameRole === "GM");
const canRemove = computed(
  () => isGm.value || props.entry.owner_id === props.currentUserId,
);

const ownerDisplay = computed(() => {
  return props.entry.player_name?.trim() || props.ownerLabel;
});

const CLOSE_ALL_EVENT = "character-list-item:close-menu";

const menuOpen = ref(false);
const menuX = ref(0);
const menuY = ref(0);

function openMenu(event: MouseEvent) {
  event.preventDefault();
  event.stopPropagation();
  window.dispatchEvent(new CustomEvent(CLOSE_ALL_EVENT));
  menuX.value = event.clientX;
  menuY.value = event.clientY;
  menuOpen.value = true;
  window.addEventListener("click", closeMenu, { once: true });
}

function closeMenu() {
  menuOpen.value = false;
}

onMounted(() => {
  window.addEventListener(CLOSE_ALL_EVENT, closeMenu);
});

onUnmounted(() => {
  window.removeEventListener(CLOSE_ALL_EVENT, closeMenu);
  window.removeEventListener("click", closeMenu);
});

function onClickRow() {
  emit("inspect", { characterId: props.entry.character_id });
}

function onToggleVisibility(event: MouseEvent) {
  event.stopPropagation();
  emit("toggleVisibility", {
    roomCharacterId: props.entry.room_character_id,
    isHidden: !props.entry.is_hidden,
  });
}

function onRemove() {
  closeMenu();
  emit("remove", props.entry.room_character_id);
}
</script>

<template>
  <li
    class="row"
    :class="{ hidden: entry.is_hidden, selected }"
    @click="onClickRow"
    @contextmenu="openMenu"
  >
    <div class="thumb">
      <img v-if="tokenUrl" :src="tokenUrl" class="thumbImg" :alt="entry.name" />
      <span v-else class="thumbInitial">{{ tokenInitial(entry.name) }}</span>
    </div>
    <div class="meta">
      <div class="nameRow">
        <span class="name">{{ entry.name }}</span>
        <span class="owner">{{ ownerDisplay }}</span>
        <span v-if="entry.is_hidden" class="hiddenBadge">{{ t("table.characterList.hidden") }}</span>
      </div>
    </div>
    <button
      v-if="isGm"
      class="visBtn"
      :title="entry.is_hidden ? t('table.characterList.showCharacter') : t('table.characterList.hideCharacter')"
      @click="onToggleVisibility"
    >
      <EyeSlashIcon v-if="entry.is_hidden" class="visBtnIcon" />
      <EyeIcon v-else class="visBtnIcon" />
    </button>
  </li>

  <Teleport to="body">
    <div
      v-if="menuOpen"
      class="ctxMenu"
      :style="{ left: `${menuX}px`, top: `${menuY}px` }"
      @click.stop
    >
      <button v-if="canRemove" class="ctxItem danger" @click="onRemove">
        <TrashIcon class="ctxIcon" />
        {{ t("table.characterList.remove") }}
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  cursor: pointer;
}

.row:hover {
  border-color: color-mix(in srgb, var(--c-accent) 40%, var(--c-border));
}

.row.hidden {
  opacity: 0.55;
  border-style: dashed;
}

.row.selected {
  border-color: var(--c-accent);
  background: color-mix(in srgb, var(--c-accent) 8%, var(--c-bg-subtle));
}

.thumb {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  border: 1px solid var(--c-border);
}

.thumbImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbInitial {
  font-size: 13px;
  font-weight: 700;
}

.meta {
  flex: 1;
  min-width: 0;
}

.nameRow {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.name {
  font-size: 14px;
  font-weight: 600;
}

.hiddenBadge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-warn, #f59e0b) 20%, transparent);
  color: var(--c-warn, #f59e0b);
}

.owner {
  font-size: 11px;
  color: var(--c-text-muted);
}

.visBtn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.visBtn:hover {
  border-color: var(--c-border);
  background: var(--c-bg);
}

.visBtnIcon {
  width: 16px;
  height: 16px;
  color: var(--c-text-muted);
}

.ctxMenu {
  position: fixed;
  z-index: 900;
  min-width: 140px;
  padding: 4px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  box-shadow: 0 6px 20px color-mix(in srgb, #000 20%, transparent);
}

.ctxItem {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font: inherit;
  font-size: 13px;
  color: var(--c-text);
  cursor: pointer;
  text-align: left;
}

.ctxItem:hover {
  background: var(--c-bg-subtle);
}

.ctxItem.danger {
  color: var(--c-danger, #ef4444);
}

.ctxIcon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
</style>
