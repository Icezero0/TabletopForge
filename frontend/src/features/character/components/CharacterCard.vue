<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import { useI18n } from "vue-i18n";
import { TrashIcon, UserCircleIcon } from "@heroicons/vue/24/outline";
import type { Character } from "@/infra/api/character.api";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import BaseIconButton from "@/ui/base/BaseIconButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{ character: Character }>();
const emit = defineEmits<{
  (e: "click", character: Character): void;
  (e: "delete", character: Character): void;
}>();

const { t } = useI18n();
const hovered = ref(false);

const portraitId = toRef(() => props.character.portrait_asset_id);
const { url: portraitUrl } = useAuthenticatedAssetUrl(portraitId);

const classSummary = computed(() => {
  const classes = (props.character.identity?.classes as { name: string; level: number }[]) ?? [];
  return classes.map((c) => {
    const label = t(`character.classes.${c.name}`, c.name);
    return `${label} ${c.level}`;
  }).join(" / ");
});

const raceName = computed(() => (props.character.identity?.race as string) ?? "");
</script>

<template>
  <div
    class="card"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    @click="emit('click', character)"
  >
    <div class="portrait">
      <img v-if="portraitUrl" :src="portraitUrl" class="portrait-img" :alt="character.name" />
      <div v-else class="portrait-placeholder">
        <AppIcon :icon="UserCircleIcon" :size="40" />
      </div>
    </div>

    <div class="body">
      <div class="name" :title="character.name">{{ character.name }}</div>
      <div class="player">{{ character.player_name }}</div>
      <div v-if="raceName || classSummary" class="meta">
        <span v-if="raceName">{{ raceName }}</span>
        <span v-if="raceName && classSummary" class="sep">·</span>
        <span v-if="classSummary">{{ classSummary }}</span>
      </div>
    </div>

    <Transition name="fade">
      <div v-if="hovered" class="overlay-actions" @click.stop>
        <BaseIconButton :aria-label="t('common.delete')" @click="emit('delete', character)">
          <AppIcon :icon="TrashIcon" :size="16" />
        </BaseIconButton>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.card {
  position: relative;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card:hover {
  border-color: var(--c-border-hover, var(--c-border));
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.portrait {
  width: 100%;
  aspect-ratio: 1;
  background: var(--c-surface-raised);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.portrait-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.portrait-placeholder {
  color: var(--c-text-muted);
  opacity: 0.4;
}

.body {
  padding: 10px 12px 12px;
  display: grid;
  gap: 3px;
}

.name {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.player {
  font-size: 12px;
  color: var(--c-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta {
  font-size: 11px;
  color: var(--c-text-muted);
  display: flex;
  gap: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sep { opacity: 0.5; }

.overlay-actions {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  gap: 4px;
  background: rgba(0,0,0,0.5);
  border-radius: var(--r-1);
  padding: 2px;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.12s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
