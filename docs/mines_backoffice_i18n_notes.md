# Mines Backoffice And I18n Notes

Nota operativa non canonica.

Questa nota raccoglie un ordine di lavoro proposto per il backoffice configurativo di Mines
e le opzioni di multilingua emerse durante il polish del prodotto.
Non sostituisce `docs/SOURCE_OF_TRUTH.md` e non introduce requisiti vincolanti.

## Ordine consigliato

1. Configurazione testi e regole del gioco
2. Configurazione griglie e mine selezionabili
3. Label UI distinte tra demo mode e real mode
4. Solo dopo: internazionalizzazione vera e propria

## Backoffice Mines

### A. Regole testuali HTML

Obiettivo:
- un pannello admin dedicato a contenuti testuali del gioco
- editing in HTML controllato
- una sorgente distinta per sezioni regole come `ways_to_win`, `payout_display`,
  `settings_menu`, `bet_collect`, `balance_display`, `general`, `history`

Direzione consigliata:
- salvare i blocchi come contenuto strutturato lato backend
- renderizzare nel frontend Mines solo HTML sanitizzato
- lasciare tabelle e componenti dinamici come embed software futuri, non come HTML libero

### B. Configurazione griglie e mine

Obiettivo:
- backoffice per decidere quali grid size sono pubblicate
- per ogni grid size, quali mine count sono pubblicabili
- definizione del valore default per ogni size
- in futuro: eventuali profili per environment o rollout

Direzione consigliata:
- introdurre una configurazione pubblicabile distinta dal runtime ufficiale
- il runtime backend resta la sorgente di verita' dei valori supportati
- il backoffice puo' solo scegliere un sottoinsieme valido e il default

### C. Label pulsanti demo / real

Obiettivo:
- pannello per label di CTA e microcopy differenziati tra demo e real mode

Direzione consigliata:
- chiavi stabili tipo `bet_cta`, `collect_cta`, `demo_balance_label`, `real_balance_label`
- valori separati per `demo` e `real`
- niente testo hardcoded nel frontend dove il copy puo' diventare di prodotto

## Multilingua

### Soluzione 1. English canonico ora, i18n key-based dopo

Approccio:
- mantenere per ora tutto in inglese come default canonico
- iniziare subito a spostare il copy variabile su chiavi stabili
- introdurre i dizionari localizzati solo dopo il backoffice contenuti

Pro:
- minimo rischio adesso
- non blocca il lavoro su UX e backoffice
- prepara bene il refactor i18n senza riscrivere due volte il copy

Contro:
- il multilingua non arriva immediatamente
- per un periodo il progetto resta solo inglese

Impatto:
- basso sul backend
- medio sul frontend, per sostituire stringhe hardcoded con chiavi

### Soluzione 2. Content registry lato backend per regole e label

Approccio:
- introdurre un registry backend con record del tipo
  `namespace`, `content_key`, `locale`, `channel`, `mode`, `html/text`
- il frontend legge gia' contenuti localizzati dal backend

Pro:
- adatto al backoffice editoriale
- supporta subito regole HTML, label demo/real e locale
- centralizza auditing e pubblicazione

Contro:
- piu' lavoro subito
- serve disegnare bene versioning, fallback e sanitizzazione

Impatto:
- medio/alto sul backend
- medio sul frontend
- molto buono se il backoffice diventa davvero editoriale

### Soluzione 3. Dizionari frontend statici + regole backend

Approccio:
- UI chrome e label brevi in dizionari frontend
- regole HTML e contenuti lunghi nel backend/backoffice

Pro:
- compromesso pratico
- meno complesso di un registry totale
- separa bene microcopy UI da contenuti editoriali

Contro:
- due sorgenti contenuto diverse
- governance piu' delicata nel tempo

Impatto:
- medio complessivo
- puo' essere un buon ponte, ma non e' la soluzione piu' pulita a lungo termine

## Scelta consigliata

Scelta consigliata a questo punto del progetto:
- nel brevissimo: Soluzione 1 per non bloccare il refactor
- subito dopo il pannello configurativo Mines: evolvere verso Soluzione 2

Motivo:
- oggi il progetto ha gia' bisogno di un backoffice contenuti/configurazioni
- se il multilingua parte troppo presto senza quel modello, rischiamo di duplicare
  stringhe e pannelli due volte
- conviene prima definire il perimetro editoriale di Mines, poi innestare le locale
  sopra una struttura coerente
