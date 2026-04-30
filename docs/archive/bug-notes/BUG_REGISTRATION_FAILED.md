# Bug Report: Registration Failed (Failed to fetch)

## Sintomo
Durante la fase di test post-riavvio del PC, il processo di registrazione si è interrotto. L'interfaccia utente ha restituito l'errore `Registration failed. Failed to fetch` durante l'esecuzione del `POST` verso `/api/v1/auth/register`.

## Analisi Temporanea
Sono stati analizzati tre potenziali problemi:
1. **CORS:** Risolto. L'API backend è stata aggiornata per accettare esplicitamente le chiamate da `http://127.0.0.1:3000` oltre a `http://localhost:3000`.
2. **Endpoint Mismatch su Windows:** Risolto. Il frontend `API_BASE_URL` è stato forzato su `127.0.0.1:8000` per evitare blocchi DNS (IPv6 vs IPv4) intrinseci a Windows e Uvicorn.
3. **Database Desincronizzato (Causa Probabile):** Poiché il PC è stato riavviato, l'istanza PostgreSQL è ripartita senza l'applicazione delle ultime migrazioni (inclusa la `0015__add_user_pii_fields.sql`). Il backend andava in crash tentando di salvare `first_name`, generando un Errore 500 che si traduceva in "Failed to fetch" sul client.

## Azione Richiesta (TODO)
- Prima di riprendere lo sviluppo, verificare che il comando `python app/tools/apply_migrations.py` sia stato eseguito con successo sul DB locale per allineare lo schema.
- Rieseguire il test E2E della registrazione dal browser.