import {
  MapIcon,
  MusicalNoteIcon,
  PhotoIcon,
  SpeakerWaveIcon,
  UserCircleIcon,
} from "@heroicons/vue/24/outline";
import type { Component } from "vue";
import type { ResourceType } from "@/infra/api/library.api";

export type ResourceTypeMeta = {
  isImage: boolean;
  isAudio: boolean;
  hasTags: boolean;
  hasComment: boolean;
  icon: Component;
  labelKey: string;
};

export const RESOURCE_TYPE_META: Record<ResourceType, ResourceTypeMeta> = {
  map_background: {
    isImage: true,
    isAudio: false,
    hasTags: false,
    hasComment: true,
    icon: MapIcon,
    labelKey: "library.types.mapBackground",
  },
  token: {
    isImage: true,
    isAudio: false,
    hasTags: true,
    hasComment: true,
    icon: UserCircleIcon,
    labelKey: "library.types.token",
  },
  sound: {
    isImage: false,
    isAudio: true,
    hasTags: true,
    hasComment: true,
    icon: SpeakerWaveIcon,
    labelKey: "library.types.sound",
  },
};

export const RESOURCE_TYPE_OPTIONS: { value: ResourceType; labelKey: string }[] = [
  { value: "map_background", labelKey: "library.types.mapBackground" },
  { value: "token", labelKey: "library.types.token" },
  { value: "sound", labelKey: "library.types.sound" },
];

export const FALLBACK_RESOURCE_META: ResourceTypeMeta = {
  isImage: false,
  isAudio: false,
  hasTags: false,
  hasComment: false,
  icon: PhotoIcon,
  labelKey: "library.types.unknown",
};

export function getResourceTypeMeta(type: ResourceType): ResourceTypeMeta {
  return RESOURCE_TYPE_META[type] ?? FALLBACK_RESOURCE_META;
}

export { MusicalNoteIcon, PhotoIcon };
