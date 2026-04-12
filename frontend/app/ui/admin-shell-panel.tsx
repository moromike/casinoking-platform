"use client";

import type { ReactNode } from "react";

type AdminSection = "menu" | "casino_king" | "players" | "games" | "my_space" | "admins";

type AdminShellPanelProps = {
  adminSection: AdminSection;
  adminSectionLabel: string;
  canAccessFinance: boolean;
  canAccessEndUser: boolean;
  canAccessMines: boolean;
  isSuperadmin: boolean;
  onOpenFinanceSection: () => void;
  onOpenPlayersSection: () => void;
  onOpenGamesSection: () => void;
  onOpenMySpaceSection: () => void;
  onOpenAdminsSection: () => void;
  onBackToMenu: () => void;
  onLogout: () => void;
  children?: ReactNode;
};

export function AdminShellPanel({
  adminSection,
  adminSectionLabel,
  canAccessFinance,
  canAccessEndUser,
  canAccessMines,
  isSuperadmin,
  onOpenFinanceSection,
  onOpenPlayersSection,
  onOpenGamesSection,
  onOpenMySpaceSection,
  onOpenAdminsSection,
  onBackToMenu,
  onLogout,
  children,
}: AdminShellPanelProps) {
  if (adminSection === "menu") {
    return (
      <>
        <div className="panel-header">
          <div>
            <h2>Backoffice</h2>
            <p>Seleziona un'area operativa.</p>
          </div>
          <button className="button-ghost" type="button" onClick={onLogout}>
            Sign out
          </button>
        </div>
        <div className="admin-shell-nav-actions admin-menu-grid">
          {canAccessFinance ? (
            <button className="button" type="button" onClick={onOpenFinanceSection}>
              Finance
            </button>
          ) : null}
          {canAccessEndUser ? (
            <button className="button" type="button" onClick={onOpenPlayersSection}>
              Player admin
            </button>
          ) : null}
          {canAccessMines ? (
            <button className="button" type="button" onClick={onOpenGamesSection}>
              Mines backoffice
            </button>
          ) : null}
          <button className="button" type="button" onClick={onOpenMySpaceSection}>
            My Space
          </button>
          {isSuperadmin ? (
            <button className="button" type="button" onClick={onOpenAdminsSection}>
              Amministratori
            </button>
          ) : null}
        </div>
      </>
    );
  }

  return (
    <>
      <div className="panel-header">
        <div>
          <h2>{adminSectionLabel}</h2>
          <p>
            {adminSection === "casino_king"
              ? "Area finanziaria operatore."
              : adminSection === "players"
                ? "Lista e schede giocatori."
                : adminSection === "my_space"
                  ? "Profilo e impostazioni dell'account admin."
                  : adminSection === "admins"
                    ? "Gestione account admin. Solo Superadmin."
                    : "Bozza editoriale, pubblicazione live, configurazioni runtime e asset della board di Mines."}
          </p>
        </div>
        <div className="inline-actions">
          <button className="button-secondary" type="button" onClick={onBackToMenu}>
            Menu
          </button>
          <button className="button-ghost" type="button" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </div>
      {children}
    </>
  );
}
