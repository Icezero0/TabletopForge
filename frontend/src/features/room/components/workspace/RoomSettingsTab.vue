<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type {
  Room,
  RoomJoinAuditMode,
  RoomPatchPayload,
  RoomVisibility,
} from "@/infra/api/rooms.api";

const props = defineProps<{
  room: Room;
  saving?: boolean;
}>();

const emit = defineEmits<{
  save: [payload: RoomPatchPayload];
}>();

const name = ref("");
const visibility = ref<RoomVisibility>("private");
const joinAuditMode = ref<RoomJoinAuditMode>("manual_review");
const { t } = useI18n();

const visibilityOptions = computed(() => [
  { value: "public", label: t("room.fields.public") },
  { value: "private", label: t("room.fields.private") },
]);

const joinAuditOptions = computed(() => [
  { value: "manual_review", label: t("room.settings.joinAuditManual") },
  { value: "auto_approve", label: t("room.settings.joinAuditAutoApprove") },
  { value: "auto_reject", label: t("room.settings.joinAuditAutoReject") },
]);

const canSave = computed(() => {
  const nextName = name.value.trim();
  return (
    nextName.length > 0 &&
    !props.saving &&
    (
      nextName !== props.room.name ||
      visibility.value !== props.room.visibility ||
      joinAuditMode.value !== props.room.join_audit_mode
    )
  );
});

watch(
  () => props.room,
  (room) => {
    name.value = room.name;
    visibility.value = room.visibility;
    joinAuditMode.value = room.join_audit_mode ?? "manual_review";
  },
  { immediate: true },
);

function submit() {
  if (!canSave.value) return;

  emit("save", {
    name: name.value.trim(),
    visibility: visibility.value,
    join_audit_mode: joinAuditMode.value,
  });
}
</script>

<template>
  <form class="settingsPanelBody" @submit.prevent="submit">
    <div class="settingsScroll">
      <label class="settingRow">
        <span class="label">{{ $t("room.settings.nameLabel") }}</span>
        <BaseInput
          v-model="name"
          :placeholder="$t('room.settings.namePlaceholder')"
          :disabled="saving"
        />
      </label>

      <div class="settingRow">
        <span class="label">{{ $t("room.settings.visibilityLabel") }}</span>

        <BaseSelect
          :model-value="visibility"
          :options="visibilityOptions"
          :disabled="saving"
          @update:model-value="visibility = $event as RoomVisibility"
        />
      </div>

      <div class="settingRow">
        <span class="label">{{ $t("room.settings.joinAuditLabel") }}</span>

        <BaseSelect
          :model-value="joinAuditMode"
          :options="joinAuditOptions"
          :disabled="saving"
          @update:model-value="joinAuditMode = $event as RoomJoinAuditMode"
        />
      </div>
    </div>

    <div class="actions">
      <BaseButton
        type="submit"
        variant="primary"
        :loading="saving"
        :disabled="!canSave"
      >
        {{ $t("common.save") }}
      </BaseButton>
    </div>
  </form>
</template>

<style scoped>
.settingsPanelBody {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.settingsScroll {
  display: grid;
  gap: 14px;
  padding: 14px;
  min-height: 0;
  align-content: start;
  overflow: auto;
}

.settingRow {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.label {
  color: var(--c-text);
  font-size: 13px;
  font-weight: 600;
}

.actions {
  display: flex;
  justify-content: flex-end;
  padding: 12px 14px 14px;
  background: var(--c-surface);
}

@media (max-width: 520px) {
  .settingRow {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}
</style>
