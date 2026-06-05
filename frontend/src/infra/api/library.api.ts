import { http } from "@/infra/http/client";

export type ResourceType = "map_background" | "token" | "sound";

export type LibraryResource = {
  id: number;
  owner_id: number;
  type: ResourceType;
  name: string;
  primary_asset_id: number | null;
  meta: Record<string, unknown>;
  usage_count: number;
  created_at: string;
  updated_at: string | null;
};

export type LibraryResourceListResponse = {
  items: LibraryResource[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export async function getLibraryResources(params?: {
  type?: ResourceType | null;
  page?: number;
  page_size?: number;
}) {
  const { data } = await http.get<LibraryResourceListResponse>(
    "/library/resources",
    { params },
  );
  return data;
}

export async function getLibraryResource(id: number) {
  const { data } = await http.get<LibraryResource>(`/library/resources/${id}`);
  return data;
}

export async function createLibraryResource(payload: {
  type: ResourceType;
  name: string;
  image?: File;
  audio?: File;
  tags?: string[];
  comment?: string;
}) {
  const form = new FormData();
  form.append("type", payload.type);
  form.append("name", payload.name);
  if (payload.image) form.append("image", payload.image);
  if (payload.audio) form.append("audio", payload.audio);
  if (payload.tags) payload.tags.forEach((tag) => form.append("tags", tag));
  if (payload.comment) form.append("comment", payload.comment);
  const { data } = await http.post<LibraryResource>("/library/resources", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function patchLibraryResource(
  id: number,
  payload: { name: string; tags?: string[]; comment?: string },
) {
  const { data } = await http.patch<LibraryResource>(`/library/resources/${id}`, payload);
  return data;
}

export async function deleteLibraryResource(id: number) {
  await http.delete(`/library/resources/${id}`);
}
