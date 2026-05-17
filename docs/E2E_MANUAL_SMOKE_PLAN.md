Status: ACTIVE
Last meaningful update: 2026-05-07

# CasinoKing - E2E Manual Smoke Plan

## Stato

Documento operativo da validare con CTO prima di considerare chiuso il
checkpoint post-cleanup locale.

Questo smoke manuale non sostituisce test automatici, riconciliazione
finanziaria, production readiness o security review. Serve a verificare che i
flussi gia' implementati lavorino insieme su dati locali puliti.

## Contesto

Dopo la pulizia locale dei cloni di test, il repository e l'ambiente locale
hanno una library pubblica ridotta ai Title reali attesi:

- `mines001b`
- `mines002a`

Il checkpoint indicato in `docs/README.md` richiede uno smoke rapido su:

- Backoffice Games preview;
- Site/Lobby Publishing;
- player lobby;
- launch demo/real;
- popup saldo insufficiente.

Il punto critico e' che questi flussi attraversano layer diversi:

```text
Games backoffice
  crea/configura/previewa varianti

Site/Lobby Publishing
  decide visibilita', demo/real, ordine e metadata

Player lobby
  consuma GET /api/v1/games/library

Mines
  lancia il title_code corretto e applica demo/real
```

## Perche' Lo Facciamo

Lo smoke serve a confermare che il sistema sia realmente usabile prima di
aprire altri cantieri UX o di launch hardening.

In particolare verifica che:

- la pulizia locale non abbia lasciato dati incoerenti in lobby;
- il backoffice e la lobby player leggano la stessa verita' operativa;
- il master Mines non appaia come prodotto pubblico ordinario;
- la preview admin usi token dedicato, non un bypass pubblico;
- demo e real rispettino i flag Site/Lobby;
- gli errori player-facing non espongano messaggi tecnici grezzi.

## Obiettivi

- Validare il percorso admin -> pubblicazione -> lobby player -> gioco.
- Verificare che `GET /api/v1/games/library` esponga solo varianti pubbliche.
- Confermare che il master `mines_classic` resti bloccato e non pubblicato in
  lobby.
- Confermare che la preview backoffice funzioni tramite `preview_token` admin.
- Verificare il lancio del `title_code` corretto in demo e real.
- Verificare il comportamento anonimo -> login per real play.
- Verificare il popup saldo insufficiente in inglese e player-friendly.
- Raccogliere evidenze condivisibili con CTO/prodotto.

## Scope

Lo smoke copre:

- Backoffice Games: vista Mines, master, varianti, preview demo.
- Site/Lobby Publishing: visibilita', demo/real, metadata, ordine, preview.
- Player lobby: card alimentate dalla library pubblica.
- Mines demo launch: `/mines?title_code={title_code}&mode=demo`.
- Mines real launch: anonimo verso login, autenticato verso gioco.
- Primo pattern errori Mines: saldo insufficiente.
- Controllo visuale rapido desktop/mobile nelle aree attraversate.

## Prerequisiti

- Stack locale avviato e verificato: frontend, backend, PostgreSQL, Redis.
- Site operativo: `casinoking`.
- Account admin locale valido.
- Almeno una variante Mines non-master con config live pubblicata.
- Player anonimo per test CTA real verso login.
- Player autenticato per test real play.
- Saldo insufficiente real ottenibile con wallet vuoto o bet superiore al saldo.
- Saldo insufficiente demo ottenibile esaurendo chip demo o usando bet superiore
  al saldo chip residuo.
- Browser con possibilita' di raccogliere screenshot e Network log.
- Browser minimi: Chrome stable e Firefox.
- Viewport minimi: desktop e mobile responsive con larghezza <= 375px.

## Trigger Di Re-Smoke

Il re-smoke e' obbligatorio prima di aprire ogni nuovo cantiere feature che
tocca pubblicazione, library, launch, auth o flussi Mines player-facing.

## Checklist Smoke

- [ ] Verificare frontend raggiungibile.
- [ ] Verificare backend health live.
- [ ] Verificare container backend, frontend, postgres e redis healthy.
- [ ] Aprire Backoffice -> Games -> Mines.
- [ ] Verificare che `mines_classic` sia visibile come master, bloccato e non
  modificabile.
- [ ] Aprire preview demo del master o di una variante dal backoffice.
- [ ] Confermare che la preview usi `preview_token` admin.
- [ ] Confermare che `preview=1` da solo non sia autorizzazione backend.
- [ ] Aprire Site/Lobby Publishing.
- [ ] Rendere visibile una variante non-master con demo e real abilitate.
- [ ] Salvare metadata lobby minimi se disponibili.
- [ ] Ricaricare Site/Lobby e verificare persistenza.
- [ ] Verificare preview/lobby tramite `GET /api/v1/games/library`.
- [ ] Aprire LOG / admin audit e verificare una entry `lobby_publication_change`
  con payload coerente.
