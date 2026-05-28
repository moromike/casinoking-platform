import { type SiteV3Version } from "../site-v3-admin-types";
import { formatDate } from "../site-v3-admin-helpers";

export function VersionHistory({ versions }: { versions: SiteV3Version[] }) {
  return (
    <section className="admin-card">
      <div className="site-v3-card-heading">
        <div>
          <h4>History</h4>
          <p>Read-only for MVP. Revert UI is Phase 2.</p>
        </div>
      </div>
      {versions.length > 0 ? (
        <ol className="site-v3-version-list">
          {versions.map((version) => (
            <li key={version.id}>
              <strong>v{version.version}</strong>
              <span className={`site-v3-status-pill is-${version.status}`}>{version.status}</span>
              <small>{formatDate(version.published_at ?? version.created_at)}</small>
            </li>
          ))}
        </ol>
      ) : (
        <p className="empty-state">No versions yet. Publish once to create history.</p>
      )}
    </section>
  );
}
