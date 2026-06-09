import { PlayerRegisterPage } from "../ui/player-register-page";
import { PlayerShell } from "../ui/player-shell";
import { loadSiteV3Page, normalizeSingleParam } from "../lib/api";
import { readRegistrationFormConfig } from "../ui/registration-form-config";
import { findFirstModule } from "../ui/site-v3-render-helpers";

export const dynamic = "force-dynamic";

type RegisterPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  const resolvedSearchParams = await searchParams;
  const siteCode = normalizeSingleParam(resolvedSearchParams?.site_code, "casinoking");
  const locale = normalizeSingleParam(resolvedSearchParams?.locale, "it");
  const result = await loadSiteV3Page({ siteCode, pageCode: "register", locale });
  const registrationModule = result.page
    ? findFirstModule(result.page.modules, "system_registration_form")
    : null;
  const registrationConfig = readRegistrationFormConfig(registrationModule?.config_json);

  return (
    <PlayerShell>
      <PlayerRegisterPage config={registrationConfig} />
    </PlayerShell>
  );
}
