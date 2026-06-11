<script setup lang="ts">
import { computed, onUnmounted, ref, toRef, useId, watch } from "vue";
import type { GameRole } from "@/features/room/types";
import type { FogSubTool, RemoteObjectSelection, TableToolMode, TabletopSelection } from "@/features/table/types";
import type { RoomCombatState, RoomDrawing, RoomFogMapMask, RoomFogState, RoomMap, RoomToken } from "@/infra/api/rooms.api";
import type { DrawPreview, TextPlacementRequest } from "@/features/table/composables/useDrawingTools";
import type { MeasureState } from "@/features/table/composables/useMeasureTool";
import type { MeasureSubTool } from "@/features/table/types";
import type { TextEditRequest } from "@/features/table/composables/useTextDrawingEdit";
import { GRID_LAYER_Z, SCENE_ORIGIN, SCENE_SPAN } from "@/features/table/constants";
import { useTabletopViewport } from "@/features/table/composables/useTabletopViewport";
import MapLayer from "@/features/table/components/MapLayer.vue";
import TokenLayer from "@/features/table/components/TokenLayer.vue";
import TokenSelectionOverlay from "@/features/table/components/TokenSelectionOverlay.vue";
import DrawingLayer from "@/features/table/components/DrawingLayer.vue";
import DrawingSelectionOverlay from "@/features/table/components/DrawingSelectionOverlay.vue";
import DrawTextBoxEditor from "@/features/table/components/DrawTextBoxEditor.vue";
import SelectionOverlay from "@/features/table/components/SelectionOverlay.vue";
import MeasureOverlay from "@/features/table/components/MeasureOverlay.vue";
import FogOverlay from "@/features/table/components/FogOverlay.vue";
import PointerOverlay from "@/features/table/components/PointerOverlay.vue";
import SceneCanvas from "@/features/table/components/SceneCanvas.vue";
import type { RemoteCursor, RemoteLaser } from "@/features/table/composables/useTabletopPointer";

const props = withDefaults(
  defineProps<{
    maps?: RoomMap[];
    tokens?: RoomToken[];
    drawings?: RoomDrawing[];
    combatState?: RoomCombatState | null;
    fogState?: RoomFogState | null;
    gridCellPx?: number;
    gridCellFt?: number;
    scaleBarCells?: number;
    toolMode?: TableToolMode;
    gameRole?: GameRole | "unknown";
    selection?: TabletopSelection;
    drawPreview?: DrawPreview;
    mapNaturalSize?: { w: number; h: number };
    drawInteractive?: boolean;
    drawSubTool?: string;
    drawStrokeWidth?: number;
    drawStrokeColor?: string;
    textPlacement?: TextPlacementRequest;
    textEdit?: TextEditRequest;
    editingDrawingId?: number | null;
    drawFontSize?: number;
    remoteCursors?: RemoteCursor[];
    remoteLasers?: RemoteLaser[];
    remoteObjectSelections?: RemoteObjectSelection[];
    measureState?: MeasureState | null;
    measureSubTool?: MeasureSubTool;
    fogSubTool?: FogSubTool;
    fogBrushRadius?: number;
    currentUserId?: number | null;
    characterOwnerById?: Map<number, number>;
    characterDataHiddenById?: Map<number, boolean>;
    playerColorByUserId?: Map<number, string>;
    roomId?: number | null;
    activeSceneId?: number | null;
  }>(),
  {
    maps: () => [],
    tokens: () => [],
    drawings: () => [],
    combatState: null,
    gridCellPx: 40,
    gridCellFt: 5,
    scaleBarCells: 5,
    toolMode: "select",
    gameRole: "unknown",
    selection: null,
    drawPreview: null,
    mapNaturalSize: () => ({ w: 0, h: 0 }),
    drawInteractive: false,
    drawSubTool: "brush",
    drawStrokeWidth: 3,
    drawStrokeColor: "#e11d48",
    textPlacement: null,
    textEdit: null,
    editingDrawingId: null,
    drawFontSize: 16,
    remoteCursors: () => [],
    remoteLasers: () => [],
    remoteObjectSelections: () => [],
    measureState: null,
    measureSubTool: "line",
    fogSubTool: "erase",
    fogBrushRadius: 54,
    currentUserId: null,
    characterOwnerById: () => new Map<number, number>(),
    characterDataHiddenById: () => new Map<number, boolean>(),
  },
);

