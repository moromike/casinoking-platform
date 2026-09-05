APPROVATO CON RISERVE

I 6 difetti originali segnalati nella revisione precedente sono stati chiusi correttamente:
1. L'uso di `CK_GATE_TEST_CMD` ora fa fallire esplicitamente il gate (riga 254).
2. Il codice di uscita di pytest viene onorato impedendo falsi verdi (riga 275).
3. L'assenza di `test_raccolti_minimo` non spegne più il controllo, ma porta a un fallimento sicuro impostando il limite a 999999999 (riga 298).
4. Il timbro viene estratto e validato attivamente contro l'elenco `SIGLE_AMMESSE` presente in `gate-baseline.json` (riga 233).
5. L'espressione regolare è stata ampliata e non pretende più la chiocciola (riga 219).
6. Gli errori di grep (exit code >= 2) vengono intercettati e fanno fallire il gate (riga 243).

Tuttavia, ci sono **DUE NUOVI AGGIRAMENTI (falsi verdi)** strutturali nel nuovo codice:

1. **Evasione dell'espressione regolare tramite importazione diretta (Riga 219):**
   Il pattern `pytest\.mark\.(skip|xfail)|pytest\.skip\(` presume che il modulo venga usato per esteso. Un utente può silenziare un test senza alcun timbro aggirando il grep con:
   ```python
   from pytest import mark
   @mark.skip
   def test_muto(): ...
   ```
   oppure usando `from pytest import skip; skip()`. Se i test restanti sono comunque superiori alla soglia `test_eseguiti_minimo`, la suite uscirà con codice 0 e il gate diventerà VERDE senza accorgersi dello skip muto.

2. **Cecità sui file nominati diversamente (Riga 203):**
   Il comando `git ls-files -- '*test_*.py' '*conftest.py'` **ignora** i file che finiscono in `_test.py` (es. `auth_test.py`). Poiché Pytest raccoglie nativamente anche il pattern `*_test.py`, un programmatore può inserire uno skip muto in quei file (o rinominare un test file in quel modo): Pytest lo salterà, ma il gate non lo scansionerà, dando VERDE. Va aggiunto il pattern `'*_test.py'`.
