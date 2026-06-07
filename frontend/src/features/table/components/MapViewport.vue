<script setup lang="ts">
import { computed, onUnmounted, ref, useId, watch } from "vue";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode, TabletopSelection } from "@/features/table/types";
import type { RoomDrawing, RoomMap, RoomToken } from "@/infra/api/rooms.api";
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
import PointerOverlay from "@/features/table/components/PointerOverlay.vue";
import SceneCanvas from "@/features/table/components/SceneCanvas.vue";
import type { RemoteCursor, RemoteLaser } from "@/features/table/composables/useTabletopPointer";

const props = withDefaults(
  defineProps<{
    maps?: RoomMap[];
    tokens?: RoomToken[];
    drawings?: RoomDrawing[];
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
    textPlacement?: TextPlacementRequest;
    textEdit?: TextEditRequest;
    editingDrawingId?: number | null;
    drawFontSize?: number;
    remoteCursors?: RemoteCursor[];
    remoteLasers?: RemoteLaser[];
    measureState?: MeasureState | null;
    measureSubTool?: MeasureSubTool;
    currentUserId?: number | null;
    characterOwnerById?: Map<number, number>;
    playerColorByUserId?: Map<number, string>;
  }>(),
  {
    maps: () => [],
    tokens: () => [],
    drawings: () => [],
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
    textPlacement: null,
    textEdit: null,
    editingDrawingId: null,
    drawFontSize: 16,
    remoteCursors: () => [],
    remoteLasers: () => [],
    measureState: null,
    measureSubTool: "line",
    currentUserId: null,
    characterOwnerById: () => new Map<number, number>(),
  },
);

const emit = defineEmits<{
  selectMap: [mapId: number];
  mapContextMenu: [mapId: number, event: MouseEvent];
  selectToken: [tokenId: number];
  tokenContextMenu: [tokenId: number, event: MouseEvent];
  selectDrawing: [drawingId: number];
  patchMap: [mapId: number, payload: { x?: number; y?: number; scale?: number; locked?: boolean }];
  patchToken: [
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
}>();

const toolModeRef = computed(() => props.toolMode);
const { viewportTransform, viewportScale, setViewportEl } = useTabletopViewport(toolModeRef);

const patternUid = useId().replace(/:/g, "");
const minorPatternId = computed(() => `grid-minor-${patternUid}`);

const gridOrigin = SCENE_ORIGIN;
const gridSpan = SCENE_SPAN;

const rootRef = ref<HTMLElement | null>(null);
const drawingLayerRef = ref<InstanceType<typeof DrawingLayer> | null>(null);

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

function scenePointFromClient(clientX: number, clientY: number) {
  return drawingLayerRef.value?.scenePointFromClient(clientX, clientY) ?? { x: 0, y: 0 };
}

function onViewportPointerMove(event: PointerEvent) {
  if (pointerMode.value) {
    emit("viewportPointerMove", event);
    return;
  }
  if (measureMode.value) {
    const pt = scenePointFromClient(event.clientX, event.clientY);
    emit("measurePointerMove", pt.x, pt.y, event);
  }
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
  }
}

const selectedDrawingId = computed(() =>
  props.selection?.type === "drawing" ? props.selection.id : null,
);

const selectedTokenId = computed(() =>
  props.selection?.type === "token" ? props.selection.id : null,
);

function onContextMenu(event: MouseEvent) {
  if (props.toolMode === "draw" || props.toolMode === "measure") return;
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
  if (props.toolMode === "draw" || props.toolMode === "pointer") return;
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

defineExpose({ getViewportWidth, scenePointFromClient, scenePointFromViewportCenter });
</script>

<template>
  <div
    ref="rootRef"
    class="mapViewport"
    :class="{
      handMode: sceneInteractive,
      pointerMode,
      measureMode,
    }"
    @contextmenu="onContextMenu"
    @click="onViewportClick"
    @pointermove="onViewportPointerMove"
    @pointerdown="onViewportPointerDown"
    @pointerup="onViewportPointerUp"
    @pointercancel="onViewportPointerUp"
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
        :tool-mode="toolMode"
        :game-role="gameRole"
        :grid-cell-ft="gridCellFt"
        :grid-cell-px="gridCellPx"
        :selected-token-id="selectedTokenId"
        :current-user-id="currentUserId"
        :character-owner-by-id="characterOwnerById"
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
        :editing-drawing-id="editingDrawingId"
        :interactive="drawInteractive"
        :sub-tool="drawSubTool"
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
      <SelectionOverlay
        :selection="selection"
        :maps="maps"
        :map-natural-size="mapNaturalSize"
        :tool-mode="toolMode"
        :game-role="gameRole"
        :viewport-scale="viewportScale"
        @patch-map="(id, p) => emit('patchMap', id, p)"
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
        @patch-token="(id, p) => emit('patchToken', id, p)"
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
.mapViewport.measureMode {
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
