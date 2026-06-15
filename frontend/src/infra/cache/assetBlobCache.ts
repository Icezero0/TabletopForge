const DB_NAME = "tabletopforge-assets";
const DB_VERSION = 1;
const STORE_NAME = "asset_blobs";

type AssetBlobRecord = {
  assetId: number;
  blob: Blob;
  updatedAt: number;
};

let dbPromise: Promise<IDBDatabase | null> | null = null;

function openDatabase(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === "undefined") return Promise.resolve(null);
  if (dbPromise) return dbPromise;

  dbPromise = new Promise((resolve) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "assetId" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
    request.onblocked = () => resolve(null);
  });

  return dbPromise;
}

async function withStore<T>(
  mode: IDBTransactionMode,
  run: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T | null> {
  const db = await openDatabase();
  if (!db) return null;

  return new Promise((resolve) => {
    const transaction = db.transaction(STORE_NAME, mode);
    const store = transaction.objectStore(STORE_NAME);
    const request = run(store);

    request.onsuccess = () => resolve(request.result ?? null);
    request.onerror = () => resolve(null);
    transaction.onerror = () => resolve(null);
  });
}

export async function getCachedAssetBlob(assetId: number): Promise<Blob | null> {
  const record = await withStore<AssetBlobRecord>("readonly", (store) => store.get(assetId));
  return record?.blob ?? null;
}

export async function putCachedAssetBlob(assetId: number, blob: Blob): Promise<void> {
  await withStore<IDBValidKey>("readwrite", (store) =>
    store.put({
      assetId,
      blob,
      updatedAt: Date.now(),
    } satisfies AssetBlobRecord),
  );
}

export async function deleteCachedAssetBlob(assetId: number): Promise<void> {
  await withStore<undefined>("readwrite", (store) => store.delete(assetId));
}
