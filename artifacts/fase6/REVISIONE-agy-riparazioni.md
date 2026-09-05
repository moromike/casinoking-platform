RESPINTO

1. **BON-09 (Falso verde / Skip permanente)**: La guardia condizionale `if mancanti:` verifica l'esistenza di file che, per tua stessa ammissione, "non sono MAI stati in git". Questo significa che nella Continuous Integration o su qualsiasi clone pulito, questa condizione sarà sempre vera e il test non girerà mai. È esattamente uno skip incondizionato mascherato da guardia logica, che mantiene il debito intatto. La vera riparazione richiede di generare file dummy temporanei (mock) durante il setup del test, oppure di versionare asset leggeri dedicati.

2. **BON-08 (Riparazione incompleta / fragilità)**: In `test_demo_read_session_replay_without_token`, la fixture `create_published_mines_variant` è stata aggiunta alla firma solo per sfruttarne l'effetto collaterale di setup del DB. Tuttavia, il test non estrae né utilizza il `title_code` generato. Se internamente il flusso conta ancora su costanti hardcoded come "mines001b", il test è fragile e passa solo per coincidenza.

Le altre modifiche (BON-11, BON-10, la risoluzione del comportamento flaky "1 su 9" dovuta alla chiusura del round e la rimozione del test duplicato) sono riparazioni reali e corrette. BON-09, tuttavia, viola il criterio del debito mascherato e rende inaccettabile la bonifica.
