<script setup lang="ts">
export type CompactRow = {
  key: string;
  label: string;
  value: string;
  placeholder: string;
  profState?: "none" | "proficient" | "expert";
};

const props = defineProps<{
  rows: CompactRow[];
  showProfDots?: boolean;
  columns?: number;
}>();
const emit = defineEmits<{
  (e: "updateValue", key: string, value: string): void;
  (e: "toggleProf", key: string): void;
}>();
</script>

<template>
  <div class="compact-list" :style="{ gridTemplateColumns: `repeat(${columns ?? 3}, 1fr)` }">
    <div v-for="row in rows" :key="row.key" class="list-item">
      <button
        v-if="showProfDots"
        class="prof-dot"
        :class="row.profState ?? 'none'"
        @click="emit('toggleProf', row.key)"
      />
      <span class="item-label">{{ row.label }}</span>
      <input
        type="text"
        class="compact-input"
        :value="row.value"
        :placeholder="row.placeholder"
        @input="emit('updateValue', row.key, ($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<style scoped>
.compact-list {
  display: grid;
  gap: 4px 10px;
}
.list-item {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-self: start;
  max-width: 100%;
}
.item-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  min-width: 0;
}
.compact-input {
  width: 44px;
  flex-shrink: 0;
  text-align: center;
  border: 1px solid var(--c-border);
  border-radius: var(--r-1);
  background: var(--c-surface);
  color: var(--c-text);
  padding: 3px 6px;
  font-size: 12px;
  font-family: inherit;
  outline: none;
}
.compact-input:focus { border-color: var(--c-accent); }
.compact-input::placeholder { color: var(--c-text-muted); opacity: 0.5; }

.prof-dot {
  position: relative;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--c-border);
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
  transition: border-color 0.12s;
}
.prof-dot.proficient { border: 3px solid var(--c-primary); }
.prof-dot.expert { border: 3px solid var(--c-primary); }
.prof-dot.expert::after {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  width: 4px; height: 4px;
  border-radius: 50%;
  background: var(--c-primary);
  transform: translate(-50%, -50%);
}
</style>
