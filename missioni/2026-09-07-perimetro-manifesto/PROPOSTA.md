motore: Codex
modello: gpt-5.6-sol
modalita: scrittura autonoma — PROPOSTA, non applicata
ruolo: proponente
data: 2026-09-07
revisione indipendente: Kimi (verdetto DA CORREGGERE, rilievi recepiti)
sha256: DA-CALCOLARE-DA-ck-provenienza.sh

# Dossier — protezione del manifesto del censimento

Riga esatta da aggiungere a `scripts/perimetro-protetto.txt`, nella sezione **I VERIFICATORI** accanto a `scripts/ck-censimento.sh`:

```text
MODIFICA scripts/censimento-specifiche.txt
```

Il manifesto contiene la data che decide se il censimento e' verde: proteggerlo impone la stessa catena di revisione richiesta per modificare il verificatore che lo legge.

Senza questa riga, un agente potrebbe dichiarare una data futura e togliere `DA-AGGIORNARE-A-MANO`, ottenendo verde senza avere ripubblicato le specifiche.
