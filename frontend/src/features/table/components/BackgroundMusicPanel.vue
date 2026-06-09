<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import {
  ArrowPathIcon,
  ArrowsRightLeftIcon,
  BackwardIcon,
  ListBulletIcon,
  MusicalNoteIcon,
  PauseIcon,
  PlayIcon,
  PlusIcon,
  SpeakerWaveIcon,
} from "@heroicons/vue/24/outline";
import { createLibraryResource, getLibraryResources, type LibraryResource } from "@/infra/api/library.api";
import type { RoomMusicState, RoomMusicTrack } from "@/infra/api/rooms.api";
import { getBackendErrorMessage } from "@/infra/http/client";
import type { GameRole } from "@/features/room/types";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import { useTabletopStore } from "@/stores/tabletop.store";

const props = defineProps<{
  roomId: number;
  gameRole: GameRole | "unknown";
  musicState: RoomMusicState | null;
}>();

const emit = defineEmits<{
  error: [message: string];
}>();

const { t } = useI18n();
const tabletopStore = useTabletopStore();

const audioEl = ref<HTMLAudioElement | null>(null);
const soundResources = ref<LibraryResource[]>([]);
const resourcesLoading = ref(false);
const uploading = ref(false);
const saving = ref(false);
const soundSearch = ref("");
const localTime = ref(0);
const duration = ref(0);
const seekingValue = ref<number | null>(null);
const localVolume = ref(readVolume());
const volumeOpen = ref(false);
const playlistOpen = ref(false);
const libraryOpen = ref(false);

const isGm = computed(() => props.gameRole === "GM");
const musicState = computed(() => props.musicState ?? defaultMusicState());
const tracks = computed(() => musicState.value.tracks ?? []);
const currentTrack = computed(() => {
  const list = tracks.value;
  if (!list.length) return null;
  return list[Math.min(Math.max(0, musicState.value.current_index), list.length - 1)] ?? null;
});
const currentAssetId = computed(() => currentTrack.value?.asset_id ?? null);
const { url: currentAudioUrl } = useAuthenticatedAssetUrl(currentAssetId);
const displayTime = computed(() => seekingValue.value ?? localTime.value);
const filteredSoundResources = computed(() => {
  const q = soundSearch.value.trim().toLowerCase();
  if (!q) return soundResources.value;
  return soundResources.value.filter((resource) => resource.name.toLowerCase().includes(q));
});
const loopModeLabel = computed(() => {
  if (musicState.value.loop_mode === "single") return t("table.music.singleLoop");
  if (musicState.value.loop_mode === "shuffle") return t("table.music.shuffle");
  return t("table.music.listLoop");
});
const loopModeIcon = computed(() => {
  if (musicState.value.loop_mode === "single") return ArrowPathIcon;
  if (musicState.value.loop_mode === "shuffle") return ArrowsRightLeftIcon;
  return ArrowPathIcon;
});

function defaultMusicState(): RoomMusicState {
  return {
    tracks: [],
    current_index: 0,
    playing: false,
    position: 0,
    loop_mode: "list",
    updated_at: null,
  };
}

function readVolume() {
  const raw = window.localStorage.getItem("tabletopforge.music.volume");
  const value = raw == null ? 0.5 : Number(raw);
  return Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0.5;
}

function persistVolume(value: number) {
  const next = Math.min(1, Math.max(0, value));
  localVolume.value = next;
  window.localStorage.setItem("tabletopforge.music.volume", String(next));
  if (audioEl.value) audioEl.value.volume = next;
}

