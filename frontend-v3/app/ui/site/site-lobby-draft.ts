import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

export type PublicationPayload = {
  lobby_visibility: "hidden" | "visible";
  demo_enabled: boolean;
  real_enabled: boolean;
  lobby_display_name?: string | null;
  lobby_description?: string | null;
  featured?: boolean;
  position?: number;
};

export type PublicationDraft = {
  lobby_visibility: "hidden" | "visible";
  demo_enabled: boolean;
  real_enabled: boolean;
  lobby_display_name: string;
  lobby_description: string;
  featured: boolean;
  position: number;
};

type LaunchHintRecord = Record<string, unknown>;

export function createPublicationDraft(title: CatalogTitle): PublicationDraft {
  return {
    lobby_visibility: title.publication.lobby_visibility,
    demo_enabled: title.publication.demo_enabled,
    real_enabled: title.publication.real_enabled,
    lobby_display_name: title.publication.lobby_display_name ?? "",
    lobby_description: title.publication.lobby_description ?? "",
    featured: title.publication.featured,
    position: title.publication.position,
  };
}

export function createPublicationDraftByCode(
  titles: CatalogTitle[],
  titleCode: string,
): PublicationDraft {
  const title = titles.find((candidate) => candidate.title_code === titleCode);
  if (title) {
    return createPublicationDraft(title);
  }

  return {
    lobby_visibility: "hidden",
    demo_enabled: false,
    real_enabled: false,
    lobby_display_name: "",
    lobby_description: "",
    featured: false,
    position: 0,
  };
}

export function draftToPayload(draft: PublicationDraft): PublicationPayload {
  return {
    lobby_visibility: draft.lobby_visibility,
    demo_enabled: draft.demo_enabled,
    real_enabled: draft.real_enabled,
    lobby_display_name: normalizeOptionalText(draft.lobby_display_name),
    lobby_description: normalizeOptionalText(draft.lobby_description),
    featured: draft.featured,
    position: draft.position,
  };
}

export function isPublicationDirty(title: CatalogTitle, draft: PublicationDraft): boolean {
  const current = createPublicationDraft(title);
  return (
    current.lobby_visibility !== draft.lobby_visibility ||
    current.demo_enabled !== draft.demo_enabled ||
    current.real_enabled !== draft.real_enabled ||
    current.lobby_display_name !== draft.lobby_display_name ||
    current.lobby_description !== draft.lobby_description ||
    current.featured !== draft.featured ||
    current.position !== draft.position
  );
}

export function normalizePositionInput(value: string): number {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return 0;
  }
  return Math.max(0, parsed);
}

export function getPublicationWarnings(
  title: CatalogTitle,
  draft: PublicationDraft,
): string[] {
  const warnings: string[] = [];

  if (title.is_master) {
    warnings.push("Master title: available for preview, but cannot be published as a lobby card.");
  }

  if (title.is_archived === true) {
    warnings.push("Archived title: cannot be published in Site/Lobby.");
  }

  if (
    draft.lobby_visibility === "visible" &&
    !draft.demo_enabled &&
    !draft.real_enabled &&
    !title.is_master
  ) {
    warnings.push("Set as visible, but without Demo or Real it will not enter the player library.");
  }

  if (draft.lobby_visibility === "visible" && hasInactiveCatalogStatus(title)) {
    warnings.push(
      `Not all statuses are active: title ${title.status}, site/title ${title.site_title_status}, engine ${title.engine.status}. Launch may be rejected.`,
    );
  }

  warnings.push(...getLaunchConfigWarnings(title, draft));

  return warnings;
}

function normalizeOptionalText(value: string): string | null {
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function hasInactiveCatalogStatus(title: CatalogTitle): boolean {
  return (
    title.status !== "active" ||
    title.site_title_status !== "active" ||
    title.engine.status !== "active"
  );
}

function getLaunchConfigWarnings(title: CatalogTitle, draft: PublicationDraft): string[] {
  if (draft.lobby_visibility !== "visible") {
    return [];
  }

  const record = title as unknown as LaunchHintRecord;
  const warnings: string[] = [];

  if (hasExplicitFalse(record, ["has_live_config", "has_published_config", "has_launch_config"])) {
    warnings.push("Live config is not available for this title.");
  }

  if (hasExplicitFalse(record, ["launch_enabled"])) {
    warnings.push("Launch is reported as disabled for this title.");
  }

  if (draft.demo_enabled && hasExplicitFalse(record, ["demo_launch_enabled", "demo_playable"])) {
    warnings.push("Demo is reported as unavailable for this title.");
  }

  if (draft.real_enabled && hasExplicitFalse(record, ["real_launch_enabled", "real_playable"])) {
    warnings.push("Real is reported as unavailable for this title.");
  }

  const liveStatus = record.live_config_status ?? record.launch_config_status;
  if (
    typeof liveStatus === "string" &&
    !["active", "live", "published", "ready"].includes(liveStatus.toLowerCase())
  ) {
    warnings.push(`Live config status is not ready: ${liveStatus}.`);
  }

  return warnings;
}

function hasExplicitFalse(record: LaunchHintRecord, keys: string[]): boolean {
  return keys.some(
    (key) => Object.prototype.hasOwnProperty.call(record, key) && record[key] === false,
  );
}
