export type TableToolMode = "select" | "hand" | "draw" | "pointer";

export type { DrawSubTool } from "@/features/table/drawingTypes";

export type TabletopSelection =
  | { type: "map"; id: number }
  | { type: "drawing"; id: number }
  | null;

export type FloatingAnchor =
  | "top-left"
  | "bottom-left"
  | "top-center"
  | "bottom-center"
  | "center-right";

export type FloatingCollapseTo = "top-left" | "bottom-left" | "top" | "bottom" | "right";
