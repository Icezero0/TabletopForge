<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import BaseButton from "@/ui/base/BaseButton.vue";
import MapSpawnPopover from "@/features/table/components/MapSpawnPopover.vue";
import SceneSpawnPopover from "@/features/table/components/SceneSpawnPopover.vue";
import TokenSpawnPopover from "@/features/table/components/TokenSpawnPopover.vue";
import type { RoomMap, RoomScene } from "@/infra/api/rooms.api";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";

const props = defineProps<{
  canAddMap?: boolean;
  maps?: RoomMap[];
  selectedMapId?: number | null;
  canManageScenes?: boolean;
  scenes?: RoomScene[];
  selectedSceneId?: number | null;
  sceneSaving?: boolean;
  canAddToken?: boolean;
  characters?: RoomCharacterEntry[];
}>();

const mapPopoverOpen = defineModel<boolean>("mapPopoverOpen", { default: false });
const scenePopoverOpen = defineModel<boolean>("scenePopoverOpen", { default: false });
const tokenPopoverOpen = defineModel<boolean>("tokenPopoverOpen", { default: false });

const emit = defineEmits<{
  addMap: [];
  selectMap: [mapId: number];
  openLibraryPicker: [];
  selectScene: [sceneId: number];
  addScene: [];
  editScene: [scene: RoomScene];
  deleteScene: [sceneId: number];
  spawnToken: [characterId: number, tokenConfigId: number];
  spawnAll: [characterId: number];
  addCharacter: [];
}>();

const { t } = useI18n();
const mapAnchorRef = ref<HTMLElement | null>(null);
const sceneAnchorRef = ref<HTMLElement | null>(null);
const tokenAnchorRef = ref<HTMLElement | null>(null);
const visibleActionCount = computed(() =>
  Number(!!props.canManageScenes) +
  Number(!!props.canAddMap) +
  Number(!!props.canAddToken),
);

function toggleMapPopover(event: MouseEvent) {
  event.stopPropagation();
  scenePopoverOpen.value = false;
  tokenPopoverOpen.value = false;
  mapPopoverOpen.value = !mapPopoverOpen.value;
}

function closeMapPopover() {
  mapPopoverOpen.value = false;
}

function toggleScenePopover(event: MouseEvent) {
  event.stopPropagation();
  mapPopoverOpen.value = false;
  tokenPopoverOpen.value = false;
  scenePopoverOpen.value = !scenePopoverOpen.value;
}

function closeScenePopover() {
  scenePopoverOpen.value = false;
}

function toggleTokenPopover(event: MouseEvent) {
  event.stopPropagation();
  mapPopoverOpen.value = false;
  scenePopoverOpen.value = false;
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
  <div class="bottomAssetBar" :class="{ single: visibleActionCount <= 1, multiple: visibleActionCount > 1 }">
    <div v-if="canManageScenes" ref="sceneAnchorRef" class="anchor">
      <BaseButton variant="default" @click="toggleScenePopover">
        切换场景
      </BaseButton>
      <SceneSpawnPopover
        :open="scenePopoverOpen"
        :anchor-el="sceneAnchorRef"
        :scenes="scenes ?? []"
        :selected-scene-id="selectedSceneId"
        :saving="sceneSaving"
        @close="closeScenePopover"
        @select-scene="(sceneId) => emit('selectScene', sceneId)"
        @add-scene="emit('addScene')"
        @edit-scene="(scene) => emit('editScene', scene)"
        @delete-scene="(sceneId) => emit('deleteScene', sceneId)"
      />
    </div>

    <div v-if="canAddMap" ref="mapAnchorRef" class="anchor">
      <BaseButton variant="default" @click="toggleMapPopover">
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
  display: grid;
  grid-template-columns: repeat(var(--asset-action-count, 1), minmax(0, 1fr));
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 4px 8px;
  min-width: max-content;
}

.bottomAssetBar.multiple {
  --asset-action-count: v-bind(visibleActionCount);
  width: 100%;
}

.bottomAssetBar.single {
  grid-template-columns: max-content;
}

.anchor {
  position: relative;
  min-width: 0;
}

.anchor :deep(.btn) {
  width: 100%;
}
</style>
