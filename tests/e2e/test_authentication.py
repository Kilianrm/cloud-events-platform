def test_invalid_credentials(get_jwt_token):
    # Credenciales incorrectas
    token = get_jwt_token("client1", "wrong-secret")
    assert token is None

def test_valid_credentials_client1(get_jwt_token):
    # Correct credentials for Client 1
    token = get_jwt_token("client1", "super-secret-pass1")
    assert token is not None

def test_valid_credentials_client2(get_jwt_token):
    # Correct credentials for Client 2
    token = get_jwt_token("client2", "super-secret-pass2")
    assert token is not None