function formatTime(seconds: number) {
  const safe = Math.max(0, Math.floor(seconds || 0));
  const m = Math.floor(safe / 60);
  const s = safe % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function projectedPosition(state: RoomMusicState) {
  if (!state.playing || !state.updated_at) return state.position || 0;
  const updatedAt = Date.parse(state.updated_at);
  if (!Number.isFinite(updatedAt)) return state.position || 0;
  return (state.position || 0) + Math.max(0, (Date.now() - updatedAt) / 1000);
}

async function fetchSoundResources() {
  resourcesLoading.value = true;
  try {
    const res = await getLibraryResources({ type: "sound", page: 1, page_size: 100 });
    soundResources.value = res.items;
  } catch (e) {
    emit("error", getBackendErrorMessage(e) || t("table.music.loadFailed"));
  } finally {
    resourcesLoading.value = false;
  }
}

function withTimestamp(state: RoomMusicState): RoomMusicState {
  return { ...state, updated_at: new Date().toISOString() };
}

async function saveMusicState(next: RoomMusicState | null) {
  if (!isGm.value || saving.value) return;
  saving.value = true;
  try {
    await tabletopStore.updateSettings(props.roomId, { music_state: next });
  } catch (e) {
    emit("error", getBackendErrorMessage(e) || t("table.music.saveFailed"));
  } finally {
    saving.value = false;
  }
}

function trackFromResource(resource: LibraryResource): RoomMusicTrack | null {
  if (resource.type !== "sound" || resource.primary_asset_id == null) return null;
  return {
    library_resource_id: resource.id,
    asset_id: resource.primary_asset_id,
    name: resource.name,
  };
}

async function addResource(resource: LibraryResource) {
  const track = trackFromResource(resource);
  if (!track) return;
  const state = musicState.value;
  if (state.tracks.some((item) => item.library_resource_id === track.library_resource_id)) return;
  await saveMusicState(withTimestamp({
    ...state,
    tracks: [...state.tracks, track],
    current_index: state.tracks.length ? state.current_index : 0,
  }));
}

async function removeTrack(index: number) {
  const state = musicState.value;
  const nextTracks = state.tracks.filter((_, i) => i !== index);
  const nextIndex = nextTracks.length ? Math.min(state.current_index, nextTracks.length - 1) : 0;
  await saveMusicState(withTimestamp({
    ...state,
    tracks: nextTracks,
    current_index: nextIndex,
    playing: nextTracks.length ? state.playing : false,
    position: nextIndex === state.current_index ? state.position : 0,
  }));
}

async function setTrack(index: number) {
  const state = musicState.value;
  if (!state.tracks[index]) return;
  await saveMusicState(withTimestamp({ ...state, current_index: index, position: 0 }));
}

async function setPlaying(playing: boolean) {
  const state = musicState.value;
  if (!state.tracks.length) return;
  await saveMusicState(withTimestamp({
    ...state,
    playing,
    position: Math.min(duration.value || Infinity, localTime.value || projectedPosition(state)),
  }));
}

async function seekTo(raw: number) {
  const state = musicState.value;
  const position = Math.max(0, raw || 0);
  seekingValue.value = null;
  await saveMusicState(withTimestamp({ ...state, position }));
}

async function cycleLoopMode() {
  const state = musicState.value;
  const next = state.loop_mode === "list"
    ? "single"
    : state.loop_mode === "single"
      ? "shuffle"
      : "list";
  await saveMusicState(withTimestamp({ ...state, loop_mode: next }));
}

async function stepTrack(delta: number) {
  const state = musicState.value;
  if (!state.tracks.length) return;
  let next = state.current_index + delta;
  if (next < 0) next = state.tracks.length - 1;
  if (next >= state.tracks.length) next = 0;
  await saveMusicState(withTimestamp({ ...state, current_index: next, position: 0 }));
}

async function handleEnded() {
  if (!isGm.value) return;
  const state = musicState.value;
  if (!state.tracks.length) return;
  if (state.loop_mode === "single") {
    await saveMusicState(withTimestamp({ ...state, position: 0, playing: true }));
    return;
  }
  const nextIndex = state.loop_mode === "shuffle"
    ? Math.floor(Math.random() * state.tracks.length)
    : (state.current_index + 1) % state.tracks.length;
  await saveMusicState(withTimestamp({
    ...state,
    current_index: nextIndex,
    position: 0,
    playing: true,
  }));
}

async function uploadAudio(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  input.value = "";
  if (!file) return;
  if (!file.type.startsWith("audio/")) {
    emit("error", t("library.upload.invalidAudioType"));
    return;
  }
  uploading.value = true;
  try {
    const name = file.name.replace(/\.[^.]+$/, "") || file.name;
    const resource = await createLibraryResource({ type: "sound", name, audio: file });
    soundResources.value = [resource, ...soundResources.value.filter((item) => item.id !== resource.id)];
    await addResource(resource);
  } catch (e) {
    emit("error", getBackendErrorMessage(e) || t("table.music.uploadFailed"));
  } finally {
    uploading.value = false;
  }
}

function togglePanel(panel: "volume" | "playlist" | "library") {
  volumeOpen.value = panel === "volume" ? !volumeOpen.value : false;
  playlistOpen.value = panel === "playlist" ? !playlistOpen.value : false;
  libraryOpen.value = panel === "library" ? !libraryOpen.value : false;
}

function onTimeUpdate() {
  if (!audioEl.value || seekingValue.value != null) return;
  localTime.value = audioEl.value.currentTime || 0;
}

function onLoadedMetadata() {
  if (!audioEl.value) return;
  duration.value = Number.isFinite(audioEl.value.duration) ? audioEl.value.duration : 0;
  void syncAudio();
}

async function syncAudio() {
  const audio = audioEl.value;
  if (!audio) return;
  audio.volume = localVolume.value;
  const state = musicState.value;
  if (!currentAudioUrl.value || !currentTrack.value) {
    audio.pause();
    localTime.value = 0;
    return;
  }
  await nextTick();
  const target = Math.max(0, Math.min(duration.value || Infinity, projectedPosition(state)));
  if (Number.isFinite(target) && Math.abs((audio.currentTime || 0) - target) > 0.75) {
    audio.currentTime = target;
    localTime.value = target;
  }
  if (state.playing) {
    try {
      await audio.play();
    } catch {
      // Browsers may block autoplay before the user interacts with the page.
    }
  } else {
    audio.pause();
  }
}

watch(localVolume, (value) => {
  if (audioEl.value) audioEl.value.volume = value;
});

watch(
  () => [
    currentAudioUrl.value,
    props.musicState?.current_index,
    props.musicState?.playing,
    props.musicState?.position,
    props.musicState?.updated_at,
  ],
  () => { void syncAudio(); },
  { immediate: true },
);

watch(
  isGm,
  (value) => {
    if (value && soundResources.value.length === 0) void fetchSoundResources();
  },
  { immediate: true },
);
</script>

<template>
  <div class="musicModule">
    <audio
      ref="audioEl"
      :src="currentAudioUrl"
      preload="auto"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="handleEnded"
    />

    <div class="musicBody">
      <div class="nowPill" :title="currentTrack?.name ?? t('table.music.noTrack')">
        <MusicalNoteIcon class="miniIcon" aria-hidden="true" />
        <span class="trackName">{{ currentTrack?.name ?? t("table.music.noTrack") }}</span>
      </div>

      <template v-if="isGm">
        <button
          type="button"
          class="iconBtn"
          :title="'上一首'"
          :disabled="!tracks.length || saving"
          @click="stepTrack(-1)"
        >
          <BackwardIcon class="miniIcon" aria-hidden="true" />
        </button>
        <button
          type="button"
          class="iconBtn primary"
          :title="musicState.playing ? '暂停' : '播放'"
          :disabled="!tracks.length || saving"
          @click="setPlaying(!musicState.playing)"
        >
          <PauseIcon v-if="musicState.playing" class="miniIcon" aria-hidden="true" />
          <PlayIcon v-else class="miniIcon" aria-hidden="true" />
        </button>
        <button
          type="button"
          class="iconBtn nextBtn"
          :title="'下一首'"
          :disabled="!tracks.length || saving"
          @click="stepTrack(1)"
        >
          <BackwardIcon class="miniIcon" aria-hidden="true" />
        </button>

        <div class="progressGroup">
          <span class="timeText">{{ formatTime(displayTime) }}</span>
          <input
            class="progress"
            type="range"
            min="0"
            :max="Math.max(1, Math.floor(duration || 0))"
            step="1"
            :value="Math.round(displayTime)"
            :disabled="!tracks.length"
            @input="seekingValue = Number(($event.target as HTMLInputElement).value)"
            @change="seekTo(Number(($event.target as HTMLInputElement).value))"
          />
          <span class="timeText">{{ formatTime(duration) }}</span>
        </div>

        <button
          type="button"
          class="iconBtn"
          :disabled="saving"
          :title="`${t('table.music.loopMode')}：${loopModeLabel}`"
          @click="cycleLoopMode"
        >
          <span class="loopIconWrap">
            <component :is="loopModeIcon" class="miniIcon" aria-hidden="true" />
            <span v-if="musicState.loop_mode === 'single'" class="loopOne">1</span>
          </span>
        </button>

        <div class="popoverWrap">
          <button type="button" class="iconBtn" :title="t('table.music.playlist')" @click="togglePanel('playlist')">
            <ListBulletIcon class="miniIcon" aria-hidden="true" />
          </button>
          <div v-if="playlistOpen" class="musicPopover listPopover">
            <div
              v-for="(track, index) in tracks"
              :key="`${track.library_resource_id}-${index}`"
              class="trackRow"
              :class="{ active: index === musicState.current_index }"
            >
              <button type="button" class="trackSelect" @click="setTrack(index)">
                <span>{{ track.name }}</span>
              </button>
              <button type="button" class="removeBtn" @click.stop="removeTrack(index)">×</button>
            </div>
            <div v-if="!tracks.length" class="emptyHint">{{ t("table.music.emptyPlaylist") }}</div>
          </div>
        </div>

        <div class="popoverWrap">
          <button type="button" class="iconBtn" :title="t('table.music.library')" @click="togglePanel('library')">
            <PlusIcon class="miniIcon" aria-hidden="true" />
          </button>
          <div v-if="libraryOpen" class="musicPopover listPopover">
            <div class="sourceActions">
              <label class="uploadChoice">
                <span class="audioThumb">
                  <PlusIcon class="miniIcon" aria-hidden="true" />
                </span>
                <span class="choiceText">
                  <span class="choiceTitle">{{ uploading ? t("common.loading") : t("table.music.upload") }}</span>
                  <span class="choiceHint">{{ t("table.music.uploadHint") }}</span>
                </span>
                <input type="file" accept="audio/*" :disabled="uploading || saving" @change="uploadAudio" />
              </label>
            </div>
            <div class="libraryToolbar">
              <input
                v-model="soundSearch"
                class="musicSearch"
                :placeholder="t('table.music.searchPlaceholder')"
              />
              <button type="button" class="musicBtn" :disabled="resourcesLoading" @click="fetchSoundResources">
                {{ t("table.music.refreshLibrary") }}
              </button>
            </div>
            <button
              v-for="resource in filteredSoundResources"
              :key="resource.id"
              type="button"
              class="resourceRow"
              :disabled="resource.primary_asset_id == null"
              @click="addResource(resource)"
            >
              <span class="audioThumb">
                <MusicalNoteIcon class="miniIcon" aria-hidden="true" />
              </span>
              <span>{{ resource.name }}</span>
              <PlusIcon class="miniIcon addIcon" aria-hidden="true" />
            </button>
            <div v-if="!resourcesLoading && !filteredSoundResources.length" class="emptyHint">{{ t("table.music.emptyLibrary") }}</div>
            <div v-if="resourcesLoading" class="emptyHint">{{ t("common.loading") }}</div>
          </div>
        </div>
      </template>

      <div class="popoverWrap">
        <button type="button" class="iconBtn" :title="t('table.music.volume')" @click="togglePanel('volume')">
          <SpeakerWaveIcon class="miniIcon" aria-hidden="true" />
        </button>
        <div v-if="volumeOpen" class="musicPopover volumePopover">
          <input
            class="verticalVolume"
            type="range"
            min="0"
            max="100"
            step="1"
            :value="Math.round(localVolume * 100)"
            @input="persistVolume(Number(($event.target as HTMLInputElement).value) / 100)"
          />
          <span class="percent">{{ Math.round(localVolume * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.musicModule {
  max-width: min(760px, calc(100vw - 48px));
}

.musicBody {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 8px;
}

.nowPill,
.sourceActions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nowPill {
  min-width: 118px;
  max-width: 180px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-bg-subtle) 56%, transparent);
}

.trackName {
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.timeText,
.percent,
.emptyHint {
  color: var(--c-text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.progressGroup {
  display: grid;
  grid-template-columns: auto minmax(90px, 150px) auto;
  align-items: center;
  gap: 6px;
}

.progress {
  width: 100%;
  min-width: 0;
  accent-color: var(--c-primary);
}

.musicBtn,
.iconBtn {
  height: 32px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.musicBtn:hover:not(:disabled),
.iconBtn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--c-primary) 10%, transparent);
  color: var(--c-text);
}

.iconBtn {
  width: 32px;
  display: inline-grid;
  place-items: center;
  padding: 0;
}

.musicBtn.primary,
.iconBtn.primary {
  background: color-mix(in srgb, var(--c-primary) 22%, transparent);
  border-color: color-mix(in srgb, var(--c-primary) 35%, transparent);
  color: var(--c-text);
}

.musicBtn:disabled,
.resourceRow:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.uploadChoice input {
  display: none;
}

.nextBtn .miniIcon {
  transform: scaleX(-1);
}

.miniIcon {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
}

.loopIconWrap {
  position: relative;
  display: inline-grid;
  place-items: center;
}

.loopOne {
  position: absolute;
  right: -3px;
  bottom: -4px;
  min-width: 10px;
  height: 10px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: color-mix(in srgb, var(--c-surface) 88%, var(--c-bg));
  color: var(--c-text);
  font-size: 8px;
  font-weight: 800;
  line-height: 1;
}

.popoverWrap {
  position: relative;
  display: inline-flex;
}

.musicPopover {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  z-index: 70;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--c-surface) 97%, var(--c-bg));
  box-shadow: 0 16px 34px rgb(0 0 0 / 28%);
}

.listPopover {
  display: grid;
  gap: 6px;
  width: 360px;
  max-height: 320px;
  overflow: auto;
  padding: 8px;
  transform: translateX(-50%);
}

.volumePopover {
  display: grid;
  justify-items: center;
  gap: 8px;
  width: 46px;
  height: 150px;
  padding: 10px 8px 8px;
  transform: translateX(-50%);
}

.verticalVolume {
  width: 20px;
  height: 104px;
  accent-color: var(--c-primary);
  writing-mode: vertical-lr;
  direction: rtl;
  appearance: slider-vertical;
}

.trackRow,
.resourceRow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  min-height: 30px;
  padding: 4px 8px;
  border: 1px solid var(--c-border);
  border-radius: 7px;
  background: color-mix(in srgb, var(--c-bg-subtle) 70%, transparent);
  color: var(--c-text);
  text-align: left;
  cursor: pointer;
}

