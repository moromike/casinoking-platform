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
