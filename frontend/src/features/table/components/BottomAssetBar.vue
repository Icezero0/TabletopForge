<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { SpawnPopoverEntry } from "@/infra/api/roomCharacters.api";
import BaseButton from "@/ui/base/BaseButton.vue";
import CharacterSpawnPopover from "@/features/room/components/CharacterSpawnPopover.vue";
import MapSpawnPopover from "@/features/table/components/MapSpawnPopover.vue";
import type { RoomMap } from "@/infra/api/rooms.api";

defineProps<{
  canAddMap?: boolean;
  canAddCharacter?: boolean;
  entries?: SpawnPopoverEntry[];
  entriesLoading?: boolean;
  ownerNameByUserId?: Map<number, string>;
  maps?: RoomMap[];
  selectedMapId?: number | null;
  gameRole?: GameRole | "unknown";
  currentUserId?: number | null;
}>();

const popoverOpen = defineModel<boolean>("popoverOpen", { default: false });
const mapPopoverOpen = defineModel<boolean>("mapPopoverOpen", { default: false });

const emit = defineEmits<{
  addMap: [];
  addCharacter: [];
  spawn: [characterId: number];
  selectMap: [mapId: number];
}>();

const { t } = useI18n();
const characterAnchorRef = ref<HTMLElement | null>(null);
const mapAnchorRef = ref<HTMLElement | null>(null);

function toggleSpawnPopover(event: MouseEvent) {
  event.stopPropagation();
  popoverOpen.value = !popoverOpen.value;
}

function closeSpawnPopover() {
  popoverOpen.value = false;
}

function onAddCharacter() {
  emit("addCharacter");
}

function onSpawn(characterId: number) {
  emit("spawn", characterId);
}

function toggleMapPopover(event: MouseEvent) {
  event.stopPropagation();
  mapPopoverOpen.value = !mapPopoverOpen.value;
}

function closeMapPopover() {
  mapPopoverOpen.value = false;
}

function onSelectMap(mapId: number) {
  emit("selectMap", mapId);
}
</script>

<template>
  <div class="bottomAssetBar">
    <div v-if="canAddMap" ref="mapAnchorRef" class="mapAnchor">
      <BaseButton variant="primary" @click="toggleMapPopover">
        {{ t("table.assets.addMap") }}
      </BaseButton>
      <MapSpawnPopover
        :open="mapPopoverOpen"
        :anchor-el="mapAnchorRef"
        :maps="maps ?? []"
        :selected-map-id="selectedMapId"
        @close="closeMapPopover"
        @select-map="onSelectMap"
        @add-map="emit('addMap')"
      />
    </div>
    <div v-if="canAddCharacter" ref="characterAnchorRef" class="characterAnchor">
      <BaseButton variant="default" @click="toggleSpawnPopover">
        {{ t("table.assets.addCharacter") }}
      </BaseButton>
      <CharacterSpawnPopover
        :open="popoverOpen"
        :anchor-el="characterAnchorRef"
        :entries="entries ?? []"
        :loading="entriesLoading"
        :owner-name-by-user-id="ownerNameByUserId"
        :game-role="gameRole ?? 'unknown'"
        :current-user-id="currentUserId"
        @close="closeSpawnPopover"
        @spawn="onSpawn"
        @add-character="onAddCharacter"
      />
    </div>
  </div>
</template>

<style scoped>
.bottomAssetBar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 4px 8px;
}

.characterAnchor,
.mapAnchor {
  position: relative;
}
</style>
