import { ref } from "vue";
import {
  getCharacters,
  deleteCharacter,
  type Character,
} from "@/infra/api/character.api";

export function useCharacters() {
  const items = ref<Character[]>([]);
  const total = ref(0);
  const page = ref(1);
  const totalPages = ref(1);
  const pageSize = 20;
  const isLoading = ref(false);
  const error = ref("");

  async function fetchPage(p = 1) {
    isLoading.value = true;
    error.value = "";
    try {
      const res = await getCharacters({ page: p, page_size: pageSize });
      items.value = res.items;
      total.value = res.total;
      page.value = res.page;
      totalPages.value = res.total_pages;
    } catch {
      error.value = "character.errors.loadFailed";
    } finally {
      isLoading.value = false;
    }
  }

  async function remove(id: number) {
    await deleteCharacter(id);
    await fetchPage(page.value);
  }

  return { items, total, page, totalPages, pageSize, isLoading, error, fetchPage, remove };
}
