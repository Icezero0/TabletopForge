export type TableToolMode = "select" | "hand" | "draw" | "pointer" | "measure" | "music";
export type MeasureSubTool = "line" | "route";

export type { DrawSubTool } from "@/features/table/drawingTypes";

export type TabletopSelection =
  | { type: "map"; id: number }
  | { type: "token"; id: number }
  | { type: "drawing"; id: number }
  | null;

export type ClaimableObjectSelection = Exclude<TabletopSelection, { type: "map"; id: number } | null>;

export type RemoteObjectSelection = ClaimableObjectSelection & {
  userId: number;
  color?: string | null;
  expiresAt?: number;
};

export type FloatingAnchor =
  | "top-left"
  | "bottom-left"
  | "top-center"
  | "bottom-center"
  | "center-right";

export type FloatingCollapseTo = "top-left" | "bottom-left" | "top" | "bottom" | "right";
