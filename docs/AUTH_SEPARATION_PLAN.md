# Piano di Refactoring: Separazione Logica Autenticazione Player e Admin

## Contesto e Obiettivo
Attualmente c'è una commistione tra l'autenticazione degli utenti (player) e degli amministratori (back office). Entrambi usano lo stesso endpoint API (`/api/v1/auth/login`) e, sul frontend, le stesse chiavi nel `localStorage` (es. `casinoking.access_token`). Questo porta a bug dove un admin che si logga sovrascrive la sessione del player, o viceversa, e permette accessi incrociati non voluti.

L'obiettivo è separare **logicamente e fisicamente** i due flussi, garantendo che un token player non possa mai accedere alle route admin, e un token admin non possa mai essere usato per giocare.

## Analisi dello Stato Attuale
- **Backend**: `auth/service.py` ha una singola funzione `authenticate_user` che non filtra per ruolo. `dependencies.py` espone `get_current_user` che ammette *qualsiasi* ruolo attivo. Le route del giocatore (es. `/wallets`, `/games/mines/session/...`) usano `get_current_user`, permettendo ad un admin di passarci in mezzo (fallendo poi per mancanza di wallet).
- **Frontend**: Sia la pagina di login player (`player-login-page.tsx`) sia la console embedded (`casinoking-console.tsx`, usata anche in area admin) salvano il token sulla chiave `"casinoking.access_token"`.

## Stato Target e Modifiche Richieste

### 1. Modifiche Backend (Separazione API e Sicurezza)
- **`app/modules/auth/service.py`**: 
  - Modificare `authenticate_user` aggiungendo un parametro opzionale `required_role: str | None = None`. Se il ruolo dell'utente non corrisponde, sollevare `AuthForbiddenError`.
- **`app/api/routes/auth.py`**:
  - L'endpoint `POST /auth/login` chiamerà `authenticate_user(..., required_role="player")`.
- **`app/api/routes/admin.py`**:
  - Aggiungere un nuovo endpoint `POST /admin/auth/login` (con un apposito schema `AdminLoginRequest`). Questo chiamerà `authenticate_user(..., required_role="admin")`.
- **`app/api/dependencies.py`**:
  - Rinominare `get_current_user` in `get_authenticated_user` (base).
  - Creare `get_current_player` che asserisce esplicitamente `role == "player"`.
  - Assicurarsi che `get_current_admin` usi la base e asserisca esplicitamente `role == "admin"`.
- **Rotelle Player** (`wallets.py`, `ledger.py`, `mines.py`, `platform_access.py`):
  - Aggiornare tutti i `Depends(get_current_user)` in `Depends(get_current_player)`. Questo elimina ogni possibilità che un admin possa chiamare endpoint di gioco.

### 2. Modifiche Frontend (Separazione Memoria e Endpoint)
- **`app/lib/admin-storage.ts`** (Nuovo file):
  - Creare una costante `ADMIN_STORAGE_KEYS` con chiavi isolate (es. `"casinoking.admin_access_token"`, `"casinoking.admin_email"`).
- **`app/ui/casinoking-console.tsx`**:
  - Rimuovere il dictionary hardcoded `STORAGE_KEYS`.
  - Utilizzare dinamicamente le chiavi di storage: `ADMIN_STORAGE_KEYS` se `area === "admin"`, altrimenti `PLAYER_STORAGE_KEYS`.
  - Nella funzione `handleLogin`, eseguire uno split: se `area === "admin"` usare l'endpoint `/admin/auth/login`, altrimenti continuare a usare `/auth/login`.

## Rischi e Attenzioni
- Questa modifica richiederà di invalidare le sessioni aperte se gli utenti hanno token mischiati, ma essendo in sviluppo locale/MVP l'impatto è controllato.
- Assicurarsi di aggiornare le suite di test E2E (es. `test_frontend_smoke.py`, test d'integrazione) qualora simulassero il login admin via `/auth/login` invece che tramite la nuova route.

## Prossimi Passi
- Una volta approvato questo piano tramite validazione Ask, verrà delegata la TODO list al modo Code per l'implementazione esatta.
