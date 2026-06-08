<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import type { GameRole } from "@/features/room/types";
import type { ActiveInspection } from "@/features/room/composables/useRoomInspection";
import { getCharacter, type Character } from "@/infra/api/character.api";
import {
  ABILITY_KEYS, ABILITY_LABEL_KEYS, DND5E_SKILLS, DND5E_ALIGNMENT_OPTIONS,
  abilityMod, fmtMod,
} from "@/features/character/constants";
import { patchRoomToken } from "@/infra/api/rooms.api";
import { getBackendErrorMessage } from "@/infra/http/client";
import { buildPathWithReturn } from "@/composables/useNavigationReturn";
import { useTabletopStore } from "@/stores/tabletop.store";
import { useAuthenticatedAssetUrl } from "@/features/table/composables/useAuthenticatedAssetUrl";
import PanelSectionHeader from "@/ui/layout/PanelSectionHeader.vue";

const props = defineProps<{
  inspection: ActiveInspection;
  roomId: number;
  gameRole: GameRole | "unknown";
  currentUserId?: number | null;
}>();

const emit = defineEmits<{
  close: [];
  tokenRenamed: [tokenId: number, name: string];
}>();

const { t, te } = useI18n();
const router = useRouter();
const tabletopStore = useTabletopStore();

const character = ref<Character | null>(null);
const loading = ref(false);
const saving = ref(false);
const renamingToken = ref(false);
const error = ref("");
const saveError = ref("");
const saveSuccess = ref(false);

const editCurrentHp = ref("");
const editMaxHp = ref("");
const editAc = ref("");
const editInstanceName = ref("");

// ── Tab state (character-only view, no tokenId) ──────────────────────────
type TabId = "identity" | "attributes" | "features" | "spells";
const activeTab = ref<TabId>("identity");
const expandedSpellLevels = ref(new Set<string>());

const TABS: { id: TabId; labelKey: string }[] = [
  { id: "identity",   labelKey: "table.inspector.tabIdentity"   },
  { id: "attributes", labelKey: "table.inspector.tabAttributes" },
  { id: "features",   labelKey: "table.inspector.tabFeatures"   },
  { id: "spells",     labelKey: "table.inspector.tabSpells"     },
];

// ── Portrait ─────────────────────────────────────────────────────────────
const portraitIdRef = computed<number | null | undefined>(() => character.value?.portrait_asset_id);
const { url: portraitUrl } = useAuthenticatedAssetUrl(portraitIdRef);

// ── Existing token-view state ────────────────────────────────────────────
const tokenInStore = computed(() => {
  const tokenId = props.inspection?.tokenId;
  if (tokenId == null) return null;
  return tabletopStore.getTokens(props.roomId).find((t) => t.id === tokenId) ?? null;
});

const tokenStateSummary = computed(() => tokenInStore.value?.state_summary ?? null);

const canEditState = computed(() => {
  if (!character.value || props.inspection?.tokenId == null) return false;
  if (props.gameRole === "GM") return true;
  if (props.gameRole === "PL") {
    return props.currentUserId != null && character.value.owner_id === props.currentUserId;
  }
  return false;
});

const canEditInstanceName = computed(
  () => props.gameRole === "GM" && props.inspection?.tokenId != null,
);

const canFullEdit = computed(() => {
  if (!character.value || props.currentUserId == null) return false;
  return character.value.owner_id === props.currentUserId;
});

const isDamageOnlyView = computed(() => {
  const s = tokenStateSummary.value;
  if (!s) return false;
  return s.current_hp == null && s.max_hp == null && s.ac == null && s.damage_taken != null;
});

const displayName = computed(() => {
  if (props.inspection?.tokenInstanceName) return props.inspection.tokenInstanceName;
  return character.value?.name ?? "";
});

const identitySummary = computed(() => {
  const identity = character.value?.identity ?? {};
  const parts: string[] = [];
  const race = identity.race;
  if (typeof race === "string" && race.trim()) parts.push(race);
  const classes = identity.classes;
  if (Array.isArray(classes) && classes.length > 0) {
    const labels = classes
      .map((entry) => {
        if (!entry || typeof entry !== "object") return "";
        const name = (entry as { name?: string }).name ?? "";
        const level = (entry as { level?: number }).level;
        return level ? `${name} ${level}` : name;
      })
      .filter(Boolean);
    if (labels.length) parts.push(labels.join(" / "));
  }
  return parts.join(" · ");
});

