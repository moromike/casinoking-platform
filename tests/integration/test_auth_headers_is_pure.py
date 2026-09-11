import inspect

def test_auth_headers_is_pure(auth_headers):
    headers_fn = auth_headers
    sig = inspect.signature(headers_fn)
    params = list(sig.parameters.keys())
    assert params == ["access_token"]
    assert headers_fn("token-di-prova") == {"Authorization": "Bearer token-di-prova"}
