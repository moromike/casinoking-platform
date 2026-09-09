# IMMAGINE DEI COLLAUDI ORDINARI — non e' l'immagine di prodotto.
#
# PERCHE' ESISTE (MET-05, 9/09/2026). Fino a oggi ck-test.sh eseguiva a OGNI lancio
# `pip install -q pytest pytest-xdist httpx playwright pillow` dentro un contenitore
# nuovo. Misurato: [GENERATO] quel pip costa 9,66 s su 9,71 s di corsa totale, mentre
# il collaudo vero dura 0,52 s. Il `docker run` a vuoto costa 0,37 s: NON e' Docker a
# essere lento, era la reinstallazione rifatta da capo. ck-difetti-veri.sh lancia
# 12 volte, la verifica di Codex ne ha lanciate centinaia: sono ore di attesa.
#
# PERCHE' UN'IMMAGINE DERIVATA E NON backend.Dockerfile. Stessa ragione di
# collaudi-browser.Dockerfile: il congelamento del prodotto e' in vigore su infra/, e
# il prodotto non deve pagare il costo dello strumento di misura.
#
# PERCHE' NON SI USA DIRETTAMENTE collaudi-browser.Dockerfile. Quella pesa 2,04 GB
# perche' porta il browser e le sue 25 librerie di sistema. Questa aggiunge solo i
# pacchetti python: serve alla corsia ORDINARIA, che il browser non lo usa.
FROM casinoking-backend:latest

# L'IMMAGINE PORTA SCRITTO DA COSA E' NATA. Due targhe: l'impronta di questo file e
# l'identita' esatta dell'immagine di base. ck-immagine-collaudi.sh le confronta con lo
# stato di adesso e ricostruisce solo se una delle due e' cambiata.
# PERCHE' NON LE DATE, che era il primo tentativo: quando i livelli sono in cache Docker
# riusa la configurazione identica, e l'immagine "ricostruita" conserva la data di nascita
# vecchia. Il confronto sulle date restava percio' bloccato su "e' vecchia" e ricostruiva
# a ogni singolo lancio — cioe' reintroduceva MET-05 in un'altra forma.
ARG CK_RICETTA=ignota
ARG CK_BASE=ignota
LABEL ck.ricetta=$CK_RICETTA
LABEL ck.base=$CK_BASE

# pytest, pytest-xdist e httpx sono gia' nell'immagine di prodotto (arrivano da
# backend[dev]). Si nominano lo stesso: cio' che il lancio pretende deve stare
# scritto in un posto solo, e questo e' quel posto.
RUN pip install --no-cache-dir pytest pytest-xdist httpx playwright pillow \
 && python -c "import pytest, xdist, httpx, playwright, PIL; print('cinque pacchetti presenti')"