const ABILITY_SHORT: Record<string, string> = {
  strength: "STR", dexterity: "DEX", constitution: "CON",
  intelligence: "INT", wisdom: "WIS", charisma: "CHA",
};

const primaryPanel = computed(() =>
  character.value?.token_configs?.find(tc => tc.is_primary)?.panel_initial ?? null
);

type SaveThrowRow = { key: (typeof ABILITY_KEYS)[number]; value: number };
const savingThrows = computed<SaveThrowRow[]>(() => {
  const st = primaryPanel.value?.saving_throws as Record<string, number | null> | undefined;
  if (!st) return [];
  const rows: SaveThrowRow[] = [];
  for (const key of ABILITY_KEYS) {
    const value = st[key] ?? null;
    if (value != null) rows.push({ key, value });
  }
  return rows;
});

type SkillRow = {
  key: (typeof DND5E_SKILLS)[number]["key"];
  labelKey: (typeof DND5E_SKILLS)[number]["labelKey"];
  value: number;
};
const skillRows = computed<SkillRow[]>(() => {
  const sk = primaryPanel.value?.skills as Record<string, number | null> | undefined;
  if (!sk) return [];
  const rows: SkillRow[] = [];
  for (const s of DND5E_SKILLS) {
    const value = sk[s.key] ?? null;
    if (value != null) rows.push({ key: s.key, labelKey: s.labelKey, value });
  }
  return rows;
});

const inventoryItems = computed(() =>
  (primaryPanel.value?.items ?? []) as { name: string; quantity: number; notes: string }[]
);

const abilityScores = computed(() => {
  const abilities = character.value?.attributes?.abilities;
  if (!abilities || typeof abilities !== "object") return [];
  return Object.entries(abilities as Record<string, unknown>)
    .map(([key, value]) => {
      if (!value || typeof value !== "object") return null;
      const score = (value as { score?: number }).score;
      return score != null ? { key, score } : null;
    })
    .filter((item): item is { key: string; score: number } => item != null);
});

// ── Character-view computed ──────────────────────────────────────────────

const charAttrs = computed(() =>
  (character.value?.attributes ?? {}) as Record<string, unknown>
);

const charIdentity = computed(() => {
  const id = (character.value?.identity ?? {}) as Record<string, unknown>;
  return {
    race:       typeof id.race       === "string" ? id.race       : "",
    alignment:  typeof id.alignment  === "string" ? id.alignment  : "",
    background: typeof id.background === "string" ? id.background : "",
    classes:    Array.isArray(id.classes)
      ? (id.classes as { name: string; level: number }[])
      : [],
  };
});

const classesLabel = computed(() =>
  charIdentity.value.classes
    .filter(c => c.name)
    .map(c => {
      const key = `character.classes.${c.name}`;
      return `${te(key) ? t(key) : c.name} ${c.level}`;
    })
    .join(" · ")
);

const alignmentLabel = computed(() => {
  const val = charIdentity.value.alignment;
  if (!val) return "";
  const opt = DND5E_ALIGNMENT_OPTIONS.find(a => a.value === val);
  return opt ? t(opt.labelKey) : val;
});

// Attributes tab
const abilityScoreMap = computed<Record<string, number>>(() => {
  const s = (charAttrs.value.ability_scores as Record<string, number>) ?? {};
  const result: Record<string, number> = {};
  for (const k of ABILITY_KEYS) result[k] = Number(s[k] ?? 10);
  return result;
});

const profBonusValue = computed(() => {
  const derived = (charAttrs.value.derived as Record<string, { value: number }>) ?? {};
  return derived.proficiency_bonus?.value ?? 2;
});

const attrAbilityRows = computed(() =>
  ABILITY_KEYS.map(key => ({
    key,
    labelKey: ABILITY_LABEL_KEYS[key],
    score: abilityScoreMap.value[key] ?? 10,
    mod: fmtMod(abilityMod(abilityScoreMap.value[key] ?? 10)),
  }))
);

const DERIVED_STAT_CONFIG = [
  { key: "ac",                 label: "AC"      },
  { key: "max_hp",             label: "HP 上限"  },
  { key: "speed",              label: "速度"     },
  { key: "initiative",         label: "先攻"     },
  { key: "proficiency_bonus",  label: "熟练加值" },
  { key: "passive_perception", label: "被动察觉" },
] as const;

const derivedStatRows = computed(() => {
  const derived = (charAttrs.value.derived as Record<string, { value: number }>) ?? {};
  return DERIVED_STAT_CONFIG.map(cfg => ({
    label: cfg.label,
    value: derived[cfg.key]?.value ?? 0,
  }));
});

