function resolveApiOrigin() {
  const configured = import.meta.env.VITE_API_ORIGIN?.trim();
  if (configured) return configured.replace(/\/$/, "");
  if (import.meta.env.DEV && typeof window !== "undefined") {
    return window.location.origin;
  }
  return "http://localhost:8000";
}

const API_ORIGIN = resolveApiOrigin();

export function resolveMediaUrl(path?: string | null) {
  if (!path) return "";

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  if (path.startsWith("//")) {
    return `${window.location.protocol}${path}`;
  }

  if (path.startsWith("/")) {
    return `${API_ORIGIN}${path}`;
  }

  return `${API_ORIGIN}/${path}`;
}
