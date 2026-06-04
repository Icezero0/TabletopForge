import { onBeforeUnmount, ref, type Ref } from "vue";
import {
  sendPointerLaser,
  sendPointerPresence,
  type PointerLaserPayload,
  type PointerPresencePayload,
} from "@/infra/realtime/tabletopRealtime";

export type RemoteCursor = {
  userId: number;
  displayName: string;
  x: number;
  y: number;
  updatedAt: number;
};

export type RemoteLaser = {
  userId: number;
  displayName: string;
  active: boolean;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

const PRESENCE_THROTTLE_MS = 50;
const STALE_CURSOR_MS = 5000;

export function useTabletopPointer(options: {
  roomId: Ref<number>;
  selfUserId: Ref<number | null | undefined>;
  canSend: Ref<boolean>;
}) {
  const remoteCursors = ref<RemoteCursor[]>([]);
  const remoteLasers = ref<RemoteLaser[]>([]);

  const cursorMap = new Map<number, RemoteCursor>();
  const laserMap = new Map<number, RemoteLaser>();
  let lastPresenceSend = 0;
  let laserActive = false;
  let pruneTimer: ReturnType<typeof setInterval> | null = null;

  function syncCursorList() {
    remoteCursors.value = [...cursorMap.values()];
  }

  function syncLaserList() {
    remoteLasers.value = [...laserMap.values()].filter((l) => l.active);
  }

  function pruneStaleCursors() {
    const now = Date.now();
    let changed = false;
    for (const [id, cursor] of cursorMap) {
      if (now - cursor.updatedAt > STALE_CURSOR_MS) {
        cursorMap.delete(id);
        changed = true;
      }
    }
    if (changed) syncCursorList();
  }

  function startPruneTimer() {
    if (pruneTimer) return;
    pruneTimer = setInterval(pruneStaleCursors, 2000);
  }

  function stopPruneTimer() {
    if (pruneTimer) {
      clearInterval(pruneTimer);
      pruneTimer = null;
    }
  }

  function handlePointerPresence(payload: PointerPresencePayload) {
    if (payload.user_id === options.selfUserId.value) return;
    cursorMap.set(payload.user_id, {
      userId: payload.user_id,
      displayName: payload.display_name,
      x: payload.x,
      y: payload.y,
      updatedAt: Date.now(),
    });
    syncCursorList();
    startPruneTimer();
  }

  function handlePointerLaser(payload: PointerLaserPayload) {
    if (payload.user_id === options.selfUserId.value) return;
    if (!payload.active) {
      laserMap.delete(payload.user_id);
    } else {
      laserMap.set(payload.user_id, {
        userId: payload.user_id,
        displayName: payload.display_name,
        active: true,
        x1: payload.x1,
        y1: payload.y1,
        x2: payload.x2 ?? payload.x1,
        y2: payload.y2 ?? payload.y1,
      });
    }
    syncLaserList();
  }

  function sendPresence(x: number, y: number) {
    const roomId = options.roomId.value;
    if (!roomId || !options.canSend.value) return;
    const now = Date.now();
    if (now - lastPresenceSend < PRESENCE_THROTTLE_MS) return;
    lastPresenceSend = now;
    sendPointerPresence(roomId, x, y);
  }

  function sendLaser(
    active: boolean,
    x1: number,
    y1: number,
    x2?: number,
    y2?: number,
  ) {
    const roomId = options.roomId.value;
    if (!roomId || !options.canSend.value) return;
    sendPointerLaser(roomId, { active, x1, y1, x2, y2 });
  }

  function onViewportPointerMove(
    clientX: number,
    clientY: number,
    toScene: (clientX: number, clientY: number) => { x: number; y: number },
  ) {
    const pt = toScene(clientX, clientY);
    sendPresence(pt.x, pt.y);
    if (laserActive) {
      sendLaser(true, laserStart.x, laserStart.y, pt.x, pt.y);
    }
  }

  let laserStart = { x: 0, y: 0 };

  function onViewportPointerDown(
    clientX: number,
    clientY: number,
    toScene: (clientX: number, clientY: number) => { x: number; y: number },
  ) {
    const pt = toScene(clientX, clientY);
    laserActive = true;
    laserStart = pt;
    sendLaser(true, pt.x, pt.y, pt.x, pt.y);
  }

  function onViewportPointerUp(
    clientX: number,
    clientY: number,
    toScene: (clientX: number, clientY: number) => { x: number; y: number },
  ) {
    if (!laserActive) return;
    const pt = toScene(clientX, clientY);
    laserActive = false;
    sendLaser(false, laserStart.x, laserStart.y, pt.x, pt.y);
  }

  onBeforeUnmount(() => {
    stopPruneTimer();
  });

  return {
    remoteCursors,
    remoteLasers,
    handlePointerPresence,
    handlePointerLaser,
    onViewportPointerMove,
    onViewportPointerDown,
    onViewportPointerUp,
  };
}
