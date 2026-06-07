<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import { useI18n } from "vue-i18n";
import { MagnifyingGlassPlusIcon, PencilIcon, TrashIcon } from "@heroicons/vue/24/outline";
import type { LibraryResource } from "@/infra/api/library.api";
import { getResourceTypeMeta } from "@/features/library/constants";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import ResourceCardThumbnail from "./ResourceCardThumbnail.vue";
import BaseIconButton from "@/ui/base/BaseIconButton.vue";
import AppIcon from "@/ui/base/AppIcon.vue";

function resourceTags(resource: LibraryResource): string[] {
  const t = resource.meta?.tags;
  return Array.isArray(t) ? t : [];
}

function resourceComment(resource: LibraryResource): string {
  const c = resource.meta?.comment;
  return typeof c === "string" ? c : "";
}

const props = defineProps<{ resource: LibraryResource }>();
const emit = defineEmits<{
  (e: "rename", resource: LibraryResource): void;
  (e: "delete", resource: LibraryResource): void;
}>();

const { t } = useI18n();
const hovered = ref(false);
const showViewer = ref(false);
const typeMeta = computed(() => getResourceTypeMeta(props.resource.type));

const canZoom = computed(
  () => (props.resource.type === "map_background" || props.resource.type === "token") && !!props.resource.primary_asset_id,
);

const assetId = toRef(props.resource, "primary_asset_id");
const { url: imageUrl } = useAuthenticatedAssetUrl(assetId);
</script>

<template>
  <div
    class="card"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
  >
    <ResourceCardThumbnail
      :type="resource.type"
      :asset-id="resource.primary_asset_id"
    />

    <div class="body">
      <div class="name" :title="resource.name">{{ resource.name }}</div>
      <div class="type-row">
        <span class="type">{{ t(typeMeta.labelKey) }}</span>
        <span class="usage-badge" :class="resource.usage_count > 0 ? 'in-use' : 'not-in-use'">
          {{ resource.usage_count > 0 ? t('library.card.inUse') : t('library.card.notInUse') }}
        </span>
      </div>
      <div v-if="resourceTags(resource).length" class="tags">
        <span v-for="tag in resourceTags(resource)" :key="tag" class="tag">{{ tag }}</span>
      </div>
      <div v-if="resourceComment(resource)" class="comment" :title="resourceComment(resource)">
        {{ resourceComment(resource) }}
      </div>
    </div>

    <Transition name="fade">
      <div v-if="hovered" class="overlay-actions">
        <BaseIconButton
          v-if="canZoom && imageUrl"
          :aria-label="t('common.preview')"
          @click.stop="showViewer = true"
        >
          <AppIcon :icon="MagnifyingGlassPlusIcon" :size="16" />
        </BaseIconButton>

        <BaseIconButton
          :aria-label="t('common.rename')"
          @click.stop="emit('rename', resource)"
        >
          <AppIcon :icon="PencilIcon" :size="16" />
        </BaseIconButton>

        <BaseIconButton
          :aria-label="t('common.delete')"
          @click.stop="emit('delete', resource)"
        >
          <AppIcon :icon="TrashIcon" :size="16" />
        </BaseIconButton>
      </div>
    </Transition>

  </div>

  <!-- Fullscreen viewer -->
  <Teleport to="body">
    <Transition name="viewer-fade">
      <div v-if="showViewer" class="viewer-overlay" @click="showViewer = false">
        <img :src="imageUrl" alt="" class="viewer-img" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.card {
  position: relative;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  overflow: hidden;
  background: var(--c-surface);
  cursor: default;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.card:hover {
  border-color: var(--c-border-hover, var(--c-border));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.body {
  padding: 10px 12px 12px;
  display: grid;
  gap: 4px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.tag {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--c-surface-raised);
  border: 1px solid var(--c-border);
  color: var(--c-text-muted);
  white-space: nowrap;
}

.name {
  font-size: 14px;
  font-weight: 500;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.type-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.type {
  font-size: 12px;
  color: var(--c-text-muted);
}

.comment {
  font-size: 12px;
  color: var(--c-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.overlay-actions {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  gap: 4px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: var(--r-1);
  padding: 2px;
}

.usage-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  border-radius: 10px;
  padding: 1px 7px;
  pointer-events: none;
  white-space: nowrap;
  line-height: 1.6;
}
.usage-badge.in-use {
  background: #16a34a;
  color: #fff;
}
.usage-badge.not-in-use {
  background: #9ca3af;
  color: #fff;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.12s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Fullscreen viewer */
.viewer-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgb(0 0 0 / 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.viewer-img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--r-1);
  cursor: default;
}

.viewer-fade-enter-active,
.viewer-fade-leave-active {
  transition: opacity 0.18s ease;
}
.viewer-fade-enter-from,
.viewer-fade-leave-to {
  opacity: 0;
}
</style>