const attrSavingThrowRows = computed(() => {
  const storedVals  = (charAttrs.value.saving_throws      as Record<string, string>)  ?? {};
  const profs       = (charAttrs.value.saving_throw_profs as Record<string, boolean>) ?? {};
  const autos       = (charAttrs.value.saving_throw_autos as Record<string, boolean>) ?? {};
  return ABILITY_KEYS.map(key => {
    const isManual = autos[key] === false && !!storedVals[key]?.trim();
    const value = isManual
      ? (storedVals[key] ?? "")
      : fmtMod(abilityMod(abilityScoreMap.value[key] ?? 10) + (profs[key] ? profBonusValue.value : 0));
    return { key, labelKey: ABILITY_LABEL_KEYS[key], value, proficient: !!profs[key] };
  });
});

const attrSkillRows = computed(() => {
  const storedVals = (charAttrs.value.skill_values      as Record<string, string>) ?? {};
  const profs      = (charAttrs.value.skill_profs       as Record<string, string>) ?? {};
  const autos      = (charAttrs.value.skill_value_autos as Record<string, boolean>) ?? {};
  return DND5E_SKILLS.map(sk => {
    const isManual = autos[sk.key] === false && !!storedVals[sk.key]?.trim();
    let value: string;
    if (isManual) {
      value = storedVals[sk.key] ?? "";
    } else {
      const mod = abilityMod(abilityScoreMap.value[sk.ability] ?? 10);
      const profLevel = profs[sk.key];
      const bonus =
        profLevel === "expertise"  ? profBonusValue.value * 2 :
        profLevel === "proficient" ? profBonusValue.value     : 0;
      value = fmtMod(mod + bonus);
    }
    return {
      key: sk.key,
      label: t(sk.labelKey),
      value,
      profLevel: (profs[sk.key] ?? "none") as "none" | "proficient" | "expertise",
    };
  });
});

// Features tab
const racialTraits = computed(() =>
  ((character.value?.features?.racial_traits ?? []) as { name: string; notes: string }[])
);
const classFeatures = computed(() =>
  ((character.value?.features?.class_features ?? []) as { name: string; source: string; notes: string }[])
);
const customFieldEntries = computed(() => {
  const cf = (character.value?.features?.custom_fields ?? {}) as Record<string, string>;
  return Object.entries(cf)
    .filter(([, v]) => v != null && String(v).trim() !== "")
    .map(([k, v]) => ({ k, v: String(v) }));
});

// Spells tab
const spellsData = computed(() =>
  (character.value?.spells ?? null) as Record<string, unknown> | null
);

const spellcastingAbilityLabel = computed(() => {
  const ability = spellsData.value?.spellcasting_ability as string | undefined;
  if (!ability) return "";
  const key = `character.abilities.${ability}`;
  return te(key) ? t(key) : ability;
});

const spellSaveDC = computed(() => {
  const dc = spellsData.value?.spell_save_dc as { value: number } | undefined;
  return dc?.value ?? null;
});

const spellAttackBonus = computed(() => {
  const b = spellsData.value?.spell_attack_bonus as { value: number } | undefined;
  return b?.value ?? null;
});

const spellLevelRows = computed(() => {
  if (!spellsData.value) return [];
  const book     = (spellsData.value.spellbook      as Record<string, string[]>) ?? {};
  const slotsMax = (spellsData.value.spell_slots_max as Record<string, number>)  ?? {};
  const cantrips = (spellsData.value.cantrips        as string[])                ?? [];
  const rows: { lvl: string; label: string; spells: string[]; slotsMax: number }[] = [];
  const cantripList = [...new Set([...(book["0"] ?? []), ...cantrips])];
  if (cantripList.length > 0) rows.push({ lvl: "0", label: "戏法", spells: cantripList, slotsMax: 0 });
  for (const lvl of ["1","2","3","4","5","6","7","8","9"]) {
    const sp    = book[lvl] ?? [];
    const slots = slotsMax[lvl] ?? 0;
    if (sp.length > 0 || slots > 0) rows.push({ lvl, label: `${lvl} 环`, spells: sp, slotsMax: slots });
  }
  return rows;
});

function toggleSpellLevel(lvl: string) {
  const s = new Set(expandedSpellLevels.value);
  s.has(lvl) ? s.delete(lvl) : s.add(lvl);
  expandedSpellLevels.value = s;
}

