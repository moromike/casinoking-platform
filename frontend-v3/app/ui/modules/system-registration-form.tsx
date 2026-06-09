import type { SiteV3PublicModule } from "../../lib/types";
import { readRegistrationFormConfig } from "../registration-form-config";

export function SystemRegistrationForm({ module }: { module: SiteV3PublicModule }) {
  const config = readRegistrationFormConfig(module.config_json);
  return (
    <section className="site-v3-rich-text">
      <p className="site-v3-kicker">{config.eyebrow}</p>
      <h2>{config.headline}</h2>
      <p>{config.body}</p>
      {config.legalNoteHtml ? <div dangerouslySetInnerHTML={{ __html: config.legalNoteHtml }} /> : null}
    </section>
  );
}
