import { ref } from "vue";
import type { TabletopSelection } from "@/features/table/types";

export function useTabletopSelection() {
  const selection = ref<TabletopSelection>(null);

  function selectMap(id: number) {
    selection.value = { type: "map", id };
  }

  function selectDrawing(id: number) {
    selection.value = { type: "drawing", id };
  }

  function selectToken(id: number) {
    selection.value = { type: "token", id };
  }

  function clearSelection() {
    selection.value = null;
  }

  return {
    selection,
    selectMap,
    selectDrawing,
    selectToken,
    clearSelection,
  };
}
