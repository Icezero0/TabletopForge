<script setup lang="ts">
import { ref } from "vue";
import { XMarkIcon } from "@heroicons/vue/24/outline";
import AppIcon from "@/ui/base/AppIcon.vue";

const props = defineProps<{
  modelValue: string[];
  placeholder?: string;
}>();

const emit = defineEmits<{ (e: "update:modelValue", v: string[]): void }>();

const input = ref("");

function commit() {
  const val = input.value.trim().replace(/,+$/, "");
  if (val && !props.modelValue.includes(val)) {
    emit("update:modelValue", [...props.modelValue, val]);
  }
  input.value = "";
}

function remove(tag: string) {
  emit("update:modelValue", props.modelValue.filter((t) => t !== tag));
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" || e.key === ",") {
    e.preventDefault();
    commit();
  } else if (e.key === "Backspace" && !input.value && props.modelValue.length) {
    emit("update:modelValue", props.modelValue.slice(0, -1));
  }
}
</script>

<template>
  <div class="tag-input">
    <span v-for="tag in modelValue" :key="tag" class="tag">
      {{ tag }}
      <button type="button" class="remove" @click="remove(tag)">
        <AppIcon :icon="XMarkIcon" :size="12" />
      </button>
    </span>
    <input
      v-model="input"
      class="inp"
      :placeholder="modelValue.length === 0 ? (placeholder ?? '') : ''"
      @keydown="onKeydown"
      @blur="commit"
    />
  </div>
</template>

<style scoped>
.tag-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 6px 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-2);
  background: var(--c-surface);
  cursor: text;
}

.tag-input:focus-within {
  border-color: var(--c-accent, var(--c-primary));
  outline: none;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--c-surface-raised);
  border: 1px solid var(--c-border);
  font-size: 12px;
  color: var(--c-text);
  white-space: nowrap;
}

.remove {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--c-text-muted);
}

.remove:hover {
  color: var(--c-text);
}

.inp {
  flex: 1;
  min-width: 80px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--c-text);
  padding: 0;
}

.inp::placeholder {
  color: var(--c-text-muted);
}
</style>
