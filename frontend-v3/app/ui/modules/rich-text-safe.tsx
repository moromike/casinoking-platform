import type { SiteV3PublicModule } from "../../lib/types";
import { readString } from "../site-v3-render-helpers";

export function RichTextSafe({ module }: { module: SiteV3PublicModule }) {
  const html = readString(module.config_json.html, "");
  if (!html) {
    return null;
  }
  return (
    <section
      className="site-v3-rich-text"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
