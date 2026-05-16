type SiteLobbySummaryProps = {
  catalogStatus: "idle" | "loading" | "error";
  siteDisplayName: string;
  siteStatus: string | null;
  visibleCount: number;
  demoEnabledCount: number;
  realEnabledCount: number;
  variantsCount: number;
};

export function SiteLobbySummary({
  catalogStatus,
  siteDisplayName,
  siteStatus,
  visibleCount,
  demoEnabledCount,
  realEnabledCount,
  variantsCount,
}: SiteLobbySummaryProps) {
  return (
    <>
      <header className="site-lobby-header">
        <div className="site-lobby-heading">
          <p className="eyebrow">Site / Lobby</p>
          <h3>Lobby publication</h3>
          <p>Manage the titles that appear on the CasinoKing player site.</p>
        </div>
        <div className="site-lobby-site-status" aria-label="Current site">
          <span>Site</span>
          <strong>{siteDisplayName}</strong>
          <span className={`status-inline ${siteStatus === "active" ? "success" : "warning"}`}>
            {catalogStatus === "loading" ? "Loading" : siteStatus ?? "n/a"}
          </span>
        </div>
      </header>

      <dl className="site-lobby-kpis">
        <div>
          <dt>Visible in lobby</dt>
          <dd>{visibleCount}</dd>
        </div>
        <div>
          <dt>Demo active</dt>
          <dd>{demoEnabledCount}</dd>
        </div>
        <div>
          <dt>Real active</dt>
          <dd>{realEnabledCount}</dd>
        </div>
        <div>
          <dt>Total variants</dt>
          <dd>{variantsCount}</dd>
        </div>
      </dl>
    </>
  );
}
