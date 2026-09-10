import inspect

def test_auth_headers_is_pure(auth_headers):
    # Call the fixture
    headers_fn = auth_headers
    sig = inspect.signature(headers_fn)
    # The signature should only contain 'access_token'
    params = list(sig.parameters.keys())
    assert params == ["access_token"]
