# RESUME - Sessione CasinoKing

> Leggi questo file all'inizio della nuova chat per riprendere esattamente da dove eravamo.
> Cancellalo quando hai finito tutto.

## Permessi
`.claude/settings.local.json` già configurato con bypassPermissions + skipDangerousModePermissionPrompt.
NON chiedere mai conferma per nessun tool. Autonomia totale.

## Ambienti
Docker Compose: `docker compose -f infra/docker/docker-compose.yml up -d`
Frontend su localhost:3000, Backend su localhost:8000.
Il backend si aggiorna in hot-reload quando modifichi i file Python.
Il frontend in Docker usa `next start` (build statica) — dopo modifiche frontend bisogna rebuilddare il container.

## Stato attuale
Tutto committato su main (D→G + fix auth `4af3cce`).
L'app funziona: login player/admin OK dopo fix KeyError user_id.

## Stato sessione 2026-04-12
Refactor backoffice admin in corso e gia' implementato sul frontend locale/Docker.

### Gia' completato
- Creato componente riusabile `frontend/app/ui/access-log.tsx`
- Creato componente `frontend/app/ui/admin-shell-panel.tsx`
- Creato componente `frontend/app/ui/admin-finance-panel.tsx`
- Creato componente dedicato `frontend/app/ui/player-admin-panel.tsx`
- `AdminManagement` rifatto con 3 sotto-view:
  - `Admin registrati`
  - `Crea admin`
  - `Accessi admin`
- Menu standalone `Access Log` rimosso dal backoffice principale
- `Player admin` rifatto come:
  - lista giocatori
  - dettaglio giocatore separato
  - accessi giocatore integrati nella scheda singola

### Regression fix gia' applicati
- fix layout sub-tab admin per evitare barre giganti full-width
- fix checkbox `Superadmin` disallineato
- fix liste admin/access log che risultavano schiacciate da scroll interno troppo aggressivo
- fix lista `Player admin` che risultava ancora compressa da scroll interno
- fix `AccessLog` per ricaricare correttamente quando cambia il player selezionato
- fix `Carica dati wallet` nel dettaglio player: non deve piu' buttare fuori dalla scheda
- fix `Vai alle sessioni`: ora apre davvero il report finance filtrato per email player

### Verifiche gia' fatte
- `npm run build` frontend OK
- rebuild/restart Docker frontend OK
- primo refactor strutturale di `casinoking-console.tsx` riuscito senza rompere la build

### Prossimo lavoro raccomandato
1. QA completa manuale del nuovo backoffice admin/player
2. chiusura ultimi bug o difetti UX emersi
3. continuare il refactor strutturale di `frontend/app/ui/casinoking-console.tsx` in componenti piu' piccoli, a step e con build/test a ogni passaggio
4. dopo `Player admin`, candidati naturali:
   - shell/menu admin
   - pannello finance
   - eventuale separazione finale di helper/admin wiring residuo

## Richieste UI da Michele (sessione 2026-04-12)

Michele ha visto l'app e vuole un **refactor completo dell'admin backoffice** in 3 aree:

### 1. Sezione AMMINISTRATORI → 2 sotto-menu
Attualmente: unico pannello caotico con lista + form creazione + gestione.
**Vuole:**
- **Sub A: Crea admin** — form pulito solo per creare nuova login admin (email, password, aree, superadmin)
- **Sub B: Admin registrati** — lista admin ordinata, click per aprire dettaglio singolo admin con: aree, ultimo login, reset password, sospendi
- Auto-caricamento lista quando si entra nel sub-menu
- Rimuovere barre giganti / elementi ingombranti

### 2. Menu ACCESS LOG → da eliminare come menu standalone
Attualmente: menu separato "Access Log" nel backoffice.
**Vuole:**
- Integrarlo come sotto-menu **dentro** il report Admin: "Accessi admin"
- Integrarlo come sotto-menu **dentro** il report Giocatori: "Accessi giocatori"
- Niente menu dedicato Access Log nel menu principale

### 3. PLAYER ADMIN → lista semplice + dettaglio
Attualmente: pannello confuso con lista + dati finanziari tutto insieme.
**Vuole:**
- **Vista 1: Lista giocatori** — ordinata dal più recente, con email + status + data registrazione
  Auto-caricamento all'ingresso nel menu
- **Vista 2: Dettaglio giocatore** — click su giocatore → apre scheda singola con:
  - Dati anagrafici
  - Wallet (cash + bonus)
  - Azioni: sospendi, reset password, bonus grant, top-up sotto soglia, wallet adjustment
  - Storico accessi (dal log)
- Niente dati finanziari globali mischiati nella lista

### Principio generale
- Pulizia e semplicità sopra tutto
- Auto-load dati all'ingresso in ogni sotto-menu
- Niente form e lista nello stesso pannello
- Niente barre di stato giganti

## File chiave da modificare
- `frontend/app/ui/admin-management.tsx` — sezione Amministratori
- `frontend/app/ui/casinoking-console.tsx` — tutto il backoffice admin (enorme, ~3500 righe)
  Il backoffice admin è dentro questo file nelle sezioni `adminSection ===`
  Sezioni rilevanti: "end_user" (player admin), "access_logs", la parte admin management

## Note architetturali
- Il frontend in Docker è `next start` (non dev server) — le modifiche richiedono rebuild del container
- Comando rebuild: `docker compose -f infra/docker/docker-compose.yml build frontend && docker compose -f infra/docker/docker-compose.yml up -d frontend`
- Il backend invece ha hot-reload automatico

## Fonti di verità
- `AGENTS.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
