<script setup lang="ts">
import { toRef } from "vue";
import BaseAvatar from "@/ui/base/BaseAvatar.vue";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";

const props = withDefaults(
  defineProps<{
    name?: string;
    assetId?: number | null;
    size?: "xs" | "sm" | "md";
  }>(),
  {
    name: "",
    assetId: null,
    size: "sm",
  },
);

const assetIdRef = toRef(() => props.assetId);
const { url } = useAuthenticatedAssetUrl(assetIdRef);
</script>

<template>
  <BaseAvatar
    :src="url"
    :name="name"
    shape="circle"
    :size="size"
    fit="cover"
  />
</template>
