class MinesValidationError(Exception):
    pass


class MinesInsufficientBalanceError(Exception):
    pass


class MinesIdempotencyConflictError(Exception):
    pass


class MinesGameStateConflictError(Exception):
    pass


class MinesSessionVoidedByOperatorError(MinesGameStateConflictError):
    pass
