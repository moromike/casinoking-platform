# CasinoKing - Documento 12 v3

Schema Database PostgreSQL definitivo (livello implementativo)

Nota importante:

Questo documento rappresenta la versione target di riferimento. Durante la fase di sviluppo potrebbe subire modifiche incrementali per adattarsi a esigenze implementative reali, ottimizzazioni o vincoli tecnici emersi.

Contenuti principali:

- Struttura completa wallet snapshot + ledger

- Tabella ledger_accounts (piano dei conti completo)

- ledger_transactions + ledger_entries con relazioni vincolate

- Foreign key e vincoli di integrità forti

- Strategia per evitare drift tra wallet e ledger

- Supporto per multi-currency futura

- Preparazione a scalabilità e audit
