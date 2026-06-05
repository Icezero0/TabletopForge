import { ref } from "vue";
import {
  getLibraryResources,
  createLibraryResource,
  patchLibraryResource,
  deleteLibraryResource,
  type LibraryResource,
  type ResourceType,
} from "@/infra/api/library.api";
import { invalidateBlobCache } from "@/features/table/composables/useAuthenticatedAssetUrl";

export function useLibraryResources() {
  const items = ref<LibraryResource[]>([]);
  const total = ref(0);
  const page = ref(1);
  const totalPages = ref(1);
  const pageSize = 20;

  const isLoading = ref(false);
  const error = ref("");

  const typeFilter = ref<ResourceType | null>(null);

  async function fetchPage(p = 1) {
    isLoading.value = true;
    error.value = "";
    try {
      const res = await getLibraryResources({
        type: typeFilter.value ?? undefined,
        page: p,
        page_size: pageSize,
      });
      items.value = res.items;
      total.value = res.total;
      page.value = res.page;
      totalPages.value = res.total_pages;
    } catch {
      error.value = "library.errors.loadFailed";
    } finally {
      isLoading.value = false;
    }
  }

  async function refresh() {
    await fetchPage(page.value);
  }

  async function create(payload: {
    type: ResourceType;
    name: string;
    image?: File;
    audio?: File;
    tags?: string[];
    comment?: string;
  }) {
    const resource = await createLibraryResource(payload);
    await fetchPage(1);
    return resource;
  }

  async function update(id: number, name: string, tags?: string[], comment?: string) {
    const updated = await patchLibraryResource(id, { name, tags, comment });
    const idx = items.value.findIndex((r) => r.id === id);
    if (idx !== -1) items.value[idx] = updated;
    return updated;
  }

  async function remove(id: number) {
    const assetId = items.value.find((r) => r.id === id)?.primary_asset_id ?? null;
    await deleteLibraryResource(id);
    if (assetId !== null) invalidateBlobCache(assetId);
    await fetchPage(page.value);
  }

  return {
    items,
    total,
    page,
    totalPages,
    pageSize,
    isLoading,
    error,
    typeFilter,
    fetchPage,
    refresh,
    create,
    update,
    remove,
  };
}
