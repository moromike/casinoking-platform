# Fase 8B, Parte A — le prove

**5 settembre 2026.** Commit della piattaforma: `c71ff03`, ramo `fase8/provider`.
Gate **VERDE**: 618 collaudi passati, 0 falliti, minimi 618/624.

## Che cosa e' stato dimostrato, e con quale ricevuta

| Ricevuta | Che cosa dimostra | Come si ristampa |
|---|---|---|
| `chiusura-a-cascata.txt` | **La prova che conta.** Quando una sessione si chiude, la cavia di collaudo restituisce la puntata trattenuta **con le stesse identiche scritture contabili di Mines**: stesso tipo di transazione, stessi conti, stessi lati, e importo pari alla puntata su entrambi. Contiene anche i due **rossi apposta**: togliendo l'iscrizione dal registro, la chiusura viene **rifiutata** invece di riuscire lasciando i soldi fermi | `./scripts/ck-test.sh tests/integration/test_cap03_liquidazione_registro.py -v -s` |
| `spostamento-non-riscrittura.txt` | 426 righe di logica contabile sono state **spostate** fuori dalla piattaforma, non riscritte: 6 righe di differenza in tutto, tutte e sole un rinominamento. Confronto meccanico funzione per funzione contro la versione precedente | confronto automatico contro `git show HEAD~1:backend/app/modules/platform/access_sessions/service.py` |
| `lettura-sessione-parita.txt` | La nuova lettura di partita della piattaforma restituisce, campo per campo e valore per valore, esattamente cio' che restituiva la vecchia lettura interna a Mines | `./scripts/ck-test.sh tests/integration/test_capacita_di_piattaforma.py -v -s` |
| `capacita-senza-giochi.txt` | **Il criterio di prodotto.** Le tre capacita' funzionano con i giochi veri **spenti**, con le loro rotte confermate 404 *prima* di dichiarare qualunque cosa. Include la prova che spegnere le rotte non spegne il dovere di restituire denaro gia' trattenuto | `./scripts/ck-prova-capacita-senza-giochi.sh` |
| `asserzioni-prima-dopo.txt` | Nessun collaudo e' stato annacquato: 828 asserzioni minime, 841 presenti. E si contano anche i **collaudi eseguiti** per file, perche' un file interamente saltato esce "zero falliti" e sembra verde. Nessun file a zero | `./scripts/ck-asserzioni-prima-dopo.sh` |
| `gate-parte-a.txt` | Il referto del semaforo: albero pulito, nessuno skip muto su 129 file, 618 passati e 0 falliti, minimi non calati | `./scripts/ck-gate.sh` |

## E queste due dicono cosa NON e' dimostrato

Sono qui perche' valgono quanto le altre. Una promessa piu' larga della prova che la
sostiene e' il modo in cui questo progetto ha gia' perso due giri di lavoro.

| Ricevuta | Che cosa dichiara |
|---|---|
| `dichiarati.md` | Ogni collaudo che **non** e' stato spostato sulla cavia, con file, riga e motivo. Fra questi una lacuna vera per la Fase 10: 17 collaudi provano il **catalogo** — varianti, pubblicazione in vetrina, archiviazione — che e' roba della piattaforma ma oggi si puo' verificare solo attraverso un gioco vero |
| `cosa-non-dimostra.md` | Che cosa *«verde a giochi spenti»* **non** dimostra: spegnere le rotte non e' togliere il codice. Il giorno che i giochi non ci saranno, la suite non fallirebbe *un po'* — **non partirebbe affatto**, zero collaudi eseguiti su 616, per due righe in un solo file. Censimento meccanico dei 32 import in `import-di-gioco.txt` |

## Una riserva, ed e' scritta apposta

Il semaforo di questa fase **l'ha eseguito chi ha orchestrato il lavoro**, non un terzo
indipendente. Le revisioni di Kimi e Antigravity ci sono state — e hanno trovato tre
difetti veri, fra cui un doppio accredito — ma sul **codice**, prima delle correzioni che
ne sono nate. **Il rilancio del gate da parte di qualcuno che non ha fatto il lavoro resta
da fare.** Fino ad allora queste ricevute sono vere ma non controfirmate.
