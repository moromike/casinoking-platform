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
          <h3>Pubblicazione lobby</h3>
          <p>Gestisci i titoli che appaiono nel sito player CasinoKing.</p>
        </div>
        <div className="site-lobby-site-status" aria-label="Sito corrente">
          <span>Site</span>
          <strong>{siteDisplayName}</strong>
          <span className={`status-inline ${siteStatus === "active" ? "success" : "warning"}`}>
            {catalogStatus === "loading" ? "Caricamento" : siteStatus ?? "n/a"}
          </span>
        </div>
      </header>

      <dl className="site-lobby-kpis">
        <div>
          <dt>Visibili in lobby</dt>
          <dd>{visibleCount}</dd>
        </div>
        <div>
          <dt>Demo attive</dt>
          <dd>{demoEnabledCount}</dd>
        </div>
        <div>
          <dt>Real attive</dt>
          <dd>{realEnabledCount}</dd>
        </div>
        <div>
          <dt>Varianti totali</dt>
          <dd>{variantsCount}</dd>
        </div>
      </dl>
    </>
  );
}
