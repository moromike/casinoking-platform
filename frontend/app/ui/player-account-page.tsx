"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";
import type { Wallet } from "@/app/lib/types";

type PlayerProfile = {
  id: string;
  email: string;
  role: string;
  status: string;
  first_name: string | null;
  last_name: string | null;
  fiscal_code: string | null;
  phone_number: string | null;
  created_at: string;
};

type LedgerTransaction = {
  id: string;
  transaction_type: string;
  created_at: string;
  reference_type: string | null;
};

type SessionHistoryItem = {
  game_session_id: string;
  status: "active" | "won" | "lost";
  bet_amount: string;
  multiplier_current: string;
  created_at: string;
};

function readStoredProfileValue(key: (typeof PLAYER_STORAGE_KEYS)[keyof typeof PLAYER_STORAGE_KEYS]): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

export function PlayerAccountPage() {
  const [accessToken, setAccessToken] = useState("");
  const [currentEmail, setCurrentEmail] = useState("");
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [transactions, setTransactions] = useState<LedgerTransaction[]>([]);
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  async function loadAccountState(token: string) {
    setLoading(true);
    setStatus(null);

    try {
      const [profileData, walletData, transactionData, sessionData] = await Promise.all([
        apiRequest<PlayerProfile>("/auth/me", {}, token),
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<LedgerTransaction[]>("/ledger/transactions", {}, token),
        apiRequest<SessionHistoryItem[]>("/games/mines/sessions", {}, token),
      ]);

      setProfile(profileData);
      setWallets(walletData);
      setTransactions(transactionData);
      setSessions(sessionData);
    } catch (error) {
      setStatus(readErrorMessage(error, "Account loading failed."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const storedToken = readStoredProfileValue(PLAYER_STORAGE_KEYS.accessToken);
    const storedEmail = readStoredProfileValue(PLAYER_STORAGE_KEYS.email);

    setAccessToken(storedToken);
    setCurrentEmail(storedEmail);

    if (storedToken) {
      void loadAccountState(storedToken);
    }
  }, []);

  const firstName = profile?.first_name ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.firstName);
  const lastName = profile?.last_name ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.lastName);
  const fiscalCode = profile?.fiscal_code ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.fiscalCode);
  const phoneNumber = profile?.phone_number ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.phoneNumber);

  return (
    <section className="panel stack">
      <div>
        <p className="eyebrow">Player</p>
        <h2 style={{ marginBottom: 8 }}>Account</h2>
        <p style={{ margin: 0 }}>Player account, profile summary, wallets, and session history.</p>
      </div>

      {!accessToken ? (
        <div className="stack">
          <div className="status-line">Guest access</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            <Link className="button" href="/login">
              Sign in
            </Link>
            <Link className="button-secondary" href="/register">
              Register
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            <div className="status-line">{profile?.email || currentEmail || "Player session"}</div>
            <button className="button-secondary" onClick={() => void loadAccountState(accessToken)}>
              {loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {status ? <div className="status-line">{status}</div> : null}

          <div className="stack">
            <h3 style={{ marginBottom: 0 }}>Player profile</h3>
            <div className="panel player-profile-grid">
              <div>
                <strong>Name</strong>
                <div>{`${firstName} ${lastName}`.trim() || "-"}</div>
              </div>
              <div>
                <strong>Email</strong>
                <div>{profile?.email || currentEmail || "-"}</div>
              </div>
              <div>
                <strong>Fiscal code</strong>
                <div>{fiscalCode || "-"}</div>
              </div>
              <div>
                <strong>Phone</strong>
                <div>{phoneNumber || "-"}</div>
              </div>
            </div>
          </div>

          <div className="stack">
            <h3 style={{ marginBottom: 0 }}>Wallets</h3>
            {wallets.length === 0 ? (
              <p style={{ margin: 0 }}>No wallets loaded.</p>
            ) : (
              wallets.map((wallet) => (
                <div key={wallet.wallet_type} className="panel">
                  <strong>{wallet.wallet_type}</strong>
                  <div>{formatChipAmount(toNumericAmount(wallet.balance_snapshot))}</div>
                </div>
              ))
            )}
          </div>

          <div className="stack">
            <h3 style={{ marginBottom: 0 }}>Recent transactions</h3>
            {transactions.length === 0 ? (
              <p style={{ margin: 0 }}>No transactions loaded.</p>
            ) : (
              transactions.slice(0, 5).map((transaction) => (
                <div key={transaction.id} className="panel">
                  <strong>{transaction.transaction_type}</strong>
                  <div>{formatDateTime(transaction.created_at)}</div>
                  <div>{transaction.reference_type ?? "direct"}</div>
                </div>
              ))
            )}
          </div>

          <div className="stack">
            <h3 style={{ marginBottom: 0 }}>Mines sessions</h3>
            {sessions.length === 0 ? (
              <p style={{ margin: 0 }}>No sessions loaded.</p>
            ) : (
              sessions.slice(0, 5).map((session) => (
                <div key={session.game_session_id} className="panel">
                  <strong>{session.status}</strong>
                  <div>{formatChipAmount(toNumericAmount(session.bet_amount))}</div>
                  <div>{session.multiplier_current}x</div>
                  <div>{formatDateTime(session.created_at)}</div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </section>
  );
}
