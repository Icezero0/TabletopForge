<script setup lang="ts">
import type { Room } from "@/infra/api/rooms.api";

defineProps<{
  room: Room;
}>();

const villageSlots = ["村庄牌堆", "英雄", "武器", "法术", "物品", "村民"];
const dungeonSlots = ["地下城 1", "地下城 2", "地下城 3"];
const playerZones = ["手牌", "抽牌堆", "弃牌堆", "已装备/场上"];
</script>

<template>
  <div class="tsPageWrap">
    <main class="tsShell">
      <header class="tsHeader">
        <div>
          <div class="eyebrow">{{ $t("room.types.ThunderStone") }}</div>
          <h1>{{ room.name }}</h1>
        </div>
        <div class="statusPill">{{ $t("room.modes.thunderStone.prototype") }}</div>
      </header>

      <section class="boardBand villageBand">
        <div class="sectionHead">
          <h2>{{ $t("room.modes.thunderStone.village") }}</h2>
        </div>
        <div class="cardGrid villageGrid">
          <div v-for="slot in villageSlots" :key="slot" class="zoneCard">
            {{ slot }}
          </div>
        </div>
      </section>

      <section class="boardBand dungeonBand">
        <div class="sectionHead">
          <h2>{{ $t("room.modes.thunderStone.dungeon") }}</h2>
        </div>
        <div class="cardGrid dungeonGrid">
          <div v-for="slot in dungeonSlots" :key="slot" class="zoneCard dungeonCard">
            {{ slot }}
          </div>
        </div>
      </section>

      <section class="boardBand playerBand">
        <div class="sectionHead">
          <h2>{{ $t("room.modes.thunderStone.playerArea") }}</h2>
        </div>
        <div class="playerGrid">
          <div v-for="zone in playerZones" :key="zone" class="playerZone">
            {{ zone }}
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.tsPageWrap {
  width: 100%;
  min-height: 100%;
}

.tsShell {
  min-height: calc(100dvh - 68px);
  padding: 20px;
  display: grid;
  grid-template-rows: auto auto auto minmax(180px, 1fr);
  gap: 14px;
  color: var(--c-text);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--c-bg) 92%, #0f172a), var(--c-bg));
}

.tsHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  margin-bottom: 4px;
  color: var(--c-text-muted);
  font-size: 12px;
  font-weight: 650;
}

h1,
h2 {
  margin: 0;
}

h1 {
  font-size: 22px;
}

h2 {
  font-size: 14px;
}

.statusPill {
  flex: 0 0 auto;
  border: 1px solid var(--c-border);
  border-radius: 999px;
  padding: 7px 12px;
  color: var(--c-text-muted);
  background: color-mix(in srgb, var(--c-surface) 82%, var(--c-bg));
  font-size: 12px;
}

.boardBand {
  border: 1px solid var(--c-border);
  border-radius: 12px;
  padding: 14px;
  background: color-mix(in srgb, var(--c-surface) 72%, var(--c-bg));
  overflow: hidden;
}

.sectionHead {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cardGrid {
  display: grid;
  gap: 10px;
}

.villageGrid {
  grid-template-columns: repeat(6, minmax(96px, 1fr));
}

.dungeonGrid {
  grid-template-columns: repeat(3, minmax(120px, 1fr));
}

.zoneCard,
.playerZone {
  min-height: 120px;
  border: 1px solid color-mix(in srgb, var(--c-border) 84%, var(--c-primary));
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--c-text-muted);
  background: color-mix(in srgb, var(--c-surface) 70%, transparent);
  font-size: 13px;
}

.dungeonCard {
  min-height: 150px;
}

.playerGrid {
  display: grid;
  grid-template-columns: 1.6fr 0.8fr 0.8fr 1fr;
  gap: 10px;
}

.playerZone {
  min-height: 180px;
}

@media (max-width: 920px) {
  .villageGrid,
  .dungeonGrid,
  .playerGrid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .tsShell {
    min-height: calc(100dvh - 52px);
    padding: 12px;
  }

  .tsHeader {
    align-items: flex-start;
    flex-direction: column;
  }

  .villageGrid,
  .dungeonGrid,
  .playerGrid {
    grid-template-columns: 1fr;
  }
}
</style>
