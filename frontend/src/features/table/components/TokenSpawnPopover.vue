<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { ChevronLeftIcon } from "@heroicons/vue/24/outline";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import CharacterTokenCard from "@/features/table/components/CharacterTokenCard.vue";
import TokenConfigCard from "@/features/table/components/TokenConfigCard.vue";

const props = defineProps<{
  open: boolean;
  anchorEl: HTMLElement | null;
  characters: RoomCharacterEntry[];
}>();

const emit = defineEmits<{
  close: [];
  spawnToken: [characterId: number, tokenConfigId: number];
  spawnAll: [characterId: number];
}>();

const { t } = useI18n();

const selectedCharacter = ref<RoomCharacterEntry | null>(null);
const popoverStyle = ref<Record<string, string>>({});
let ignoreBackdropUntil = 0;

function syncPosition() {
  const el = props.anchorEl;
  if (!el) { popoverStyle.value = { visibility: "hidden" }; return; }
  const rect = el.getBoundingClientRect();
  popoverStyle.value = {
    position: "fixed",
    left: `${rect.left + rect.width / 2}px`,
    top: `${rect.top - 8}px`,
    transform: "translate(-50%, -100%)",
    zIndex: "450",
  };
}

function markOpened() { ignoreBackdropUntil = Date.now() + 200; }

function onBackdropPointerDown() {
  if (Date.now() < ignoreBackdropUntil) return;
  emit("close");
}

function onKeydown(e: KeyboardEvent) {
  if (!props.open) return;
  if (e.key === "Escape") {
    if (selectedCharacter.value) {
      selectedCharacter.value = null;
    } else {
      emit("close");
    }
  }
}

watch(() => props.open, (open) => {
  if (open) {
    markOpened();
    syncPosition();
  } else {
    selectedCharacter.value = null;
  }
});

watch(() => props.anchorEl, () => { if (props.open) syncPosition(); });

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

function selectCharacter(entry: RoomCharacterEntry) {
  selectedCharacter.value = entry;
}

function goBack() {
  selectedCharacter.value = null;
}

function onSpawn(characterId: number, tokenConfigId: number) {
  emit("spawnToken", characterId, tokenConfigId);
  emit("close");
}

function onSpawnAll() {
  if (!selectedCharacter.value) return;
  emit("spawnAll", selectedCharacter.value.character_id);
  emit("close");
}
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
      <!-- Level 1: character list -->
      <template v-if="!selectedCharacter">
        <div class="popoverHeader">
          <span class="popoverTitle">{{ t("table.assets.addToken") }}</span>
        </div>
        <div class="track">
          <p v-if="characters.length === 0" class="muted">
            {{ t("table.assets.tokenPopoverEmpty") }}
          </p>
          <CharacterTokenCard
            v-for="entry in characters"
            :key="entry.character_id"
            :entry="entry"
            @select="selectCharacter(entry)"
          />
        </div>
      </template>

      <!-- Level 2: token configs of selected character -->
      <template v-else>
        <div class="popoverHeader">
          <button type="button" class="backBtn" @click="goBack">
            <ChevronLeftIcon class="backIcon" aria-hidden="true" />
          </button>
          <span class="popoverTitle characterName">{{ selectedCharacter.name }}</span>
          <button
            v-if="selectedCharacter.token_configs.length > 1"
            type="button"
            class="spawnAllBtn"
            @click="onSpawnAll"
          >
            {{ t("table.assets.tokenSpawnAll") }}
          </button>
        </div>
        <div class="track">
          <p v-if="selectedCharacter.token_configs.length === 0" class="muted">
            {{ t("table.assets.tokenConfigEmpty") }}
          </p>
          <TokenConfigCard
            v-for="cfg in selectedCharacter.token_configs"
            :key="cfg.id"
            :config="cfg"
            :character-name="selectedCharacter.name"
            :primary-label="t('table.assets.tokenPrimary')"
            :secondary-label="t('table.assets.tokenSecondary')"
            @spawn="onSpawn(selectedCharacter!.character_id, cfg.id)"
          />
        </div>
      </template>
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
  min-width: 220px;
  max-width: min(90vw, 680px);
  padding: 10px;
  border-radius: 14px;
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  box-shadow: 0 10px 32px color-mix(in srgb, var(--c-bg) 50%, transparent);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.popoverHeader {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 2px 0 2px;
}

.popoverTitle {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-muted);
  flex: 1;
}

.popoverTitle.characterName {
  color: var(--c-text);
}

.backBtn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
}

.backBtn:hover {
  background: var(--c-hover);
  color: var(--c-text);
}

.backIcon {
  width: 16px;
  height: 16px;
}

.spawnAllBtn {
  height: 26px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid var(--c-border);
  background: transparent;
  color: var(--c-text-muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.spawnAllBtn:hover {
  border-color: color-mix(in srgb, var(--c-accent) 45%, var(--c-border));
  background: color-mix(in srgb, var(--c-accent) 6%, transparent);
  color: var(--c-text);
}

.track {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.muted {
  margin: 0;
  padding: 12px 4px;
  font-size: 13px;
  color: var(--c-text-muted);
}
</style>
