import { computed, type ComputedRef } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter, type RouteLocationRaw } from "vue-router";

export const RETURN_TO_QUERY = "returnTo";

export function isSafeReturnPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//");
}

export function resolveReturnTo(
  queryValue: unknown,
  fallback = "/",
): string {
  if (typeof queryValue === "string" && isSafeReturnPath(queryValue)) {
    return queryValue;
  }
  return fallback;
}

export function buildPathWithReturn(
  path: string,
  currentFullPath: string,
  fromRoom: boolean,
): RouteLocationRaw {
  if (fromRoom) {
    return { path, query: { [RETURN_TO_QUERY]: currentFullPath } };
  }
  return path;
}

export function useNavigationReturn() {
  const route = useRoute();
  const router = useRouter();

  const isOnRoomPage = computed(() => route.name === "room");

  function navigateFromAppChrome(path: string) {
    void router.push(
      buildPathWithReturn(path, route.fullPath, isOnRoomPage.value),
    );
  }

  function linkTarget(path: string): RouteLocationRaw {
    return buildPathWithReturn(path, route.fullPath, isOnRoomPage.value);
  }

  return {
    isOnRoomPage,
    navigateFromAppChrome,
    linkTarget,
  };
}

export function usePageReturnTo(fallback = "/"): {
  backTo: ComputedRef<string>;
  backText: ComputedRef<string>;
} {
  const route = useRoute();
  const { t } = useI18n();

  const backTo = computed(() => resolveReturnTo(route.query[RETURN_TO_QUERY], fallback));

  const backText = computed(() => {
    const target = backTo.value;
    if (target.startsWith("/rooms/")) {
      return t("common.backToRoom");
    }
    return t("common.backHome");
  });

  return { backTo, backText };
}
