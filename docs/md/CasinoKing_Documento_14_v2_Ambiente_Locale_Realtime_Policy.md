# CasinoKing – Documento 14 v2

Ambiente locale, workflow e strategia realtime UI

## 1. Cosa cambia rispetto alla v1

- Aggiunta decisione esplicita su realtime UI per Mines.
- Polling scelto per MVP; WebSocket rimandato a fase successiva.

## 2. Decisione realtime

Per Mines MVP si sceglie polling leggero o modello request/response, non WebSocket.

- Mines è turn-based, quindi non richiede canale realtime persistente.
- Ogni azione importante (start, reveal, cashout) riceve già risposta completa dal backend.
- Endpoint GET session/{id} resta disponibile per recover state e refresh UI.
- WebSocket sarà valutato per feature future: tornei, chat, notifiche live, multiplayer, streaming state.

## 3. Impatto architetturale

- Nessun servizio websocket in docker-compose MVP.
- Frontend può usare chiamate request/response classiche.
- La readiness del sistema non dipende da infrastruttura realtime.
