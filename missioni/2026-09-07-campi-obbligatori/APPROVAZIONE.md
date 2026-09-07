# APPROVAZIONE — campi obbligatori sulle rotte seamless

**Questo documento vale solo se il commit che lo introduce e' FIRMATO.**
Non conta chi risulta autore: su questa macchina tutti i motori committano gia' sotto
il nome di Michele Morotti, quindi l'autore di un commit non prova niente. Prova
qualcosa solo la firma, perche' la sua passphrase la sa una persona sola.

Verifica di questo anello:

    git log -1 --show-signature -- missioni/2026-09-07-campi-obbligatori/APPROVAZIONE.md

## Cosa autorizzo

L'applicazione dei cinque blocchi del dossier `PROPOSTA.md` di questa cartella, ai file
del perimetro protetto qui elencati, **esattamente nei byte la cui impronta e' scritta
sotto**. Un byte diverso e' una modifica diversa, e non e' autorizzata.

| File | sha256 del testo autorizzato |
|---|---|
| `backend/app/api/v1/seamless/router.py` | `a68b87eb8cc6c2fbc34182c1ab6b578cdb95aefdd046f666ec8c641cba9599c1` |
| `tests/integration/test_seamless_parita_contabile.py` | `ce2301d5289ee00cb94c14575d4a31521f67a33ae8031f6b56e78f083d77d002` |
| `tests/integration/test_seamless_scrive_davvero.py` | `aa73d7e9b0bec50e582189be3b31132e943832c8578b730dcfa6e179b807f7a0` |
| `tests/integration/test_seamless_ordine_operazioni.py` | `4fc5f78928d395c494a6bed5a28d9802680b216cf1572deba946bc1b494157fe` |
| `tests/integration/test_seamless_controlli_di_casa.py` | `9ff9b6c68d46b4a3379c58c721e8d0cafb6972d117b1e0d306dc97e9b4a0a412` |

## Cosa NON autorizzo

- Nessuna migrazione, nessuna modifica allo schema del database.
- Nessun altro file del perimetro protetto.
- Nessun motore in modalita' autonoma di scrittura puo' eseguire questa applicazione:
  REG-01 lo vieta sul percorso del denaro anche a firma ottenuta.

## La catena, per intero

| Anello | Chi | Esito | Dove |
|---|---|---|---|
| proposta | Claude (claude-opus-5) | — | `PROPOSTA.md` |
| revisione 1 | Kimi K3 | **DA CORREGGERE** — un collaudo verde sarebbe diventato rosso | `REVISIONE-1-KIMI.md` |
| revisione 2 | Kimi K3 | **DA CORREGGERE** — altri tre file di collaudo colpiti | `REVISIONE-2-KIMI.md` |
| revisione 3 | Kimi K3 | **APPROVATA** — otto controlli, impronte ricalcolate | `REVISIONE-3-KIMI.md` |
| misura | Claude, stack acceso | 657→663 verdi, 19→13 rossi, **zero regressioni** | `MISURA-*.txt` |
| approvazione | **Michele** | la firma di questo commit | questo file |
| applicazione | Claude, corsa non autonoma | dopo la firma | commit successivo |

## Il criterio di arresto che resta in piedi dopo la firma

Se applicando i cinque blocchi **un collaudo verde diventa rosso**, l'applicazione si
ferma e si torna al dossier. La firma autorizza un testo, non un risultato: il risultato
lo dice la suite, e la sua parola viene dopo la mia.

## Cosa resta scoperto, e lo so

Questi campi diventano **obbligatori**, non ancora **verificati**: `timestamp` non e'
controllato come data, `nonce` non ha unicita', e il `provider_code` firmato non e' ancora
confrontato con l'intestazione. E' POR-03, ed e' il passo dopo. Chi legge il cruscotto non
deve credere che il rigioco sia chiuso: non lo e'.
