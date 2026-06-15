import { onUnmounted, ref, watch, type Ref } from "vue";
import {
  deleteCachedAssetBlob,
  getCachedAssetBlob,
  putCachedAssetBlob,
} from "@/infra/cache/assetBlobCache";
import { http } from "@/infra/http/client";
import { assetContentUrl } from "@/infra/api/rooms.api";

const blobCache = new Map<number, string>();
const loadingPromises = new Map<number, Promise<string>>();

export function invalidateBlobCache(assetId: number) {
  const url = blobCache.get(assetId);
  if (url) {
    URL.revokeObjectURL(url);
    blobCache.delete(assetId);
  }
  void deleteCachedAssetBlob(assetId);
}

export function useAuthenticatedAssetUrl(assetId: Ref<number | null | undefined>) {
  const url = ref("");
  const loading = ref(false);
  let requestVersion = 0;

  function setObjectUrl(id: number, blob: Blob) {
    const objectUrl = URL.createObjectURL(blob);
    blobCache.set(id, objectUrl);
    return objectUrl;
  }

  async function resolveObjectUrl(id: number) {
    if (blobCache.has(id)) {
      return blobCache.get(id)!;
    }

    const cachedBlob = await getCachedAssetBlob(id);
    if (cachedBlob) {
      return setObjectUrl(id, cachedBlob);
    }

    const existing = loadingPromises.get(id);
    if (existing) return existing;

    const promise = http
      .get(assetContentUrl(id), {
        responseType: "blob",
        timeout: 120000,
      })
      .then(async ({ data }) => {
        await putCachedAssetBlob(id, data);
        return setObjectUrl(id, data);
      })
      .finally(() => {
        loadingPromises.delete(id);
      });

    loadingPromises.set(id, promise);
    return promise;
  }

  async function load(id: number) {
    const version = ++requestVersion;
    loading.value = true;
    try {
      const objectUrl = await resolveObjectUrl(id);
      if (version === requestVersion && assetId.value === id) {
        url.value = objectUrl;
      }
    } catch {
      if (version === requestVersion) {
        url.value = "";
      }
    } finally {
      if (version === requestVersion) {
        loading.value = false;
      }
    }
  }

  watch(
    assetId,
    (id) => {
      requestVersion += 1;
      if (!id) {
        url.value = "";
        loading.value = false;
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
