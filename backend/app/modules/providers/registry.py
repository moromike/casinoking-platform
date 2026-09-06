"""Elenco dei provider esterni riconosciuti dalla piattaforma.

PERCHE' NON C'E' PIU' UNA CHIAVE DI RIPIEGO: fino al 4/09/2026 questo file diceva

    os.environ.get("MANDM_SECRET_KEY", <una stringa fissa scritta nel sorgente>)

con una stringa fissa come valore di ripiego, e la stessa stringa stava anche
dal lato del provider. Chiunque conoscesse quel
valore — cioe' chiunque avesse letto il sorgente — poteva firmare una richiesta
valida verso gli endpoint del portafoglio. Un segreto scritto nel codice non e' un
segreto: e' una porta con la chiave appesa accanto.

Ora, se la chiave non e' in ambiente, il provider **non viene registrato affatto** e
ogni sua chiamata riceve 401. Si chiude, non si apre: e' l'unico verso accettabile
per un errore di configurazione che riguarda dei soldi.
"""

import os

PROVIDERS: dict[str, dict[str, bytes]] = {}

_chiave_mandm = os.environ.get("MANDM_SECRET_KEY")
if _chiave_mandm:
    PROVIDERS["m-and-m-games"] = {"secret_key": _chiave_mandm.encode()}


def get_provider_secret(provider_id: str) -> bytes | None:
    provider = PROVIDERS.get(provider_id)
    if not provider:
        return None
    return provider["secret_key"]

_chiave_collaudo = os.environ.get("CK_COLLAUDO_SECRET_KEY")
if _chiave_collaudo:
    PROVIDERS["ck_collaudo"] = {"secret_key": _chiave_collaudo.encode()}
