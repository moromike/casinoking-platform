"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";

const HIDDEN_SITE_ACCESS_PASSWORD = "change-me";
const PLAYER_AUTH_EVENT = "player-auth-changed";

type RegisterStep = 1 | 2;

type RegisterResponse = {
  user_id: string;
  bootstrap_transaction_id: string;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
};

export function PlayerRegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<RegisterStep>(1);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [fiscalCode, setFiscalCode] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [documentFrontName, setDocumentFrontName] = useState("");
  const [documentBackName, setDocumentBackName] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [createdUserId, setCreatedUserId] = useState<string | null>(null);

  function handleContinue() {
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail || !password) {
      setStatus("Enter email and password before continuing.");
      return;
    }

    setEmail(normalizedEmail);
    setStep(2);
    setStatus(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!documentFrontName || !documentBackName) {
      setStatus("Add both document sides before completing registration.");
      return;
    }

    setBusy(true);
    setStatus(null);

    try {
      const normalizedEmail = email.trim().toLowerCase();
      const normalizedFirstName = firstName.trim();
      const normalizedLastName = lastName.trim();
      const normalizedFiscalCode = fiscalCode.trim();
      const normalizedPhoneNumber = phoneNumber.trim();

      const data = await apiRequest<RegisterResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: normalizedEmail,
          password,
          site_access_password: HIDDEN_SITE_ACCESS_PASSWORD,
          first_name: normalizedFirstName,
          last_name: normalizedLastName,
          fiscal_code: normalizedFiscalCode,
          phone_number: normalizedPhoneNumber,
        }),
      });

      const loginData = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
      });

      if (typeof window !== "undefined") {
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.accessToken, loginData.access_token);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.email, normalizedEmail);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.firstName, normalizedFirstName);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.lastName, normalizedLastName);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.fiscalCode, normalizedFiscalCode);
        window.localStorage.setItem(PLAYER_STORAGE_KEYS.phoneNumber, normalizedPhoneNumber);
        window.dispatchEvent(new Event(PLAYER_AUTH_EVENT));
      }

      setCreatedUserId(data.user_id);
      setStatus("Registration completed. Your document images will be requested again when backend upload is enabled.");
      router.push("/account");
      router.refresh();
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

      <form className="form-card stack" onSubmit={handleSubmit}>
        {step === 1 ? (
          <div className="field-grid player-form-fields">
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
          </div>
        ) : (
          <div className="stack">
            <div className="field-grid player-form-fields">
              <label>
                Document front
                <input
                  name="document_front"
                  type="file"
                  accept="image/*"
                  onChange={(event) =>
                    setDocumentFrontName(event.target.files?.[0]?.name ?? "")
                  }
                  required
                />
              </label>
              <label>
                Document back
                <input
                  name="document_back"
                  type="file"
                  accept="image/*"
                  onChange={(event) =>
                    setDocumentBackName(event.target.files?.[0]?.name ?? "")
                  }
                  required
                />
              </label>
            </div>
            <div className="status-line">
              Registration will continue with the Step 1 data. The backend does not store document files yet, so they are ignored for now.
            </div>
          </div>
        )}

        <div className="player-form-actions">
          {step === 1 ? (
            <button className="button" type="button" onClick={handleContinue}>
              Continue
            </button>
          ) : (
            <>
              <button
                className="button-secondary"
                type="button"
                onClick={() => {
                  setStep(1);
                  setStatus(null);
                }}
              >
                Back
              </button>
              <button className="button" type="submit" disabled={busy}>
                {busy ? "Creating player..." : "Complete registration"}
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