- [ ] Confermare che il master non appaia nella library player.
- [ ] Aprire player lobby.
- [ ] Verificare card, ordine, copy e CTA demo/real.
- [ ] Cliccare Demo e verificare apertura del `title_code` corretto.
- [ ] Da anonimo, cliccare Real e verificare passaggio a login.
- [ ] Da autenticato, aprire Real e verificare ingresso nel flusso Mines.
- [ ] Pubblicare config live di un Title o verificare un publish recente e
  confermare in LOG / admin audit una entry `title_config_publish` con payload
  coerente.
- [ ] Provocare saldo insufficiente real e verificare messaggio player-facing.
- [ ] Provocare saldo insufficiente demo e verificare messaggio player-facing.
- [ ] Disabilitare demo o real per una variante e verificare che il launch
  pubblico diretto venga respinto.
- [ ] Verificare assenza di overlap evidente su desktop.
- [ ] Verificare assenza di overlap evidente su mobile.

## Evidenze Da Raccogliere

- Screenshot o output dello stato container/health.
- Screenshot Backoffice Games con master bloccato e varianti.
- Screenshot preview admin, con token mascherato se visibile.
- Screenshot Site/Lobby dopo salvataggio.
- Screenshot LOG / admin audit con `lobby_publication_change`.
- Screenshot LOG / admin audit con `title_config_publish`.
- Payload o screenshot Network di `GET /api/v1/games/library`.
- Screenshot player lobby con le card pubblicate.
- Screenshot demo launch del Title corretto.
- Screenshot real launch/login flow.
- Screenshot popup saldo insufficiente real.
- Screenshot popup saldo insufficiente demo.
- Nota con data, branch/commit locale, browser usato e Title testato.

## Criteri Di Accettazione

Lo smoke e' accettato se:

- il flusso admin -> Site/Lobby -> player lobby -> Mines funziona per almeno una
  variante non-master;
- la player lobby usa la library pubblica come fonte dati;
- il master non viene renderizzato come item lobby ordinario;
- la preview backoffice richiede token admin dedicato;
- demo/real rispettano i flag Site/Lobby;
- il real anonimo porta a login;
- il saldo insufficiente real mostra popup player-friendly;
- il saldo insufficiente demo mostra popup player-friendly;
- `lobby_publication_change` e `title_config_publish` sono visibili nel LOG /
  admin audit con payload coerente;
- non emergono regressioni evidenti desktop/mobile nelle aree verificate.

## Criteri Di Rifiuto

Lo smoke e' rifiutato se fallisce almeno un item critico:

- Site/Lobby non persiste o non alimenta correttamente la library.
- Player lobby non riflette `GET /api/v1/games/library`.
- Demo o real launch non rispettano `title_code` e flag Site/Lobby.
- Auth real play non distingue correttamente anonimo e player autenticato.
- Preview admin non richiede `preview_token`.
- Audit log non mostra eventi essenziali di publish/config o lobby publication.

Se fallisce un item critico, l'apertura di nuove slice resta bloccata fino al
fix e al re-smoke.

Se fallisce solo un item secondario visuale, come overlap o polish responsive
non bloccante, si apre un ticket in `docs/PRODUCT_CLOSURE_BACKLOG.md` e non si
blocca l'avvio del cantiere successivo.

## Fuori Scope

- Nuove feature UI o backend.
- CMS completo sito/homepage.
- Creazione engine non-Mines.
- Modifiche payout, RTP, RNG o fairness.
- Reconciliation wallet/ledger approfondita.
- Audit finanziario o gameplay round-by-round.
- Production readiness e security review.
- WebSocket o external adapter.
- i18n foundation.
- Refactor globale error/notification.

## Rischi Se Non Lo Facciamo

- Cleanup locale apparentemente riuscito ma stack non davvero usabile.
- Disallineamento tra backoffice publishing e player lobby.
- Varianti nascoste o modalita' disabilitate ancora lanciabili via link diretto.
- Master Mines trattato come prodotto pubblicabile ordinario.
- Preview admin confusa con autorizzazione pubblica.
- Errori tecnici esposti al player.
- Regressioni UX non viste prima del prossimo cantiere.

## Decisioni Richieste Al CTO

- Confermare che questo smoke sia prerequisito prima di rimuovere l'eccezione
  legacy master launch.
- Confermare quali evidenze sono sufficienti per chiudere il checkpoint.
- Confermare se lo smoke deve essere solo manuale o se alcuni passaggi vanno
  successivamente trasformati in Playwright smoke stabile.
