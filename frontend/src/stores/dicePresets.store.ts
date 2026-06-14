import { defineStore } from "pinia";
import {
  createDicePreset,
  deleteDicePreset,
  getDicePresets,
  patchDicePreset,
  type DicePreset,
  type DicePresetCreate,
  type DicePresetPatch,
} from "@/infra/api/dice.api";
import { useAuthStore } from "@/stores/auth.store";

type LegacyDicePreset = {
  id: string;
  name: string;
  formula: string;
  label: string;
  visibility: "public" | "blind";
};

type State = {
  items: DicePreset[];
  isLoaded: boolean;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
};

function sortPresets(items: DicePreset[]) {
  return [...items].sort((a, b) => {
    const parentA = a.parent_id ?? 0;
    const parentB = b.parent_id ?? 0;
    if (parentA !== parentB) return parentA - parentB;
    if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order;
    return a.id - b.id;
  });
}

function isLegacyPreset(value: unknown): value is LegacyDicePreset {
  if (!value || typeof value !== "object") return false;
  const preset = value as Partial<LegacyDicePreset>;
  return (
    typeof preset.id === "string" &&
    typeof preset.name === "string" &&
    typeof preset.formula === "string" &&
    typeof preset.label === "string" &&
    (preset.visibility === "public" || preset.visibility === "blind")
  );
}

function legacyKey(userId: number | string | null | undefined) {
  return `tabletopforge:dice-presets:${userId ?? "guest"}`;
}

function extractErrorMessage(error: any, fallback: string) {
  return error?.response?.data?.error?.message ?? error?.response?.data?.detail ?? error?.message ?? fallback;
}

export const useDicePresetsStore = defineStore("dicePresets", {
  state: (): State => ({
    items: [],
    isLoaded: false,
    isLoading: false,
    isSaving: false,
    error: null,
  }),

  getters: {
    flatPresets: (state) => sortPresets(state.items.filter((item) => item.kind === "preset")),
    childrenByParent: (state) => {
      return (parentId: number | null) =>
        sortPresets(state.items.filter((item) => (item.parent_id ?? null) === parentId));
    },
  },

  actions: {
    async load(force = false) {
      if (this.isLoading || (this.isLoaded && !force)) return this.items;
      this.isLoading = true;
      this.error = null;
      try {
        const response = await getDicePresets();
        this.items = sortPresets(response.items);
        this.isLoaded = true;
        await this.migrateLegacyPresets();
        return this.items;
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to load dice presets");
        this.error = message;
        throw new Error(message);
      } finally {
        this.isLoading = false;
      }
    },

    async create(payload: DicePresetCreate) {
      this.isSaving = true;
      this.error = null;
      try {
        const created = await createDicePreset(payload);
        this.items = sortPresets([...this.items, created]);
        this.isLoaded = true;
        return created;
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to save dice preset");
        this.error = message;
        throw new Error(message);
      } finally {
        this.isSaving = false;
      }
    },

    async update(presetId: number, payload: DicePresetPatch) {
      this.isSaving = true;
      this.error = null;
      try {
        const updated = await patchDicePreset(presetId, payload);
        this.items = sortPresets(this.items.map((item) => (item.id === presetId ? updated : item)));
        return updated;
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to update dice preset");
        this.error = message;
        throw new Error(message);
      } finally {
        this.isSaving = false;
      }
    },

    async remove(presetId: number) {
      this.isSaving = true;
      this.error = null;
      try {
        await deleteDicePreset(presetId);
        const removedIds = new Set<number>([presetId]);
        let changed = true;
        while (changed) {
          changed = false;
          for (const item of this.items) {
            if (item.parent_id != null && removedIds.has(item.parent_id) && !removedIds.has(item.id)) {
              removedIds.add(item.id);
              changed = true;
            }
          }
        }
        this.items = this.items.filter((item) => !removedIds.has(item.id));
      } catch (error: any) {
        const message = extractErrorMessage(error, "Failed to delete dice preset");
        this.error = message;
        throw new Error(message);
      } finally {
        this.isSaving = false;
      }
    },

    async move(presetId: number, direction: -1 | 1) {
      const item = this.items.find((entry) => entry.id === presetId);
      if (!item) return;
      const siblings = sortPresets(this.items.filter((entry) => (entry.parent_id ?? null) === (item.parent_id ?? null)));
      const index = siblings.findIndex((entry) => entry.id === presetId);
      const target = siblings[index + direction];
      if (!target) return;
      const currentOrder = item.sort_order;
      await this.update(item.id, { sort_order: target.sort_order });
      await this.update(target.id, { sort_order: currentOrder });
    },

    async migrateLegacyPresets() {
      const auth = useAuthStore();
      if (this.items.length > 0 || !auth.me?.id) return;
      const key = legacyKey(auth.me.id);
      const raw = localStorage.getItem(key);
      if (!raw) return;
      try {
        const parsed = JSON.parse(raw);
        const legacyItems = Array.isArray(parsed) ? parsed.filter(isLegacyPreset) : [];
        for (const [index, preset] of legacyItems.entries()) {
          await this.create({
            kind: "preset",
            name: preset.name,
            formula: preset.formula,
            label: preset.label,
            visibility: preset.visibility,
            sort_order: index,
          });
        }
        localStorage.removeItem(key);
      } catch {
        // Legacy migration is best effort; the old local copy is kept if anything fails.
      }
    },
  },
});
