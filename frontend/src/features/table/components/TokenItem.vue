<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { RoomToken } from "@/infra/api/rooms.api";
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
  gameRole?: import("@/features/room/types").GameRole | "unknown";
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

const previewText = computed(() => {
  const summary = props.token.state_summary;
  if (!summary) return "";
  return formatTokenPreview(summary, {
    damageLabel: t("room.characters.damageTakenShort"),
  });
});

const ownerColor = computed(() => {
  const ownerId = props.token.linked_character_owner_id;
  if (ownerId == null || !props.playerColorByUserId) return undefined;
  return props.playerColorByUserId.get(ownerId) ?? undefined;
});
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
      :class="{ hasImage: !!imageUrl }"
      :style="{
        width: `${displaySize}px`,
        height: `${displaySize}px`,
        '--owner-color': ownerColor,
      }"
    >
      <img v-if="imageUrl" class="tokenImage" :src="imageUrl" alt="" draggable="false" />
      <span v-else class="tokenInitial" :style="{ fontSize: initialFontSize }">{{ initial }}</span>
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
