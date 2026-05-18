"use client";

export function BoxeHowToPlayContent({ onContinue }: { onContinue: () => void }) {
  return (
    <article className="boxe-gate boxe-how-to-play" aria-labelledby="boxe-how-to-title">
      <div className="boxe-gate-heading">
        <span className="eyebrow">BOXE</span>
        <h1 id="boxe-how-to-title">Come si gioca</h1>
      </div>
      <div className="boxe-how-to-grid">
        <section>
          <span>1</span>
          <h2>Bet</h2>
          <p>Scegli puntata, righe e difficolta prima della mano.</p>
        </section>
        <section>
          <span>2</span>
          <h2>Pick</h2>
          <p>Seleziona una box nella riga attiva e sali nella piramide.</p>
        </section>
        <section>
          <span>3</span>
          <h2>Collect</h2>
          <p>Incassa dopo una scelta sicura o completa la riga finale.</p>
        </section>
      </div>
      <button className="button boxe-primary-action" type="button" onClick={onContinue}>
        Continua
      </button>
    </article>
  );
}
