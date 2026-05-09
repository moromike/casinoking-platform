# Mines Sound Assets Plan

Documento di progetto per introdurre suoni runtime e backoffice modificabile per Mines.

## Stato

- Tipo: piano operativo Mines UX/backoffice/assets.
- Stato: pronto per review CTO.
- Ambito: upload audio, asset registry, tab backoffice, playback runtime.
- Non sostituisce: `docs/ASSET_REGISTRY_PLAN.md`, `docs/ARCHITECTURE_ATLAS_MINES.md`.

## Contesto

I suoni non sono oggi inseriti nel gioco.

Lo schema `title_assets` prevede gia' alcuni asset kind audio (`audio_win`, `audio_lose`, `audio_click`), ma il service backend attuale rifiuta upload non immagine con errore "Asset kind is not uploadable in Phase 4".

Quindi i suoni non vanno embeddati nel codice: vanno completati come estensione dell'asset registry e gestiti da backoffice per Title.

## Obiettivo

Rendere configurabili da backoffice i suoni Mines per Title, con runtime player che li usa dopo interazioni esplicite del player.

Eventi minimi:

| Evento | Asset kind proposto | Quando suona |
| --- | --- | --- |
| Diamante trovato | `audio_safe_reveal` | reveal con esito safe |
| Mina trovata | `audio_mine_hit` | reveal con esito mine/loss |
| Riscossione | `audio_collect` | click Collect/cashout riuscito |
| Vittoria | `audio_win` | round vinto o payout finale positivo |

Nota:

- `audio_win` puo' coincidere con `audio_collect` nella prima slice, ma tenerli separati evita di ridisegnare il contratto subito dopo.

## Decisione Tecnica

Estendere `title_assets`, non creare un sistema audio separato.

Motivo:

- esiste gia' storage filesystem;
- esistono URL versionati per checksum;
- esistono upload/delete/list admin;
- esiste audit operativo;
- esiste risoluzione asset nel theme endpoint.

## Backend Scope

Azioni:

- aggiungere asset kind audio espliciti se non presenti:
  - `audio_safe_reveal`;
  - `audio_mine_hit`;
  - `audio_collect`;
  - `audio_win`.
- supportare MIME:
  - `audio/mpeg`;
  - `audio/wav`;
  - `audio/ogg`;
  - eventualmente `audio/webm` solo se serve.
- aggiungere size cap dedicato audio, per esempio 1 MB iniziale.
- chiarire in UI che WAV e' ammesso solo per suoni cortissimi, indicativamente
  sotto 1 secondo; per suoni piu' lunghi usare `ogg` o `mp3`.
- mantenere checksum, one-active-kind-per-title e audit upload/delete.
- aggiornare test asset registry.

Compatibilita':

- i nuovi asset kind sostituiscono il vocabolario legacy.
- `audio_lose` e `audio_click` restano in DB per compatibilita' storica, ma sono
  deprecati in scrittura e vietati nella nuova UI.
- la UI deve esporre solo `audio_safe_reveal`, `audio_mine_hit`,
  `audio_collect` e `audio_win`.
- non serve migration distruttiva.

## Backoffice Scope

Creare sezione dedicata nel detail Mines:

```text
Sounds
  Safe reveal
  Mine hit
  Collect
  Win
```

Per ogni riga:

- stato: nessun suono oppure custom asset;
- upload file;
- play preview;
- delete;
- public URL o checksum compatto in dettaglio tecnico.

Regola:

- il backoffice deve modificare asset audio, non logica gioco.
- publish separato non necessario se asset registry e' gia' active-on-upload; se si vuole draft/publish audio, serve piano piu' ampio.

## Runtime Frontend Scope

Creare un piccolo hook:

```text
useMinesSounds(titleTheme.assets)
```

Responsabilita':

- precaricare audio quando disponibile;
- suonare solo dopo interazione utente;
- non bloccare gameplay se audio fallisce;
- volume base conservativo;
- mute toggle locale;
- rispettare preferenze browser.

Eventi di integrazione:

- `handleRevealCell`: safe -> `audio_safe_reveal`;
- `handleRevealCell`: mine -> `audio_mine_hit`;
- `handleCashout`: successo -> `audio_collect`;
- win automatico se presente -> `audio_win`.

## Out Of Scope

- musica di sottofondo;
- mixer avanzato;
- volume per singolo suono;
- suoni globali sito;
- audio real-time server side;
- cambio payout/RNG/fairness/wallet/ledger.

## Rischi

| Rischio | Mitigazione |
| --- | --- |
| Browser blocca autoplay | Suoni solo dopo click player. |
| File pesanti | Size cap e formati limitati. |
| Audio fastidiosi | Mute toggle e volume basso. |
| Backoffice monolite cresce | Nuovo componente `MinesSoundAssetsEditor`. |
| Confusione asset raw/runtime | Upload solo tramite asset registry. |

## Verifiche

Backend:

```powershell
python -m pytest tests/integration/test_asset_registry.py tests/contract/test_admin_assets_contract.py
```

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Runtime:

- upload audio safe;
- play preview in backoffice;
- aprire Mines demo;
- reveal safe: suono safe;
- reveal mine: suono mine;
- collect: suono collect/win;
- delete asset: nessun suono per quell'evento.

## Criteri Di Accettazione

- I suoni sono caricabili da backoffice.
- I suoni non sono hardcoded nel bundle.
- Il gioco funziona anche senza audio.
- Se un evento non ha asset audio attivo, resta silenzioso: non esiste fallback
  bundled di default nella prima slice.
- Audio error non rompe reveal/cashout.
- Upload/delete scrivono audit operativo.
- Nessun cambio a core Mines, payout, RNG, wallet o ledger.
