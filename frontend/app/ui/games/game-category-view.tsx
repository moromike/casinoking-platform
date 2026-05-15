"use client";

import { FormEvent, useState } from "react";

import {
  isTitleCodeValid,
  normalizeTitleCodeInput,
  TITLE_CODE_HELPER_TEXT,
} from "@/app/lib/title-code";
import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GameMasterCard } from "./game-master-card";
import { GameVariantList } from "./game-variant-list";

type VariantFilter = "active" | "inactive" | "archived" | "all";

type GameCategoryViewProps = {
  master: CatalogTitle;
  variants: CatalogTitle[];
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onDuplicateTitle?: (
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string; is_test?: boolean },
  ) => Promise<boolean | void>;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
  onArchiveTitle?: (title: CatalogTitle) => Promise<void>;
  onRestoreTitle?: (title: CatalogTitle) => Promise<void>;
};

export function GameCategoryView({
  master,
  variants,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
  onPreviewTitle,
  onArchiveTitle,
  onRestoreTitle,
}: GameCategoryViewProps) {
  const [variantTitleCode, setVariantTitleCode] = useState("");
  const [variantName, setVariantName] = useState("");
  const [variantIsTest, setVariantIsTest] = useState(false);
  const [variantFilter, setVariantFilter] = useState<VariantFilter>("active");
  const [testOnly, setTestOnly] = useState(false);
  const normalizedVariantTitleCode = normalizeTitleCodeInput(variantTitleCode);
  const hasTitleCodeInput = normalizedVariantTitleCode.length > 0;
  const isVariantTitleCodeValid = isTitleCodeValid(normalizedVariantTitleCode);
  const isVariantTitleCodeInvalid = hasTitleCodeInput && !isVariantTitleCodeValid;
  const isDuplicateBusy = busyAction === "duplicate-title";
  const canCreateVariant =
    Boolean(onDuplicateTitle) &&
    busyAction === null &&
    isVariantTitleCodeValid &&
    variantName.trim().length > 0;
  const activeCount = variants.filter((title) => isActiveVariant(title)).length;
  const inactiveCount = variants.filter((title) => isInactiveVariant(title)).length;
  const archivedCount = variants.filter((title) => title.is_archived === true).length;
  const testCount = variants.filter((title) => title.is_test === true).length;
  const filteredVariants = variants.filter((title) => {
    if (testOnly && title.is_test !== true) {
      return false;
    }
    if (variantFilter === "all") {
      return true;
    }
    if (variantFilter === "active") {
      return isActiveVariant(title);
    }
    if (variantFilter === "inactive") {
      return isInactiveVariant(title);
    }
    return title.is_archived === true;
  });

  async function handleCreateVariant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!onDuplicateTitle || !canCreateVariant) {
      return;
    }

    const wasCreated = await onDuplicateTitle(master, {
      title_code: normalizedVariantTitleCode,
      display_name: variantName.trim(),
      is_test: variantIsTest,
    });
    if (wasCreated === false) {
      return;
    }
    setVariantTitleCode("");
    setVariantName("");
    setVariantIsTest(false);
  }

  return (
    <section className="games-category-view" aria-labelledby="games-category-mines-title">
      <div className="games-category-header">
        <div className="games-category-heading">
          <span className="games-section-label">Game category</span>
          <h4 id="games-category-mines-title">Mines</h4>
        </div>
        <dl className="games-category-meta" aria-label="Mines summary">
          <div>
            <dt>Engine</dt>
            <dd>{master.engine_code}</dd>
          </div>
          <div>
            <dt>Variants</dt>
            <dd>{variants.length}</dd>
          </div>
          <div>
            <dt>Site</dt>
            <dd>{master.site_title_status}</dd>
          </div>
        </dl>
      </div>

      <GameMasterCard
        master={master}
        variantsCount={variants.length}
        onPreviewTitle={onPreviewTitle}
      />

      <section className="games-variants-section" aria-labelledby="games-variants-title">
        <div className="games-variants-toolbar">
          <div className="games-variants-title">
            <span className="games-section-label">Editable titles</span>
            <h5 id="games-variants-title">Variants</h5>
          </div>

          {onDuplicateTitle ? (
            <form
              className="games-create-inline"
              aria-label="Create Mines variant from master"
              onSubmit={handleCreateVariant}
            >
              <label className="games-create-field">
                <span>Title code</span>
                <input
                  aria-describedby="games-create-title-code-helper"
                  aria-invalid={isVariantTitleCodeInvalid}
                  autoCapitalize="none"
                  maxLength={64}
                  minLength={3}
                  spellCheck={false}
                  value={variantTitleCode}
                  onChange={(event) => setVariantTitleCode(normalizeTitleCodeInput(event.target.value))}
                  placeholder="mines_lagoon"
                />
                <span
                  className={`games-create-helper ${isVariantTitleCodeInvalid ? "error" : ""}`}
                  id="games-create-title-code-helper"
                >
                  {TITLE_CODE_HELPER_TEXT}
                </span>
              </label>
              <label className="games-create-field">
                <span>Display name</span>
                <input
                  value={variantName}
                  onChange={(event) => setVariantName(event.target.value)}
                  placeholder="Mines Lagoon"
                />
              </label>
              <label className="games-create-test-field">
                <input
                  type="checkbox"
                  checked={variantIsTest}
                  onChange={(event) => setVariantIsTest(event.target.checked)}
                />
                Test
              </label>
              <button className="button" type="submit" disabled={!canCreateVariant}>
                {isDuplicateBusy ? "Creating..." : "Create variant"}
              </button>
            </form>
          ) : null}
        </div>

        <div className="games-variants-filters" aria-label="Variant filters">
          <div className="games-filter-tabs" role="group" aria-label="Status filter">
            {([
              ["active", `Active (${activeCount})`],
              ["inactive", `Inactive (${inactiveCount})`],
              ["archived", `Archived (${archivedCount})`],
              ["all", `All (${variants.length})`],
            ] as const).map(([value, label]) => (
              <button
                className={variantFilter === value ? "button" : "button-secondary"}
                key={value}
                type="button"
                onClick={() => setVariantFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="games-test-filter">
            <input
              type="checkbox"
              checked={testOnly}
              onChange={(event) => setTestOnly(event.target.checked)}
            />
            Test only ({testCount})
          </label>
        </div>

        <GameVariantList
          variants={filteredVariants}
          emptyMessage={variants.length === 0 ? "No variants yet." : "No variants match these filters."}
          selectedTitleCode={selectedTitleCode}
          busyAction={busyAction}
          onOpenTitle={onOpenTitle}
          onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          onPreviewTitle={onPreviewTitle}
          onArchiveTitle={onArchiveTitle}
          onRestoreTitle={onRestoreTitle}
        />
      </section>
    </section>
  );
}

function isActiveVariant(title: CatalogTitle) {
  return (
    title.is_archived !== true &&
    title.status === "active" &&
    title.site_title_status === "active"
  );
}

function isInactiveVariant(title: CatalogTitle) {
  return title.is_archived !== true && !isActiveVariant(title);
}
