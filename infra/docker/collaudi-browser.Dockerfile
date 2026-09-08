# IMMAGINE DEI SOLI COLLAUDI DI SCHERMO — non e' l'immagine di prodotto.
#
# PERCHE' ESISTE. I 72 collaudi che guardano il browser si sono saltati per giorni
# ("Chromium executable not available"). La causa vera, trovata l'8/09/2026 chiedendo a
# pytest il motivo dei salti invece di supporlo, e' in tre strati:
#   1. il pacchetto python playwright non bastava: manca il BINARIO del browser;
#   2. i collaudi cercano un chromium DI SISTEMA sul PATH, non quello di playwright;
#   3. il binario di playwright non parte nell'immagine del backend: 25 librerie di
#      sistema mancanti, exitCode 127.
#
# PERCHE' UN'IMMAGINE DERIVATA E NON UNA MODIFICA A backend.Dockerfile. Il congelamento
# del prodotto e' ancora in vigore su infra/. Aggiungere 25 librerie all'immagine che
# gira in produzione per far passare dei collaudi sarebbe far pagare al prodotto il costo
# dello strumento di misura. Questa immagine esiste solo per i collaudi.
FROM casinoking-backend:latest

RUN pip install --no-cache-dir playwright pytest pytest-xdist httpx pillow \
 && python -m playwright install --with-deps chromium \
 && ln -sf "$(find /root/.cache/ms-playwright -name chrome -path '*chrome-linux*' | head -1)" \
           /usr/local/bin/chromium \
 && chromium --version
