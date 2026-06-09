import {
  loadSiteV3Page,
  normalizeSingleParam,
  titleMap,
} from "../lib/api";
import { loadSiteV3Preview } from "../lib/preview";
import { ModuleRenderer } from "./modules/module-renderer";
import { SiteFooter } from "./modules/site-footer";
import { SiteHeader } from "./modules/site-header";
import { PreviewBanner } from "./preview-banner";
import { findFirstModule, sortedModules } from "./site-v3-render-helpers";

export async function SiteV3PublicPage({
  mode = "published",
  pageCode,
  previewToken,
  searchParams,
}: {
  mode?: "published" | "preview";
  pageCode: string;
  previewToken?: string;
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const siteCode = normalizeSingleParam(searchParams.site_code, "casinoking");
  const locale = normalizeSingleParam(searchParams.locale, "it");
  const result =
    mode === "preview" && previewToken
      ? await loadSiteV3Preview(previewToken)
      : await loadSiteV3Page({ siteCode, pageCode, locale });

  if (!result.page) {
    return (
      <main className="site-v3-page site-v3-page-fallback">
        {mode === "preview" ? <PreviewBanner /> : null}
        <section className="site-v3-fallback-panel">
          <p className="site-v3-kicker">Site V3 {mode === "preview" ? "Preview" : ""}</p>
          <h1>{mode === "preview" ? "Preview unavailable" : "Page not published"}</h1>
          <p>
            {mode === "preview"
              ? "Preview token is invalid or expired. Refresh it from the builder."
              : "This page does not have a live snapshot yet. Publish it from the admin builder before opening it on the public site."}
          </p>
          <small>{result.error ?? "Published page unavailable"}</small>
        </section>
      </main>
    );
  }

  const page = result.page;
  const modules = sortedModules(page.modules);
  const header =
    findFirstModule(modules, "global_header") ?? result.navigation?.header ?? null;
  const footer =
    findFirstModule(modules, "global_footer") ?? result.navigation?.footer ?? null;
  const bodyModules = modules.filter(
    (module) => module.module_code !== "global_header" && module.module_code !== "global_footer",
  );
  const games = titleMap(result.gameLibrary);

  return (
    <main className="site-v3-page">
      {mode === "preview" ? <PreviewBanner /> : null}
      <SiteHeader module={header} />
      <div className="site-v3-main" data-page-code={page.page_code}>
        {bodyModules.length > 0 ? (
          <>
            {bodyModules.map((module) => (
              <ModuleRenderer
                gameLibrary={result.gameLibrary}
                games={games}
                homeSlots={result.homeSlots}
                key={module.id}
                module={module}
                page={page}
              />
            ))}
          </>
        ) : (
          <section className="site-v3-empty-section">
            <p>The published page does not contain visual modules yet.</p>
          </section>
        )}
      </div>
      <SiteFooter module={footer} />
    </main>
  );
}
