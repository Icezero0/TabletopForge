<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { Swords } from "lucide-vue-next";
import type { RoomToken } from "@/infra/api/rooms.api";
import { resolveMediaUrl } from "@/infra/media";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import { TOKEN_BAND_BASE, sceneBandZ } from "@/features/table/constants";
import { formatTokenPreview, tokenInitial, tokenSizePx } from "@/features/table/utils/tokenDisplay";

const props = defineProps<{
  token: RoomToken;
  gridCellFt: number;
  gridCellPx: number;
  selected?: boolean;
  inactive?: boolean;
  dimmed?: boolean;
  inCombat?: boolean;
  activeCombatTurn?: boolean;
  remoteSelectionColor?: string | null;
  remoteSelectionLabel?: string;
  remoteSelectionAvatarUrl?: string | null;
  gameRole?: import("@/features/room/types").GameRole | "unknown";
  characterDataHidden?: boolean;
  playerColorByUserId?: Map<number, string>;
}>();

const emit = defineEmits<{
  pointerdown: [event: PointerEvent];
  click: [event: MouseEvent];
  contextmenu: [event: MouseEvent];
}>();

const { t } = useI18n();

const assetIdRef = computed(() => props.token.asset_id);
const { url: imageUrl } = useAuthenticatedAssetUrl(assetIdRef);

const displaySize = computed(() =>
  tokenSizePx(props.token.width, props.gridCellFt, props.gridCellPx),
);

const initial = computed(() => tokenInitial(props.token.name));

const initialFontSize = computed(() => `${Math.max(14, Math.round(displaySize.value * 0.42))}px`);

function panelNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string" && value.trim()) {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function cumulativeDamageFromHp(current: unknown, max: unknown): number | null {
  const currentHp = panelNumber(current);
  const maxHp = panelNumber(max);
  if (currentHp == null || maxHp == null) return null;
  return Math.max(0, maxHp - currentHp);
}

const previewText = computed(() => {
  const panel = props.token.panel;
  const mode = typeof panel?.hide_data_mode === "string" ? panel.hide_data_mode : "inherit";
  const hidden =
    mode === "hidden" ||
    (mode !== "visible" && (panel?.hide_data === true || props.characterDataHidden === true));
  if (hidden) {
    const panelDamage =
      cumulativeDamageFromHp(panel?.hp_current, panel?.hp_max) ??
      cumulativeDamageFromHp(props.token.state_summary?.current_hp, props.token.state_summary?.max_hp);
    return formatTokenPreview({ damage_taken: panelDamage ?? props.token.state_summary?.damage_taken ?? 0 }, {
      damageLabel: t("room.characters.cumulativeDamage"),
    });
  }
  const summary = props.token.state_summary;
  if (!summary) return "";
  return formatTokenPreview(summary, {
    damageLabel: t("room.characters.cumulativeDamage"),
  });
});

const ownerColor = computed(() => {
  const ownerId = props.token.linked_character_owner_id;
  if (ownerId == null || !props.playerColorByUserId) return undefined;
  return props.playerColorByUserId.get(ownerId) ?? undefined;
});

const remoteAvatarSrc = computed(() => resolveMediaUrl(props.remoteSelectionAvatarUrl));

const remoteInitial = computed(() =>
  (props.remoteSelectionLabel || "?").trim().slice(0, 1).toUpperCase(),
);
</script>

