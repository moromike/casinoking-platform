import type { SiteV3PublicModule } from "../../lib/types";
import { readNavItems, readString, resolveLink } from "../site-v3-render-helpers";

export function SiteFooter({ module }: { module: SiteV3PublicModule | null }) {
  const config = module?.config_json ?? {};
  const links = readNavItems(config.links);

  return (
    <footer className="site-v3-footer">
      <p>{readString(config.legal_text, "CasinoKing - gioco responsabile.")}</p>
      {links.length > 0 ? (
        <nav aria-label="Footer links">
          {links.slice(0, 8).map((item) => (
            <a href={resolveLink(item.url ?? item.title_code ?? "/")} key={`${item.label}:${item.url ?? item.title_code}`}>
              {item.label}
            </a>
          ))}
        </nav>
      ) : null}
    </footer>
  );
}
