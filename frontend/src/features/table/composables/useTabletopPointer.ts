import { onBeforeUnmount, ref, type Ref } from "vue";
import {
  sendPointerLaser,
  sendPointerPresence,
  type PointerLaserPayload,
  type PointerPresencePayload,
} from "@/infra/realtime/tabletopRealtime";
import { useRealtimePreviewChannel } from "@/features/table/composables/useRealtimePreviewChannel";

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
  x: number;
  y: number;
  trail: RemoteLaserTrailPoint[];
};

export type RemoteLaserTrailPoint = {
  id: number;
  createdAt: number;
  x: number;
  y: number;
  opacity: number;
};

const PRESENCE_THROTTLE_MS = 50;
const STALE_CURSOR_MS = 5000;
const LASER_TRAIL_MS = 850;
const LASER_TRAIL_MAX_POINTS = 18;
const POINTER_PRUNE_INTERVAL_MS = 80;

export function useTabletopPointer(options: {
  roomId: Ref<number>;
  selfUserId: Ref<number | null | undefined>;
  selfDisplayName?: Ref<string | null | undefined>;
  canSend: Ref<boolean>;
}) {
  const remoteCursors = ref<RemoteCursor[]>([]);
  const remoteLasers = ref<RemoteLaser[]>([]);

  const cursorMap = new Map<number, RemoteCursor>();
  const laserMap = new Map<number, RemoteLaser>();
  let laserActive = false;
  let pruneTimer: ReturnType<typeof setInterval> | null = null;
  let trailPointSeq = 0;

  const presencePreview = useRealtimePreviewChannel<{ x: number; y: number }>({
    throttleMs: PRESENCE_THROTTLE_MS,
    canSend: () => !!options.roomId.value && options.canSend.value,
    send: (payload) => {
      sendPointerPresence(options.roomId.value, payload.x, payload.y);
    },
  });

  function syncCursorList() {
    remoteCursors.value = [...cursorMap.values()];
  }

  function syncLaserList() {
    remoteLasers.value = [...laserMap.values()].filter((l) => l.active || l.trail.length > 0);
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
    for (const [id, laser] of laserMap) {
      const nextTrail = laser.trail
        .map((point) => ({
          ...point,
          opacity: Math.max(0, 1 - (now - point.createdAt) / LASER_TRAIL_MS),
        }))
        .filter((point) => point.opacity > 0);
      if (!laser.active && nextTrail.length === 0) {
        laserMap.delete(id);
        changed = true;
      } else if (nextTrail.length !== laser.trail.length) {
        laserMap.set(id, { ...laser, trail: nextTrail });
        changed = true;
      } else if (nextTrail.some((point, index) => point.opacity !== laser.trail[index]?.opacity)) {
        laserMap.set(id, { ...laser, trail: nextTrail });
        changed = true;
      }
    }
    if (changed) syncCursorList();
    if (changed) syncLaserList();
  }

  function startPruneTimer() {
    if (pruneTimer) return;
    pruneTimer = setInterval(pruneStaleCursors, POINTER_PRUNE_INTERVAL_MS);
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

  function applyLaserSample(
    userId: number,
    displayName: string,
    active: boolean,
    x: number,
    y: number,
  ) {
    const now = Date.now();
    const current = laserMap.get(userId);
    const trail = [
      ...(current?.trail ?? []),
      {
        id: trailPointSeq++,
        createdAt: now,
        x,
        y,
        opacity: 1,
      },
    ].slice(-LASER_TRAIL_MAX_POINTS);
    if (!active) {
      if (current) {
        laserMap.set(userId, {
          ...current,
          active: false,
          x,
          y,
          trail,
        });
      }
    } else {
      laserMap.set(userId, {
        userId,
        displayName,
        active: true,
        x,
        y,
        trail,
      });
    }
    syncLaserList();
    startPruneTimer();
  }

  function handlePointerLaser(payload: PointerLaserPayload) {
    if (payload.user_id === options.selfUserId.value) return;
    applyLaserSample(
      payload.user_id,
      payload.display_name,
      payload.active,
      payload.x,
      payload.y,
    );
  }

  function sendPresence(x: number, y: number) {
    presencePreview.preview({ x, y });
  }

  function sendLaser(
    active: boolean,
    x: number,
    y: number,
  ) {
    const roomId = options.roomId.value;
    if (!roomId || !options.canSend.value) return;
    const selfUserId = options.selfUserId.value;
    if (selfUserId != null) {
      applyLaserSample(
        selfUserId,
        options.selfDisplayName?.value || "You",
        active,
        x,
        y,
      );
    }
    sendPointerLaser(roomId, { active, x, y });
  }

  function onViewportPointerMove(
    clientX: number,
    clientY: number,
    toScene: (clientX: number, clientY: number) => { x: number; y: number },
  ) {
    const pt = toScene(clientX, clientY);
    sendPresence(pt.x, pt.y);
    if (laserActive) {
      sendLaser(true, pt.x, pt.y);
    }
  }

  function onViewportPointerDown(
    clientX: number,
    clientY: number,
    toScene: (clientX: number, clientY: number) => { x: number; y: number },
  ) {
    const pt = toScene(clientX, clientY);
    laserActive = true;
    sendLaser(true, pt.x, pt.y);
  }

  function onViewportPointerUp(
    clientX: number,
    clientY: number,
    toScene: (clientX: number, clientY: number) => { x: number; y: number },
  ) {
    if (!laserActive) return;
    const pt = toScene(clientX, clientY);
    laserActive = false;
    sendLaser(false, pt.x, pt.y);
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
