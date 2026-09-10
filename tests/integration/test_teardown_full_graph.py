import pytest
import psycopg

pytest_plugins = ["tests.fixtures.mines"]

def test_teardown_full_graph_works(create_published_mines_variant, mines_auth_headers, client, _mines_cleanup_registrar):
    # Just creating it triggers the cleanup logic on teardown
    create_published_mines_variant()
    # If the cleanup fails, pytest will report an error during the test teardown phase.
    assert True
