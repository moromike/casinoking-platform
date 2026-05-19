"use client";

import type { TitleEditorConfigField } from "./types";

type TitleEditorConfigTabProps = {
  fields: readonly TitleEditorConfigField[];
};

export function TitleEditorConfigTab({ fields }: TitleEditorConfigTabProps) {
  return (
    <div className="stack">
      {fields.map((field) => {
        if (field.kind === "custom") {
          return <div key={field.id}>{field.render()}</div>;
        }

        return (
          <article className="admin-card" key={field.id}>
            <div className="admin-card-heading">
              <div>
                <h3>{field.title}</h3>
                {field.description ? <p>{field.description}</p> : null}
              </div>
            </div>
            <div className="stack">
              <section className="stack compact">
                <div className="inline-actions">
                  {field.choices.map((choice) => (
                    <label className="meta-pill" key={String(choice)}>
                      <input
                        type="checkbox"
                        checked={field.selectedValues.includes(choice)}
                        onChange={() => field.onToggleChoice(choice)}
                      />
                      {field.formatChoice ? field.formatChoice(choice) : String(choice)}
                    </label>
                  ))}
                </div>
                <label className="field">
                  <span>Default</span>
                  <select
                    value={String(field.defaultValue)}
                    onChange={(event) => {
                      const selected = field.choices.find(
                        (choice) => String(choice) === event.target.value,
                      );
                      if (selected !== undefined) {
                        field.onDefaultChange(selected);
                      }
                    }}
                  >
                    {field.selectedValues.map((choice) => (
                      <option key={String(choice)} value={String(choice)}>
                        {field.formatDefaultChoice
                          ? field.formatDefaultChoice(choice)
                          : field.formatChoice
                            ? field.formatChoice(choice)
                            : String(choice)}
                      </option>
                    ))}
                  </select>
                </label>
              </section>
            </div>
          </article>
        );
      })}
    </div>
  );
}
