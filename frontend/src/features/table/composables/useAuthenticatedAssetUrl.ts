import { onUnmounted, ref, watch, type Ref } from "vue";
import { http } from "@/infra/http/client";
import { assetContentUrl } from "@/infra/api/rooms.api";

const blobCache = new Map<number, string>();

export function invalidateBlobCache(assetId: number) {
  const url = blobCache.get(assetId);
  if (url) {
    URL.revokeObjectURL(url);
    blobCache.delete(assetId);
  }
}

export function useAuthenticatedAssetUrl(assetId: Ref<number | null | undefined>) {
  const url = ref("");
  const loading = ref(false);

  async function load(id: number) {
    if (blobCache.has(id)) {
      url.value = blobCache.get(id)!;
      return;
    }
    loading.value = true;
    try {
      const { data } = await http.get(assetContentUrl(id), { responseType: "blob" });
      const objectUrl = URL.createObjectURL(data);
      blobCache.set(id, objectUrl);
      url.value = objectUrl;
    } catch {
      url.value = "";
    } finally {
      loading.value = false;
    }
  }

  watch(
    assetId,
    (id) => {
      if (!id) {
        url.value = "";
        return;
      }
      void load(id);
    },
    { immediate: true },
  );

  onUnmounted(() => {
    // URLs kept in cache for session reuse
  });

  return { url, loading };
}