const emit = defineEmits<{
  selectMap: [mapId: number];
  mapContextMenu: [mapId: number, event: MouseEvent];
  selectToken: [tokenId: number];
  tokenContextMenu: [tokenId: number, event: MouseEvent];
  selectDrawing: [drawingId: number];
  patchMap: [mapId: number, payload: { x?: number; y?: number; scale?: number; locked?: boolean }];
  previewToken: [
    tokenId: number,
    payload: { x?: number; y?: number; width?: number; height?: number },
  ];
  commitToken: [
    tokenId: number,
    payload: { x?: number; y?: number; width?: number; height?: number },
  ];
  patchDrawing: [
    drawingId: number,
    payload: { geometry?: Record<string, unknown>; style?: Record<string, unknown> },
  ];
  mapNaturalSize: [payload: { mapId: number; w: number; h: number }];
  drawPointerDown: [x: number, y: number, event: PointerEvent];
  drawPointerMove: [x: number, y: number, event: PointerEvent];
  drawPointerUp: [x: number, y: number, event: PointerEvent];
  confirmText: [payload: { text: string; width: number; height: number }];
  cancelText: [];
  confirmTextEdit: [payload: { text: string; width: number; height: number }];
  cancelTextEdit: [];
  textPlacementResize: [width: number];
  editText: [drawingId: number];
  drawingContextMenu: [drawingId: number, event: MouseEvent];
  contextMenu: [event: MouseEvent];
  clearSelection: [];
  viewportPointerMove: [event: PointerEvent];
  viewportPointerDown: [event: PointerEvent];
  viewportPointerUp: [event: PointerEvent];
  measurePointerDown: [x: number, y: number, event: PointerEvent];
  measurePointerMove: [x: number, y: number, event: PointerEvent];
  measurePointerUp: [x: number, y: number, event: PointerEvent];
  measureRouteClick: [x: number, y: number];
  measureRouteFinish: [];
  fogPointerDown: [x: number, y: number, event: PointerEvent];
  fogPointerMove: [x: number, y: number, event: PointerEvent];
  fogPointerUp: [x: number, y: number, event: PointerEvent];
}>();

const toolModeRef = computed(() => props.toolMode);
const roomIdRef = toRef(props, "roomId");
const activeSceneIdRef = toRef(props, "activeSceneId");
const { viewportTransform, viewportScale, setViewportEl, resetViewport, centerScenePoint } = useTabletopViewport(toolModeRef, roomIdRef, activeSceneIdRef);


const patternUid = useId().replace(/:/g, "");
const minorPatternId = computed(() => `grid-minor-${patternUid}`);

const gridOrigin = SCENE_ORIGIN;
const gridSpan = SCENE_SPAN;
const rootRef = ref<HTMLElement | null>(null);
const drawingLayerRef = ref<InstanceType<typeof DrawingLayer> | null>(null);
const fogPreviewPoint = ref<{ x: number; y: number } | null>(null);
const fogHitMasks = ref<Record<number, { mask: RoomFogMapMask; pixels: Uint8ClampedArray }>>({});

watch(
  rootRef,
  (el) => {
    setViewportEl(el);
  },
  { immediate: true },
);

onUnmounted(() => {
  setViewportEl(null);
});

const sceneInteractive = computed(() => props.toolMode === "hand");
const pointerMode = computed(() => props.toolMode === "pointer");
const measureMode = computed(() => props.toolMode === "measure");
const fogMode = computed(() => props.toolMode === "fog" && props.gameRole === "GM");

function scenePointFromClient(clientX: number, clientY: number) {
  return drawingLayerRef.value?.scenePointFromClient(clientX, clientY) ?? { x: 0, y: 0 };
}

function loadFogMaskPixels(mask: RoomFogMapMask) {
  return new Promise<{ mask: RoomFogMapMask; pixels: Uint8ClampedArray }>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = mask.width;
      canvas.height = mask.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas context unavailable"));
        return;
      }
      ctx.drawImage(img, 0, 0, mask.width, mask.height);
      resolve({ mask, pixels: ctx.getImageData(0, 0, mask.width, mask.height).data });
    };
    img.onerror = reject;
    img.src = mask.data_url;
  });
}