// ── Loading ──────────────────────────────────────────────────────────────
function syncEditFieldsFromSummary() {
  const s = tokenStateSummary.value;
  editCurrentHp.value = s?.current_hp != null ? String(s.current_hp) : "";
  editMaxHp.value     = s?.max_hp     != null ? String(s.max_hp)     : "";
  editAc.value        = s?.ac         != null ? String(s.ac)         : "";
}

async function loadInspection() {
  const inspection = props.inspection;
  if (!inspection || inspection.kind !== "character") {
    character.value = null;
    return;
  }
  loading.value = true;
  error.value = "";
  saveError.value = "";
  saveSuccess.value = false;
  try {
    const char = await getCharacter(inspection.characterId);
    character.value = char;
    syncEditFieldsFromSummary();
    editInstanceName.value = inspection.tokenInstanceName ?? char.name;
  } catch (e) {
    error.value = e instanceof Error ? e.message : t("table.inspector.loadFailed");
    character.value = null;
  } finally {
    loading.value = false;
  }
}

watch(() => props.inspection, loadInspection, { immediate: true });

watch(() => props.inspection?.characterId, () => {
  activeTab.value = "identity";
  expandedSpellLevels.value = new Set();
});

watch(tokenStateSummary, () => {
  if (!saving.value) syncEditFieldsFromSummary();
});

watch([editCurrentHp, editMaxHp, editAc], () => {
  saveSuccess.value = false;
  saveError.value = "";
});

