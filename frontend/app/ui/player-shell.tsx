import Link from "next/link";
import type { ReactNode } from "react";

const PLAYER_NAV_ITEMS = [
  { href: "/", label: "Lobby" },
  { href: "/mines", label: "Mines" },
  { href: "/register", label: "Register" },
  { href: "/account", label: "Account" },
  { href: "/login", label: "Login" },
];

export function PlayerShell({ children }: { children: ReactNode }) {
  return (
    <main className="page-shell player-shell">
      <div className="player-shell-frame">
        <div className="player-shell-grid">
          <aside className="player-sidebar stack" data-player-sidebar-desktop>
            <div className="player-brand-block">
              <p className="eyebrow">CasinoKing</p>
              <h1 style={{ margin: 0 }}>Player</h1>
              <p className="player-muted-copy">Dedicated player shell with desktop sidebar and mobile bottom navigation.</p>
            </div>
            <nav className="stack" aria-label="Player navigation">
              {PLAYER_NAV_ITEMS.map((item) => (
                <Link key={item.href} className="button-secondary" href={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>

          <div className="stack player-content">{children}</div>
        </div>

        <div className="player-bottom-nav" data-player-bottom-nav-mobile>
          <nav aria-label="Player mobile navigation" className="player-bottom-nav-items">
            {PLAYER_NAV_ITEMS.map((item) => (
              <Link key={item.href} className="button-secondary" href={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </main>
  );
}
