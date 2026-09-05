Status: ACTIVE
Last meaningful update: 2026-07-16

# CasinoKing — AI Operational Authority

## 1. Authority granted

L'utente Michele ha concesso all'agente AI (Kimi Code CLI / Claude Code / strumenti
agentic in uso sul progetto) **piena autorità operativa sul repository e sull'ambiente
locale di CasinoKing**, con effetto immediato e senza necessità di richiedere
conferma per ogni singola azione.

## 2. Cosa l'agente può fare autonomamente

Nel perimetro del progetto `/home/micheleubuntu/Downloads/CasinoKing/casinoking-platform`:

- Leggere, creare, modificare, rinominare ed eliminare qualsiasi file o cartella.
- Modificare configurazioni di build, Docker, environment, script e tooling.
- Eseguire comandi `docker`, `docker compose`, build, rebuild, up, down, logs.
- Eseguire test, script, migration, seed, smoke test e utility di sviluppo.
- Avviare, fermare e riavviare servizi locali (frontend-v3, edge, backend, postgres,
  redis, container ausiliari).
- Modificare file `.env` locali e variabili di configurazione non-secret.
- Generare asset, variabili runtime, file temporanei di lavoro e artefatti di build.
- Aggiornare documentazione di progetto (`docs/`, `AGENTS.md`, README, manuali).
- Operare su branch di lavoro locali e su file versionati.

## 3. Permessi tecnici già verificati

- Utente di esecuzione: `micheleubuntu` (uid 1000).
- Directory di progetto di proprietà di `micheleubuntu:micheleubuntu` con permessi
  di lettura/scrittura/esecuzione.
- Appartenenza ai gruppi `sudo` e `docker` confermata.
- Docker Engine accessibile senza `sudo` (`docker info` funzionante).

Nessuna modifica a `/etc/sudoers`, `/etc/group` o altri file di sistema e'
necessaria ne' richiesta.

## 4. Cosa l'agente DEVE ancora chiedere esplicitamente

Anche con questa autorita', l'agente non agisce al di fuori del perimetro del
progetto e non esegue operazioni irreversibili o ad alto impatto senza conferma.
In particolare, richiede conferma esplicita prima di:

- Installazione o rimozione di pacchetti/software a livello di sistema operativo
  (al di fuori di ambienti virtuali o isolated environment dentro il progetto).
- Modifica di file di sistema al di fuori della working directory del progetto.
- Accesso a dati, credenziali o segreti non strettamente necessari al task.
- Operazioni che potrebbero causare perdita di dati personali o di produzione
  al di fuori del repository CasinoKing.
- Scelte tecniche che contraddicono palesemente `docs/TASK_EXECUTION_GUARDRAILS.md`
  o `docs/AI_CRITICAL_JUDGMENT_RULES.md`.

## 5. Operazioni git

L'utente ha esplicitamente autorizzato l'agente a eseguire mutazioni git
(`git commit`, `git push`, `git reset`, `git rebase`, `git clean -fd`, force-push,
cancellazione branch) quando necessarie al task o richieste dall'utente, senza
richiedere una conferma preventiva separata.

Per operazioni git particolarmente distruttive (es. `git reset --hard`,
`git push --force`, `git clean -fd`, rebase interattivo su branch condivisi),
l'agente informa l'utente dell'azione eseguita immediatamente dopo averla
compiuta, riassumendo cosa e' cambiato.

## 6. Regole di collaborazione che restano valide

L'autonomia operativa non sovrascrive le regole di qualita' del progetto:

- Continua a valere `docs/TASK_EXECUTION_GUARDRAILS.md`.
- Continua a valere `docs/AI_CRITICAL_JUDGMENT_RULES.md` (l'AI non deve essere
  accondiscendente su scelte fragili).
- Continua a valere `docs/DOCUMENTATION_MAINTENANCE.md`.
- Ogni WP che cambia comportamento UI o capability admin DEVE aggiornare
  `docs/BACKOFFICE_MANUAL.md` nello stesso intervento.

## 7. Scope

Questa autorita' vale per il progetto CasinoKing nella working directory attuale.
Non vale per altri repository, dati personali dell'utente o sistemi remoti.
