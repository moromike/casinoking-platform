import pytest


@pytest.fixture(scope="session", autouse=True)
def wait_for_backend():
    yield


@pytest.fixture(autouse=True)
def preserve_mines_backoffice_config():
    yield
