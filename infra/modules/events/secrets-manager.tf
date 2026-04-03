# JWT SECRET
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "auth/jwt_secret"
  description             = "JWT signing secret for authorization Lambda"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_secret_version" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = "super-secret-jwt-key"
}

#CLIENTS
# CLIENT 1
resource "aws_secretsmanager_secret" "client1_secret" {
  name                    = "auth/client/client1"
  description             = "Credentials for client1"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "client1_secret_version" {
  secret_id = aws_secretsmanager_secret.client1_secret.id
  secret_string = jsonencode({
    client_id     = "client1"
    client_secret = "super-secret-pass1"
    scope         = ["read", "write"]
  })
}

# CLIENT 2
resource "aws_secretsmanager_secret" "client2_secret" {
  name                    = "auth/client/client2"
  description             = "Credentials for client2"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "client2_secret_version" {
  secret_id = aws_secretsmanager_secret.client2_secret.id
  secret_string = jsonencode({
    client_id     = "client2"
    client_secret = "super-secret-pass2"
    scope         = ["read"]
  })
}