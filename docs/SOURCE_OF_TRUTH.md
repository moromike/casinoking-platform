# CasinoKing – Source of Truth

Questo file definisce i documenti ufficiali del progetto CasinoKing e il loro ordine di precedenza.

## Regola generale
- I documenti elencati qui sono la base ufficiale del progetto.
- Se due documenti sembrano in conflitto, vale la versione più recente e più specifica.
- I file Word restano i documenti canonici.
- Gli allegati runtime (Excel / JSON / CSV) sono vincolanti per la parte operativa a cui si riferiscono.

## Obiettivo del progetto
CasinoKing è composto da due macro-componenti:

1. **Piattaforma casino**
   - frontend
   - backend
   - auth
   - wallet
   - ledger
   - admin
   - promo
   - reporting

2. **Giochi proprietari**
   - primo gioco: Mines
   - progettati come moduli separabili e in futuro integrabili anche all’esterno

## Principi architetturali chiave
- stack: FastAPI + Next.js + PostgreSQL + Redis + Docker
- sviluppo locale su Ubuntu
- wallet con **snapshot materializzato**
- ledger come **fonte contabile primaria**
- modello **double-entry**
- piano dei conti con `ledger_accounts`
- Mines con payout runtime tabellare
- polling / request-response per il MVP, non WebSocket
- idempotenza obbligatoria sugli endpoint finanziariamente sensibili

## Documenti finali ufficiali

### Core
- `docs/word/CasinoKing_Documento_00_FINALE.docx`
- `docs/word/CasinoKing_Documento_02_Fondazioni_Architettura.docx`
- `docs/word/CasinoKing_Documento_03_Architettura_DB_API.docx`

### Financial core
- `docs/word/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.docx`

### Mines / game design
- `docs/word/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.docx`
- `docs/word/CasinoKing_Documento_07_v2_Mines_Matematica_Congelata.docx`
- `docs/word/CasinoKing_Documento_08_v2_Game_Tuning_Numerico.docx`
- `docs/word/CasinoKing_Documento_09_v2_Game_Engine_Testing.docx`
- `docs/word/CasinoKing_Documento_10_Fairness_Randomness_Seed_Audit.docx`

### API / backend
- `docs/word/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.docx`

### Database / SQL
- `docs/word/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.docx`
- `docs/word/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.docx`

### Infra / execution
- `docs/word/CasinoKing_Documento_14_v2_Ambiente_Locale_Realtime_Policy.docx`
- `docs/word/CasinoKing_Documento_15_Piano_Implementazione.docx`

## Allegati runtime ufficiali
- `docs/runtime/CasinoKing_Documento_07_Allegato_A_Payout_Table_Mines_v3.xlsx`
- `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json`
- `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.csv`

## Ordine di precedenza pratico

### 1. Regole finanziarie
Se il tema riguarda wallet, saldo, posting, contabilità, riconciliazione:
- prima leggere `Documento_05_v3`
- poi `Documento_11_v2`
- poi `Documento_12_v3` e `Documento_13_v3`

### 2. Mines
Se il tema riguarda Mines:
- prima leggere `Documento_06`
- poi `Documento_07_v2`
- poi gli allegati runtime in `docs/runtime`
- poi `Documento_08_v2`
- poi `Documento_09_v2`
- poi `Documento_10`

### 3. API
Se il tema riguarda endpoint, payload, errori, idempotenza:
- prima leggere `Documento_11_v2`
- poi `Documento_05_v3`
- poi `Documento_09_v2`

### 4. Ambiente di sviluppo
Se il tema riguarda setup locale, Docker, workflow:
- leggere `Documento_14_v2`
- poi `Documento_15`

## Nota importante
I documenti 12 v3 e 13 v3 rappresentano la versione target di riferimento.
Durante la fase di sviluppo possono subire modifiche incrementali per adattarsi a esigenze implementative reali, ottimizzazioni o vincoli tecnici emersi, senza cambiare le fondamenta del modello.

## Cosa non usare come riferimento
- documenti vecchi o superati
- versioni precedenti già sostituite da v2/v3
- assunzioni non presenti nei documenti ufficiali