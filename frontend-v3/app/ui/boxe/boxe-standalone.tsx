"use client";

import { useCallback, useEffect, useState } from "react";
import type { TitleTheme, TitleThemeSkin } from "@/app/lib/types";
import { GameActionError } from "../game-runtime/game-action-error";
import { GameBootShell } from "../game-runtime/game-boot-shell";
import {
  buildGameErrorDiagnostic,
  buildGameErrorMessage,
  classifyGameError,
  type GameErrorDiagnostic,
  type GameErrorCopyMap,
} from "../game-runtime/game-error-copy-adapter";
import { GameHowToPlayGate } from "../game-runtime/game-how-to-play-gate";
import {
  GameProviderBootstrap,
  GameProviderBootstrapPreload,
} from "../game-runtime/game-provider-bootstrap";
import {
  filterSafeTableBalanceQuickAmounts,
  GameTableBalanceGate,
  type GameTableBalanceConfirmParams,
  type GameTableBalanceWalletSource,
} from "../game-runtime/game-table-balance-gate";
import { BOXE_GAME_STORAGE_NAMESPACE } from "../game-runtime/game-storage";
import { useGameEmbedBridge } from "../game-runtime/use-game-embed-bridge";
import { useGameLaunchContext } from "../game-runtime/use-game-launch-context";
import { BoxeGameplay } from "./boxe-gameplay";
import { BOXE_TABLE_BALANCE_CONFIG } from "./boxe-table-balance-config";
import {
  closeBoxeAccessSession,
  createBoxeAccessSession,
  createBoxeTableSession,
  loadBoxeRuntimeConfig,
  loadBoxeTableSessionLimits,
  type BoxeAccessSession,
  type BoxeRuntimeConfig,
  type BoxeTableSession,
  type BoxeTableSessionLimits,
} from "./use-boxe-runtime";

const BOXE_RUNTIME_ERROR_COPY_MAP = {
  auth_invalid: "Sessione scaduta, ricarica",
  validation: "Controlla puntata e selezioni.",
  insufficient_balance: "Saldo insufficiente.",
  bonus_wallet_empty: "Saldo bonus vuoto.",
  round_closed: "La mano e' gia' conclusa.",
  network: "Connessione instabile. Riprova.",
  service_unavailable: "Servizio temporaneamente non disponibile.",
  reload_required: "Sessione scaduta, ricarica",
  generic: "Operazione non riuscita. Riprova.",
} satisfies GameErrorCopyMap;

