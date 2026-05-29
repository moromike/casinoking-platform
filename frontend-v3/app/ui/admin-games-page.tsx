"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ADMIN_STORAGE_KEYS } from "../lib/admin-storage";
import { ApiRequestError, apiRequest, readErrorMessage } from "../lib/api";
import { isTitleCodeValid, normalizeTitleCodeInput } from "../lib/title-code";
import type { FairnessCurrentConfig, StatusMessage } from "../lib/types";
import { PlatformCatalogPanel, type CatalogTitle } from "./platform-catalog-panel";
import { TitleEditorShell } from "./title-editor/title-editor-shell";

type AdminGamesRouteIntent = {
  engineCode?: string;
  titleCode?: string;
};

type AdminLoginResponse = {
  access_token: string;
  token_type: string;
  role: string;
};

type AdminProfile = {
  id: string;
  email: string;
  role: string;
  status: string;
  is_superadmin?: boolean;
  areas?: string[];
};

type AdminPreviewLaunchResponse = {
  game_code: string;
  title_code: string;
  site_code: string;
  mode: "demo";
  preview_token: string;
  expires_at: string;
};

type FairnessVerifyResult = {
  game_session_id: string;
  status: string;
  fairness_version: string;
  verified: boolean;
};

type AdminGamesStatus = StatusMessage | null;

const DEFAULT_ADMIN_TITLE: CatalogTitle = {
  title_code: "mines_classic",
  engine_code: "mines",
  display_name: "Mines Classic",
  status: "active",
  archived_at: null,
  is_archived: false,
  is_test: false,
  is_master: true,
  source_title_code: null,
  site_title_status: "active",
  publication: {
    site_title_status: "active",
    lobby_visibility: "hidden",
    demo_enabled: false,
    real_enabled: false,
    lobby_display_name: null,
    lobby_description: null,
    featured: false,
    position: 0,
  },
  engine: {
    engine_code: "mines",
    display_name: "Mines",
    status: "active",
  },
};

function getGameLaunchRoute(engineCode: string): string {
  if (engineCode === "boxe") {
    return "/boxe";
  }
  if (engineCode === "hi_lo" || engineCode === "hi-lo") {
    return "/hi-lo";
  }
  return "/mines";
}

function normalizeAdminAreas(profile: AdminProfile | null): string[] {
  return (profile?.areas ?? []).map((area) => (area === "mines" ? "games" : area));
}

