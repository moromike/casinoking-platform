#!/usr/bin/env bash
# ck-firma-setup.sh — prepara la firma delle approvazioni di Michele.
#
# PERCHE' ESISTE. REG-01 pretende che l'approvazione di Michele sia FIRMATA.
# La ragione non e' formale: su questa macchina TUTTI i motori committano gia'
# sotto il nome "Michele Morotti", quindi l'autore di un commit non prova nulla.
# Senza una firma, un agente puo' scrivere l'approvazione, attribuirla a Michele
# e committarla, e nessuno se ne accorge.
#
# LA SOLA COSA CHE RENDE VERA LA FIRMA E' UNA PASSPHRASE CHE SOLO MICHELE SA.
# Per questo lo script la CHIEDE e non la genera: se la generasse un agente, un
# agente potrebbe rifirmare, e l'anello 4 tornerebbe a essere una recita.
#
# LIMITE DICHIARATO: la chiave vive dentro questa macchina virtuale. Protegge da
# tutti i motori AI che ci girano dentro, che e' il rischio vero e misurato.
# Non protegge da chi ha accesso completo alla VM: quello e' Michele.
set -euo pipefail

# NON in ~/.ssh: il portachiavi di Gnome carica in automatico ogni chiave che
# trova li dentro, e una chiave gia sbloccata nel portachiavi e firmabile da
# QUALUNQUE processo della macchina, agenti AI compresi. Verificato il 7/09/2026
# falsificando una firma di Michele in venti secondi. Fuori da ~/.ssh non la tocca.
mkdir -p "$HOME/.casinoking-firma"; chmod 700 "$HOME/.casinoking-firma"
CHIAVE="$HOME/.casinoking-firma/approvazioni"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo
echo "======================================================================"
echo " FIRMA DELLE APPROVAZIONI — CasinoKing"
echo "======================================================================"
echo
echo "Sto per creare una chiave usata SOLO per approvare le modifiche"
echo "al percorso del denaro. Ti chiedera' una password: sceglila tu,"
echo "scrivila due volte, e NON dirla a nessuno (nemmeno a me)."
echo
echo "Da quel momento in poi: ogni volta che approvi qualcosa, ti verra'"
echo "chiesta quella password. E' l'unica cosa, in tutta la catena, che"
echo "nessun motore AI puo' fare al posto tuo."
echo

if [ -f "$CHIAVE" ]; then
  echo "La chiave esiste gia': $CHIAVE"
  echo "Non la tocco. Passo alla configurazione."
else
  echo "--- creazione della chiave (ti chiedera' la password) ---"
  echo
  ssh-keygen -t ed25519 -C "approvazioni-casinoking-moromike" -f "$CHIAVE"
  echo
fi

# La chiave NON va caricata nell'agente ssh: se ci finisse, la password non
# verrebbe piu' chiesta e qualunque processo della macchina potrebbe firmare.
# ATTENZIONE AL CONFRONTO: `ssh-add -l` elenca il COMMENTO della chiave
# ("approvazioni-casinoking-moromike"), non il nome del file. Cercare il nome
# del file non trova niente e il controllo passa a vuoto: successo il 7/09/2026,
# e la chiave e' rimasta nel portachiavi con la password gia' aperta — cioe'
# firmabile da qualunque agente. Si confronta l'IMPRONTA della chiave pubblica.
IMPRONTA_CHIAVE="$(ssh-keygen -lf "$CHIAVE.pub" | awk '{print $2}')"
if ssh-add -l 2>/dev/null | grep -qF "$IMPRONTA_CHIAVE"; then
  echo "ATTENZIONE: la chiave e' caricata nell'agente ssh. La tolgo,"
  echo "altrimenti la password non verrebbe piu' chiesta e la firma"
  echo "tornerebbe a essere producibile da un agente."
  ssh-add -d "$CHIAVE" 2>/dev/null || true
fi

echo "--- configurazione di git (solo per questo progetto) ---"
git -C "$REPO" config gpg.format ssh
git -C "$REPO" config user.signingkey "$CHIAVE.pub"
# NON si attiva commit.gpgsign: firmerebbe OGNI commit, chiederebbe la password
# a ogni salvataggio e bloccherebbe gli agenti che lavorano senza una persona
# davanti. Le approvazioni si firmano una per una, con `git commit -S`.
git -C "$REPO" config --unset commit.gpgsign 2>/dev/null || true

FIRMATARI="$HOME/.ssh/allowed_signers"
EMAIL="$(git -C "$REPO" config user.email)"
PUB="$(cat "$CHIAVE.pub")"
touch "$FIRMATARI"
if ! grep -qF "$PUB" "$FIRMATARI" 2>/dev/null; then
  echo "$EMAIL $PUB" >> "$FIRMATARI"
fi
git -C "$REPO" config gpg.ssh.allowedSignersFile "$FIRMATARI"

echo
echo "--- verifica: firmo un commit di prova in un repository USA-E-GETTA ---"
echo "(ti chiedera' la password: e' il collaudo che funziona)"
echo "Il progetto vero non viene toccato in nessun modo."
echo
PROVA="$(mktemp -d)"
trap 'rm -rf "$PROVA"' EXIT
git -C "$PROVA" init -q
git -C "$PROVA" config user.name  "$(git -C "$REPO" config user.name)"
git -C "$PROVA" config user.email "$EMAIL"
git -C "$PROVA" config gpg.format ssh
git -C "$PROVA" config user.signingkey "$CHIAVE.pub"
git -C "$PROVA" config gpg.ssh.allowedSignersFile "$FIRMATARI"
git -C "$PROVA" commit --allow-empty -S -m "prova di firma" >/dev/null
STATO="$(git -C "$PROVA" log -1 --format='%G?')"
if [ "$STATO" = "G" ] || [ "$STATO" = "U" ]; then
  echo "  VERDE: la firma c'e' ed e' verificabile."
  ESITO=0
else
  echo "  ROSSO: il commit non risulta firmato. Stato git: '$STATO'"
  ESITO=1
fi

echo
if [ "$ESITO" -eq 0 ]; then
  echo "======================================================================"
  echo " FATTO. Da adesso l'anello 4 di REG-01 e' vero e non piu' dichiarato"
  echo " mancante. ck-provenienza.sh puo' verificarlo."
  echo "======================================================================"
else
  echo "Qualcosa non ha funzionato. Riporta a Claude l'output qui sopra."
fi
echo
exit "$ESITO"
