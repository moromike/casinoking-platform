"use client";

import type { ReactNode } from "react";

type AdminSection =
  | "menu"
  | "casino_king"
  | "players"
  | "games"
  | "site"
  | "site_v3"
  | "audit_log"
  | "my_space"
  | "admins"
  | "platform_settings";

type AdminShellPanelProps = {
  adminSection: AdminSection;
  adminSectionLabel: string;
  canAccessFinance: boolean;
  canAccessEndUser: boolean;
  canAccessGames: boolean;
  canAccessAuditLog: boolean;
  isSuperadmin: boolean;
  onOpenFinanceSection: () => void;
  onOpenPlayersSection: () => void;
  onOpenGamesSection: () => void;
  onOpenSiteSection: () => void;
  onOpenSiteV3Section: () => void;
  onOpenAuditLogSection: () => void;
  onOpenMySpaceSection: () => void;
  onOpenAdminsSection: () => void;
  onOpenPlatformSettingsSection: () => void;
  onBackToMenu: () => void;
  onLogout: () => void;
  children?: ReactNode;
};

export function AdminShellPanel({
  adminSection,
  adminSectionLabel,
  canAccessFinance,
  canAccessEndUser,
  canAccessGames,
  canAccessAuditLog,
  isSuperadmin,
  onOpenFinanceSection,
  onOpenPlayersSection,
  onOpenGamesSection,
  onOpenSiteSection,
  onOpenSiteV3Section,
  onOpenAuditLogSection,
  onOpenMySpaceSection,
  onOpenAdminsSection,
  onOpenPlatformSettingsSection,
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
            <p>Select an operating area.</p>
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
          {canAccessGames ? (
            <button className="button" type="button" onClick={onOpenGamesSection}>
              Games
            </button>
          ) : null}
          {canAccessGames ? (
            <button className="button" type="button" onClick={onOpenSiteSection}>
              Site
            </button>
          ) : null}
          {canAccessGames ? (
            <button className="button" type="button" onClick={onOpenSiteV3Section}>
              Site V3
            </button>
          ) : null}
          {canAccessAuditLog ? (
            <button className="button" type="button" onClick={onOpenAuditLogSection}>
              LOG
            </button>
          ) : null}
          <button className="button" type="button" onClick={onOpenMySpaceSection}>
            My Space
          </button>
          {isSuperadmin ? (
            <button className="button" type="button" onClick={onOpenAdminsSection}>
              Administrators
            </button>
          ) : null}
          {isSuperadmin ? (
            <button className="button" type="button" onClick={onOpenPlatformSettingsSection}>
              Platform Settings
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
              ? "Operator finance area."
              : adminSection === "players"
                ? "Player list and profile records."
                : adminSection === "site"
                  ? "Lightweight publication for the site's game lobby."
                  : adminSection === "site_v3"
                    ? "Modular Site V3 builder. Drafts, validation and published snapshots."
                    : adminSection === "audit_log"
                      ? "Operational admin audit events."
                      : adminSection === "my_space"
                        ? "Admin profile and account settings."
                        : adminSection === "admins"
                          ? "Admin account management. Superadmin only."
                          : adminSection === "platform_settings"
                            ? "Read-only platform configuration inventory."
                            : "Game catalog, variants, runtime settings, and title assets."}
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
