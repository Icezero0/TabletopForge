import { onBeforeUnmount } from "vue";

type PreviewKey = string | number;

export function useRealtimePreviewChannel<TPayload>(options: {
  throttleMs: number;
  send: (payload: TPayload) => void;
  canSend?: () => boolean;
  applyLocal?: (payload: TPayload) => void;
  merge?: (pending: TPayload, next: TPayload) => TPayload;
  key?: (payload: TPayload) => PreviewKey;
}) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let lastSentAt = 0;
  let pending: TPayload | null = null;

  function clearTimer() {
    if (!timer) return;
    clearTimeout(timer);
    timer = null;
  }

  function canSendNow() {
    return options.canSend ? options.canSend() : true;
  }

  function mergePayload(next: TPayload) {
    if (pending == null) {
      pending = next;
      return;
    }
    if (options.key && options.key(pending) !== options.key(next)) {
      flush();
      pending = next;
      return;
    }
    pending = options.merge ? options.merge(pending, next) : next;
  }

  function flush() {
    const payload = pending;
    pending = null;
    clearTimer();
    if (payload == null || !canSendNow()) return;
    lastSentAt = Date.now();
    options.send(payload);
  }

  function preview(payload: TPayload) {
    options.applyLocal?.(payload);
    if (!canSendNow()) return;

    mergePayload(payload);
    const now = Date.now();
    const elapsed = now - lastSentAt;
    if (elapsed >= options.throttleMs) {
      flush();
      return;
    }
    if (!timer) {
      timer = setTimeout(flush, options.throttleMs - elapsed);
    }
  }

  function cancel() {
    pending = null;
    clearTimer();
  }

  onBeforeUnmount(cancel);

  return {
    preview,
    flush,
    cancel,
  };
}
