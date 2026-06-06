<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from "vue";

const props = defineProps<{
  bounds: { x: number; y: number; width: number; height: number };
  fontSize: number;
  initialText?: string;
  isEdit?: boolean;
  textColor?: string;
}>();

const emit = defineEmits<{
  confirm: [payload: { text: string; width: number; height: number }];
  cancel: [];
  resize: [width: number];
}>();

const inputRef = ref<HTMLTextAreaElement | null>(null);
const localWidth = ref(props.bounds.width);
const localHeight = ref(props.bounds.height);

function applyInitialText() {
  const el = inputRef.value;
  if (!el) return;
  el.value = props.initialText ?? "";
  measureSize();
}

watch(
  () => props.bounds,
  (b, prev) => {
    localWidth.value = b.width;
    localHeight.value = b.height;
    const moved = prev == null || b.x !== prev.x || b.y !== prev.y;
    if (!moved) return;
    void nextTick(() => {
      inputRef.value?.focus();
      applyInitialText();
    });
  },
  { immediate: true },
);

watch(
  () => props.initialText,
  () => {
    void nextTick(applyInitialText);
  },
);

onMounted(() => {
  if (inputRef.value) applyInitialText();
});

function measureSize() {
  const el = inputRef.value;
  if (!el) return;
  el.style.width = "0px";
  const w = Math.max(10, el.scrollWidth + 4);
  localWidth.value = w;
  el.style.width = `${w}px`;
  el.style.height = "0px";
  const h = Math.max(props.bounds.height, el.scrollHeight + 4);
  localHeight.value = h;
  el.style.height = `${h}px`;
  if (w !== props.bounds.width) {
    emit("resize", w);
  }
}

function submit() {
  measureSize();
  const text = inputRef.value?.value ?? "";
  if (!text.trim()) {
    emit("cancel");
    return;
  }
  emit("confirm", { text, width: localWidth.value, height: localHeight.value });
}

function cancel() {
  emit("cancel");
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    event.preventDefault();
    cancel();
    return;
  }
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submit();
  }
}
</script>

<template>
  <div
    class="textBoxEditor"
    :style="{
      transform: `translate(${bounds.x}px, ${bounds.y}px)`,
      width: `${localWidth}px`,
      height: `${localHeight}px`,
    }"
    @pointerdown.stop
  >
    <textarea
      ref="inputRef"
      class="input"
      rows="1"
      :style="{
        fontSize: `${fontSize}px`,
        lineHeight: 1.35,
        color: textColor ?? 'var(--c-text)',
      }"
      @input="measureSize"
      @keydown="onKeydown"
      @blur="submit"
    />
  </div>
</template>

<style scoped>
.textBoxEditor {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  z-index: 230;
  box-sizing: border-box;
  border: 2px dashed color-mix(in srgb, var(--c-primary) 70%, transparent);
  border-radius: 2px;
  background: color-mix(in srgb, var(--c-surface) 90%, transparent);
  pointer-events: auto;
  overflow: visible;
}

.input {
  display: block;
  min-width: 8px;
  height: 100%;
  box-sizing: border-box;
  resize: none;
  border: none;
  outline: none;
  padding: 2px 4px;
  margin: 0;
  background: transparent;
  font: inherit;
  line-height: 1.35;
  overflow: hidden;
  white-space: pre;
  field-sizing: content;
}
</style>
