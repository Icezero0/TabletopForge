import { computed, ref, watch, type Ref } from "vue";
import {
  DEFAULT_GRID_CELL_PX,
  GRID_CELL_FT,
  GRID_CELL_PX_STEP,
  MAX_GRID_CELL_PX,
  MIN_GRID_CELL_PX,
} from "@/features/table/constants";
import { useTabletopStore } from "@/stores/tabletop.store";

export function useGridScale(
  roomId: Ref<number>,
  options?: { canEdit?: Ref<boolean> },
) {
  const tabletopStore = useTabletopStore();
  const gridCellPx = ref(DEFAULT_GRID_CELL_PX);

  function clampGridCellPx(value: number) {
    return Math.min(
      MAX_GRID_CELL_PX,
      Math.max(MIN_GRID_CELL_PX, Math.round(value / GRID_CELL_PX_STEP) * GRID_CELL_PX_STEP),
    );
  }

  const settings = computed(() => tabletopStore.getSettings(roomId.value));

  watch(
    settings,
    (value) => {
      if (value?.grid_cell_px) {
        gridCellPx.value = clampGridCellPx(value.grid_cell_px);
      }
    },
    { immediate: true },
  );

  const gridCellFt = computed(() => GRID_CELL_FT);

  async function persistGridCellPx(next: number) {
    gridCellPx.value = next;
    if (options?.canEdit?.value && roomId.value) {
      await tabletopStore.updateSettings(roomId.value, { grid_cell_px: next });
    }
  }

  async function increase() {
    const next = clampGridCellPx(gridCellPx.value + GRID_CELL_PX_STEP);
    await persistGridCellPx(next);
  }

  async function decrease() {
    const next = clampGridCellPx(gridCellPx.value - GRID_CELL_PX_STEP);
    await persistGridCellPx(next);
  }

  const canIncrease = computed(() => gridCellPx.value < MAX_GRID_CELL_PX);
  const canDecrease = computed(() => gridCellPx.value > MIN_GRID_CELL_PX);
  const canEditGrid = computed(() => options?.canEdit?.value ?? false);

  const scaleBarCells = 5;
  const scaleBarFt = computed(() => gridCellFt.value * scaleBarCells);
  const scaleBarWidthPx = computed(() => gridCellPx.value * scaleBarCells);

  return {
    gridCellPx,
    gridCellFt,
    scaleBarCells,
    scaleBarFt,
    scaleBarWidthPx,
    canIncrease: computed(() => canEditGrid.value && canIncrease.value),
    canDecrease: computed(() => canEditGrid.value && canDecrease.value),
    increase,
    decrease,
  };
}
