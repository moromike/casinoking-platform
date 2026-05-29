import { sanitizeAuthReturnTo } from "@/app/lib/auth-return";

export type GameBootRequest = {
  titleCode: string;
  forceDemoMode: boolean;
  previewToken: string;
  isEmbeddedView: boolean;
  returnTo: string | null;
  walletSource: "cash" | "bonus" | null;
};

export function readGameBootRequestFromLocation(
  location: Pick<Location, "search">,
): GameBootRequest | null {
  const searchParams = new URLSearchParams(location.search);
  const titleCode = normalizeGameBootTitleCode(searchParams.get("title_code"));
  if (!titleCode) {
    return null;
  }

  return {
    titleCode,
    forceDemoMode: searchParams.get("mode") === "demo" || searchParams.get("preview") === "1",
    previewToken: searchParams.get("preview_token") ?? "",
    isEmbeddedView: searchParams.get("embed") === "1",
    returnTo: sanitizeAuthReturnTo(searchParams.get("return_to")),
    walletSource: readGameBootWalletSource(searchParams.get("wallet_source")),
  };
}

export function normalizeGameBootTitleCode(value: string | null): string {
  const normalized = (value ?? "").trim().toLowerCase();
  return /^[a-z0-9_]{3,64}$/.test(normalized) ? normalized : "";
}

function readGameBootWalletSource(value: string | null): "cash" | "bonus" | null {
  if (value === "real") {
    return "cash";
  }
  if (value === "bonus") {
    return "bonus";
  }
  return null;
}
