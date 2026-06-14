<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

type BaseEntitySelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
  [key: string]: unknown;
};

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: BaseEntitySelectOption[];
    disabled?: boolean;
    width?: string | number;
    maxHeight?: number;
  }>(),
  {
    disabled: false,
    width: "144px",
    maxHeight: 220,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  "open-change": [open: boolean];
}>();

const rootRef = ref<HTMLElement | null>(null);
const menuRef = ref<HTMLElement | null>(null);
const open = ref(false);
const menuPlacement = ref<"down" | "up">("up");
const menuMaxHeight = ref<number | null>(null);

const selectedOption = computed(() => {
  return props.options.find((option) => option.value === props.modelValue) ?? props.options[0] ?? null;
});

const rootStyle = computed(() => ({
  width: typeof props.width === "number" ? `${props.width}px` : props.width,
}));

const menuStyle = computed(() => ({
  maxHeight: `${menuMaxHeight.value ?? props.maxHeight}px`,
}));

function getScrollParent(element: HTMLElement | null) {
  let current = element?.parentElement ?? null;
  while (current) {
    const style = window.getComputedStyle(current);
    if (["auto", "scroll", "overlay"].includes(style.overflowY)) return current;
    current = current.parentElement;
  }
  return null;
}

async function updateMenuPlacement() {
  await nextTick();
  const root = rootRef.value;
  const menu = menuRef.value;
  if (!root || !menu) return;

  const rootRect = root.getBoundingClientRect();
  const scrollParent = getScrollParent(root);
  const scrollParentRect = scrollParent?.getBoundingClientRect();
  const viewportTop = Math.max(0, scrollParentRect?.top ?? 0);
  const viewportBottom = Math.min(window.innerHeight, scrollParentRect?.bottom ?? window.innerHeight);
  const gap = 6;
  const availableBelow = Math.max(0, viewportBottom - rootRect.bottom - gap);
  const availableAbove = Math.max(0, rootRect.top - viewportTop - gap);
  const naturalHeight = menu.scrollHeight;
  const shouldOpenUp = availableBelow < naturalHeight && availableAbove > availableBelow;
  const availableHeight = shouldOpenUp ? availableAbove : availableBelow;

  menuPlacement.value = shouldOpenUp ? "up" : "down";
  menuMaxHeight.value = naturalHeight > availableHeight
    ? Math.max(80, availableHeight)
    : null;
}

function close() {
  if (!open.value) return;
  open.value = false;
  menuMaxHeight.value = null;
  emit("open-change", false);
}

function toggle() {
  if (props.disabled) return;
  open.value = !open.value;
  emit("open-change", open.value);
  if (open.value) void updateMenuPlacement();
}

function selectOption(option: BaseEntitySelectOption) {
  if (props.disabled || option.disabled) return;
  emit("update:modelValue", option.value);
  close();
}

function onDocPointerDown(event: PointerEvent) {
  if (!open.value) return;
  const root = rootRef.value;
  const target = event.target as Node | null;
  if (root && target && !root.contains(target)) close();
}

function onKeyDown(event: KeyboardEvent) {
  if (event.key === "Escape") close();
}

function onWindowChange() {
  if (open.value) void updateMenuPlacement();
}

onMounted(() => {
  document.addEventListener("pointerdown", onDocPointerDown);
  document.addEventListener("keydown", onKeyDown);
  window.addEventListener("resize", onWindowChange);
  window.addEventListener("scroll", onWindowChange, true);
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", onDocPointerDown);
  document.removeEventListener("keydown", onKeyDown);
  window.removeEventListener("resize", onWindowChange);
  window.removeEventListener("scroll", onWindowChange, true);
});
</script>

<template>
  <div
    ref="rootRef"
    class="entitySelect"
    :class="{ open, disabled, 'placement-down': menuPlacement === 'down' }"
    :style="rootStyle"
  >
    <button
      type="button"
      class="entitySelectTrigger"
      :disabled="disabled"
      aria-haspopup="listbox"
      :aria-expanded="open"
      @click="toggle"
    >
      <slot name="selected" :option="selectedOption">
        <span class="entitySelectName">{{ selectedOption?.label }}</span>
      </slot>
      <span class="entitySelectArrow" aria-hidden="true"></span>
    </button>

    <Transition name="entity-select-menu">
      <div
        v-show="open"
        ref="menuRef"
        class="entitySelectMenu"
        role="listbox"
        :style="menuStyle"
      >
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          class="entitySelectOption"
          :class="{ selected: option.value === modelValue }"
          role="option"
          :aria-selected="option.value === modelValue"
          :disabled="option.disabled"
          @click="selectOption(option)"
        >
          <slot name="option" :option="option">
            <span class="entitySelectName">{{ option.label }}</span>
          </slot>
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.entitySelect {
  position: relative;
  flex: 0 0 auto;
  min-width: 0;
}

.entitySelectTrigger {
  width: 100%;
  height: 28px;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px 3px 4px;
  border: 1px solid var(--c-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-surface) 92%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.entitySelectTrigger:hover:not(:disabled),
.entitySelect.open .entitySelectTrigger {
  border-color: color-mix(in srgb, var(--c-primary) 32%, var(--c-border));
  background: color-mix(in srgb, var(--c-surface) 86%, var(--c-bg));
}

.entitySelectTrigger:disabled,
.entitySelect.disabled .entitySelectTrigger {
  opacity: 0.6;
  cursor: not-allowed;
}

.entitySelectName {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
  font-weight: 700;
}

.entitySelectArrow {
  width: 7px;
  height: 7px;
  flex: 0 0 auto;
  border-right: 1px solid currentColor;
  border-bottom: 1px solid currentColor;
  transform: translateY(-2px) rotate(45deg);
  color: var(--c-text-muted);
}

.entitySelectMenu {
  position: absolute;
  z-index: 360;
  left: 0;
  right: 0;
  bottom: calc(100% + 6px);
  overflow-y: auto;
  display: grid;
  gap: 3px;
  padding: 5px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.32);
}

.entitySelect.placement-down .entitySelectMenu {
  top: calc(100% + 6px);
  bottom: auto;
}

.entitySelectOption {
  min-width: 0;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 7px 4px 4px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.entitySelectOption:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 24%, transparent);
}

.entitySelectOption.selected {
  background: color-mix(in srgb, var(--c-primary) 16%, var(--c-surface));
  border-color: color-mix(in srgb, var(--c-primary) 34%, var(--c-border));
}

.entitySelectOption:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.entity-select-menu-enter-active,
.entity-select-menu-leave-active {
  transition: opacity 120ms ease, transform 120ms ease;
}

.entity-select-menu-enter-from,
.entity-select-menu-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.entitySelect.placement-down .entity-select-menu-enter-from,
.entitySelect.placement-down .entity-select-menu-leave-to {
  transform: translateY(-6px);
}

.entity-select-menu-enter-to,
.entity-select-menu-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>
