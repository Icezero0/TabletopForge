import { http } from "@/infra/http/client";

export type AssetResponse = {
  id: number;
  asset_type: string;
  owner_id: number | null;
  original_filename: string | null;
  content_type: string;
  size_bytes: number;
  url: string;
  created_at: string;
};

export async function uploadAsset(file: File, assetType: "image" | "audio"): Promise<AssetResponse> {
  const form = new FormData();
  form.append("asset_type", assetType);
  form.append("file", file);
  const { data } = await http.post<AssetResponse>("/assets", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
