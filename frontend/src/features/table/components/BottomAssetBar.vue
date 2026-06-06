<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { RoomCharacterEntry } from "@/infra/api/roomCharacters.api";
import BaseButton from "@/ui/base/BaseButton.vue";
import CharacterSpawnPopover from "@/features/room/components/CharacterSpawnPopover.vue";

defineProps<{
  canAddMap?: boolean;
  canAddCharacter?: boolean;
  characters?: RoomCharacterEntry[];
  charactersLoading?: boolean;
  gameRole?: GameRole | "unknown";
  currentUserId?: number | null;
}>();

const popoverOpen = defineModel<boolean>("popoverOpen", { default: false });

const emit = defineEmits<{
  addMap: [];
  addCharacter: [];
  spawn: [characterId: number];
}>();

const { t } = useI18n();
const characterAnchorRef = ref<HTMLElement | null>(null);

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
</script>

<template>
  <div class="bottomAssetBar">
    <BaseButton
      v-if="canAddMap"
      variant="primary"
      @click="emit('addMap')"
    >
      {{ t("table.assets.addMap") }}
    </BaseButton>
    <div v-if="canAddCharacter" ref="characterAnchorRef" class="characterAnchor">
      <BaseButton variant="default" @click="toggleSpawnPopover">
        {{ t("table.assets.addCharacter") }}
      </BaseButton>
      <CharacterSpawnPopover
        :open="popoverOpen"
        :anchor-el="characterAnchorRef"
        :characters="characters ?? []"
        :loading="charactersLoading"
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

.characterAnchor {
  position: relative;
}
</style>
