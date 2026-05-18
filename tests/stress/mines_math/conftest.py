import pytest


@pytest.fixture(scope="session", autouse=True)
def mines_math_stress_context():
    yield
