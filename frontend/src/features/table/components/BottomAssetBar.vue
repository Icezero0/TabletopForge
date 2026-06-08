<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import BaseButton from "@/ui/base/BaseButton.vue";
import MapSpawnPopover from "@/features/table/components/MapSpawnPopover.vue";
import TokenSpawnPopover from "@/features/table/components/TokenSpawnPopover.vue";
import type { RoomMap } from "@/infra/api/rooms.api";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";

defineProps<{
  canAddMap?: boolean;
  maps?: RoomMap[];
  selectedMapId?: number | null;
  canAddToken?: boolean;
  characters?: RoomCharacterEntry[];
}>();

const mapPopoverOpen = defineModel<boolean>("mapPopoverOpen", { default: false });
const tokenPopoverOpen = defineModel<boolean>("tokenPopoverOpen", { default: false });

const emit = defineEmits<{
  addMap: [];
  selectMap: [mapId: number];
  openLibraryPicker: [];
  spawnToken: [characterId: number, tokenConfigId: number];
  spawnAll: [characterId: number];
  addCharacter: [];
}>();

const { t } = useI18n();
const mapAnchorRef = ref<HTMLElement | null>(null);
const tokenAnchorRef = ref<HTMLElement | null>(null);

function toggleMapPopover(event: MouseEvent) {
  event.stopPropagation();
  tokenPopoverOpen.value = false;
  mapPopoverOpen.value = !mapPopoverOpen.value;
}

function closeMapPopover() {
  mapPopoverOpen.value = false;
}

function toggleTokenPopover(event: MouseEvent) {
  event.stopPropagation();
  mapPopoverOpen.value = false;
  tokenPopoverOpen.value = !tokenPopoverOpen.value;
}

function closeTokenPopover() {
  tokenPopoverOpen.value = false;
}

function onSelectMap(mapId: number) {
  emit("selectMap", mapId);
}
</script>

<template>
  <div class="bottomAssetBar">
    <div v-if="canAddMap" ref="mapAnchorRef" class="anchor">
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
        @open-library-picker="emit('openLibraryPicker')"
      />
    </div>

    <div v-if="canAddToken" ref="tokenAnchorRef" class="anchor">
      <BaseButton variant="default" @click="toggleTokenPopover">
        {{ t("table.assets.addToken") }}
      </BaseButton>
      <TokenSpawnPopover
        :open="tokenPopoverOpen"
        :anchor-el="tokenAnchorRef"
        :characters="characters ?? []"
        @close="closeTokenPopover"
        @spawn-token="(cid, cfgId) => emit('spawnToken', cid, cfgId)"
        @spawn-all="(cid) => emit('spawnAll', cid)"
        @add-character="emit('addCharacter')"
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

.anchor {
  position: relative;
}
</style>
