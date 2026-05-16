# Site Banner And Mockup Plan

Documento di progetto per completare homepage/banner CMS e migliorare il sito player.

## Stato

- Tipo: piano operativo Site CMS e redesign sito.
- Stato: pronto per review CTO.
- Ambito: homepage slots, media banner, mockup sito, direzione visuale.
- Non sostituisce: `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md`, `docs/SITE_CMS_EDITORIAL_UX_PLAN.md`.

## Stato Attuale

Gia' fatto:

- `site_home_slots` backend;
- API admin/public;
- audit operativo;
- UI admin `Homepage slots`;
- lobby player legge `/site/home`;
- CTA demo/real validate contro Site/Lobby.
- CMS-2D media banner:
  - tabella `site_assets` limitata a `asset_kind = homepage_banner`;
  - upload/list/delete da admin Site UI;
  - selezione immagine sullo slot homepage;
  - render immagine nella lobby player con fallback.

Non ancora fatto:

- mockup visuale del sito;
- nuovo main tab richiesto in futuro.

## Decisione

Completare prima il banner come superficie CMS reale, poi rifare il sito su mockup.

Motivo:

- senza immagine/media, il banner e' solo copy/CTA;
- senza mockup, rischiamo di fare polish incrementale su una pagina ancora basica;
- mockup e implementation devono restare separati.

## CMS Banner Completion

Obiettivo:

- collegare un'immagine `homepage_banner` allo slot homepage;
- permettere upload/select da backoffice;
- renderizzare immagine nella lobby/home;
- mantenere fallback se manca media.

Backend:

- usare `title_assets` solo se l'asset e' legato a un Title;
- per banner generico di sito usare `site_assets` con `asset_kind =
  homepage_banner`.

Posizione severa:

- non userei `title_assets` per banner generico sito se il banner non appartiene a un Title. Sarebbe una scorciatoia confusa.

Proposta:

- per CMS-2D creare solo una superficie media site-owned minima:
  - `site_assets` implementata da `0034__site_assets.sql`;
  - `asset_kind = homepage_banner`;
  - upload/delete/list;
  - audit operativo `site_asset_upload` / `site_asset_delete`;
  - `site_home_slots.media_asset_id` punta a `site_assets.id`.

Stato implementativo:

- completato upload/select/render;
- storage locale sotto `var/assets/sites/...`;
- URL pubblico `/static/sites/{site_code}/homepage_banner/{checksum8}.{ext}`;
- formati ammessi: PNG, JPEG, WebP;
- cap iniziale: 2 MB;
- consiglio UI: 16:9, 1280 x 720 px;
- delete asset disassocia gli slot collegati e fa tornare il fallback.

Limite esplicito CMS-2D:

- niente media library generica;
- niente folders;
- niente tagging;
- niente asset multi-kind;
- niente editor immagini;
- una tabella, un kind, upload/delete/list.

Alternativa piu' piccola:

- se il banner e' sempre promozione di un Title, usare asset del Title `background` o `game_card`.
- limite: non copre banner istituzionali o promozioni sito.

## Mockup Sito

Obiettivo:

- definire una direzione visuale prima di rifare codice.

Direzioni consigliate:

1. `Premium Casino Lobby`
   - sito compatto, elegante, orientato a giochi e promozioni;
   - hero forte;
   - card giochi professionali;
   - account/login chiari.

2. `Mines First`
   - Mines come prodotto principale;
   - hero con gioco/board/diamanti;
   - CTA demo immediata;
   - sezione varianti sotto.

3. `Player Dashboard`
   - meno marketing, piu' app;
   - saldo, giochi, ultimi movimenti e continue playing;
   - utile se vogliamo sensazione da piattaforma operativa.

Direzione CTO consigliata:

- partire da `Premium Casino Lobby`;
- usare `Mines First` solo come esplorazione secondaria, perche' rischia di
  vincolare il sito a un prodotto solo;
- non usare `Player Dashboard` come direzione della homepage commerciale:
  e' piu' adatta a un'area account/app interna.

Input richiesti:

- 3-5 siti o screenshot che piacciono a Michele;
- cosa piace di ognuno: layout, colori, card, hero, densita', menu;
- cosa evitare: eccesso promo, look crypto, look slot generico, dark troppo cupo.

Output mockup:

- 2-3 screenshot statici PNG oppure mock HTML/CSS serviti da `/mockup/*`;
- non collegati al backend;
- review chiusa solo con ok scritto di Michele;
- poi implementation.

## Nuovo Main Tab Futuro

Il nuovo main tab va trattato come requisito separato.

Non va infilato nel redesign senza nome, contenuto e priorita'.

Quando Michele lo spiega, il piano deve chiarire:

- label tab;
- pubblico target;
- route;
- dati necessari;
- relazione con lobby/account/admin;
- se richiede CMS.

## Sequenza Operativa

1. CMS-2D `site_assets` limitato a `homepage_banner`. Completato.
2. Implementare upload/select banner. Completato.
3. Render player banner con fallback. Completato.
4. Preparare 2-3 mockup sito.
5. Validare direzione.
6. Implementare redesign sito a slice.

## Criteri Di Accettazione

- banner con immagine non richiede rebuild;
- upload/delete scrive audit;
- slot senza media resta funzionante;
- CTA continua a rispettare Site/Lobby publication;
- mockup approvato prima del redesign;
- niente settlement, wallet o runtime Mines toccati.
