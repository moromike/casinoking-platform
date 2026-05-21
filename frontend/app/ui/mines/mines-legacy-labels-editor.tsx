"use client";

const MINES_LABEL_FIELDS: Array<{
  key: MinesUiLabelKey;
  label: string;
}> = [
  { key: "bet", label: "Bet" },
  { key: "bet_loading", label: "Bet loading" },
  { key: "collect", label: "Collect" },
  { key: "collect_loading", label: "Collect loading" },
  { key: "home", label: "Home" },
  { key: "fullscreen", label: "Fullscreen" },
  { key: "game_info", label: "Game info" },
];

export type MinesUiLabelKey =
  | "bet"
  | "bet_loading"
  | "collect"
  | "collect_loading"
  | "home"
  | "fullscreen"
  | "game_info";

export type MinesUiLabels = Record<"demo" | "real", Record<MinesUiLabelKey, string>>;

type MinesLegacyLabelsEditorProps = {
  labels: MinesUiLabels;
  onChange: (mode: "demo" | "real", key: MinesUiLabelKey, value: string) => void;
};

export function MinesLegacyLabelsEditor({
  labels,
  onChange,
}: MinesLegacyLabelsEditorProps) {
  return (
    <div className="labels-editor-panel">
      <div className="labels-editor-toolbar">
        <h3>Demo / Real labels</h3>
      </div>
      <div className="labels-editor-table">
        <div className="labels-editor-head">
          <span />
          <span>Demo mode labels</span>
          <span>Real mode labels</span>
        </div>
        {MINES_LABEL_FIELDS.map((field) => (
          <div className="labels-editor-row" key={field.key}>
            <label htmlFor={`demo-${field.key}`}>{field.label}</label>
            <input
              id={`demo-${field.key}`}
              value={labels.demo?.[field.key] ?? ""}
              onChange={(event) => onChange("demo", field.key, event.target.value)}
            />
            <input
              id={`real-${field.key}`}
              value={labels.real?.[field.key] ?? ""}
              onChange={(event) => onChange("real", field.key, event.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
