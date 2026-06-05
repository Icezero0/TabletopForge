import {
  MusicalNoteIcon,
  PhotoIcon,
  MapIcon,
} from "@heroicons/vue/24/outline";
import type { Component } from "vue";
import type { ResourceType } from "@/infra/api/library.api";

export type ResourceTypeMeta = {
  isImage: boolean;
  isAudio: boolean;
  icon: Component;
  labelKey: string;
};

export const RESOURCE_TYPE_META: Record<ResourceType, ResourceTypeMeta> = {
  map_background: {
    isImage: true,
    isAudio: false,
    icon: MapIcon,
    labelKey: "library.types.mapBackground",
  },
};

export const RESOURCE_TYPE_OPTIONS: { value: ResourceType; labelKey: string }[] = [
  { value: "map_background", labelKey: "library.types.mapBackground" },
];

export const FALLBACK_RESOURCE_META: ResourceTypeMeta = {
  isImage: false,
  isAudio: false,
  icon: PhotoIcon,
  labelKey: "library.types.unknown",
};

export function getResourceTypeMeta(type: ResourceType): ResourceTypeMeta {
  return RESOURCE_TYPE_META[type] ?? FALLBACK_RESOURCE_META;
}

export { MusicalNoteIcon, PhotoIcon };