.trackRow {
  padding: 4px;
}

.resourceRow,
.uploadChoice {
  grid-template-columns: auto minmax(0, 1fr) auto;
  min-height: 42px;
  padding: 7px 9px;
  border-radius: 8px;
  background: var(--c-bg-subtle);
}

.uploadChoice {
  display: grid;
  align-items: center;
  gap: 9px;
  border: 1px solid var(--c-border);
  color: var(--c-text);
  cursor: pointer;
}

.uploadChoice:hover,
.resourceRow:hover:not(:disabled) {
  border-color: var(--c-accent);
}

.sourceActions,
.libraryToolbar {
  display: grid;
  gap: 8px;
}

.libraryToolbar {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.musicSearch {
  min-width: 0;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-surface);
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
}

.audioThumb {
  width: 30px;
  height: 30px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-accent) 15%, var(--c-bg));
  color: var(--c-accent);
  flex-shrink: 0;
}

.choiceText {
  min-width: 0;
  display: grid;
  gap: 2px;
  text-align: left;
}

.choiceTitle {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text);
}

.choiceHint {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 11px;
  color: var(--c-text-muted);
}

.addIcon {
  color: var(--c-text-muted);
}

.trackSelect {
  min-width: 0;
  height: 22px;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.trackSelect span {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  display: block;
}

.resourceRow > span:nth-child(2) {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text);
}

.trackRow.active {
  border-color: color-mix(in srgb, var(--c-primary) 48%, var(--c-border));
  background: color-mix(in srgb, var(--c-primary) 14%, transparent);
}

.removeBtn {
  width: 22px;
  height: 22px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-muted);
  cursor: pointer;
}
</style>