watch(
  () => ({ gameRole: props.gameRole, masks: props.fogState?.maps ?? {} }),
  async ({ gameRole, masks }) => {
    if (gameRole === "GM") {
      fogHitMasks.value = {};
      return;
    }
    const entries = Object.values(masks);
    if (!entries.length) {
      fogHitMasks.value = {};
      return;
    }
    const loaded = await Promise.allSettled(entries.map(loadFogMaskPixels));
    const next: Record<number, { mask: RoomFogMapMask; pixels: Uint8ClampedArray }> = {};
    for (const result of loaded) {
      if (result.status === "fulfilled") {
        next[result.value.mask.map_id] = result.value;
      }
    }
    fogHitMasks.value = next;
  },
  { immediate: true, deep: true },
);

function isScenePointFogged(x: number, y: number) {
  if (props.gameRole === "GM") return false;
  const mapsByTop = [...props.maps].sort((a, b) => b.z_index - a.z_index || b.id - a.id);
  for (const map of mapsByTop) {
    const maskMeta = props.fogState?.maps?.[String(map.id)];
    const hitMask = fogHitMasks.value[map.id];
    const scaleX = map.scale_x ?? map.scale;
    const scaleY = map.scale_y ?? map.scale;
    const localX = (x - map.x) / scaleX;
    const localY = (y - map.y) / scaleY;
    const mapWidth = hitMask?.mask.map_width ?? maskMeta?.map_width;
    const mapHeight = hitMask?.mask.map_height ?? maskMeta?.map_height;
    if (mapWidth == null || mapHeight == null) continue;
    if (localX < 0 || localY < 0 || localX > mapWidth || localY > mapHeight) {
      continue;
    }
    if (!hitMask) return true;
    const maskX = Math.min(hitMask.mask.width - 1, Math.max(0, Math.floor(localX * hitMask.mask.width / hitMask.mask.map_width)));
    const maskY = Math.min(hitMask.mask.height - 1, Math.max(0, Math.floor(localY * hitMask.mask.height / hitMask.mask.map_height)));
    const index = (maskY * hitMask.mask.width + maskX) * 4;
    return (hitMask.pixels[index] ?? 0) > 127;
  }
  return false;
}

function isClientPointFogged(clientX: number, clientY: number) {
  const pt = scenePointFromClient(clientX, clientY);
  return isScenePointFogged(pt.x, pt.y);
}

function updateFogPreview(event: PointerEvent) {
  const pt = scenePointFromClient(event.clientX, event.clientY);
  fogPreviewPoint.value = pt;
  return pt;
}

function onViewportPointerMove(event: PointerEvent) {
  if (pointerMode.value) {
    emit("viewportPointerMove", event);
    return;
  }
  if (measureMode.value) {
    const pt = scenePointFromClient(event.clientX, event.clientY);
    emit("measurePointerMove", pt.x, pt.y, event);
    return;
  }
  if (fogMode.value) {
    const pt = updateFogPreview(event);
    emit("fogPointerMove", pt.x, pt.y, event);
    return;
  }
  fogPreviewPoint.value = null;
}

function onViewportPointerDown(event: PointerEvent) {
  if (pointerMode.value && event.button === 0) {
    emit("viewportPointerDown", event);
    return;
  }
  if (measureMode.value && event.button === 0) {
    event.preventDefault();
    if (props.measureSubTool === "line") {
      const pt = scenePointFromClient(event.clientX, event.clientY);
      emit("measurePointerDown", pt.x, pt.y, event);
    }
    // Route mode is handled via click events (onViewportClick)
    return;
  }
  if (fogMode.value && event.button === 0) {
    event.preventDefault();
    const pt = updateFogPreview(event);
    emit("fogPointerDown", pt.x, pt.y, event);
  }
}

function onViewportPointerUp(event: PointerEvent) {
  if (pointerMode.value) {
    emit("viewportPointerUp", event);
    return;
  }
  if (measureMode.value) {
    const pt = scenePointFromClient(event.clientX, event.clientY);
    emit("measurePointerUp", pt.x, pt.y, event);
    return;
  }
  if (fogMode.value) {
    const pt = updateFogPreview(event);
    emit("fogPointerUp", pt.x, pt.y, event);
  }
}

function onViewportPointerLeave() {
  fogPreviewPoint.value = null;
}

const selectedDrawingId = computed(() =>
  props.selection?.type === "drawing" ? props.selection.id : null,
);

const selectedTokenId = computed(() =>
  props.selection?.type === "token" ? props.selection.id : null,
);