function parseOptionalInt(raw: string | number | null | undefined): number | null {
  if (raw == null) return null;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : null;
  const trimmed = String(raw).trim();
  if (!trimmed) return null;
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

async function saveState() {
  if (!canEditState.value) return;
  const tokenId = props.inspection?.tokenId;
  if (tokenId == null) return;
  saving.value = true;
  saveError.value = "";
  saveSuccess.value = false;
  try {
    const updated = await patchRoomToken(props.roomId, tokenId, {
      panel: {
        hp_current: parseOptionalInt(editCurrentHp.value),
        hp_max:     parseOptionalInt(editMaxHp.value),
        ac:         parseOptionalInt(editAc.value),
      },
    });
    tabletopStore.applyTokenUpdated(props.roomId, updated);
    saveSuccess.value = true;
  } catch (e) {
    saveError.value = getBackendErrorMessage(e) || t("table.inspector.saveFailed");
  } finally {
    saving.value = false;
  }
}

async function saveInstanceName() {
  const tokenId = props.inspection?.tokenId;
  if (!canEditInstanceName.value || tokenId == null) return;
  const trimmed = editInstanceName.value.trim();
  if (!trimmed) return;
  renamingToken.value = true;
  try {
    await patchRoomToken(props.roomId, tokenId, { name: trimmed });
    emit("tokenRenamed", tokenId, trimmed);
  } catch (e) {
    saveError.value = getBackendErrorMessage(e) || t("table.inspector.saveFailed");
  } finally {
    renamingToken.value = false;
  }
}

function openFullEdit() {
  if (!character.value || !canFullEdit.value) return;
  void router.push(
    buildPathWithReturn(
      `/characters/${character.value.id}`,
      `/rooms/${props.roomId}`,
      true,
    ),
  );
}
</script>

<template>
  <section class="infoPanel">
    <div class="panelHead">
      <PanelSectionHeader :title="t('table.inspector.infoTitle')" />
      <div class="headActions">
        <button
          v-if="character && canFullEdit"
          type="button"
          class="headBtn"
          @click="openFullEdit"
        >编辑</button>
        <button v-if="inspection" type="button" class="headBtn closeBtn" @click="emit('close')">
          ×
        </button>
      </div>
    </div>

    <p v-if="loading" class="empty">{{ t("common.loading") }}</p>
    <p v-else-if="error" class="empty">{{ error }}</p>

    <template v-else-if="character">

      <!-- ── Token selected: unchanged view ────────────────────────────── -->
      <template v-if="inspection?.tokenId != null">
        <header class="hero">
          <h3 v-if="!canEditInstanceName" class="heroTitle">{{ displayName }}</h3>
          <label v-else class="field instanceField">
            <span>{{ t("room.characters.instanceName") }}</span>
            <div class="inlineRow">
              <input v-model="editInstanceName" type="text" />
              <button
                type="button"
                class="saveBtn small"
                :disabled="renamingToken"
                @click="saveInstanceName"
              >{{ t("table.inspector.saveState") }}</button>
            </div>
          </label>
          <p v-if="character.player_name" class="heroSub">{{ character.player_name }}</p>
          <p v-if="identitySummary" class="heroSub">{{ identitySummary }}</p>
        </header>

        <div v-if="abilityScores.length" class="section">
          <h4 class="sectionTitle">{{ t("table.inspector.abilities") }}</h4>
          <div class="abilityGrid">
            <span v-for="item in abilityScores" :key="item.key" class="abilityChip">
              {{ item.key.toUpperCase() }} {{ item.score }}
            </span>
          </div>
        </div>

        <div v-if="savingThrows.length" class="section">
          <h4 class="sectionTitle">{{ t("table.inspector.savingThrows") }}</h4>
          <div class="chipRow">
            <span v-for="st in savingThrows" :key="st.key" class="compactChip">
              {{ ABILITY_SHORT[st.key] }} {{ fmtMod(st.value) }}
            </span>
          </div>
        </div>

        <div v-if="skillRows.length" class="section">
          <h4 class="sectionTitle">{{ t("table.inspector.skills") }}</h4>
          <div class="kvList">
            <div v-for="sk in skillRows" :key="sk.key" class="kvRow">
              <span class="kvLabel">{{ t(sk.labelKey) }}</span>
              <span class="kvVal">{{ fmtMod(sk.value) }}</span>
            </div>
          </div>
        </div>

        <div v-if="inventoryItems.length" class="section">
          <h4 class="sectionTitle">{{ t("table.inspector.inventory") }}</h4>
          <div class="kvList">
            <div v-for="(item, i) in inventoryItems" :key="i" class="kvRow">
              <span class="kvLabel">{{ item.name }}</span>
              <span class="kvVal muted">×{{ item.quantity }}</span>
            </div>
          </div>
        </div>

        <div class="section">
          <h4 class="sectionTitle">{{ t("table.inspector.state") }}</h4>
          <div v-if="canEditState" class="stateForm">
            <label class="field">
              <span>{{ t("table.inspector.currentHp") }}</span>
              <input v-model="editCurrentHp" type="number" />
            </label>
            <label class="field">
              <span>{{ t("table.inspector.maxHp") }}</span>
              <input v-model="editMaxHp" type="number" />
            </label>
            <label class="field">
              <span>{{ t("table.inspector.ac") }}</span>
              <input v-model="editAc" type="number" />
            </label>
            <button type="button" class="saveBtn" :disabled="saving" @click="saveState">
              {{ t("table.inspector.saveState") }}
            </button>
            <p v-if="saveSuccess" class="saveHint success">{{ t("table.inspector.stateSaved") }}</p>
            <p v-else-if="saveError" class="saveHint error">{{ saveError }}</p>
          </div>
          <div v-else-if="tokenStateSummary && isDamageOnlyView" class="stateReadonly">
            {{ t("room.characters.damageTaken") }}: {{ tokenStateSummary.damage_taken }}
          </div>
          <div v-else-if="tokenStateSummary" class="stateReadonly">
            HP {{ tokenStateSummary.current_hp ?? "?" }}/{{ tokenStateSummary.max_hp ?? "?" }} · AC
            {{ tokenStateSummary.ac ?? "?" }}
          </div>
        </div>

      </template>

      <!-- ── Character selected (no token): multi-tab view ─────────────── -->
      <template v-else>

        <!-- Tab bar -->
        <div class="tabBar" role="tablist">
          <button
            v-for="tab in TABS"
            :key="tab.id"
            role="tab"
            type="button"
            class="tabBtn"
            :class="{ active: activeTab === tab.id }"
            :aria-selected="activeTab === tab.id"
            @click="activeTab = tab.id"
          >{{ t(tab.labelKey) }}</button>
        </div>

        <!-- Tab pane -->
        <div class="tabPane">

          <!-- ── Identity ── -->
          <template v-if="activeTab === 'identity'">
            <div class="heroRow">
              <div class="portrait">
                <img v-if="portraitUrl" :src="portraitUrl" class="portraitImg" alt="" />
                <span v-else class="portraitFallback">{{ character.name.charAt(0) }}</span>
              </div>
              <div class="heroInfo">
                <div class="heroName">{{ character.name }}</div>
                <div v-if="character.player_name" class="heroSub">{{ character.player_name }}</div>
              </div>
            </div>

            <div class="infoRows">
              <div v-if="charIdentity.race" class="infoRow">
                <span class="infoLabel">种族</span>
                <span class="infoVal">{{ charIdentity.race }}</span>
              </div>
              <div v-if="alignmentLabel" class="infoRow">
                <span class="infoLabel">阵营</span>
                <span class="infoVal">{{ alignmentLabel }}</span>
              </div>
              <div v-if="charIdentity.background" class="infoRow">
                <span class="infoLabel">背景</span>
                <span class="infoVal">{{ charIdentity.background }}</span>
              </div>
              <div v-if="classesLabel" class="infoRow">
                <span class="infoLabel">职业</span>
                <span class="infoVal">{{ classesLabel }}</span>
              </div>
            </div>
          </template>

          <!-- ── Attributes ── -->
          <template v-else-if="activeTab === 'attributes'">
            <div class="abilityGrid6">
              <div v-for="ab in attrAbilityRows" :key="ab.key" class="abCell">
                <span class="abName">{{ t(ab.labelKey) }}</span>
                <span class="abScore">{{ ab.score }}</span>
                <span class="abMod">{{ ab.mod }}</span>
              </div>
            </div>

            <div class="attrBlock">
              <div class="attrBlockTitle">衍生属性</div>
              <div class="derivedGrid">
                <div v-for="d in derivedStatRows" :key="d.label" class="derivedItem">
                  <span class="derivedLabel">{{ d.label }}</span>
                  <span class="derivedVal">{{ d.value }}</span>
                </div>
              </div>
            </div>

            <div class="attrBlock">
              <div class="attrBlockTitle">{{ t("table.inspector.savingThrows") }}</div>
              <div class="saveGrid">
                <div v-for="st in attrSavingThrowRows" :key="st.key" class="saveItem">
                  <span class="saveAbility">{{ t(st.labelKey) }}</span>
                  <span class="saveVal">{{ st.value }}</span>
                </div>
              </div>
            </div>

            <div class="attrBlock">
              <div class="attrBlockTitle">{{ t("table.inspector.skills") }}</div>
              <div class="skillList">
                <div v-for="sk in attrSkillRows" :key="sk.key" class="skillItem">
                  <span class="skillLabel">{{ sk.label }}</span>
                  <span class="skillVal">{{ sk.value }}</span>
                </div>
              </div>
            </div>
          </template>

          <!-- ── Features ── -->
          <template v-else-if="activeTab === 'features'">
            <div v-if="racialTraits.length" class="featureBlock">
              <div class="attrBlockTitle">种族特性</div>
              <div v-for="(trait, i) in racialTraits" :key="i" class="featureItem">
                <div class="featureName">{{ trait.name }}</div>
                <div v-if="trait.notes" class="featureNotes">{{ trait.notes }}</div>
              </div>
            </div>

            <div v-if="classFeatures.length" class="featureBlock">
              <div class="attrBlockTitle">职业特性</div>
              <div v-for="(feat, i) in classFeatures" :key="i" class="featureItem">
                <div class="featureHead">
                  <span class="featureName">{{ feat.name }}</span>
                  <span v-if="feat.source" class="featureSource">
                    {{ te(`character.classes.${feat.source}`) ? t(`character.classes.${feat.source}`) : feat.source }}
                  </span>
                </div>
                <div v-if="feat.notes" class="featureNotes">{{ feat.notes }}</div>
              </div>
            </div>

            <div v-if="customFieldEntries.length" class="featureBlock">
              <div class="attrBlockTitle">{{ t("table.inspector.customFields") }}</div>
              <div v-for="entry in customFieldEntries" :key="entry.k" class="kvRow">
                <span class="kvLabel">{{ entry.k }}</span>
                <span class="kvVal">{{ entry.v }}</span>
              </div>
            </div>

            <div
              v-if="!racialTraits.length && !classFeatures.length && !customFieldEntries.length"
              class="emptyHint"
            >—</div>
          </template>

          <!-- ── Spells ── -->
          <template v-else-if="activeTab === 'spells'">
            <template v-if="spellsData">
              <div
                v-if="spellcastingAbilityLabel || spellSaveDC != null || spellAttackBonus != null"
                class="spellStats"
              >
                <div v-if="spellcastingAbilityLabel" class="spellStat">
                  <span class="spellStatLabel">施法属性</span>
                  <span class="spellStatVal">{{ spellcastingAbilityLabel }}</span>
                </div>
                <div v-if="spellSaveDC != null" class="spellStat">
                  <span class="spellStatLabel">豁免DC</span>
                  <span class="spellStatVal">{{ spellSaveDC }}</span>
                </div>
                <div v-if="spellAttackBonus != null" class="spellStat">
                  <span class="spellStatLabel">法术攻击</span>
                  <span class="spellStatVal">{{ fmtMod(spellAttackBonus) }}</span>
                </div>
              </div>

              <div v-if="spellLevelRows.length" class="spellLevels">
                <div v-for="row in spellLevelRows" :key="row.lvl" class="spellLevelGroup">
                  <button type="button" class="levelToggle" @click="toggleSpellLevel(row.lvl)">
                    <span>{{ row.label }}</span>
                    <span v-if="row.slotsMax > 0" class="slotBadge">{{ row.slotsMax }} 槽</span>
                    <span class="chevron" :class="{ open: expandedSpellLevels.has(row.lvl) }">▾</span>
                  </button>
                  <div v-if="expandedSpellLevels.has(row.lvl)" class="spellNames">
                    <span v-for="sp in row.spells" :key="sp" class="spellName">{{ sp }}</span>
                    <span v-if="!row.spells.length" class="emptyHint">—</span>
                  </div>
                </div>
              </div>
              <div v-else class="emptyHint">暂无法术</div>
            </template>
            <div v-else class="emptyHint">—</div>
          </template>

        </div>

      </template>
    </template>
  </section>
</template>

<style scoped>
.infoPanel {
  display: grid;
  gap: 12px;
  color: var(--c-text);
  width: min(320px, calc(100vw - 24px));
  max-height: min(70vh, 560px);
  overflow-y: scroll;
  scrollbar-gutter: stable;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--c-border) 72%, transparent);
  background: color-mix(in srgb, var(--c-surface) 94%, var(--c-bg));
  box-shadow: 0 10px 28px rgb(15 23 42 / 0.12);
  padding: 10px 14px 14px;
}

