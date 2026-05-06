"use client";

import { FormEvent, useState } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GameMasterCard } from "./game-master-card";
import { GameVariantList } from "./game-variant-list";

type GameCategoryViewProps = {
  master: CatalogTitle;
  variants: CatalogTitle[];
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onDuplicateTitle?: (
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string },
  ) => Promise<void>;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
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
}: GameCategoryViewProps) {
  const [variantTitleCode, setVariantTitleCode] = useState("");
  const [variantName, setVariantName] = useState("");
  const isDuplicateBusy = busyAction === "duplicate-title";
  const canCreateVariant =
    Boolean(onDuplicateTitle) &&
    busyAction === null &&
    variantTitleCode.trim().length > 0 &&
    variantName.trim().length > 0;

  async function handleCreateVariant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!onDuplicateTitle || !canCreateVariant) {
      return;
    }

    await onDuplicateTitle(master, {
      title_code: variantTitleCode.trim().toLowerCase(),
      display_name: variantName.trim(),
    });
    setVariantTitleCode("");
    setVariantName("");
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
                  value={variantTitleCode}
                  onChange={(event) => setVariantTitleCode(event.target.value)}
                  placeholder="mines_lagoon"
                />
              </label>
              <label className="games-create-field">
                <span>Display name</span>
                <input
                  value={variantName}
                  onChange={(event) => setVariantName(event.target.value)}
                  placeholder="Mines Lagoon"
                />
              </label>
              <button className="button" type="submit" disabled={!canCreateVariant}>
                {isDuplicateBusy ? "Creating..." : "Create variant"}
              </button>
            </form>
          ) : null}
        </div>

        <GameVariantList
          variants={variants}
          selectedTitleCode={selectedTitleCode}
          busyAction={busyAction}
          onOpenTitle={onOpenTitle}
          onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          onPreviewTitle={onPreviewTitle}
        />
      </section>
    </section>
  );
}