function onContextMenu(event: MouseEvent) {
  if (props.toolMode === "draw" || props.toolMode === "measure" || props.toolMode === "fog") return;
  if ((event.target as Element).closest(".mapItem, .tokenWrap, .tokenItem, .tokenSelectionOverlay, .drawingLayer")) return;
  event.preventDefault();
  emit("contextMenu", event);
}

function onTokenSelectionContextMenu(event: MouseEvent) {
  const id = selectedTokenId.value;
  if (id == null) return;
  emit("tokenContextMenu", id, event);
}

function onViewportClick(event: MouseEvent) {
  if (props.toolMode === "draw" || props.toolMode === "pointer" || props.toolMode === "fog") return;
  if (props.toolMode === "measure") {
    if (props.measureSubTool === "route" && event.button === 0) {
      const pt = scenePointFromClient(event.clientX, event.clientY);
      if (event.detail >= 2) {
        emit("measureRouteFinish");
      } else {
        emit("measureRouteClick", pt.x, pt.y);
      }
    }
    return;
  }
  const target = event.target as Element;
  if (
    target.closest(
      ".mapItem, .tokenWrap, .tokenItem, .selectionOverlay, .tokenSelectionOverlay, .drawingSelectionOverlay, .textBoxEditor, .drawingLayer.pickMode",
    )
  ) {
    return;
  }
  emit("clearSelection");
}

function getViewportWidth() {
  return rootRef.value?.clientWidth ?? 0;
}

function scenePointFromViewportCenter() {
  const el = rootRef.value;
  if (!el) return { x: 0, y: 0 };
  const rect = el.getBoundingClientRect();
  return scenePointFromClient(rect.left + rect.width / 2, rect.top + rect.height / 2);
}

defineExpose({ getViewportWidth, scenePointFromClient, scenePointFromViewportCenter, resetViewport, centerScenePoint });
</script>

