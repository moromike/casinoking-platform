import pytest


@pytest.fixture(scope="session", autouse=True)
def wait_for_backend():
    yield


# NON C'E' PIU' NIENTE DA SPEGNERE QUI (10/09/2026, PASSO 4A).
# C'era uno stub vuoto che serviva solo a neutralizzare `preserve_mines_backoffice_config`,
# la fixture `autouse` del conftest di radice specifica di UN gioco: due sottoalberi
# avevano dovuto disattivarla a mano, ed era il sintomo. Ora non e' piu' `autouse`.
