export const PLAYER_COLOR_PRESETS = [
  "#e11d48",
  "#2563eb",
  "#16a34a",
  "#ca8a04",
  "#9333ea",
  "#0891b2",
  "#ea580c",
  "#4b5563",
] as const;

export type PlayerColor = (typeof PLAYER_COLOR_PRESETS)[number];