<template>
  <div
    ref="rootRef"
    class="mapViewport"
    :class="{
      handMode: sceneInteractive,
      pointerMode,
      measureMode,
      fogMode,
    }"
    @contextmenu="onContextMenu"
    @click="onViewportClick"
    @pointermove="onViewportPointerMove"
    @pointerdown="onViewportPointerDown"
    @pointerup="onViewportPointerUp"
    @pointercancel="onViewportPointerUp"
    @pointerleave="onViewportPointerLeave"
  >
    <SceneCanvas
      :transform="viewportTransform"
      :interactive="sceneInteractive"
    >
      <MapLayer
        :maps="maps"
        :tool-mode="toolMode"
        :game-role="gameRole"
        @select="emit('selectMap', $event)"
        @map-context-menu="(id, ev) => emit('mapContextMenu', id, ev)"
        @natural-size="emit('mapNaturalSize', $event)"
      />
      <TokenLayer
        :tokens="tokens"
        :combat-state="combatState"
        :tool-mode="toolMode"
        :game-role="gameRole"
        :grid-cell-ft="gridCellFt"
        :grid-cell-px="gridCellPx"
        :selected-token-id="selectedTokenId"
        :current-user-id="currentUserId"
        :character-owner-by-id="characterOwnerById"
        :character-data-hidden-by-id="characterDataHiddenById"
        :player-color-by-user-id="playerColorByUserId"
        :remote-selections="remoteObjectSelections.filter((claim) => claim.type === 'token')"
        :is-client-point-fogged="isClientPointFogged"
        @select-token="emit('selectToken', $event)"
        @token-context-menu="(id, ev) => emit('tokenContextMenu', id, ev)"
      />
      <DrawingLayer
        ref="drawingLayerRef"
        :drawings="drawings"
        :tool-mode="toolMode"
        :game-role="gameRole"
        :preview="drawPreview"
        :selected-drawing-id="selectedDrawingId"
        :remote-selections="remoteObjectSelections.filter((claim) => claim.type === 'drawing')"
        :editing-drawing-id="editingDrawingId"
        :interactive="drawInteractive"
        :sub-tool="drawSubTool"
        :stroke-width="drawStrokeWidth"
        :stroke-color="drawStrokeColor"
        :viewport-scale="viewportScale"
        @select-drawing="emit('selectDrawing', $event)"
        @edit-text="emit('editText', $event)"
        @pointer-down="(x, y, e) => emit('drawPointerDown', x, y, e)"
        @pointer-move="(x, y, e) => emit('drawPointerMove', x, y, e)"
        @pointer-up="(x, y, e) => emit('drawPointerUp', x, y, e)"
        @drawing-context-menu="(id, ev) => emit('drawingContextMenu', id, ev)"
      />
      <MeasureOverlay :state="measureState" />
      <svg
        class="gridLayer"
        aria-hidden="true"
        :viewBox="`${gridOrigin} ${gridOrigin} ${gridSpan} ${gridSpan}`"
        :style="{
          left: `${gridOrigin}px`,
          top: `${gridOrigin}px`,
          width: `${gridSpan}px`,
          height: `${gridSpan}px`,
          zIndex: GRID_LAYER_Z,
        }"
      >
        <defs>
          <pattern
            :id="minorPatternId"
            :width="gridCellPx"
            :height="gridCellPx"
            patternUnits="userSpaceOnUse"
          >
            <path
              :d="`M ${gridCellPx} 0 L 0 0 0 ${gridCellPx}`"
              class="gridLineMinor"
            />
          </pattern>
        </defs>
        <rect
          :x="gridOrigin"
          :y="gridOrigin"
          :width="gridSpan"
          :height="gridSpan"
          :fill="`url(#${minorPatternId})`"
        />
      </svg>
      <FogOverlay
        :fog-state="fogState ?? null"
        :maps="maps"
        :game-role="gameRole"
        :preview-point="fogMode ? fogPreviewPoint : null"
        :preview-mode="fogSubTool"
        :preview-radius="fogBrushRadius"
      />
      <SelectionOverlay
        :selection="selection"
        :maps="maps"
        :map-natural-size="mapNaturalSize"
        :tool-mode="toolMode"
        :game-role="gameRole"
        :viewport-scale="viewportScale"
        @patch-map="(id, p) => emit('patchMap', id, p)"
        @context-menu="(id, ev) => emit('mapContextMenu', id, ev)"
      />
      <TokenSelectionOverlay
        :selection="selection"
        :tokens="tokens"
        :tool-mode="toolMode"
        :game-role="gameRole"
        :grid-cell-ft="gridCellFt"
        :grid-cell-px="gridCellPx"
        :current-user-id="currentUserId"
        :character-owner-by-id="characterOwnerById"
        :viewport-scale="viewportScale"
        @preview-token="(id, p) => emit('previewToken', id, p)"
        @commit-token="(id, p) => emit('commitToken', id, p)"
        @token-context-menu="onTokenSelectionContextMenu"
      />
      <DrawingSelectionOverlay
        :selection="selection"
        :drawings="drawings"
        :tool-mode="toolMode"
        :game-role="gameRole"
        :viewport-scale="viewportScale"
        @patch-drawing="(id, p) => emit('patchDrawing', id, p)"
      />
      <DrawTextBoxEditor
        v-if="textPlacement"
        :bounds="textPlacement"
        :font-size="drawFontSize"
        @confirm="emit('confirmText', $event)"
        @cancel="emit('cancelText')"
        @resize="emit('textPlacementResize', $event)"
      />
      <DrawTextBoxEditor
        v-if="textEdit"
        :bounds="{
          x: textEdit!.x,
          y: textEdit!.y,
          width: textEdit!.width,
          height: textEdit!.height,
        }"
        :font-size="textEdit!.fontSize"
        :initial-text="textEdit!.text"
        :text-color="textEdit!.color"
        is-edit
        @confirm="emit('confirmTextEdit', $event)"
        @cancel="emit('cancelTextEdit')"
      />
      <PointerOverlay
        :cursors="remoteCursors"
        :lasers="remoteLasers"
        :color-by-user-id="playerColorByUserId"
      />
    </SceneCanvas>
  </div>
</template>

<style scoped>
.mapViewport {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  background: color-mix(in srgb, var(--c-surface) 78%, var(--c-bg));
  overflow: hidden;
}

.mapViewport.handMode {
  cursor: grab;
}

.mapViewport.handMode:active {
  cursor: grabbing;
}

.mapViewport.pointerMode,
.mapViewport.measureMode,
.mapViewport.fogMode {
  cursor: crosshair;
}

.gridLayer {
  position: absolute;
  top: 0;
  left: 0;
  overflow: visible;
  pointer-events: none;
}

.gridLineMinor {
  fill: none;
  stroke: color-mix(in srgb, var(--c-text) 32%, transparent);
  stroke-width: 1.25;
  stroke-dasharray: 5 4;
  vector-effect: non-scaling-stroke;
}

:deep(.sceneCanvas) {
  position: absolute;
  inset: 0;
}
</style>