<template>
  <div
    class="tokenWrap"
    :class="{ inactive, selected, dimmed }"
    :style="{
      transform: `translate(${token.x}px, ${token.y}px) rotate(${token.rotation}deg)`,
      zIndex: sceneBandZ(token.z_index, TOKEN_BAND_BASE),
    }"
    @pointerdown="emit('pointerdown', $event)"
    @click="emit('click', $event)"
    @contextmenu="emit('contextmenu', $event)"
  >
    <div
      class="tokenItem"
      :class="{ hasImage: !!imageUrl, remoteSelected: !!remoteSelectionLabel }"
      :style="{
        width: `${displaySize}px`,
        height: `${displaySize}px`,
        '--owner-color': ownerColor,
        '--remote-selection-color': remoteSelectionColor ?? 'var(--c-primary)',
      }"
    >
      <img v-if="imageUrl" class="tokenImage" :src="imageUrl" alt="" draggable="false" />
      <span v-else class="tokenInitial" :style="{ fontSize: initialFontSize }">{{ initial }}</span>
    </div>
    <div
      v-if="inCombat"
      class="combatBadge"
      :class="{ active: activeCombatTurn }"
      title="交战中"
      aria-label="交战中"
    >
      <Swords aria-hidden="true" />
    </div>
    <div
      v-if="remoteSelectionLabel"
      class="remoteSelectionLabel"
      :class="{ withCombatBadge: inCombat }"
      :style="{
        '--remote-selection-color': remoteSelectionColor ?? 'var(--c-primary)',
      }"
    >
      <span class="remoteAvatar">
        <img v-if="remoteAvatarSrc" :src="remoteAvatarSrc" alt="" draggable="false" />
        <span v-else>{{ remoteInitial }}</span>
      </span>
      <span class="remoteName">{{ remoteSelectionLabel }}</span>
    </div>
    <div v-if="previewText" class="previewBadge">{{ previewText }}</div>
  </div>
</template>

<style scoped>
.tokenWrap {
  position: absolute;
  left: 0;
  top: 0;
  user-select: none;
}

.tokenWrap:not(.selected) {
  transition: transform 80ms linear;
}

.tokenWrap.inactive {
  pointer-events: none;
}

.tokenWrap.dimmed {
  opacity: 0.7;
}

.tokenWrap:not(.inactive) {
  pointer-events: auto;
  cursor: default;
}

.tokenItem {
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-surface);
  border: 2px solid var(--owner-color, var(--c-border));
  box-sizing: border-box;
  pointer-events: none;
}

.tokenWrap.selected .tokenItem {
  border-color: var(--color-accent, #6b9fff);
}

.tokenItem.remoteSelected {
  border-color: var(--remote-selection-color, var(--c-primary));
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--remote-selection-color, var(--c-primary)) 42%, transparent),
    0 0 12px color-mix(in srgb, var(--remote-selection-color, var(--c-primary)) 48%, transparent);
}

.combatBadge {
  position: absolute;
  left: 50%;
  top: -18px;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border: 1px solid color-mix(in srgb, var(--c-border) 78%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-bg, #111) 84%, transparent);
  color: color-mix(in srgb, var(--c-text, #eee) 78%, transparent);
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.28);
  transform: translateX(-50%);
  pointer-events: none;
}

.combatBadge svg {
  width: 14px;
  height: 14px;
  stroke-width: 2.4;
}

.combatBadge.active {
  border-color: color-mix(in srgb, var(--c-primary) 76%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 24%, var(--c-bg, #111));
  color: var(--c-primary);
  box-shadow:
    0 0 0 2px color-mix(in srgb, var(--c-primary) 20%, transparent),
    0 4px 12px color-mix(in srgb, var(--c-primary) 30%, transparent);
}

.remoteSelectionLabel {
  position: absolute;
  left: 50%;
  bottom: 100%;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 168px;
  min-width: 0;
  padding: 2px 6px 2px 3px;
  border: 1px solid var(--remote-selection-color, var(--c-primary));
  border-radius: 999px;
  background: color-mix(in srgb, var(--remote-selection-color, var(--c-primary)) 18%, var(--c-surface));
  color: var(--c-text);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.2;
  box-shadow: 0 4px 12px rgb(0 0 0 / 0.26);
  transform: translate(-50%, -5px);
  pointer-events: none;
}

.remoteSelectionLabel.withCombatBadge {
  transform: translate(-50%, -29px);
}

.remoteAvatar {
  display: inline-grid;
  place-items: center;
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 999px;
  background: var(--remote-selection-color, var(--c-primary));
  color: white;
  font-size: 9px;
  font-weight: 800;
}

.remoteAvatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remoteName {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tokenImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}

.tokenInitial {
  font-weight: 600;
  pointer-events: none;
  line-height: 1;
}

.previewBadge {
  position: absolute;
  left: 50%;
  top: 100%;
  transform: translateX(-50%);
  margin-top: 2px;
  max-width: 160px;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 10px;
  line-height: 1.3;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background: color-mix(in srgb, var(--c-bg, #111) 75%, transparent);
  border: 1px solid var(--color-border-strong, #555);
  color: var(--c-text, #eee);
  pointer-events: none;
}
</style>
