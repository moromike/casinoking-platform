# CAP-05 — cosa "verde a giochi spenti" NON dimostra

**5 settembre 2026.** Dichiarato adesso, non scoperto in Fase 10. E' il tipo di promessa
piu' larga della prova che l'ha sostenuta, ed e' esattamente cio' che in questa fase ci e'
gia' costato due giri.

---

## Cosa dimostra davvero la prova che abbiamo

`./scripts/ck-prova-capacita-senza-giochi.sh` spegne `CK_GIOCHI_INTERNI`, verifica che le
tre rotte dei giochi rispondano **404**, e poi esegue le capacita' di piattaforma.
Dimostra una cosa sola, ed e' vera: **le rotte dei giochi non servono** a quelle capacita'.

## Cosa NON dimostra, e la differenza e' tutta qui

Spegnere l'interruttore **non toglie il codice**: i moduli `app.modules.games.*` restano
sul disco e restano importabili. Il giorno dell'estrazione **non ci saranno**. Sono due
situazioni diverse, e la prova di oggi copre solo la prima.

### Il blocco n.1 — la radice dei collaudi importa Mines, e uccide la RACCOLTA

```
tests/conftest.py:19   from app.modules.games.mines.randomness import generate_board
tests/conftest.py:20   from app.modules.games.mines.runtime   import get_runtime_config
```

E' il `conftest.py` **di radice**: pytest lo importa prima di raccogliere qualunque
collaudo. Se quel modulo non esiste, la raccolta muore all'import e **la suite intera non
parte**. Non "tredici file falliscono": **zero collaudi vengono eseguiti**, su 616 raccolti
oggi. Un verde a giochi spenti non dice niente su questo, perche' a giochi spenti il modulo
c'e' ancora.

Peggiora: `preserve_mines_backoffice_config` (`tests/conftest.py:229`) e' `autouse=True`,
cioe' gira **a ogni singolo collaudo**, e scrive su `title_configs` e
`mines_title_configs`. E `_build_test_mines_backoffice_snapshot` (`tests/conftest.py:1362`)
chiama `get_runtime_config()` di Mines per costruire la fotografia di partenza.

### Il censimento completo — meccanico, non a impressione

Estratto con l'analizzatore sintattico di Python sull'intero albero `tests/`:

| | |
|---|---|
| Import di moduli di gioco **a livello di modulo** | **32** in **21 file** |
| di cui in `tests/conftest.py` (uccidono la raccolta di TUTTO) | **2** |
| Import dentro una funzione (uccidono solo quel collaudo) | **1** |

Ripartizione per gioco: Boxe 14, Mines 8 (di cui 2 nel conftest di radice), Hi-Lo 5,
manichino 5. Elenco integrale con file e riga in `artifacts/fase8b/import-di-gioco.txt`.

### Nota di metodo, e vale piu' del numero

Il primo censimento l'ho fatto col Python della macchina, che e' il **3.10**.
`tests/conftest.py` usa sintassi del **3.12** (`type X = ...` alla riga 25): l'analizzatore
non l'ha compilato, il mio script ha **saltato il file in silenzio**, e il conteggio usciva
**31 anziche' 32** — senza proprio i due import che contano di piu'.

Un attrezzo di verifica che salta cio' che non riesce a leggere **e' peggio di nessun
attrezzo**, perche' produce un numero dall'aria precisa. Rifatto dentro il contenitore, con
il Python 3.12 e con il conteggio dei file illeggibili stampato in testa: **0 illeggibili**.
Il conteggio di sopra e' quello buono.

---

## Cosa serve districare, ed e' lavoro della Fase 10

| Da fare | Dove | Peso |
|---|---|---|
| Togliere i due import di Mines dal `conftest.py` di radice | `tests/conftest.py:19-20` | **e' il blocco**: finche' c'e', niente altro conta |
| Rendere la fixture `autouse` neutra rispetto al gioco | `tests/conftest.py:229-343` | media: la fotografia di configurazione va presa in modo generico |
| Sostituire `get_runtime_config()` di Mines nella fotografia di prova | `tests/conftest.py:1362-1375` | media |
| Spostare i 30 import di gioco restanti dentro i file dei giochi | 20 file, elenco in `import-di-gioco.txt` | bassa ma numerosa: sono collaudi **dei giochi**, se ne vanno col gioco |
| Un cricchetto che pretenda `0` import di gioco nel `conftest.py` di radice | nuovo | bassa, e impedisce la ricaduta |

**Stima:** 1-2 giornate di lavoro, di cui la maggior parte sul solo `conftest.py`. Non e'
grande: e' **bloccante**, che e' un'altra cosa. Va fatto **prima** di dichiarare qualunque
cosa sull'estrazione, non dopo.

## La frase da non dire piu'

*"La suite e' verde a giochi spenti, quindi la piattaforma sta in piedi senza i giochi."*
La prima meta' e' vera e misurata. La seconda **non segue**, e questo documento e' il
perche'.
