export function getTitleDetailHref(engineCode: string, titleCode: string): string {
  return `/admin/games/${encodeURIComponent(engineCode)}/titles/${encodeURIComponent(titleCode)}`;
}
