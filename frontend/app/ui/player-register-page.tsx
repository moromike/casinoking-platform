"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  dispatchPlayerAuthChanged,
  hasStoredPlayerAccessToken,
  preparePlayerAuthReturnHandoff,
  storePlayerAuthSession,
} from "@/app/lib/auth-storage";
import { sanitizeAuthReturnTo, withAuthReturnTo } from "@/app/lib/auth-return";
import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { Button } from "@/app/ui/components/button";

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
  const [registrationGate, setRegistrationGate] =
    useState<RegistrationGateState>("checking");
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

    if (hasStoredPlayerAccessToken()) {
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
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
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
        preparePlayerAuthReturnHandoff({
          accessToken: loginData.access_token,
          email: normalizedEmail,
          returnTo,
        });
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
      <section className="panel stack">
        <div>
          <p className="eyebrow">Player</p>
          <h2 style={{ marginBottom: 8 }}>Registration</h2>
          <p style={{ margin: 0 }}>Checking current player session.</p>
        </div>
      </section>
    );
  }

  if (registrationGate === "authenticated") {
    return (
      <section className="panel stack">
        <div>
          <p className="eyebrow">Player</p>
          <h2 style={{ marginBottom: 8 }}>Registration</h2>
          <p style={{ margin: 0 }}>You are already signed in. Opening your account.</p>
        </div>
        <div className="status-line">Registration is available only before signing in.</div>
      </section>
    );
  }

  return (
    <section className="panel stack">
      <div>
        <p className="eyebrow">Player</p>
        <h2 style={{ marginBottom: 8 }}>Registration</h2>
        <p style={{ margin: 0 }}>Two-step player onboarding with a server-checked access code.</p>
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
            <label>
              Access code
              <input
                name="site_access_password"
                type="password"
                value={siteAccessPassword}
                onChange={(event) => setSiteAccessPassword(event.target.value)}
                autoComplete="off"
                required
              />
            </label>
          </div>
        ) : (
          <div className="stack">
            <div className="status-line">
              Document images: PNG, JPEG, or WebP recommended, max 5 MB per side.
              Recommended 1600 x 1000 px or 1000 x 1600 px, matching document
              orientation. They are not rendered or resized yet; the backend does not
              store document files.
            </div>
            <div className="field-grid player-form-fields">
              <label>
                Document front
                <input
                  name="document_front"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => {
                    const isValid = handleDocumentFileChange(
                      event.target.files?.[0] ?? null,
                      setDocumentFrontName,
                    );
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
                  name="document_back"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => {
                    const isValid = handleDocumentFileChange(
                      event.target.files?.[0] ?? null,
                      setDocumentBackName,
                    );
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

        <div className="player-form-actions">
          {step === 1 ? (
            <Button type="button" onClick={handleContinue}>
              Continue
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setStep(1);
                  setStatus(null);
                }}
              >
                Back
              </Button>
              <Button isLoading={busy} type="submit" disabled={busy}>
                Complete registration
              </Button>
            </>
          )}
        </div>
      </form>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        <Button href={withAuthReturnTo("/login", returnTo)} variant="secondary">
          Sign in
        </Button>
        <Button href={returnTo ?? "/"} variant="secondary">
          Back to lobby
        </Button>
      </div>

      {createdUserId ? (
        <div className="status-line">Player created: {createdUserId}</div>
      ) : null}
    </section>
  );
}