export function AdminGamesPage({ routeIntent = {} }: { routeIntent?: AdminGamesRouteIntent }) {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [status, setStatus] = useState<AdminGamesStatus>({ kind: "info", text: "Checking admin session." });
  const [isChecking, setIsChecking] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [catalogRefreshKey, setCatalogRefreshKey] = useState(0);
  const [selectedAdminTitle, setSelectedAdminTitle] = useState<CatalogTitle>(DEFAULT_ADMIN_TITLE);
  const [adminGamesView, setAdminGamesView] = useState<"overview" | "detail">(
    routeIntent.titleCode ? "detail" : "overview",
  );
  const [adminRouteTitleStatus, setAdminRouteTitleStatus] = useState<"idle" | "loading" | "error">("idle");
  const [selectedTitleEditorRuntimeConfig, setSelectedTitleEditorRuntimeConfig] = useState<unknown | null>(null);
  const [adminFairnessCurrent, setAdminFairnessCurrent] = useState<FairnessCurrentConfig | null>(null);
  const [verifySessionId, setVerifySessionId] = useState("");

  const normalizedAdminAreas = normalizeAdminAreas(profile);
  const canAccessGames = profile === null || profile.is_superadmin === true || normalizedAdminAreas.includes("games");

  useEffect(() => {
    const storedToken = window.localStorage.getItem(ADMIN_STORAGE_KEYS.accessToken);
    const storedEmail = window.localStorage.getItem(ADMIN_STORAGE_KEYS.email);
    if (storedEmail) {
      setEmail(storedEmail);
    }
    if (!storedToken) {
      setIsChecking(false);
      setStatus(null);
      return;
    }
    void validateStoredSession(storedToken);
  }, []);

  useEffect(() => {
    setAdminGamesView(routeIntent.titleCode ? "detail" : "overview");
  }, [routeIntent.titleCode]);

  useEffect(() => {
    if (!routeIntent.titleCode) {
      setAdminRouteTitleStatus("idle");
      return;
    }

    let isMounted = true;
    setAdminRouteTitleStatus("loading");
    apiRequest<CatalogTitle>(`/catalog/titles/${encodeURIComponent(routeIntent.titleCode)}`)
      .then((title) => {
        if (!isMounted) {
          return;
        }
        if (routeIntent.engineCode && title.engine_code !== routeIntent.engineCode) {
          setAdminRouteTitleStatus("error");
          setStatus({
            kind: "error",
            text: `Title ${title.title_code} belongs to ${title.engine_code}, not ${routeIntent.engineCode}.`,
          });
          return;
        }
        setSelectedAdminTitle(title);
        setAdminRouteTitleStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setAdminRouteTitleStatus("error");
        setStatus({
          kind: "error",
          text: readErrorMessage(error, "Title detail loading failed."),
        });
      });

    return () => {
      isMounted = false;
    };
  }, [routeIntent.engineCode, routeIntent.titleCode]);

  useEffect(() => {
    if (adminGamesView !== "detail") {
      setSelectedTitleEditorRuntimeConfig(null);
      return;
    }
    if (selectedAdminTitle.is_master || selectedAdminTitle.is_archived === true) {
      setSelectedTitleEditorRuntimeConfig(null);
      return;
    }

    const engineCode = selectedAdminTitle.engine_code;
    const titleCode = selectedAdminTitle.title_code;
    let isMounted = true;
    const params = new URLSearchParams({ title_code: titleCode });
    apiRequest<unknown>(`/games/${encodeURIComponent(engineCode)}/config?${params.toString()}`)
      .then((data) => {
        if (isMounted) {
          setSelectedTitleEditorRuntimeConfig(data);
        }
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setSelectedTitleEditorRuntimeConfig(null);
        setStatus({
          kind: "error",
          text: readErrorMessage(error, `Unable to load the ${engineCode} runtime config for this Title.`),
        });
      });

    return () => {
      isMounted = false;
    };
  }, [
    adminGamesView,
    selectedAdminTitle.engine_code,
    selectedAdminTitle.is_archived,
    selectedAdminTitle.is_master,
    selectedAdminTitle.title_code,
  ]);

  async function validateStoredSession(token: string) {
    setIsChecking(true);
    try {
      const nextProfile = await apiRequest<AdminProfile>("/admin/auth/me", {}, token);
      setAccessToken(token);
      setProfile(nextProfile);
      setEmail(nextProfile.email);
      window.localStorage.setItem(ADMIN_STORAGE_KEYS.email, nextProfile.email);
      setStatus({ kind: "success", text: "Admin session restored." });
    } catch {
      clearStoredSession();
      setStatus(null);
    } finally {
      setIsChecking(false);
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus(null);

    try {
      const normalizedEmail = email.trim().toLowerCase();
      const login = await apiRequest<AdminLoginResponse>("/admin/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
      });
      if (login.role !== "admin") {
        throw new Error("The authenticated user is not an admin.");
      }

      const nextProfile = await apiRequest<AdminProfile>("/admin/auth/me", {}, login.access_token);
      window.localStorage.setItem(ADMIN_STORAGE_KEYS.accessToken, login.access_token);
      window.localStorage.setItem(ADMIN_STORAGE_KEYS.email, nextProfile.email);
      setAccessToken(login.access_token);
      setProfile(nextProfile);
      setPassword("");
      setStatus({ kind: "success", text: "Admin sign-in completed." });
    } catch (error) {
      clearStoredSession();
      setStatus({ kind: "error", text: readErrorMessage(error, "Admin sign-in failed.") });
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSignOut() {
    clearStoredSession();
    setAccessToken(null);
    setProfile(null);
    setPassword("");
    setStatus(null);
  }

  function clearStoredSession() {
    window.localStorage.removeItem(ADMIN_STORAGE_KEYS.accessToken);
    window.localStorage.removeItem(ADMIN_STORAGE_KEYS.sessionId);
  }

  function handleExpiredAdminSession(error: unknown, fallback: string): boolean {
    if (error instanceof ApiRequestError && error.status === 401) {
      clearStoredSession();
      setAccessToken(null);
      setProfile(null);
      setStatus({ kind: "error", text: "The admin session is no longer valid. Sign in again." });
      return true;
    }
    setStatus({ kind: "error", text: readErrorMessage(error, fallback) });
    return false;
  }

  async function handleRefreshFairnessCurrent() {
    setBusyAction("admin-fairness-current");
    try {
      const data = await apiRequest<FairnessCurrentConfig>("/games/mines/fairness/current");
      setAdminFairnessCurrent(data);
      setStatus({ kind: "info", text: "Current fairness configuration synced." });
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Fairness current loading failed.") });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDuplicateGameTitle(
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string; is_test?: boolean },
  ) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Admin login is required." });
      return false;
    }

    const requestedTitleCode = normalizeTitleCodeInput(payload.title_code);
    const requestedDisplayName = payload.display_name.trim();
    if (!isTitleCodeValid(requestedTitleCode) || !requestedDisplayName) {
      setStatus({ kind: "error", text: "Enter a valid title code and display name." });
      return false;
    }

    setBusyAction("duplicate-title");
    try {
      const duplicatedTitle = await apiRequest<CatalogTitle>(
        `/admin/games/titles/${encodeURIComponent(sourceTitle.title_code)}/duplicate`,
        {
          method: "POST",
          body: JSON.stringify({
            title_code: requestedTitleCode,
            display_name: requestedDisplayName,
            site_code: "casinoking",
            is_test: payload.is_test === true,
          }),
        },
        accessToken,
      );
      setSelectedAdminTitle(duplicatedTitle);
      setAdminGamesView("detail");
      router.push(
        `/admin/games/${encodeURIComponent(duplicatedTitle.engine_code)}/titles/${encodeURIComponent(duplicatedTitle.title_code)}`,
      );
      setCatalogRefreshKey((current) => current + 1);
      setStatus({
        kind: "success",
        text: `Variant ${duplicatedTitle.title_code} was created and is ready to customize.`,
      });
      return true;
    } catch (error) {
      handleExpiredAdminSession(error, "Variant creation failed.");
      return false;
    } finally {
      setBusyAction(null);
    }
  }

  function handleOpenAdminTitle(title: CatalogTitle) {
    setSelectedAdminTitle(title);
    setAdminGamesView("detail");
    router.push(`/admin/games/${encodeURIComponent(title.engine_code)}/titles/${encodeURIComponent(title.title_code)}`);
  }

  function handleOpenAdminEngine(engineCode: string) {
    setAdminGamesView("overview");
    router.push(`/admin/games/${encodeURIComponent(engineCode)}`);
  }

  function handleBackToAdminGamesList() {
    setAdminGamesView("overview");
    router.push(routeIntent.engineCode ? `/admin/games/${encodeURIComponent(routeIntent.engineCode)}` : "/admin/games");
  }

  function handlePreviewAdminTitle(title: CatalogTitle) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Admin login is required." });
      return;
    }

    const previewWindow = window.open("about:blank", "_blank");
    if (previewWindow) {
      previewWindow.opener = null;
    }
    void (async () => {
      try {
        const data = await apiRequest<AdminPreviewLaunchResponse>(
          `/admin/games/titles/${encodeURIComponent(title.title_code)}/preview-launch`,
          {
            method: "POST",
            body: JSON.stringify({
              game_code: title.engine_code,
              site_code: "casinoking",
            }),
          },
          accessToken,
        );
        const previewHref =
          `${getGameLaunchRoute(data.game_code)}?title_code=${encodeURIComponent(data.title_code)}` +
          `&mode=demo&preview=1&preview_token=${encodeURIComponent(data.preview_token)}`;
        if (previewWindow) {
          previewWindow.location.href = previewHref;
        } else {
          window.open(previewHref, "_blank");
        }
      } catch (error) {
        previewWindow?.close();
        handleExpiredAdminSession(error, "Preview launch failed.");
      }
    })();
  }

  async function handleUpdateTitleDisplayName(title: CatalogTitle, payload: { display_name: string }) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Admin login is required." });
      return;
    }

    const requestedDisplayName = payload.display_name.trim();
    if (!requestedDisplayName) {
      setStatus({ kind: "error", text: "Enter a valid variant display name." });
      return;
    }

    setBusyAction("update-title-profile");
    try {
      const updatedTitle = await apiRequest<CatalogTitle>(
        `/admin/games/titles/${encodeURIComponent(title.title_code)}/profile`,
        {
          method: "PUT",
          body: JSON.stringify({
            display_name: requestedDisplayName,
            site_code: "casinoking",
          }),
        },
        accessToken,
      );
      if (selectedAdminTitle.title_code === updatedTitle.title_code) {
        setSelectedAdminTitle(updatedTitle);
      }
      setCatalogRefreshKey((current) => current + 1);
      setStatus({ kind: "success", text: `Variant display name updated: ${updatedTitle.display_name}.` });
    } catch (error) {
      handleExpiredAdminSession(error, "Variant display name update failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleArchiveAdminTitle(title: CatalogTitle) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Admin login is required." });
      return;
    }
    if (title.is_master) {
      setStatus({ kind: "error", text: "Master titles cannot be archived." });
      return;
    }

    setBusyAction(`archive-title:${title.title_code}`);
    try {
      const archivedTitle = await apiRequest<CatalogTitle>(
        `/admin/games/titles/${encodeURIComponent(title.title_code)}/archive`,
        {
          method: "POST",
          body: JSON.stringify({
            site_code: "casinoking",
            reason: "Archived from Games backoffice",
          }),
        },
        accessToken,
      );
      if (selectedAdminTitle.title_code === archivedTitle.title_code) {
        setSelectedAdminTitle(archivedTitle);
      }
      setCatalogRefreshKey((current) => current + 1);
      setStatus({ kind: "success", text: `Variant ${archivedTitle.title_code} archived.` });
    } catch (error) {
      handleExpiredAdminSession(error, "Variant archive failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRestoreAdminTitle(title: CatalogTitle) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Admin login is required." });
      return;
    }

    setBusyAction(`restore-title:${title.title_code}`);
    try {
      const restoredTitle = await apiRequest<CatalogTitle>(
        `/admin/games/titles/${encodeURIComponent(title.title_code)}/restore`,
        {
          method: "POST",
          body: JSON.stringify({ site_code: "casinoking" }),
        },
        accessToken,
      );
      if (selectedAdminTitle.title_code === restoredTitle.title_code) {
        setSelectedAdminTitle(restoredTitle);
      }
      setCatalogRefreshKey((current) => current + 1);
      setStatus({ kind: "success", text: `Variant ${restoredTitle.title_code} restored as inactive and hidden.` });
    } catch (error) {
      handleExpiredAdminSession(error, "Variant restore failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleVerifyFairness(sessionId?: string) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "An admin bearer token is required to verify a Mines session." });
      return;
    }
    const effectiveSessionId = sessionId?.trim() || verifySessionId.trim();
    if (!effectiveSessionId) {
      setStatus({ kind: "error", text: "Enter a game session id before running fairness verification." });
      return;
    }

    setBusyAction("admin-fairness-verify");
    try {
      const data = await apiRequest<FairnessVerifyResult>(
        `/games/mines/verify?session_id=${encodeURIComponent(effectiveSessionId)}`,
        {},
        accessToken,
      );
      if (sessionId) {
        setVerifySessionId(effectiveSessionId);
      }
      setStatus({
        kind: data.verified ? "success" : "error",
        text: data.verified
          ? `Fairness verification passed for session ${data.game_session_id.slice(0, 8)}.`
          : `Fairness verification failed for session ${data.game_session_id.slice(0, 8)}.`,
      });
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Fairness verification failed.") });
    } finally {
      setBusyAction(null);
    }
  }

  if (isChecking) {
    return (
      <main className="site-v3-admin-page">
        <section className="site-v3-admin-login" aria-live="polite">
          <span className="site-v3-admin-kicker">CasinoKing Backoffice</span>
          <h1>Games Admin</h1>
          <p>Checking the current admin session.</p>
        </section>
      </main>
    );
  }

  if (!accessToken) {
    return (
      <main className="site-v3-admin-page">
        <section className="site-v3-admin-login">
          <span className="site-v3-admin-kicker">CasinoKing Backoffice</span>
          <h1>Games Admin</h1>
          <form onSubmit={handleLogin}>
            <label>
              <span>Email</span>
              <input
                autoComplete="username"
                inputMode="email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
            </label>
            <label>
              <span>Password</span>
              <input
                autoComplete="current-password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </label>
            {status ? <p className={`site-v3-admin-status is-${status.kind}`}>{status.text}</p> : null}
            <button className="site-v3-button" disabled={isSubmitting} type="submit">
              {isSubmitting ? "Signing in" : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="site-v3-admin-page">
      <header className="site-v3-admin-topbar">
        <div>
          <span className="site-v3-admin-kicker">CasinoKing Backoffice</span>
          <strong>Games Admin</strong>
          {profile ? <small>{profile.email}</small> : null}
        </div>
        <div className="site-v3-admin-topbar-actions">
          <a className="site-v3-button is-secondary" href="/admin/site-v3">
            Site V3 CMS
          </a>
          <a className="site-v3-button is-secondary" href="/">
            Public site
          </a>
          <button className="site-v3-button is-secondary" onClick={handleSignOut} type="button">
            Sign out
          </button>
        </div>
      </header>

      {status ? <p className={`site-v3-admin-status is-${status.kind}`}>{status.text}</p> : null}

      {!canAccessGames ? (
        <article className="admin-card">
          <div className="admin-card-heading">
            <div>
              <h3>Games</h3>
              <p>Your admin account is not enabled for this area.</p>
            </div>
          </div>
        </article>
      ) : adminGamesView === "overview" ? (
        <PlatformCatalogPanel
          engineFilterCode={routeIntent.engineCode}
          selectedTitleCode={undefined}
          refreshKey={catalogRefreshKey}
          busyAction={busyAction}
          onConfigureTitle={handleOpenAdminTitle}
          onDuplicateTitle={handleDuplicateGameTitle}
          onUpdateTitleDisplayName={handleUpdateTitleDisplayName}
          onPreviewTitle={handlePreviewAdminTitle}
          onArchiveTitle={handleArchiveAdminTitle}
          onRestoreTitle={handleRestoreAdminTitle}
          onOpenEngine={handleOpenAdminEngine}
        />
      ) : (
        <div className="stack">
          {adminRouteTitleStatus === "loading" ? (
            <article className="admin-card">
              <p className="empty-state">Loading title detail.</p>
            </article>
          ) : adminRouteTitleStatus === "error" ? (
            <article className="admin-card">
              <p className="empty-state">Title detail is unavailable.</p>
            </article>
          ) : (
            <>
              <div className="title-detail-header">
                <div className="title-detail-heading">
                  <button className="button-secondary" type="button" onClick={handleBackToAdminGamesList}>
                    Back to list
                  </button>
                  <div>
                    <h3>{selectedAdminTitle.display_name}</h3>
                    <p className="mono">{selectedAdminTitle.title_code}</p>
                  </div>
                </div>
                <div className="title-detail-actions">
                  <span className={`status-inline ${selectedAdminTitle.is_master ? "warning" : "success"}`}>
                    {selectedAdminTitle.is_master ? "locked master" : "variant"}
                  </span>
                  {selectedAdminTitle.is_archived === true ? <span className="status-inline error">archived</span> : null}
                  <span className="status-inline info">{selectedAdminTitle.engine.display_name}</span>
                  <button
                    className="button-secondary"
                    disabled={selectedAdminTitle.is_archived === true}
                    onClick={() => handlePreviewAdminTitle(selectedAdminTitle)}
                    type="button"
                  >
                    Preview
                  </button>
                  {!selectedAdminTitle.is_master && selectedAdminTitle.is_archived === true ? (
                    <button
                      className="button-secondary"
                      disabled={busyAction !== null}
                      onClick={() => void handleRestoreAdminTitle(selectedAdminTitle)}
                      type="button"
                    >
                      {busyAction === `restore-title:${selectedAdminTitle.title_code}` ? "Restoring..." : "Restore"}
                    </button>
                  ) : !selectedAdminTitle.is_master ? (
                    <button
                      className="button-secondary danger"
                      disabled={busyAction !== null}
                      onClick={() => void handleArchiveAdminTitle(selectedAdminTitle)}
                      type="button"
                    >
                      {busyAction === `archive-title:${selectedAdminTitle.title_code}` ? "Archiving..." : "Archive"}
                    </button>
                  ) : null}
                </div>
              </div>

              <TitleEditorShell
                titleCode={selectedAdminTitle.title_code}
                engineCode={selectedAdminTitle.engine_code}
                displayName={selectedAdminTitle.display_name}
                isReadOnly={selectedAdminTitle.is_master || selectedAdminTitle.is_archived === true}
                accessToken={accessToken}
                runtimeConfig={selectedTitleEditorRuntimeConfig}
                busyAction={busyAction}
                setBusyAction={setBusyAction}
                setStatus={setStatus}
                setRuntimeConfig={setSelectedTitleEditorRuntimeConfig}
                adminFairnessCurrent={adminFairnessCurrent}
                verifySessionId={verifySessionId}
                setVerifySessionId={setVerifySessionId}
                onRefreshFairnessCurrent={handleRefreshFairnessCurrent}
                onVerifyFairness={handleVerifyFairness}
                showSummaryHeader={false}
              />
            </>
          )}
        </div>
      )}
    </main>
  );
}
