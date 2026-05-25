Status: ACTIVE
Last meaningful update: 2026-05-23

# CasinoKing - CMS v2 Module Composer Plan (Corrected Handoff)

Documento di sintesi riallineato per il passaggio del progetto CMS v2.

## Architettura Target (Corretta)

Il sistema deve essere diviso secondo questo schema rigoroso:

- **Porta 3000 (Admin & Builder)**:
  - Backoffice legacy stabile.
  - **Nuova Sezione Builder v2**: Il "Module Composer" (Picker, Editor, Preview di gestione) deve vivere qui come sezione interna all'admin (es: `/admin/site-v2`).
- **Porta 3001 (Sito Player v2)**:
  - Deve ospitare esclusivamente il **nuovo sito player modulare**.
  - Consuma le API del CMS v2 per renderizzare la homepage e le altre pagine in base ai draft pubblicati.
- **Backend (Porta 8000)**:
  - Modulo `cms_v2` condiviso che gestisce la persistenza di pagine e moduli.

## Stato Attuale (Situazione da Riallineare)

Al momento il lavoro è stato svolto in modo invertito ed è necessario spostare i pezzi:
1. **Il Builder è nel posto sbagliato**: Attualmente risiede in `frontend-v2` (porta 3001). Deve essere migrato dentro `frontend` (porta 3000).
2. **Il Sito v2 manca**: La porta 3001 non ha ancora il sito player modulare, poiché è occupata dal builder.
3. **Backend è Corretto**: Le tabelle `cms_v2_pages`, `cms_v2_modules` e le relative API (`/admin/cms-v2/...`) sono pronte, testate e funzionanti.

## Componenti Tecnici Pronti per la Migrazione
I seguenti componenti sono stati sviluppati e vanno spostati nel Backoffice (Port 3000):
- `ModuleRegistry`: Definizione dei tipi di moduli.
- `ModulePicker`: Modale di selezione moduli.
- `ModuleEditor`: Form dinamico per la configurazione dei parametri.
- `ComposerPreview`: Canvas di anteprima con controlli di riordinamento (↑/↓).

## Guida per la prossima AI
1. **Spostamento Builder**: Portare i componenti UI dal laboratorio `frontend-v2` alla cartella `frontend/app/ui/admin/site-v2`.
2. **Integrazione BO**: Sostituire il link esterno "Site v2" con una rotta interna che carica il Builder direttamente nella shell admin della porta 3000.
3. **Creazione Sito v2**: Svuotare `frontend-v2` e implementare una Next.js app leggera sulla porta 3001 che agisca solo da visualizzatore (Player Site) per i moduli pubblicati.

## Conclusione
L'infrastruttura dati e la logica degli editor sono complete. Il compito principale rimasto è il riposizionamento architettonico dei componenti per rispettare la separazione tra Strumento di Gestione (3000) e Sito Pubblico (3001).
