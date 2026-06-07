<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { RoomMap } from "@/infra/api/rooms.api";
import MapSpawnPopoverItem from "@/features/table/components/MapSpawnPopoverItem.vue";
import { FolderOpenIcon, ArrowUpTrayIcon } from "@heroicons/vue/24/outline";

const props = defineProps<{
  open: boolean;
  anchorEl: HTMLElement | null;
  maps: RoomMap[];
  selectedMapId?: number | null;
}>();

const emit = defineEmits<{
  close: [];
  selectMap: [mapId: number];
  addMap: [];
  openLibraryPicker: [];
}>();

const { t } = useI18n();

const popoverStyle = ref<Record<string, string>>({});
let ignoreBackdropUntil = 0;

function syncPosition() {
  const el = props.anchorEl;
  if (!el) {
    popoverStyle.value = { visibility: "hidden" };
    return;
  }
  const rect = el.getBoundingClientRect();
  popoverStyle.value = {
    position: "fixed",
    left: `${rect.left + rect.width / 2}px`,
    top: `${rect.top - 8}px`,
    transform: "translate(-50%, -100%)",
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

function onSelect(mapId: number) {
  emit("selectMap", mapId);
  emit("close");
}

function onAddMap() {
  emit("addMap");
  emit("close");
}

function onOpenLibraryPicker() {
  emit("openLibraryPicker");
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
      <p v-if="!maps.length" class="muted">{{ t("table.assets.mapsPopoverEmpty") }}</p>
      <div class="track">
        <MapSpawnPopoverItem
          v-for="map in maps"
          :key="map.id"
          :asset-id="map.asset_id"
          :name="t('table.assets.mapLabel', { id: map.id })"
          :selected="selectedMapId === map.id"
          @select="onSelect(map.id)"
        />
        <button type="button" class="addCard" @click="onOpenLibraryPicker">
          <FolderOpenIcon class="addIcon" aria-hidden="true" />
          <span>{{ t("table.assets.mapFromLibrary") }}</span>
        </button>
        <button type="button" class="addCard" @click="onAddMap">
          <ArrowUpTrayIcon class="addIcon" aria-hidden="true" />
          <span>{{ t("table.assets.mapDirectUpload") }}</span>
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
  min-width: 200px;
  max-width: min(90vw, 640px);
  padding: 10px;
  border-radius: 14px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  box-shadow: 0 10px 32px color-mix(in srgb, var(--c-bg) 50%, transparent);
}

.muted {
  margin: 0 0 8px;
  padding: 0 4px;
  font-size: 13px;
  color: var(--c-text-muted);
}

.track {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.addCard {
  flex: 0 0 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: 12px;
  border: 1px dashed var(--c-border);
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
  font-size: 12px;
}

.addCard:hover {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  color: var(--c-text);
  background: color-mix(in srgb, var(--c-accent) 6%, transparent);
}

.addIcon {
  width: 22px;
  height: 22px;
}
</style>
