<script setup lang="ts">
import { computed, toRef } from "vue";
import BaseAvatar from "@/ui/base/BaseAvatar.vue";
import { resolveMediaUrl } from "@/infra/media";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = withDefaults(
  defineProps<{
    kind?: "user" | "token";
    name?: string;
    avatarUrl?: string | null;
    assetId?: number | null;
  }>(),
  {
    kind: "user",
    name: "",
    avatarUrl: null,
    assetId: null,
  },
);

const assetIdRef = toRef(() => props.assetId);
const { url: assetUrl } = useAuthenticatedAssetUrl(assetIdRef);

const src = computed(() => {
  if (props.kind === "token") return assetUrl.value;
  return resolveMediaUrl(props.avatarUrl);
});
</script>

<template>
  <BaseAvatar
    :src="src"
    :name="name"
    shape="circle"
    size="xs"
    fit="cover"
  />
</template>
