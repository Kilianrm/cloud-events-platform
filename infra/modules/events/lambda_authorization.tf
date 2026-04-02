
# ZIP
data "archive_file" "authorization_zip" {
  type        = "zip"
  output_path = "${path.module}/build/authorization.zip"

  source {
    content  = file("${var.app_path}/authorization/handler.py")
    filename = "authorization/handler.py"
  }

  source {
    content  = file("${var.app_path}/authorization/permissions.py")
    filename = "authorization/permissions.py"
  }

  source {
    content  = file("${var.app_path}/authorization/policy_builder.py")
    filename = "authorization/policy_builder.py"
  }

  source {
    content  = file("${var.app_path}/shared/jwt_utils.py")
    filename = "shared/jwt_utils.py"
  }

  source {
    content  = file("${var.app_path}/shared/secrets_service.py")
    filename = "shared/secrets_service.py"
  }

  source {
    content  = file("${var.app_path}/shared/logging_utils.py")
    filename = "shared/logging_utils.py"
  }

  source {
    content  = file("${var.app_path}/shared/parse_utils.py")
    filename = "shared/parse_utils.py"
  }
}


# LAMBDA
resource "aws_lambda_function" "authorization" {
  function_name = "authorization-${var.environment}"
  role          = aws_iam_role.authorization.arn
  handler       = "authorization.handler.handler"
  runtime       = "python3.11"

  filename         = data.archive_file.authorization_zip.output_path
  source_code_hash = data.archive_file.authorization_zip.output_base64sha256

  timeout     = 5
  memory_size = 128

  environment {
    variables = {
      JWT_SECRET_NAME = var.jwt_secret_name
    }
  }

  layers = [aws_lambda_layer_version.pyjwt_layer.arn]

  tags = {
    Name        = "authorization"
    Component   = "authorization"
    Environment = var.environment
  }

  depends_on = [
    aws_iam_role_policy_attachment.authorization_logs_attach,
    aws_iam_role_policy_attachment.authorization_secrets_attach,
    aws_lambda_layer_version.pyjwt_layer,
  ]
}

# ROLES ( WHO AM I?)
resource "aws_iam_role" "authorization" {
  name = "authorization-${var.environment}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "authorization-role"
    Component   = "authorization"
    Environment = var.environment
  }
}

# POLICIES -> ( WHAT CAN I DO?)
resource "aws_iam_policy" "authorization_secrets_policy" {
  name = "authorization-secrets-${var.environment}"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["secretsmanager:GetSecretValue"],
        Resource = [
          aws_secretsmanager_secret.jwt_secret.arn,
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "authorization_secrets_attach" {
  role       = aws_iam_role.authorization.name
  policy_arn = aws_iam_policy.authorization_secrets_policy.arn
}
resource "aws_iam_role_policy_attachment" "authorization_logs_attach" {
  role       = aws_iam_role.authorization.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# PERMISSIONS ( WHO CAN USE ME?)
resource "aws_lambda_permission" "authorization_apigw" {
  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorization.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/$default/*/*"

  depends_on = [
    aws_apigatewayv2_authorizer.authorization
  ]
}