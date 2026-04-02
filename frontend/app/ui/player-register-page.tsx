"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";

const HIDDEN_SITE_ACCESS_PASSWORD = "change-me";

type RegisterStep = 1 | 2;

type RegisterResponse = {
  user_id: string;
  bootstrap_transaction_id: string;
};

export function PlayerRegisterPage() {
  const [step, setStep] = useState<RegisterStep>(1);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [fiscalCode, setFiscalCode] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [createdUserId, setCreatedUserId] = useState<string | null>(null);

  function handleContinue() {
    setStep(2);
    setStatus(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus(null);

    try {
      const data = await apiRequest<RegisterResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          site_access_password: HIDDEN_SITE_ACCESS_PASSWORD,
          first_name: firstName,
          last_name: lastName,
          fiscal_code: fiscalCode,
          phone_number: phoneNumber,
        }),
      });

      if (typeof window !== "undefined") {
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.email, email);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.firstName, firstName);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.lastName, lastName);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.fiscalCode, fiscalCode);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.phoneNumber, phoneNumber);
      }

      setCreatedUserId(data.user_id);
      setStatus("Registration completed.");
    } catch (error) {
      setStatus(readErrorMessage(error, "Registration failed."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel stack">
      <div>
        <p className="eyebrow">Player</p>
        <h2 style={{ marginBottom: 8 }}>Registration</h2>
        <p style={{ margin: 0 }}>Two-step player onboarding with hidden site access bootstrap.</p>
      </div>

      {status ? <div className="status-line">{status}</div> : null}

      <form className="form-card" onSubmit={handleSubmit}>
        {step === 1 ? (
          <div className="field-grid">
            <label>
              First name
              <input
                name="first_name"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                autoComplete="given-name"
              />
            </label>
            <label>
              Last name
              <input
                name="last_name"
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                autoComplete="family-name"
              />
            </label>
            <label>
              Fiscal code
              <input
                name="fiscal_code"
                value={fiscalCode}
                onChange={(event) => setFiscalCode(event.target.value)}
                autoComplete="off"
              />
            </label>
            <label>
              Phone number
              <input
                name="phone_number"
                value={phoneNumber}
                onChange={(event) => setPhoneNumber(event.target.value)}
                autoComplete="tel"
              />
            </label>
          </div>
        ) : (
          <div className="field-grid">
            <label>
              Email
              <input
                name="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </label>
            <div className="status-line">OTP email verification will be introduced in the next registration iteration.</div>
          </div>
        )}

        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          {step === 1 ? (
            <button className="button" type="button" onClick={handleContinue}>
              Continue
            </button>
          ) : (
            <>
              <button
                className="button-secondary"
                type="button"
                onClick={() => setStep(1)}
              >
                Back
              </button>
              <button className="button" type="submit" disabled={busy}>
                {busy ? "Creating player..." : "Create player"}
              </button>
            </>
          )}
        </div>
      </form>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        <Link className="button-secondary" href="/login">
          Sign in
        </Link>
        <Link className="button-secondary" href="/">
          Back to lobby
        </Link>
      </div>

      {createdUserId ? (
        <div className="status-line">Player created: {createdUserId}</div>
      ) : null}
    </section>
  );
}
