"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { apiRequest, readErrorMessage } from "../lib/api";
import { sanitizeAuthReturnTo, withAuthReturnTo } from "../lib/auth-return";
import {
  dispatchPlayerAuthChanged,
  hasPlayerAuthSnapshot,
  readPlayerAuthSnapshot,
  storePlayerAuthSession,
} from "../lib/player-auth";

const PLAYER_DOCUMENT_ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"];
const PLAYER_DOCUMENT_MAX_BYTES = 5 * 1024 * 1024;

type RegisterStep = 1 | 2;

type RegisterResponse = {
  user_id: string;
  bootstrap_transaction_id: string;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
};

type RegistrationGateState = "checking" | "guest" | "authenticated";

export function PlayerRegisterPage() {
  const router = useRouter();
  const [registrationGate, setRegistrationGate] = useState<RegistrationGateState>("checking");
  const [step, setStep] = useState<RegisterStep>(1);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [fiscalCode, setFiscalCode] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [siteAccessPassword, setSiteAccessPassword] = useState("");
  const [documentFrontName, setDocumentFrontName] = useState("");
  const [documentBackName, setDocumentBackName] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [createdUserId, setCreatedUserId] = useState<string | null>(null);
  const [returnTo, setReturnTo] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sanitizedReturnTo = sanitizeAuthReturnTo(params.get("return_to"));
    setReturnTo(sanitizedReturnTo);

    if (hasPlayerAuthSnapshot(readPlayerAuthSnapshot())) {
      setRegistrationGate("authenticated");
      if (sanitizedReturnTo) {
        window.location.replace(sanitizedReturnTo);
        return;
      }
      router.replace("/account");
      return;
    }
    setRegistrationGate("guest");
  }, [router]);

  function handleContinue() {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password || !siteAccessPassword.trim()) {
      setStatus("Enter email, password and access code before continuing.");
      return;
    }

    setEmail(normalizedEmail);
    setStep(2);
    setStatus(null);
  }

  function handleDocumentFileChange(file: File | null, onValidFileName: (fileName: string) => void) {
    if (!file) {
      onValidFileName("");
      return true;
    }
    if (!PLAYER_DOCUMENT_ALLOWED_MIME_TYPES.includes(file.type)) {
      onValidFileName("");
      setStatus("Document images must be PNG, JPEG, or WebP.");
      return false;
    }
    if (file.size > PLAYER_DOCUMENT_MAX_BYTES) {
      onValidFileName("");
      setStatus("Document images must be 5 MB or smaller per side.");
      return false;
    }
    onValidFileName(file.name);
    setStatus(null);
    return true;
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
          site_access_password: siteAccessPassword.trim(),
          first_name: normalizedFirstName,
          last_name: normalizedLastName,
          fiscal_code: normalizedFiscalCode,
          phone_number: normalizedPhoneNumber,
        }),
      });

      const loginData = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: normalizedEmail, password }),
      });

      storePlayerAuthSession({
        accessToken: loginData.access_token,
        email: normalizedEmail,
        firstName: normalizedFirstName,
        lastName: normalizedLastName,
        fiscalCode: normalizedFiscalCode,
        phoneNumber: normalizedPhoneNumber,
      });
      dispatchPlayerAuthChanged();

      setCreatedUserId(data.user_id);
      setStatus("Registration completed. Your document images will be requested again when backend upload is enabled.");
      if (returnTo) {
        window.location.assign(returnTo);
        return;
      }
      router.push("/account");
      router.refresh();
    } catch (error) {
      setStatus(readErrorMessage(error, "Registration failed."));
    } finally {
      setBusy(false);
    }
  }

  if (registrationGate === "checking") {
    return (
      <section className="site-v3-player-panel">
        <p className="site-v3-player-eyebrow">Player</p>
        <h1>Registration</h1>
        <p>Checking current player session.</p>
      </section>
    );
  }

  if (registrationGate === "authenticated") {
    return (
      <section className="site-v3-player-panel">
        <p className="site-v3-player-eyebrow">Player</p>
        <h1>Registration</h1>
        <p>You are already signed in. Opening your account.</p>
        <div className="site-v3-player-status">Registration is available only before signing in.</div>
      </section>
    );
  }

  return (
    <section className="site-v3-player-panel">
      <div>
        <p className="site-v3-player-eyebrow">Player</p>
        <h1>Registration</h1>
        <p>Crea il tuo account player.</p>
      </div>

      {status ? <div className="site-v3-player-status">{status}</div> : null}

      <form className="site-v3-player-form" onSubmit={(event) => void handleSubmit(event)}>
        {step === 1 ? (
          <div className="site-v3-player-field-grid">
            <label>
              First name
              <input value={firstName} onChange={(event) => setFirstName(event.target.value)} autoComplete="given-name" />
            </label>
            <label>
              Last name
              <input value={lastName} onChange={(event) => setLastName(event.target.value)} autoComplete="family-name" />
            </label>
            <label>
              Fiscal code
              <input value={fiscalCode} onChange={(event) => setFiscalCode(event.target.value)} autoComplete="off" />
            </label>
            <label>
              Phone number
              <input value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} autoComplete="tel" />
            </label>
            <label>
              Email
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </label>
            <label>
              Access code
              <input
                type="password"
                value={siteAccessPassword}
                onChange={(event) => setSiteAccessPassword(event.target.value)}
                autoComplete="off"
                required
              />
            </label>
          </div>
        ) : (
          <div className="site-v3-player-stack">
            <div className="site-v3-player-status">
              Document images: PNG, JPEG, or WebP recommended, max 5 MB per side. Recommended 1600 x 1000 px
              or 1000 x 1600 px, matching document orientation. They are not rendered or resized yet; the backend
              does not store document files.
            </div>
            <div className="site-v3-player-field-grid">
              <label>
                Document front
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => {
                    const isValid = handleDocumentFileChange(event.target.files?.[0] ?? null, setDocumentFrontName);
                    if (!isValid) {
                      event.currentTarget.value = "";
                    }
                  }}
                  required
                />
              </label>
              <label>
                Document back
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => {
                    const isValid = handleDocumentFileChange(event.target.files?.[0] ?? null, setDocumentBackName);
                    if (!isValid) {
                      event.currentTarget.value = "";
                    }
                  }}
                  required
                />
              </label>
            </div>
          </div>
        )}

        <div className="site-v3-player-form-actions">
          {step === 1 ? (
            <button className="site-v3-button" type="button" onClick={handleContinue}>
              Continue
            </button>
          ) : (
            <>
              <button className="site-v3-button is-secondary" type="button" onClick={() => setStep(1)}>
                Back
              </button>
              <button className="site-v3-button" disabled={busy} type="submit">
                {busy ? "Completing..." : "Complete registration"}
              </button>
            </>
          )}
        </div>
      </form>

      <div className="site-v3-player-form-actions">
        <a className="site-v3-button is-secondary" href={withAuthReturnTo("/login", returnTo)}>
          Sign in
        </a>
        <a className="site-v3-button is-secondary" href={returnTo ?? "/"}>
          Back to lobby
        </a>
      </div>

      {createdUserId ? <div className="site-v3-player-status">Player created: {createdUserId}</div> : null}
    </section>
  );
}
