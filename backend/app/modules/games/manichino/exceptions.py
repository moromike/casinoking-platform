"""Errori di dominio del manichino.

PERCHE' errori propri e non quelli di Mines: le rotte traducono le eccezioni
in risposte HTTP per codice; riusare MinesValidationError farebbe apparire un
gioco dentro l'altro nei log e nei contratti d'errore.
"""


class ManichinoValidationError(Exception):
    pass


class ManichinoInsufficientBalanceError(Exception):
    pass


class ManichinoIdempotencyConflictError(Exception):
    pass


class ManichinoGameStateConflictError(Exception):
    pass


class ManichinoSessionVoidedByOperatorError(ManichinoGameStateConflictError):
    """La sessione e' stata chiusa d'ufficio da un operatore.

    PERCHE' UN ERRORE A PARTE, e perche' sottoclasse del conflitto di stato:
    quando un amministratore chiude d'ufficio una sessione, la piattaforma liquida il
    round. Il giocatore che prova a chiuderlo un istante dopo trova un round gia'
    chiuso, e senza questa distinzione si vedrebbe rispondere "stato non valido" —
    vero ma inutile, perche' non dice che e' stato un operatore. Mines fa esattamente
    questa distinzione (games/mines/state_machine.py:91): la cavia deve somigliargli
    anche negli errori, o i collaudi di piattaforma che verificano come una decisione
    dell'operatore ARRIVA AL GIOCATORE non possono passare da lei.
    """