export function BoxeStandalone() {
  const [runtimeConfig, setRuntimeConfig] = useState<BoxeRuntimeConfig | null>(null);
  const [runtimeError, setRuntimeError] = useState("");
  const [runtimeErrorDiagnostic, setRuntimeErrorDiagnostic] =
    useState<GameErrorDiagnostic | null>(null);
  const [titleThemeAssets, setTitleThemeAssets] = useState<Record<string, string>>({});
  const [titleThemeSkin, setTitleThemeSkin] = useState<TitleThemeSkin | null>(null);
  const [isTitleThemeResolved, setIsTitleThemeResolved] = useState(false);
  const [isProviderIntroComplete, setIsProviderIntroComplete] = useState(false);
  const [isHowToPlayComplete, setIsHowToPlayComplete] = useState(false);
  const [isTableBalanceComplete, setIsTableBalanceComplete] = useState(false);
  const [selectedTableWalletType, setSelectedTableWalletType] =
    useState<GameTableBalanceWalletSource>("cash");
  const [accessSession, setAccessSession] = useState<BoxeAccessSession | null>(null);
  const [tableSession, setTableSession] = useState<BoxeTableSession | null>(null);
  const [tableSessionLimits, setTableSessionLimits] =
    useState<BoxeTableSessionLimits | null>(null);
  const [tableEntryAmount, setTableEntryAmount] = useState("");
  const [gameLaunchToken, setGameLaunchToken] = useState("");
  const [gameLaunchTokenExpiresAt, setGameLaunchTokenExpiresAt] = useState("");
  const [audioPreferences, setAudioPreferences] = useState({
    muted: false,
    setMuted: (_value: boolean) => {},
    setVolume: (_value: number) => {},
    volume: 0.45,
  });

  const {
    status: bootStatus,
    markRuntimeReady,
    markFatal,
  } = useGameLaunchContext({
    storageNamespace: BOXE_GAME_STORAGE_NAMESPACE,
    missingTitleRedirectTo: "/",
  });

  const handleTitleThemeChange = useCallback((theme: TitleTheme | null) => {
    setTitleThemeAssets(theme?.assets ?? {});
    setTitleThemeSkin(theme?.skin ?? null);
    setIsTitleThemeResolved(true);
  }, []);

  const isLaunchContextReady =
    bootStatus.kind === "launch_ready" || bootStatus.kind === "runtime_ready";
  const isRuntimeReady = bootStatus.kind === "runtime_ready";
  const canRenderBootSurface =
    isLaunchContextReady || (bootStatus.kind === "fatal" && "request" in bootStatus);
  const titleCode = "request" in bootStatus && bootStatus.request
    ? bootStatus.request.titleCode
    : "boxe001";

  useEffect(() => {
    if (bootStatus.kind !== "launch_ready") {
      return;
    }

    setRuntimeConfig(null);
    setRuntimeError("");
    setRuntimeErrorDiagnostic(null);
    setIsTitleThemeResolved(false);
    setIsProviderIntroComplete(false);
    setIsHowToPlayComplete(false);
    setIsTableBalanceComplete(false);
    setAccessSession(null);
    setTableSession(null);
    setTableSessionLimits(null);
    setSelectedTableWalletType(bootStatus.request.walletSource ?? "cash");
    setTableEntryAmount("");

    let isMounted = true;
    loadBoxeRuntimeConfig(bootStatus.request.titleCode)
      .then((config) => {
        if (isMounted) {
          setRuntimeConfig(config);
        }
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setRuntimeGameError(error);
        if (classifyGameError(error) === "service_unavailable") {
          markFatal("runtime");
        }
      });

    return () => {
      isMounted = false;
    };
  }, [bootStatus, markFatal]);

  useEffect(() => {
    if (bootStatus.kind === "launch_ready" && runtimeConfig && isTitleThemeResolved) {
      markRuntimeReady();
    }
  }, [bootStatus.kind, isTitleThemeResolved, markRuntimeReady, runtimeConfig]);

  const isDemoMode =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.forceDemoMode : true;
  const isEmbeddedView =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.isEmbeddedView : false;
  const returnTo =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.returnTo : null;
  const { isHostFullscreen, requestClose: requestEmbedClose } = useGameEmbedBridge({
    gameCode: "boxe",
    enabled: isEmbeddedView,
  });
  const pageShellClassName = [
    "page-shell",
    "mines-page-shell",
    isEmbeddedView ? "mines-page-shell-embedded" : null,
    "boxe-page-shell",
  ].filter(Boolean).join(" ");
  const productShellClassName = [
    "panel",
    "game-product-shell",
    "mines-product-shell",
    "mines-product-shell-clean",
    isEmbeddedView ? "mines-product-shell-embedded" : null,
    "boxe-product-shell",
    titleThemeSkin ? "mines-product-shell-skinned" : null,
    titleThemeSkin ? `mines-button-density-${titleThemeSkin.button_density}` : null,
    titleThemeSkin ? `mines-button-radius-${titleThemeSkin.button_radius}` : null,
    titleThemeSkin ? `mines-button-style-${titleThemeSkin.button_style}` : null,
    titleThemeSkin ? `mines-button-emphasis-${titleThemeSkin.button_emphasis}` : null,
  ].filter(Boolean).join(" ");
  const showTableBalanceGate =
    isLaunchContextReady && !isDemoMode && !isTableBalanceComplete;
  const showProviderIntroGate =
    (isLaunchContextReady || bootStatus.kind === "fatal") &&
    !showTableBalanceGate &&
    !isProviderIntroComplete;
  const showHowToPlayGate =
    isRuntimeReady &&
    !showTableBalanceGate &&
    isProviderIntroComplete &&
    !isHowToPlayComplete;
  const lockedTableWalletSource =
    "request" in bootStatus && bootStatus.request && !bootStatus.request.forceDemoMode
      ? bootStatus.request.walletSource
      : null;
  const tableGateToken =
    "storageSnapshot" in bootStatus ? (bootStatus.storageSnapshot?.accessToken ?? "") : "";
  const tableGateGameLaunchToken =
    "storageSnapshot" in bootStatus ? (bootStatus.storageSnapshot?.gameLaunchToken ?? "") : "";
  const tableGateGameLaunchTokenExpiresAt =
    "storageSnapshot" in bootStatus ? (bootStatus.storageSnapshot?.gameLaunchTokenExpiresAt ?? "") : "";
  const tableGateTitleCode =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.titleCode : titleCode;
  const tableEntryMaxAmount = tableSessionLimits?.max_table_amount ?? "0";
  const tableAvailableBalance = tableSessionLimits?.wallet_balance_available ?? "0";
  const tableDefaultAmount =
    tableSessionLimits?.default_table_amount ?? BOXE_TABLE_BALANCE_CONFIG.defaultEntryAmount;

  useEffect(() => {
    if (!showTableBalanceGate || !tableGateToken) {
      return;
    }
    let isMounted = true;
    setTableSessionLimits(null);
    loadBoxeTableSessionLimits(tableGateToken, selectedTableWalletType)
      .then((limits) => {
        if (!isMounted) {
          return;
        }
        setTableSessionLimits(limits);
        setTableEntryAmount(formatSafeDefaultTableEntry(limits.default_table_amount));
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setRuntimeGameError(error);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [selectedTableWalletType, showTableBalanceGate, tableGateToken]);

  const handleExit = useCallback(async () => {
    if (isHostFullscreen) {
      setAccessSession(null);
      setTableSession(null);
      return;
    }
    const currentAccessSessionId = accessSession?.id ?? tableSession?.access_session_id;
    if (!isDemoMode && currentAccessSessionId && tableGateToken) {
      try {
        await closeBoxeAccessSession({
          accessSessionId: currentAccessSessionId,
          token: tableGateToken,
        });
      } catch {
        // Do not trap the player on exit. The server timeout path will still auto-settle.
      }
      setAccessSession(null);
      setTableSession(null);
    }
    if (requestEmbedClose()) {
      return;
    }
    window.location.assign(returnTo ?? "/");
  }, [
    accessSession?.id,
    isDemoMode,
    isHostFullscreen,
    requestEmbedClose,
    returnTo,
    tableGateToken,
    tableSession?.access_session_id,
  ]);

  const handleConfirmTableBalance = useCallback(
    async ({ tableEntryAmount: nextEntryAmount, walletSource }: GameTableBalanceConfirmParams) => {
      if (!tableGateToken) {
        setRuntimeError(BOXE_RUNTIME_ERROR_COPY_MAP.auth_invalid);
        setRuntimeErrorDiagnostic(null);
        return;
      }
      try {
        const normalizedAmount = formatWholeChipInput(nextEntryAmount);
        const nextAccessSession = await createBoxeAccessSession({
          titleCode: tableGateTitleCode,
          token: tableGateToken,
        });
        const nextTableSession = await createBoxeTableSession({
          titleCode: tableGateTitleCode,
          walletType: walletSource,
          tableBudgetAmount: normalizedAmount,
          accessSessionId: nextAccessSession.id,
          token: tableGateToken,
        });
        setAccessSession(nextAccessSession);
        setTableSession(nextTableSession);
        setSelectedTableWalletType(nextTableSession.wallet_type);
        setTableEntryAmount(normalizedAmount);
        setRuntimeError("");
        setRuntimeErrorDiagnostic(null);
        setIsTableBalanceComplete(true);
      } catch (error) {
        setRuntimeGameError(error);
      }
    },
    [tableGateTitleCode, tableGateToken],
  );

  const providerIntro = showProviderIntroGate ? (
    <GameProviderBootstrap
      ready={isRuntimeReady || runtimeError.length > 0}
      onComplete={() => setIsProviderIntroComplete(true)}
    />
  ) : null;

  const howToPlay = showHowToPlayGate ? (
    <GameHowToPlayGate
      title="Come si gioca"
      titleId="boxe-how-to-play-title"
      intro="Punta, scegli una box e incassa quando sei in vantaggio."
      continueLabel="Continua"
      cards={[
        {
          title: "Bet",
          text: "Imposta puntata, righe e difficolta.",
          visual: (
            <div className="game-how-to-play-mobile-hidden">
              <BoxeHowToPlayVisual index={0} />
            </div>
          ),
        },
        {
          title: "Pick",
          text: "Scegli una box nella riga attiva.",
          visual: (
            <div className="game-how-to-play-mobile-hidden">
              <BoxeHowToPlayVisual index={1} />
            </div>
          ),
        },
        {
          title: "Collect",
          text: "Incassa dopo una scelta sicura oppure completa la riga finale per chiudere la mano.",
          visual: (
            <div className="game-how-to-play-mobile-hidden">
              <BoxeHowToPlayVisual index={2} />
            </div>
          ),
        },
      ]}
      onContinue={() => setIsHowToPlayComplete(true)}
    />
  ) : null;

  const tableGate = showTableBalanceGate ? (
    <GameTableBalanceGate
      amount={tableEntryAmount}
      amountLabel="Importo ingresso tavolo"
      amountPlaceholder={formatWholeChipInput(tableDefaultAmount)}
      availableBalanceAmount={formatWholeChipInput(tableAvailableBalance)}
      availableBalanceLabel="Saldo disponibile"
      availableBalanceValue={`${formatWholeChipInput(tableAvailableBalance)} CHIP`}
      busyLabel="Ingresso..."
      closeAriaLabel="Torna al sito"
      confirmLabel="Entra nel gioco"
      eyebrow="BOXE"
      isReady={tableSessionLimits !== null}
      lockedWalletSource={lockedTableWalletSource}
      maximumAmount={formatWholeChipInput(tableEntryMaxAmount)}
      maximumAmountLabel={`${formatWholeChipInput(tableEntryMaxAmount)} CHIP`}
      maximumLabel="Massimo"
      onAmountChange={(amount) => setTableEntryAmount(amount.replace(/\D/g, ""))}
      onClose={handleExit}
      onConfirm={handleConfirmTableBalance}
      onWalletSourceChange={setSelectedTableWalletType}
      preload={<GameProviderBootstrapPreload />}
      quickAmounts={filterSafeTableBalanceQuickAmounts(
        BOXE_TABLE_BALANCE_CONFIG.quickAmounts.map((amount) => ({ value: amount })),
        tableEntryMaxAmount,
        tableAvailableBalance,
      )}
      selectedWalletSource={selectedTableWalletType}
      testId="boxe-table-balance-gate"
      title="Scegli il saldo del tavolo"
      walletGroupAriaLabel="Fonte saldo"
      walletOptions={[
        {
          balanceLabel: "100 CHIP",
          label: "Saldo reale",
          value: "cash",
        },
        {
          balanceLabel: "100 CHIP",
          label: "Bonus",
          value: "bonus",
        },
      ]}
    />
  ) : null;

  const errorDialog = runtimeError ? (
    <GameActionError
      actionLabel="Riprova"
      code={runtimeErrorDiagnostic?.code}
      message={runtimeError}
      onAction={() => window.location.reload()}
      requestId={runtimeErrorDiagnostic?.requestId}
      supportId={runtimeErrorDiagnostic?.supportId}
      testId="boxe-runtime-error-dialog"
      title="Azione richiesta"
    />
  ) : null;

  return (
    <GameBootShell
      titleCode={titleCode}
      statusKind={bootStatus.kind}
      canRenderBootSurface={canRenderBootSurface}
      isRuntimeReady={isRuntimeReady}
      showTableBalanceGate={showTableBalanceGate}
      showProviderIntroGate={showProviderIntroGate}
      showHowToPlayGate={showHowToPlayGate}
      tableGatePageShellClassName="page-shell game-table-balance-page"
      pageShellClassName={pageShellClassName}
      productShellClassName={productShellClassName}
      onThemeChange={handleTitleThemeChange}
      onAudioPreferencesChange={setAudioPreferences}
      tableGate={tableGate}
      providerIntro={providerIntro}
      howToPlay={howToPlay}
      errorDialog={errorDialog}
      runtimeOverlay={null}
    >
      {runtimeConfig ? (
        <BoxeGameplay
          audioPreferences={audioPreferences}
          bootRequest={bootStatus.kind === "runtime_ready" ? bootStatus.request : {
            titleCode,
            forceDemoMode: true,
            previewToken: "",
            isEmbeddedView: false,
            returnTo: null,
            walletSource: null,
          }}
          initialAccessToken={
            bootStatus.kind === "runtime_ready"
              ? bootStatus.storageSnapshot.accessToken
              : ""
          }
          initialGameLaunchToken={
            bootStatus.kind === "runtime_ready"
              ? bootStatus.storageSnapshot.gameLaunchToken
              : ""
          }
          initialGameLaunchTokenExpiresAt={
            bootStatus.kind === "runtime_ready"
              ? bootStatus.storageSnapshot.gameLaunchTokenExpiresAt
              : ""
          }
          onGameLaunchTokenChange={setGameLaunchToken}
          onGameLaunchTokenExpiresAtChange={setGameLaunchTokenExpiresAt}
          runtimeConfig={runtimeConfig}
          titleThemeAssets={titleThemeAssets}
          titleThemeSkin={titleThemeSkin}
          accessSessionId={accessSession?.id ?? null}
          tableSession={tableSession}
          onExit={handleExit}
          onTableSessionChange={setTableSession}
        />
      ) : (
        <div className="boxe-loading" role="status">
          Caricamento BOXE...
        </div>
      )}
      <span className="boxe-audio-state" data-muted={audioPreferences.muted} hidden />
    </GameBootShell>
  );

  function setRuntimeGameError(error: unknown) {
    setRuntimeError(buildGameErrorMessage(error, BOXE_RUNTIME_ERROR_COPY_MAP));
    setRuntimeErrorDiagnostic(buildGameErrorDiagnostic(error));
  }
}

function BoxeHowToPlayVisual({ index }: { index: number }) {
  const rows = 4;
  const cardNumber = Math.min(Math.max(index + 1, 1), 3);
  const cellsForRow = (row: number, totalRows: number) => totalRows - row + 1;
  const cellKey = (row: number, position: number) => `${row}:${position}`;
  const cardState =
    cardNumber === 1
      ? {
          activeRow: 0,
          safeCells: new Set<string>(),
          selectedCells: new Set([cellKey(0, 2)]),
          mineCells: new Set<string>(),
        }
      : cardNumber === 2
        ? {
            activeRow: 2,
            safeCells: new Set([cellKey(0, 2), cellKey(1, 1)]),
            selectedCells: new Set([cellKey(2, 1)]),
            mineCells: new Set<string>(),
          }
        : {
            activeRow: 2,
            safeCells: new Set([cellKey(0, 2), cellKey(1, 1)]),
            selectedCells: new Set<string>(),
            mineCells: new Set([cellKey(2, 1)]),
          };
  const pyramidRows = Array.from({ length: rows }, (_item, row) => {
    const cellCount = cellsForRow(row, rows);

    return {
      cellCount,
      row,
      cells: Array.from({ length: cellCount }, (_cell, position) => {
        const key = cellKey(row, position);
        const isSafe = cardState.safeCells.has(key);
        const isMine = cardState.mineCells.has(key);
        const isSelected = cardState.selectedCells.has(key);
        const isActive = cardState.activeRow === row;
        const state = isMine
          ? "mine"
          : isSafe
            ? "safe"
            : isSelected
              ? "selected"
              : row > cardState.activeRow
                ? "opaque"
                : "covered";

        return {
          isActive,
          key,
          position,
          state,
        };
      }),
    };
  });
  const visualRows = [...pyramidRows].reverse();

  return (
    <div
      className={`game-how-to-play-visual boxe-how-to-play-pyramid is-card-${cardNumber}`}
      aria-hidden="true"
    >
      <div className="boxe-how-to-play-pyramid-board">
        {visualRows.map((row) => (
          <div
            className={`boxe-how-to-play-pyramid-row has-${row.cellCount}-cells`}
            data-row={row.row}
            key={row.row}
          >
            {row.cells.map((cell) => (
              <span
                className={[
                  "boxe-how-to-play-pyramid-cell",
                  `is-${cell.state}`,
                  cell.isActive ? "is-active" : "",
                ].filter(Boolean).join(" ")}
                data-position={cell.position}
                key={cell.key}
              >
                <span className="boxe-how-to-play-pyramid-cell-face">
                  {cell.state === "safe" ? (
                    <img
                      src="/game-assets/boxe/diamond_green_v001.png"
                      alt=""
                      draggable={false}
                    />
                  ) : null}
                  {cell.state === "mine" ? (
                    <img
                      src="/game-assets/boxe/mine_fucsia_002.png"
                      alt=""
                      draggable={false}
                    />
                  ) : null}
                </span>
              </span>
            ))}
          </div>
        ))}
      </div>
      <div className="boxe-how-to-play-pyramid-controls">
        {[1, 2, 3].map((controlIndex) => (
          <span
            className={[
              "boxe-how-to-play-pyramid-control",
              controlIndex === cardNumber ? "is-active" : "",
            ].filter(Boolean).join(" ")}
            key={controlIndex}
          />
        ))}
      </div>
    </div>
  );
}

function formatWholeChipInput(value: string | number | null | undefined) {
  const numeric = Number.parseFloat(String(value ?? "0"));
  if (!Number.isFinite(numeric)) {
    return "0";
  }
  return String(Math.floor(numeric));
}

function formatSafeDefaultTableEntry(value: string | number | null | undefined) {
  const numeric = Number.parseFloat(String(value ?? "0"));
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return "";
  }
  return formatWholeChipInput(value);
}