.empty {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
  line-height: 1.5;
}

.panelHead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.linkBtn {
  border: none;
  background: transparent;
  color: var(--c-text-muted);
  font-size: 12px;
  cursor: pointer;
}

.headActions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.headBtn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  height: 22px;
  border: 1px solid var(--c-border);
  border-radius: 5px;
  background: transparent;
  color: var(--c-text-muted);
  font: inherit;
  font-size: 11px;
  cursor: pointer;
  line-height: 1;
  white-space: nowrap;
}

.headBtn:hover {
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-bg-subtle));
  color: var(--c-text);
  border-color: color-mix(in srgb, var(--c-primary) 40%, var(--c-border));
}

.headBtn.closeBtn {
  padding: 0;
  width: 22px;
  font-size: 15px;
  color: var(--c-text-muted);
}

/* ── Token view ─────────────────────────────────────────────────────── */
.heroTitle {
  margin: 0;
  font-size: 16px;
  color: var(--c-text);
}

.heroSub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--c-text-muted);
}

.section {
  display: grid;
  gap: 8px;
}

.sectionTitle {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--c-text-muted);
}

.abilityGrid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.abilityChip {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 8px;
  background: var(--c-bg-subtle);
  border: 1px solid var(--c-border);
  color: var(--c-text);
}

