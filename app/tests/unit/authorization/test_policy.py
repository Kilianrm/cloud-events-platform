from authorization.policy_builder import build_policy


def test_build_policy_allow():
    # Test a basic Allow policy for a specific method
    principal_id = "user123"
    effect = "Allow"
    resource = "arn:aws:execute-api:us-east-1:123456789012:abcd1234/prod/GET/users"

    policy = build_policy(principal_id, effect, resource)

    assert policy["principalId"] == principal_id
    statement = policy["policyDocument"]["Statement"][0]
    assert statement["Action"] == "execute-api:Invoke"
    assert statement["Effect"] == "Allow"
    assert statement["Resource"] == resource


def test_build_policy_deny():
    # Test a basic Deny policy for a specific method
    principal_id = "anonymous"
    effect = "Deny"
    resource = "arn:aws:execute-api:us-east-1:123456789012:abcd1234/prod/POST/orders"

    policy = build_policy(principal_id, effect, resource)

    statement = policy["policyDocument"]["Statement"][0]
    assert statement["Effect"] == "Deny"
    assert statement["Resource"] == resource


def test_build_policy_principal_id():
    # Ensure principalId is set correctly
    principal_id = "testuser"
    policy = build_policy(principal_id, "Allow", "*")
    assert policy["principalId"] == principal_id


def test_policy_structure():
    # Verify the overall policy structure matches AWS expectations
    policy = build_policy("user", "Allow", "*")
    assert "policyDocument" in policy
    assert "Version" in policy["policyDocument"]
    assert policy["policyDocument"]["Version"] == "2012-10-17"
    assert "Statement" in policy["policyDocument"]
    assert isinstance(policy["policyDocument"]["Statement"], list)
    statement = policy["policyDocument"]["Statement"][0]
    assert set(statement.keys()) == {"Action", "Effect", "Resource"}


def test_policy_with_wildcard():
    # Test policy with wildcard resource (all methods and resources)
    resource = "arn:aws:execute-api:us-east-1:123456789012:abcd1234/prod/*/*"
    policy = build_policy("user", "Allow", resource)
    assert policy["policyDocument"]["Statement"][0]["Resource"] == resource