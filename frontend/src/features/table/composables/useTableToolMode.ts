import { computed, ref, type Ref } from "vue";
import type { GameRole } from "@/features/room/types";
import type { TableToolMode } from "@/features/table/types";

export function useTableToolMode(gameRole: Ref<GameRole | "unknown">) {
  const toolMode = ref<TableToolMode>("select");

  const disabledTools = computed<TableToolMode[]>(() => {
    if (gameRole.value === "GM") return [];
    if (gameRole.value === "OB") return ["draw", "pointer", "fog"];
    return ["fog"];
  });

  function setToolMode(mode: TableToolMode) {
    if (disabledTools.value.includes(mode)) return;
    toolMode.value = mode;
  }

  return {
    toolMode,
    disabledTools,
    setToolMode,
  };
}
