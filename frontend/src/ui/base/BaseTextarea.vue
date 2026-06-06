<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    rows?: number;
    minHeight?: string;
    maxHeight?: string;
    disabled?: boolean;
  }>(),
  {},
);

const emit = defineEmits<{ (e: "update:modelValue", v: string): void }>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);

function autoResize() {
  const el = textareaRef.value;
  if (!el) return;
  // Reset to 0 so scrollHeight reflects pure content height
  el.style.height = "0";
  const h = el.scrollHeight;
  el.style.height = h + "px";
  // If max-height CSS is capping the rendered height, enable scroll
  el.style.overflowY = el.scrollHeight > el.clientHeight ? "auto" : "hidden";
}

onMounted(autoResize);
watch(() => props.modelValue, () => nextTick(autoResize));

function handleInput(e: Event) {
  emit("update:modelValue", (e.target as HTMLTextAreaElement).value);
  autoResize();
}
</script>

<template>
  <textarea
    ref="textareaRef"
    class="textarea"
    :rows="rows"
    :placeholder="placeholder"
    :disabled="disabled"
    :value="modelValue"
    @input="handleInput"
  />
</template>

<style scoped>
.textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text);
  font-size: 13px;
  font-family: inherit;
  line-height: 1.6;
  outline: none;
  transition: border-color 0.15s;
  resize: none;
  overflow-y: hidden;
  min-height: v-bind(props.minHeight);
  max-height: v-bind(props.maxHeight);
  scrollbar-width: none;
  display: block;
}
.textarea::-webkit-scrollbar { display: none; }
.textarea:focus { border-color: var(--c-accent, var(--c-primary)); }
.textarea::placeholder { color: var(--c-text-muted); }
.textarea:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
