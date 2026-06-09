"use client";

import { useEffect, useMemo, useState } from "react";

import { readErrorMessage } from "@/app/lib/api";
import { issueSiteV3DraftPreviewToken } from "./site-v3-admin-api";

const STORAGE_KEY = "site_v3_preview_panel_expanded";

export function SiteV3DraftPreviewPanel({
  accessToken,
  draftVersion,
  isDirty,
  locale,
  pageCode,
  siteCode,
}: {
  accessToken: string;
  draftVersion: number;
  isDirty: boolean;
  locale: string;
  pageCode: string;
  siteCode: string;
}) {
  const [expanded, setExpanded] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [loadedAt, setLoadedAt] = useState<Date | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "false") {
      setExpanded(false);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, expanded ? "true" : "false");
  }, [expanded]);

  useEffect(() => {
    if (!expanded || !accessToken || !pageCode) {
      return;
    }
    const timeout = window.setTimeout(() => {
      void refreshPreview();
    }, isDirty ? 1000 : 0);
    return () => window.clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, draftVersion, expanded, isDirty, locale, pageCode, refreshNonce, siteCode]);

  const loadedLabel = useMemo(() => {
    if (!loadedAt) {
      return "Not loaded yet";
    }
    return `Updated ${loadedAt.toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })}`;
  }, [loadedAt]);

  async function refreshPreview() {
    setStatus("loading");
    setError(null);
    try {
      const token = await issueSiteV3DraftPreviewToken({
        accessToken,
        siteCode,
        pageCode,
        locale,
      });
      setPreviewUrl(token.preview_url);
      setExpiresAt(token.expires_at);
      setLoadedAt(new Date());
      setStatus("idle");
    } catch (nextError) {
      setStatus("error");
      setError(readErrorMessage(nextError, "Preview could not be loaded."));
    }
  }

  return (
    <section className="site-v3-draft-preview-panel" data-testid="site-v3-draft-preview-panel">
      <button
        className="site-v3-draft-preview-toggle"
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded((value) => !value)}
      >
        <span>
          <strong>Preview live</strong>
          <small>{isDirty ? "Unsaved local changes: save draft to persist preview." : loadedLabel}</small>
        </span>
        <span>{expanded ? "Collapse" : "Expand"}</span>
      </button>

      {expanded ? (
        <div className="site-v3-draft-preview-body">
          <div className="site-v3-draft-preview-toolbar">
            <span>Draft v{draftVersion}</span>
            {expiresAt ? <span>Token expires {new Date(expiresAt).toLocaleTimeString("it-IT")}</span> : null}
            <button className="button-secondary" type="button" onClick={() => setRefreshNonce((value) => value + 1)}>
              Refresh preview
            </button>
            {previewUrl ? (
              <a className="button-secondary" href={previewUrl} target="_blank" rel="noreferrer">
                Open in new tab
              </a>
            ) : null}
          </div>

          {status === "error" ? (
            <div className="site-v3-draft-preview-error" role="alert">
              <span>{error}</span>
              <button className="button-secondary" type="button" onClick={() => setRefreshNonce((value) => value + 1)}>
                Retry
              </button>
            </div>
          ) : null}

          {previewUrl ? (
            <iframe
              key={previewUrl}
              className="site-v3-draft-preview-frame"
              src={previewUrl}
              title={`Preview live ${pageCode}`}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
            />
          ) : (
            <div className="site-v3-draft-preview-placeholder">
              {status === "loading" ? "Loading preview..." : "Preview will appear here."}
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
