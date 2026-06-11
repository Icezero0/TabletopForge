<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import {
  ChevronDownIcon,
  ChevronUpIcon,
} from "@heroicons/vue/24/outline";
import type { FloatingAnchor, FloatingCollapseTo } from "@/features/table/types";

const props = withDefaults(
  defineProps<{
    title: string;
    anchor?: FloatingAnchor;
    collapseTo: FloatingCollapseTo;
    storageKey?: string;
    defaultCollapsed?: boolean;
    inline?: boolean;
    variant?: "governance" | "chat" | "tools" | "assets" | "combat" | "info" | "memo" | "character_list";
  }>(),
  {
    anchor: "top-left",
    defaultCollapsed: false,
    inline: false,
  },
);

const collapsed = defineModel<boolean>("collapsed", { default: false });

const collapseIcon = computed(() => {
  const collapseTarget =
    props.collapseTo === "right" && props.variant === "memo"
      ? "bottom-left"
      : props.collapseTo === "right"
        ? "top-left"
        : props.collapseTo;

  if (collapsed.value) {
    if (collapseTarget === "top" || collapseTarget === "top-left") return ChevronDownIcon;
    if (collapseTarget === "bottom" || collapseTarget === "bottom-left") return ChevronUpIcon;
    return ChevronDownIcon;
  }

  if (collapseTarget === "top" || collapseTarget === "top-left") return ChevronUpIcon;
  if (collapseTarget === "bottom" || collapseTarget === "bottom-left") return ChevronDownIcon;
  return ChevronUpIcon;
});

function persistKey() {
  return props.storageKey ? `tabletop:panel:${props.storageKey}` : null;
}

function loadCollapsed() {
  const key = persistKey();
  if (!key || typeof localStorage === "undefined") return;
  const raw = localStorage.getItem(key);
  if (raw === "1") collapsed.value = true;
  else if (raw === "0") collapsed.value = false;
}

function saveCollapsed() {
  const key = persistKey();
  if (!key || typeof localStorage === "undefined") return;
  localStorage.setItem(key, collapsed.value ? "1" : "0");
}

function toggle() {
  collapsed.value = !collapsed.value;
  saveCollapsed();
}

onMounted(loadCollapsed);

watch(
  () => props.storageKey,
  () => loadCollapsed(),
);
</script>

<template>
  <div
    class="floatingPanel"
    :class="[
      anchor,
      collapseTo,
      variant,
      { collapsed, inline },
    ]"
  >
    <button
      type="button"
      class="panelHeader"
      :aria-expanded="!collapsed"
      @click="toggle"
    >
      <span class="panelTitle">{{ title }}</span>
      <component :is="collapseIcon" class="chevron" aria-hidden="true" />
    </button>

    <div v-show="!collapsed" class="panelBody">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.floatingPanel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--c-border) 72%, transparent);
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
  box-shadow: 0 10px 28px rgb(15 23 42 / 0.12);
  overflow: hidden;
  pointer-events: auto;
  z-index: 2;
}

.floatingPanel.tools {
  overflow: visible;
}

.floatingPanel.collapsed {
  grid-template-rows: auto;
}

.floatingPanel:not(.inline).top-left {
  position: absolute;
  top: 12px;
  left: 12px;
  width: min(320px, calc(100vw - 24px));
  max-height: min(70vh, 520px);
}

.floatingPanel:not(.inline).bottom-left {
  position: absolute;
  bottom: 12px;
  left: 12px;
  width: min(360px, calc(100vw - 24px));
  height: min(48vh, 420px);
}

.floatingPanel:not(.inline).top-center {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: max-content;
  max-width: calc(100vw - 24px);
}

.floatingPanel:not(.inline).bottom-center {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: max-content;
  max-width: calc(100vw - 24px);
}

.floatingPanel:not(.inline).bottom-center.combat {
  width: max-content;
  min-width: 0;
  max-width: calc(100vw - 24px);
}

.floatingPanel.inline {
  position: relative;
  width: min(300px, calc(100vw - 48px));
  max-height: min(40vh, 280px);
}

.floatingPanel.inline.collapsed {
  width: max-content;
  min-width: 0;
  max-height: none;
}

.floatingPanel.collapsed:not(.inline).bottom-left,
.floatingPanel.collapsed:not(.inline).top-left {
  width: auto;
  min-width: 120px;
  max-width: min(320px, calc(100vw - 24px));
  height: auto;
  max-height: none;
}

.floatingPanel.collapsed:not(.inline).bottom-left,
.floatingPanel.collapsed:not(.inline).top-center,
.floatingPanel.collapsed:not(.inline).bottom-center {
  height: auto;
}

.floatingPanel.collapsed:not(.inline).bottom-center.combat {
  width: auto;
  min-width: 96px;
}

.panelHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  border-radius: 13px 13px 0 0;
}

.floatingPanel.collapsed > .panelHeader {
  border-radius: 13px;
}

.panelTitle {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--c-text-muted);
}

.panelBody {
  min-height: 0;
  overflow: auto;
  border-radius: 0 0 13px 13px;
}

.floatingPanel.governance .panelBody {
  display: flex;
  flex-direction: column;
  min-height: 200px;
  max-height: min(62vh, 480px);
}

.floatingPanel.chat .panelBody {
  display: grid;
  grid-template-rows: minmax(0, 1fr);
  overflow: hidden;
}

.floatingPanel.tools .panelBody {
  padding: 0 4px 4px;
  overflow: visible;
}

.floatingPanel.assets .panelBody {
  padding: 0 6px 6px;
}

.floatingPanel.combat .panelBody {
  padding: 0 6px 6px;
}

.floatingPanel.info .panelBody,
.floatingPanel.memo .panelBody {
  padding: 0 12px 12px;
}

@media (max-width: 720px) {
  .floatingPanel:not(.inline).top-left,
  .floatingPanel:not(.inline).bottom-left {
    width: calc(100vw - 24px);
  }
}
</style>
