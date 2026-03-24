# CasinoKing – Documento 08 v2

Mines – tuning di prodotto con numeri e policy di bilanciamento

## 1. Cosa cambia rispetto alla v1

- Il documento non resta solo filosofico.
- Viene introdotta la necessità di curve payout numeriche reali e non solo qualitative.
- Si separa chiaramente: matematica base, tuning prodotto, configurazione commerciale.

## 2. Policy di tuning

- Stile scelto confermato: bilanciato tra Stake e Hacksaw.
- Volatilità: media, con early dopamine ma progressione non gratuita.
- Le prime 1-2 reveal devono risultare psicologicamente attraenti, ma non eccessivamente generose.
- Le combinazioni ad alto mine count devono essere volutamente più aggressive.

## 3. Nuovo requisito

Per ogni grid_size supportata deve esistere una matrice di tuning che definisca:

- mine_count consentiti
- moltiplicatori netti per reveal progressivo
- cap massimo di payout per policy prodotto
- flag di disponibilità per UI/admin

## 4. Output richiesto prima dell'implementazione definitiva

- Tabella completa di tuning per tutte le configurazioni supportate.
- Simulazione Monte Carlo o equivalente per controllare RTP/edge effettivo.
- Confronto tra payout teorico e payout commercializzato.
- Range bet e max win per demo.

## 5. Decisione

Il gioco non entra in implementazione definitiva del payout engine finché le tabelle non sono numericamente congelate e testate.
