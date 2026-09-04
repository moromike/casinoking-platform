RESPINTO

1. `backend/app/api/router.py:7-15,34,42,44` — reinserisce e pubblica le route BOXE, HI-LO e Mines; `a51cb30` le aveva rimosse insieme ai moduli per trasferirli in `m-and-m-games`. Non e' un ripristino neutro: annulla il disaccoppiamento deliberato e riporta circa 14.500 righe di logica gioco nella piattaforma. HMAC e disinnesco Seamless restano presenti (`backend/app/api/v1/seamless/router.py:35-89`), ma non sanano questa regressione architetturale.

2. `tests/integration/test_mines_network_header_verification.py:49-73` — BON-08 e' una scusa: il test dipende da `mines001b` seedato invece di usare la fixture gia' disponibile `tests/conftest.py:595-634`, che crea e ripulisce un titolo Mines pubblicato senza cancellare il DB. Cinque prove di start/reveal/cashout, ownership e fairness restano silenziate benché riparabili ora.

3. `scripts/ck-test.sh:28-34`; `tests/integration/test_player_lobby_game_card_asset.py:173-176,244-247` — BON-11 e' riparabile: il runner collega gia' il container alla rete `casinoking_default`, ma non esporta `CASINOKING_SITE_V3_FRONTEND_BASE_URL=http://frontend-v3:3001`; la fixture quindi usa `localhost:3001`. I due test Playwright devono essere `browser_smoke` e ricevere quell'endpoint, non essere skip incondizionati. Il verde ordinario esclude proprio la superficie player che dichiarava di controllare.

4. `tests/contract/test_player_auth_return_handoff_contract.py:62-91` — BON-10 non dimostra che il test sia “avanti”: documenta invece che la game card non conserva la pagina d'origine prima di login/registrazione, mentre runtime e helper gia' propagano e consumano `return_to`. Lo skip nasconde un ritorno del giocatore alla pagina sbagliata; implementazione e test sono riparabili nello stesso WP.

5. `gate-baseline.json:2-3` — 574 eseguiti e 589 raccolti sono coerenti con il run registrato (`stato-notte.md:4-5`, cioe' 574 passati + 15 skip), ma non rendono veri i nove ritiri: BON-08, BON-10 e BON-11 sono debito eseguibile mascherato. La baseline fotografa un verde numerico, non una suite integralmente bonificata.
