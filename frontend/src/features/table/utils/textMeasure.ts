import { TEXT_INITIAL_WIDTH } from "@/features/table/constants";

const LINE_HEIGHT_RATIO = 1.35;
const PADDING_X = 12;
const PADDING_Y = 8;

export function lineHeightForFont(fontSize: number) {
  return Math.round(fontSize * LINE_HEIGHT_RATIO);
}

export function measureTextBoxSize(
  text: string,
  fontSize: number,
  minWidth = TEXT_INITIAL_WIDTH,
): { width: number; height: number } {
  const lines = text.split("\n");
  const lineH = lineHeightForFont(fontSize);

  let maxLineW = 0;
  if (typeof document !== "undefined") {
    const ctx = document.createElement("canvas").getContext("2d");
    if (ctx) {
      ctx.font = `${fontSize}px system-ui, -apple-system, sans-serif`;
      for (const line of lines) {
        maxLineW = Math.max(maxLineW, ctx.measureText(line || " ").width);
      }
    }
  }
  if (!maxLineW) {
    const longest = Math.max(...lines.map((l) => l.length), 1);
    maxLineW = longest * fontSize * 0.55;
  }

  return {
    width: Math.max(minWidth, Math.ceil(maxLineW + PADDING_X)),
    height: Math.max(lineH, lineH * lines.length + PADDING_Y),
  };
}
