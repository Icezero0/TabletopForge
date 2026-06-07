import type { GameRole } from "@/features/room/types";
import type { RoomToken, TokenStateSummary } from "@/infra/api/rooms.api";

export function tokenInitial(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return "?";
  const first = trimmed.charAt(0);
  if (/[\u4e00-\u9fff]/.test(first)) return first;
  return first.toUpperCase();
}

export function tokenSizePx(widthFt: number, gridCellFt: number, gridCellPx: number): number {
  if (!gridCellFt) return gridCellPx;
  return (widthFt / gridCellFt) * gridCellPx;
}

export function canManageToken(
  token: RoomToken,
  gameRole: GameRole | "unknown",
  currentUserId: number | null | undefined,
  characterOwnerById: Map<number, number>,
): boolean {
  if (gameRole === "GM") return true;
  if (gameRole !== "PL" || currentUserId == null) return false;
  if (token.linked_character_id != null) {
    const ownerId =
      characterOwnerById.get(token.linked_character_id) ??
      token.linked_character_owner_id ??
      null;
    return ownerId === currentUserId;
  }
  return token.owner_user_id === currentUserId;
}

export function canInspectToken(token: RoomToken): boolean {
  return token.linked_character_id != null;
}

export function canSpawnCharacter(
  entry: { owner_id: number },
  gameRole: GameRole | "unknown",
  currentUserId: number | null | undefined,
): boolean {
  if (gameRole === "GM") return true;
  if (gameRole === "PL") {
    return currentUserId != null && entry.owner_id === currentUserId;
  }
  return false;
}

type StatePreviewInput = {
  current_hp?: number | null;
  max_hp?: number | null;
  ac?: number | null;
  armor_class?: number | null;
  pp?: number | null;
  damage_taken?: number | null;
};

function isDamageOnlyView(summary: StatePreviewInput): boolean {
  return (
    summary.current_hp == null &&
    summary.max_hp == null &&
    (summary.ac ?? summary.armor_class) == null &&
    summary.damage_taken != null
  );
}

export function formatTokenPreview(
  summary: StatePreviewInput,
  options?: { damageLabel?: string },
): string {
  if (isDamageOnlyView(summary)) {
    const label = options?.damageLabel ?? "DMG";
    return `${label} ${summary.damage_taken ?? 0}`;
  }

  const parts: string[] = [];
  if (summary.current_hp != null || summary.max_hp != null) {
    parts.push(`HP ${summary.current_hp ?? "?"}/${summary.max_hp ?? "?"}`);
  }
  const ac = summary.ac ?? summary.armor_class ?? null;
  if (ac != null) parts.push(`AC ${ac}`);
  if (summary.pp != null) parts.push(`PP ${summary.pp}`);
  return parts.join(" · ");
}

export function pickCharacterStateSummaryForRole(
  payload: {
    state_summary: TokenStateSummary;
    state_summary_public?: TokenStateSummary;
  },
  gameRole: GameRole | "unknown",
): TokenStateSummary {
  if (gameRole !== "GM" && payload.state_summary_public) {
    return payload.state_summary_public;
  }
  return payload.state_summary;
}