.stateForm {
  display: grid;
  gap: 8px;
}

.field {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--c-text);
}

.field input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
}

.inlineRow {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.inlineRow input {
  flex: 1;
  min-width: 80px;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: color-mix(in srgb, var(--c-surface) 96%, var(--c-bg));
  color: var(--c-text);
  font: inherit;
}

.saveBtn,
.fullEditBtn {
  justify-self: start;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  color: var(--c-text);
  cursor: pointer;
  font-size: 13px;
  font: inherit;
}

.saveBtn.small {
  padding: 4px 10px;
  font-size: 12px;
}

.saveBtn:hover:not(:disabled),
.fullEditBtn:hover {
  background: color-mix(in srgb, var(--c-primary) 12%, var(--c-bg-subtle));
}

.saveBtn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.saveHint {
  margin: 0;
  font-size: 12px;
}

.saveHint.success { color: var(--c-success, #16a34a); }
.saveHint.error   { color: var(--c-danger); }

.stateReadonly {
  font-size: 13px;
  color: var(--c-text-muted);
}

.chipRow {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.compactChip {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 6px;
  background: var(--c-bg-subtle);
  border: 1px solid var(--c-border);
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
}

.kvList { display: grid; gap: 1px; }

.kvRow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  padding: 2px 0;
  gap: 8px;
}

.kvLabel {
  color: var(--c-text-muted);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kvVal {
  font-weight: 500;
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.kvVal.muted {
  font-weight: 400;
  color: var(--c-text-muted);
}

.instanceField { margin-top: 0; }

/* ── Character-only multi-tab view ──────────────────────────────────── */
.tabBar {
  display: flex;
  gap: 2px;
  background: var(--c-bg-subtle);
  border-radius: 8px;
  padding: 2px;
}

.tabBtn {
  flex: 1;
  padding: 5px 2px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font: inherit;
  font-size: 11px;
  color: var(--c-text-muted);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tabBtn.active {
  background: var(--c-surface);
  color: var(--c-text);
  font-weight: 600;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.1);
}

.tabPane { display: grid; gap: 12px; }

/* Identity tab */
.heroRow {
  display: flex;
  align-items: center;
  gap: 10px;
}

.portrait {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--c-border);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--c-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.portraitImg { width: 100%; height: 100%; object-fit: cover; }

.portraitFallback {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text-muted);
}

.heroInfo { flex: 1; min-width: 0; }
.heroName { font-size: 15px; font-weight: 600; color: var(--c-text); }

.infoRows { display: grid; gap: 4px; }

.infoRow {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  font-size: 12px;
}

.infoLabel { color: var(--c-text-muted); flex-shrink: 0; }

.infoVal {
  color: var(--c-text);
  font-weight: 500;
  text-align: right;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Attributes tab */
.abilityGrid6 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
}

.abCell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 4px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  gap: 1px;
}

.abName  { font-size: 10px; color: var(--c-text-muted); font-weight: 500; }
.abScore { font-size: 17px; font-weight: 700; color: var(--c-text); line-height: 1.1; }
.abMod   { font-size: 11px; color: var(--c-text-muted); font-variant-numeric: tabular-nums; }

.attrBlock { display: grid; gap: 6px; }

.attrBlockTitle {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-text-muted);
}

.derivedGrid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.derivedItem {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 5px 4px;
  border-radius: 7px;
  background: var(--c-bg-subtle);
  border: 1px solid var(--c-border);
  gap: 1px;
}

.derivedLabel { font-size: 9px; color: var(--c-text-muted); font-weight: 500; text-align: center; }
.derivedVal   { font-size: 14px; font-weight: 700; color: var(--c-text); }

.saveGrid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.saveItem {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.saveAbility { flex: 1; color: var(--c-text-muted); font-size: 10px; }

.saveVal {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--c-text);
  text-align: center;
  min-width: 22px;
}

.skillList {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px 8px;
}

.skillItem {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 0;
}

.skillLabel {
  flex: 1;
  color: var(--c-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skillVal {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--c-text);
  min-width: 22px;
  text-align: center;
}

/* Features tab */
.featureBlock { display: grid; gap: 6px; }

.featureItem {
  display: grid;
  gap: 3px;
  padding: 6px 8px;
  border-radius: 7px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
}

.featureHead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.featureName { font-size: 12px; font-weight: 600; color: var(--c-text); }

.featureSource {
  font-size: 10px;
  color: var(--c-text-muted);
  flex-shrink: 0;
}

.featureNotes {
  font-size: 11px;
  color: var(--c-text-muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Spells tab */
.spellStats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.spellStat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid var(--c-border);
  background: var(--c-bg-subtle);
  gap: 1px;
}

.spellStatLabel { font-size: 9px; color: var(--c-text-muted); font-weight: 500; }
.spellStatVal   { font-size: 14px; font-weight: 700; color: var(--c-text); }

.spellLevels { display: grid; gap: 4px; }

.spellLevelGroup { display: grid; gap: 4px; }

.levelToggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 5px 8px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-bg-subtle);
  color: var(--c-text);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
}

.levelToggle:hover {
  background: color-mix(in srgb, var(--c-primary) 8%, var(--c-bg-subtle));
}

.slotBadge {
  font-size: 10px;
  color: var(--c-text-muted);
  background: color-mix(in srgb, var(--c-border) 60%, transparent);
  border-radius: 4px;
  padding: 1px 5px;
}

.chevron {
  margin-left: auto;
  font-size: 12px;
  color: var(--c-text-muted);
  transition: transform 0.15s;
  display: inline-block;
  line-height: 1;
}

.chevron.open { transform: rotate(180deg); }

.spellNames {
  padding: 4px 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.spellName {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 5px;
  background: color-mix(in srgb, var(--c-primary) 10%, var(--c-bg-subtle));
  border: 1px solid color-mix(in srgb, var(--c-primary) 25%, transparent);
  color: var(--c-text);
}

.emptyHint {
  font-size: 12px;
  color: var(--c-text-muted);
  text-align: center;
  padding: 6px 0;
}
</style>
