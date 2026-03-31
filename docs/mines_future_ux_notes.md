# Mines Future UX Notes

Nota operativa non canonica.

Questa nota raccoglie idee future di UX per Mines emerse durante il polish del prodotto.
Non sostituisce `docs/SOURCE_OF_TRUTH.md` e non introduce requisiti vincolanti.

## Osservazione emersa dal fix del rail desktop

- Il rail sinistro desktop di Mines non dovrebbe dipendere da classi layout troppo generiche condivise in [`globals.css`](../frontend/app/globals.css).
- Per le sezioni opzioni (`Grid size`, `Mines`, `Bet amount`) il layout deterministico a griglia è risultato più robusto del precedente approccio con wrapping generico.
- In futuro conviene mantenere il rail Mines come blocco visivo isolato, con namespace CSS dedicato, per ridurre regressioni di prodotto.

## Idee da rivalutare piu' avanti

- Mobile embedded shell: valutare un lancio mobile in iframe/shell dedicata piu' compatta, invece dell'attuale pagina gioco piena.
- Launch / intro page del gioco: valutare una schermata iniziale di introduzione al gameplay, con spiegazione rapida `Bet / Pick / Collect`, separata dal tavolo principale.
- Allineamento di prodotto: continuare a osservare pattern di riferimento esterni solo come ispirazione UX, senza compromettere separazione piattaforma/gioco e vincoli server-authoritative.
