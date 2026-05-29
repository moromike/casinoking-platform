"use client";

import { apiFormRequest, apiRequest } from "@/app/lib/api";
import type {
  SiteV3ArchivePayload,
  SiteV3DraftPayload,
  SiteV3ListStatusFilter,
  SiteV3ModuleDefinitionPayload,
  SiteV3ModuleDefinitionPublishResponse,
  SiteV3ModuleDefinitionResponse,
  SiteV3ModuleDefinitionsResponse,
  SiteV3PageResponse,
  SiteV3PagesResponse,
  SiteV3PublishPayload,
  SiteV3PublishResponse,
  SiteV3SiteAsset,
  SiteV3ValidatePayload,
  SiteV3ValidationResult,
  SiteV3VersionsResponse,
} from "./site-v3-admin-types";

export async function listSiteV3Pages({
  accessToken,
  siteCode,
  locale,
  status,
}: {
  accessToken: string;
  siteCode: string;
  locale: string;
  status: SiteV3ListStatusFilter;
}): Promise<SiteV3PagesResponse> {
  const params = new URLSearchParams({
    locale,
    status,
    page: "1",
    limit: "50",
  });
  return apiRequest<SiteV3PagesResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages?${params.toString()}`,
    {},
    accessToken,
  );
}

export async function getSiteV3Page({
  accessToken,
  siteCode,
  pageCode,
  locale,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  locale: string;
}): Promise<SiteV3PageResponse> {
  const params = new URLSearchParams({ locale });
  return apiRequest<SiteV3PageResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}?${params.toString()}`,
    {},
    accessToken,
  );
}

export async function saveSiteV3Draft({
  accessToken,
  siteCode,
  pageCode,
  payload,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  payload: SiteV3DraftPayload;
}): Promise<SiteV3PageResponse> {
  return apiRequest<SiteV3PageResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}/draft`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function validateSiteV3Draft({
  accessToken,
  siteCode,
  pageCode,
  payload,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  payload: SiteV3ValidatePayload;
}): Promise<SiteV3ValidationResult> {
  return apiRequest<SiteV3ValidationResult>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}/validate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function publishSiteV3Page({
  accessToken,
  siteCode,
  pageCode,
  payload,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  payload: SiteV3PublishPayload;
}): Promise<SiteV3PublishResponse> {
  return apiRequest<SiteV3PublishResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}/publish`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function archiveSiteV3Page({
  accessToken,
  siteCode,
  pageCode,
  payload,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  payload: SiteV3ArchivePayload;
}): Promise<{ page: SiteV3PageResponse["page"] }> {
  return apiRequest<{ page: SiteV3PageResponse["page"] }>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}/archive`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function listSiteV3Versions({
  accessToken,
  siteCode,
  pageCode,
  locale,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  locale: string;
}): Promise<SiteV3VersionsResponse> {
  const params = new URLSearchParams({ locale });
  return apiRequest<SiteV3VersionsResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}/versions?${params.toString()}`,
    {},
    accessToken,
  );
}

export async function listSiteV3ModuleDefinitions({
  accessToken,
  siteCode,
  status = "all",
}: {
  accessToken: string;
  siteCode: string;
  status?: "draft" | "published" | "archived" | "all";
}): Promise<SiteV3ModuleDefinitionsResponse> {
  const params = new URLSearchParams({ status });
  return apiRequest<SiteV3ModuleDefinitionsResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/module-definitions?${params.toString()}`,
    {},
    accessToken,
  );
}

export async function createSiteV3ModuleDefinition({
  accessToken,
  siteCode,
  payload,
}: {
  accessToken: string;
  siteCode: string;
  payload: SiteV3ModuleDefinitionPayload;
}): Promise<SiteV3ModuleDefinitionResponse> {
  return apiRequest<SiteV3ModuleDefinitionResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/module-definitions`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    accessToken,
  );
}

export async function publishSiteV3ModuleDefinition({
  accessToken,
  siteCode,
  moduleCode,
}: {
  accessToken: string;
  siteCode: string;
  moduleCode: string;
}): Promise<SiteV3ModuleDefinitionPublishResponse> {
  return apiRequest<SiteV3ModuleDefinitionPublishResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/module-definitions/${encodeURIComponent(moduleCode)}/publish`,
    { method: "POST" },
    accessToken,
  );
}

export async function archiveSiteV3ModuleDefinition({
  accessToken,
  siteCode,
  moduleCode,
}: {
  accessToken: string;
  siteCode: string;
  moduleCode: string;
}): Promise<SiteV3ModuleDefinitionResponse> {
  return apiRequest<SiteV3ModuleDefinitionResponse>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/module-definitions/${encodeURIComponent(moduleCode)}/archive`,
    { method: "POST" },
    accessToken,
  );
}

export async function issueSiteV3DraftPreviewToken({
  accessToken,
  siteCode,
  pageCode,
  locale,
}: {
  accessToken: string;
  siteCode: string;
  pageCode: string;
  locale: string;
}): Promise<{ token: string; preview_url: string; expires_at: string; draft_version: number }> {
  const params = new URLSearchParams({ locale });
  return apiRequest<{ token: string; preview_url: string; expires_at: string; draft_version: number }>(
    `/admin/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}/draft-preview-token?${params.toString()}`,
    { method: "POST" },
    accessToken,
  );
}

export async function listSiteV3Assets({
  accessToken,
  siteCode,
  assetKind = "homepage_banner",
}: {
  accessToken: string;
  siteCode: string;
  assetKind?: string;
}): Promise<SiteV3SiteAsset[]> {
  const params = new URLSearchParams({ asset_kind: assetKind });
  return apiRequest<SiteV3SiteAsset[]>(
    `/admin/sites/${encodeURIComponent(siteCode)}/assets?${params.toString()}`,
    {},
    accessToken,
  );
}

export async function uploadSiteV3Asset({
  accessToken,
  siteCode,
  file,
  assetKind = "homepage_banner",
}: {
  accessToken: string;
  siteCode: string;
  file: File;
  assetKind?: string;
}): Promise<SiteV3SiteAsset> {
  const formData = new FormData();
  formData.set("asset_kind", assetKind);
  formData.set("file", file);

  return apiFormRequest<SiteV3SiteAsset>(
    `/admin/sites/${encodeURIComponent(siteCode)}/assets`,
    formData,
    accessToken,
  );
}
