<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { PaperAirplaneIcon } from "@heroicons/vue/24/outline";
import AppIcon from "@/ui/base/AppIcon.vue";
import type { ChatSegment } from "@/features/chat/types";

const props = defineProps<{
  sendLabel?: string;
  sending?: boolean;
  sendMessage?: (segments: ChatSegment[]) => Promise<void> | void;
}>();

const emit = defineEmits<{
  send: [segments: ChatSegment[]];
}>();

const draft = ref("");
const sendPending = ref(false);
const inputRef = ref<HTMLTextAreaElement | null>(null);
const canSend = computed(() => draft.value.trim().length > 0);

function resizeInput() {
  const input = inputRef.value;
  if (!input) return;

  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
}

async function refocusInput() {
  await nextTick();
  resizeInput();
  inputRef.value?.focus();
}

async function sendMessage() {
  if (!canSend.value || props.sending || sendPending.value) return;

  const segments: ChatSegment[] = [
    {
      id: `text-${Date.now()}`,
      type: "text",
      content: draft.value,
    },
  ];

  sendPending.value = true;
  try {
    if (props.sendMessage) {
      await props.sendMessage(segments);
    } else {
      emit("send", segments);
    }
    draft.value = "";
    await refocusInput();
  } catch {
    // Keep the draft in place so the user can retry or edit it.
    await refocusInput();
  } finally {
    sendPending.value = false;
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  void sendMessage();
}

watch(draft, () => {
  void nextTick(resizeInput);
});

onMounted(() => {
  resizeInput();
});
</script>

<template>
  <div class="composer">
    <textarea
      ref="inputRef"
      v-model="draft"
      class="input"
      rows="2"
      placeholder="输入消息..."
      @keydown="handleKeydown"
    />

    <BaseIconButton
      class="sendButton"
      :aria-label="props.sendLabel || 'Send'"
      :disabled="!canSend || props.sending || sendPending"
      @mousedown.prevent
      @click="sendMessage"
    >
      <AppIcon :icon="PaperAirplaneIcon" :size="16" />
    </BaseIconButton>
  </div>
</template>

<style scoped>
.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: end;
}

.input {
  width: 100%;
  min-height: calc((13px * 1.45 * 2) + 20px);
  max-height: calc((13px * 1.45 * 3) + 20px);
  resize: none;
  box-sizing: border-box;
  padding: 9px 11px;
  border: 1px solid var(--c-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--c-surface) 78%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
  font-size: 13px;
  line-height: 1.45;
  outline: none;
  overflow-y: auto;
  scrollbar-width: none;
}

.input::-webkit-scrollbar {
  display: none;
}

.input:focus {
  border-color: var(--c-primary);
}

.sendButton {
  width: 38px;
  height: 38px;
  min-width: 38px;
  background: color-mix(in srgb, var(--c-primary) 8%, var(--c-surface));
  color: var(--c-primary);
  border-radius: 12px;
}

.sendButton:disabled {
  opacity: 0.45;
}
</style>
