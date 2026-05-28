import { type SiteV3ValidationResult } from "../site-v3-admin-types";

export function ValidationPanel({
  validation,
  errorCount,
  warningCount,
}: {
  validation: SiteV3ValidationResult;
  errorCount: number;
  warningCount: number;
}) {
  return (
    <section className="admin-card">
      <div className="site-v3-card-heading">
        <div>
          <h4>Validation</h4>
          <p>Publish is unavailable while error severity issues exist. Codes stay visible for support.</p>
        </div>
        <span className={`site-v3-status-pill is-${validation.status}`}>
          {validation.status}
        </span>
      </div>
      <div className="site-v3-validation-summary">
        <span>{errorCount} errors</span>
        <span>{warningCount} warnings</span>
      </div>
      {validation.issues.length > 0 ? (
        <ul className="site-v3-issue-list">
          {validation.issues.map((issue, index) => (
            <li className={`is-${issue.severity}`} key={`${issue.code}-${issue.field}-${index}`}>
              <strong>{issue.message}</strong>
              <span>{issue.code}</span>
              <small>
                {issue.module_id ?? "page"} / {issue.field}
              </small>
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-state">Run validation to see readiness for publish.</p>
      )}
    </section>
  );
}
