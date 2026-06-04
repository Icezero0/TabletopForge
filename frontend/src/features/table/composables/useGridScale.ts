import { computed, ref, watch, type Ref } from "vue";
import {
  DEFAULT_GRID_CELL_PX,
  GRID_CELL_FT,
  GRID_CELL_PX_STEP,
  MAX_GRID_CELL_PX,
  MIN_GRID_CELL_PX,
} from "@/features/table/constants";

export function useGridScale(roomId: Ref<number>) {
  const gridCellPx = ref(DEFAULT_GRID_CELL_PX);

  function storageKey() {
    return `tabletop:room:${roomId.value}:grid-cell-px`;
  }

  function load() {
    if (!roomId.value || typeof localStorage === "undefined") return;
    const raw = localStorage.getItem(storageKey());
    const parsed = raw ? Number(raw) : NaN;
    if (Number.isFinite(parsed)) {
      gridCellPx.value = clampGridCellPx(parsed);
    } else {
      gridCellPx.value = DEFAULT_GRID_CELL_PX;
    }
  }

  function persist() {
    if (!roomId.value || typeof localStorage === "undefined") return;
    localStorage.setItem(storageKey(), String(gridCellPx.value));
  }

  function clampGridCellPx(value: number) {
    return Math.min(
      MAX_GRID_CELL_PX,
      Math.max(MIN_GRID_CELL_PX, Math.round(value / GRID_CELL_PX_STEP) * GRID_CELL_PX_STEP),
    );
  }

  function increase() {
    gridCellPx.value = clampGridCellPx(gridCellPx.value + GRID_CELL_PX_STEP);
    persist();
  }

  function decrease() {
    gridCellPx.value = clampGridCellPx(gridCellPx.value - GRID_CELL_PX_STEP);
    persist();
  }

  const canIncrease = computed(() => gridCellPx.value < MAX_GRID_CELL_PX);
  const canDecrease = computed(() => gridCellPx.value > MIN_GRID_CELL_PX);

  const scaleBarCells = 5;
  const scaleBarFt = computed(() => GRID_CELL_FT * scaleBarCells);
  const scaleBarWidthPx = computed(() => gridCellPx.value * scaleBarCells);

  watch(roomId, () => load(), { immediate: true });

  return {
    gridCellPx,
    gridCellFt: GRID_CELL_FT,
    scaleBarCells,
    scaleBarFt,
    scaleBarWidthPx,
    canIncrease,
    canDecrease,
    increase,
    decrease,
  };
}
