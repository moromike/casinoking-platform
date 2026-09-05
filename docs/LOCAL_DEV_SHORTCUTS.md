# Local Dev Shortcuts (macchina di Michele)

Scorciatoie operative valide sulla postazione locale (Ubuntu in VM Hyper-V, accesso via RDP).
Questo file NON contiene regole di progetto: solo comandi comodi che l'utente può chiedere in linguaggio naturale.

## "Lancia Antigravity"

Quando l'utente scrive qualcosa come **"lancia antigravity"**, **"apri antigravity"** o
**"avvia agy"**, l'agente deve aprire Antigravity CLI in una **nuova finestra di terminale
grafica** con cui l'utente possa interagire.

Motivo: `agy` è un programma interattivo (TUI). Se viene lanciato nella shell non interattiva
dell'agente, l'utente non può digitarci dentro. Va quindi aperto in un terminale reale sul
desktop dell'utente.

Comando da eseguire (verificato funzionante il 2026-07-22):

```bash
export DISPLAY=:10.0
setsid gnome-terminal --working-directory="$HOME/Downloads/CasinoKing" \
  -- bash -c 'agy; echo; echo "[Antigravity terminato - premi Invio per chiudere]"; read' \
  >/dev/null 2>&1 &
```

Dettagli:
- Il binario si chiama **`agy`** (in `~/.local/bin/agy`), NON `antigravity`. Installato con
  `curl -fsSL https://antigravity.google/cli/install.sh | bash`.
- Se l'utente indica una cartella diversa, sostituire il valore di `--working-directory`.
- Ambiente: `DISPLAY=:10.0`, terminale grafico disponibile: `gnome-terminal`.
- L'agente non vede lo schermo dell'utente: dopo il lancio, chiedere conferma che la finestra
  sia comparsa.
- Nota: in alcuni sandbox l'apertura di finestre grafiche può essere bloccata; in tal caso
  segnalarlo all'utente invece di fingere che sia partito.

## "Lancia Codex" / "Lancia Codex CLI"

Quando l'utente scrive qualcosa come **"lancia codex"**, **"apri codex"** o
**"lancia codex cli"**, l'agente deve aprire Codex CLI in una **nuova finestra di terminale
grafica** con cui l'utente possa interagire (stessa logica di Antigravity: `codex` è una TUI
interattiva e non va lanciata nella shell non interattiva dell'agente).

Comando da eseguire (verificato funzionante il 2026-07-22):

```bash
export DISPLAY=:10.0
setsid gnome-terminal --working-directory="$HOME/Downloads/CasinoKing" \
  -- bash -lic 'codex; echo; echo "[Codex terminato - premi Invio per chiudere]"; read' \
  >/dev/null 2>&1 &
```

Dettagli:
- Il binario è **`codex`** (installato via npm, in `~/.nvm/.../bin/codex`). Si usa `bash -lic`
  (login+interattiva) così la shell nuova carica nvm e trova `codex` senza path assoluti.
- Questo è il Codex **CLI da terminale**, che usa il modello più recente (es. gpt-5.6-sol) —
  distinto dall'estensione grafica di VS Code, che è tenuta a una versione vecchia per un bug
  su VM Hyper-V (vedi memoria del progetto).
- Se l'utente indica una cartella diversa, sostituire il valore di `--working-directory`.
- L'agente non vede lo schermo: dopo il lancio, chiedere conferma che la finestra sia comparsa.
