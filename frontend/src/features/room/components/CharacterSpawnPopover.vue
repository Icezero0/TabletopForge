<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { SpawnPopoverEntry } from "@/infra/api/roomCharacters.api";
import CharacterSpawnPopoverItem from "@/features/room/components/CharacterSpawnPopoverItem.vue";
import { canSpawnCharacter, formatTokenPreview } from "@/features/table/utils/tokenDisplay";
import { PlusIcon } from "@heroicons/vue/24/outline";

const props = defineProps<{
  open: boolean;
  anchorEl: HTMLElement | null;
  entries: SpawnPopoverEntry[];
  loading?: boolean;
  ownerNameByUserId?: Map<number, string>;
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
}>();

const emit = defineEmits<{
  close: [];
  spawn: [characterId: number];
  addCharacter: [];
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

function canSpawn(entry: SpawnPopoverEntry): boolean {
  return canSpawnCharacter(entry, props.gameRole, props.currentUserId);
}

function onSpawn(entry: SpawnPopoverEntry) {
  emit("spawn", entry.character_id);
  emit("close");
}

function onAddCharacter() {
  emit("addCharacter");
}

function entryStats(entry: SpawnPopoverEntry): string {
  if (!entry.inRoom) return "";
  return formatTokenPreview(entry.state, {
    damageLabel: t("room.characters.cumulativeDamage"),
  });
}

function ownerLabel(entry: SpawnPopoverEntry): string {
  const name = props.ownerNameByUserId?.get(entry.owner_id);
  return name ?? `User #${entry.owner_id}`;
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

const visibleEntries = computed(() =>
  props.entries.filter((entry) =>
    canSpawnCharacter(entry, props.gameRole, props.currentUserId),
  ),
);
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
      <p v-if="loading" class="muted">{{ t("common.loading") }}</p>
      <div v-else class="track">
        <CharacterSpawnPopoverItem
          v-for="entry in visibleEntries"
          :key="entry.character_id"
          :entry="entry"
          :can-spawn="canSpawn(entry)"
          :stats-text="entryStats(entry)"
          :owner-label="gameRole === 'GM' ? ownerLabel(entry) : undefined"
          @spawn="onSpawn(entry)"
        />
        <button type="button" class="addCard" @click="onAddCharacter">
          <PlusIcon class="addIcon" aria-hidden="true" />
          <span>{{ t("table.assets.spawnPopoverAdd") }}</span>
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
  margin: 0;
  padding: 8px 12px;
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
  flex: 0 0 132px;
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
