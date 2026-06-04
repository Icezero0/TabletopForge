import { ref, type Ref } from "vue";
import type { RoomDrawing } from "@/infra/api/rooms.api";
import { measureTextBoxSize } from "@/features/table/utils/textMeasure";

export type TextEditRequest = {
  drawingId: number;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  color: string;
  fontSize: number;
} | null;

type UseTextDrawingEditOptions = {
  drawings: Ref<RoomDrawing[]>;
  onUpdate: (
    drawingId: number,
    payload: { geometry: Record<string, unknown>; style: Record<string, unknown> },
  ) => void | Promise<void>;
};

export function useTextDrawingEdit(options: UseTextDrawingEditOptions) {
  const textEdit = ref<TextEditRequest>(null);

  function beginEdit(drawingId: number) {
    const drawing = options.drawings.value.find((d) => d.id === drawingId);
    if (!drawing || drawing.kind !== "text") return;
    const g = drawing.geometry;
    const w = Number(g.width);
    const h = Number(g.height);
    if (!(w > 0 && h > 0)) return;
    textEdit.value = {
      drawingId: drawing.id,
      x: Number(g.x),
      y: Number(g.y),
      width: w,
      height: h,
      text: String(g.text ?? ""),
      color: String(drawing.style.color ?? "#e11d48"),
      fontSize: Number(drawing.style.fontSize ?? 16),
    };
  }

  function cancelEdit() {
    textEdit.value = null;
  }

  function confirmEdit(payload: { text: string; width: number; height: number }) {
    const edit = textEdit.value;
    textEdit.value = null;
    const trimmed = payload.text.trim();
    if (!edit || !trimmed) return;
    const measured = measureTextBoxSize(trimmed, edit.fontSize);
    const width = Math.max(measured.width, payload.width, edit.width);
    const height = Math.max(measured.height, payload.height, edit.height);
    void options.onUpdate(edit.drawingId, {
      geometry: {
        x: edit.x,
        y: edit.y,
        width,
        height,
        text: trimmed,
      },
      style: { color: edit.color, fontSize: edit.fontSize },
    });
  }

  return {
    textEdit,
    beginEdit,
    cancelEdit,
    confirmEdit,
  };
}
