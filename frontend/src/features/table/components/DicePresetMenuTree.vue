<script setup lang="ts">
import { computed, ref } from "vue";
import { FolderIcon } from "@heroicons/vue/24/outline";
import { Dices } from "lucide-vue-next";
import type { DicePreset } from "@/infra/api/dice.api";

defineOptions({ name: "DicePresetMenuTree" });

const props = withDefaults(
  defineProps<{
    items: DicePreset[];
    parentId?: number | null;
    direction?: "upward" | "downward";
  }>(),
  {
    parentId: null,
    direction: "downward",
  },
);

const emit = defineEmits<{
  select: [preset: DicePreset];
}>();

const openFolderId = ref<number | null>(null);

const children = computed(() =>
  props.items
    .filter((item) => (item.parent_id ?? null) === props.parentId)
    .sort((a, b) => {
      if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order;
      return a.id - b.id;
    }),
);

function hasChildren(folderId: number) {
  return props.items.some((item) => item.parent_id === folderId);
}

function toggleFolder(folderId: number) {
  openFolderId.value = openFolderId.value === folderId ? null : folderId;
}

function selectPreset(preset: DicePreset) {
  emit("select", preset);
}
</script>

<template>
  <template v-for="item in children" :key="item.id">
    <div
      v-if="item.kind === 'folder'"
      class="submenuHost"
      :class="direction"
    >
      <button
        type="button"
        class="menuItem submenuTrigger presetFolderItem"
        :class="{ active: openFolderId === item.id }"
        @click.stop="toggleFolder(item.id)"
      >
        <span class="presetMenuLabel">
          <FolderIcon class="presetMenuIcon" />
          <span class="presetName">{{ item.name }}</span>
        </span>
        <span class="submenuArrow">›</span>
      </button>
      <div
        v-if="openFolderId === item.id"
        class="submenu nestedSubmenu presetSubmenu"
        @click.stop
      >
        <DicePresetMenuTree
          v-if="hasChildren(item.id)"
          :items="items"
          :parent-id="item.id"
          :direction="direction"
          @select="selectPreset"
        />
        <button v-else type="button" class="menuItem" disabled>空分组</button>
      </div>
    </div>
    <button
      v-else
      type="button"
      class="menuItem presetMenuItem"
      @click="selectPreset(item)"
    >
      <span class="presetMenuLabel">
        <Dices class="presetMenuIcon" />
        <span class="presetName">{{ item.name }}</span>
      </span>
      <span class="presetFormula">{{ item.formula }}</span>
    </button>
  </template>
</template>

<style scoped>
.submenuHost {
  position: relative;
}

.menuItem {
  width: 100%;
  min-width: 0;
  max-width: 220px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 13px;
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
}

.menuItem:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 12%, transparent);
}

.menuItem:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.submenuTrigger {
  justify-content: space-between;
  gap: 14px;
}

.submenuTrigger.active {
  background: color-mix(in srgb, var(--c-primary) 14%, transparent);
}

.submenuArrow {
  color: var(--c-text-muted);
  font-size: 16px;
  line-height: 1;
}

.submenu {
  position: absolute;
  top: 0;
  left: calc(100% + 6px);
  width: max-content;
  min-width: 112px;
  max-width: 220px;
  padding: 6px;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  background: var(--c-surface);
  box-shadow: 0 8px 28px color-mix(in srgb, var(--c-bg) 45%, transparent);
}

.submenuHost.upward > .submenu {
  top: auto;
  bottom: 0;
}

.nestedSubmenu {
  top: -6px;
}

.submenuHost.upward > .nestedSubmenu {
  top: auto;
  bottom: -6px;
}

.presetSubmenu {
  width: max-content;
  min-width: 112px;
  max-width: 220px;
  overflow: visible;
  z-index: 20;
}

.presetMenuItem {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 2px;
}

.presetFolderItem {
  min-width: 112px;
  max-width: 220px;
}

.presetMenuLabel {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 180px;
}

.presetMenuIcon {
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
  color: var(--c-text-muted);
}

.presetName,
.presetFormula {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.presetName {
  font-weight: 700;
}

.presetFormula {
  color: var(--c-text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}
</style>
