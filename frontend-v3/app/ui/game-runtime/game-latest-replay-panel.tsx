"use client";

import type { ReactNode } from "react";
import "./game-latest-replay-panel.css";

export type GameLatestAccessSessionHistory<TRound> = {
  id: string;
  game_code: string;
  title_code: string;
  site_code: string;
  status: "active" | "closed" | "timed_out";
  started_at: string;
  last_activity_at: string;
  ended_at: string | null;
  rounds: TRound[];
};

type GameLatestReplaySessionsPanelProps<TRound> = {
  sessions: GameLatestAccessSessionHistory<TRound>[];
  loading: boolean;
  error: string | null;
  selectedRoundId: string | null;
  onSelectRound: (roundId: string) => void;
  onSelectPrevious: () => void;
  onSelectNext: () => void;
  canSelectPrevious: boolean;
  canSelectNext: boolean;
  renderViewer: (round: TRound) => ReactNode;
  getRoundId: (round: TRound) => string;
  formatDateTime: (value: string | null) => string;
  formatStatus: (round: TRound) => string;
  formatChipValue: (value: string | number | null | undefined) => string;
  getBetAmount: (round: TRound) => string | number | null | undefined;
  getPayoutAmount: (round: TRound) => string | number | null | undefined;
  getRoundDate: (round: TRound) => string | null;
  loadingMessage?: string;
  errorMessage?: string;
  emptyMessage?: string;
  noRoundsInSessionMessage?: string;
  noRoundSelectedMessage?: string;
  sessionLabel?: string;
  handsLabel?: string;
  betLabel?: string;
  winLabel?: string;
  previousAriaLabel?: string;
  nextAriaLabel?: string;
};

export function GameLatestReplaySessionsPanel<TRound>({
  sessions,
  loading,
  error,
  selectedRoundId,
  onSelectRound,
  onSelectPrevious,
  onSelectNext,
  canSelectPrevious,
  canSelectNext,
  renderViewer,
  getRoundId,
  formatDateTime,
  formatStatus,
  formatChipValue,
  getBetAmount,
  getPayoutAmount,
  getRoundDate,
  loadingMessage = "Caricamento ultime sessioni...",
  errorMessage,
  emptyMessage = "Nessuna sessione trovata per questo Title.",
  noRoundsInSessionMessage = "Nessuna mano in questa sessione.",
  noRoundSelectedMessage = "Seleziona una mano chiusa.",
  sessionLabel = "Sessione",
  handsLabel = "mani",
  betLabel = "Bet",
  winLabel = "Win",
  previousAriaLabel = "Mano precedente",
  nextAriaLabel = "Mano successiva",
}: GameLatestReplaySessionsPanelProps<TRound>) {
  const allRounds = sessions.flatMap((session) => session.rounds);
  const selectedRound = allRounds.find(
    (round) => getRoundId(round) === selectedRoundId,
  ) ?? allRounds[0] ?? null;

  return (
    <div className="game-latest-replay-panel">
      {loading ? (
        <p className="empty-state">{loadingMessage}</p>
      ) : error ? (
        <p className="status-line">{errorMessage ?? error}</p>
      ) : sessions.length === 0 ? (
        <p className="empty-state">{emptyMessage}</p>
      ) : (
        <div className="game-latest-replay-layout">
          <div className="game-latest-session-list">
            {sessions.map((session, sessionIndex) => (
              <article className="game-latest-session-card" key={session.id}>
                <header className="game-latest-session-header">
                  <div>
                    <span>{sessionLabel} {sessionIndex + 1}</span>
                    <strong>{formatDateTime(session.started_at)}</strong>
                  </div>
                  <span className="game-latest-session-count">
                    {session.rounds.length} {handsLabel}
                  </span>
                </header>
                {session.rounds.length > 0 ? (
                  <div className="game-latest-round-list">
                    {session.rounds.map((round) => {
                      const roundId = getRoundId(round);
                      const isSelected =
                        selectedRound && getRoundId(selectedRound) === roundId;
                      return (
                        <button
                          className={`game-latest-round-button${isSelected ? " is-active" : ""}`}
                          type="button"
                          key={roundId}
                          onClick={() => onSelectRound(roundId)}
                        >
                          <span className="game-latest-round-time">
                            {formatDateTime(getRoundDate(round))}
                          </span>
                          <strong className="game-latest-round-status">
                            {formatStatus(round)}
                          </strong>
                          <span className="game-latest-round-amounts">
                            <span>
                              {betLabel} {formatChipValue(getBetAmount(round))}
                            </span>
                            <span>
                              {winLabel} {formatChipValue(getPayoutAmount(round))}
                            </span>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="empty-state">{noRoundsInSessionMessage}</p>
                )}
              </article>
            ))}
          </div>

          <div className="game-latest-replay-preview">
            {selectedRound ? (
              <>
                {renderViewer(selectedRound)}
                <div className="game-latest-replay-nav" aria-label="Scorri mani replay">
                  <button
                    type="button"
                    aria-label={previousAriaLabel}
                    disabled={!canSelectPrevious}
                    onClick={onSelectPrevious}
                  >
                    &larr;
                  </button>
                  <button
                    type="button"
                    aria-label={nextAriaLabel}
                    disabled={!canSelectNext}
                    onClick={onSelectNext}
                  >
                    &rarr;
                  </button>
                </div>
              </>
            ) : (
              <p className="empty-state">{noRoundSelectedMessage}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
