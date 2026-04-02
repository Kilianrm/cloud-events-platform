
# ZIP
data "archive_file" "authentication_zip" {
  type        = "zip"
  output_path = "${path.module}/build/authentication.zip"

  source {
    content  = file("${var.app_path}/authentication/handler.py")
    filename = "authentication/handler.py"
  }

  source {
    content  = file("${var.app_path}/authentication/authenticate_client.py")
    filename = "authentication/authenticate_client.py"
  }

  source {
    content  = file("${var.app_path}/shared/secrets_service.py")
    filename = "shared/secrets_service.py"
  }

  source {
    content  = file("${var.app_path}/shared/jwt_utils.py")
    filename = "shared/jwt_utils.py"
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
resource "aws_lambda_function" "authentication" {
  function_name = "authentication-${var.environment}"
  role          = aws_iam_role.authentication.arn
  handler       = "authentication.handler.handler"
  runtime       = "python3.11"

  filename         = data.archive_file.authentication_zip.output_path
  source_code_hash = data.archive_file.authentication_zip.output_base64sha256

  timeout     = 5
  memory_size = 128

  environment {
    variables = {
      JWT_SECRET_NAME      = var.jwt_secret_name
      CLIENT_SECRET_PREFIX = var.client_secret_prefix
    }
  }

  tags = {
    Name        = "authentication"
    Component   = "authentication"
    Environment = var.environment
  }

  layers = [aws_lambda_layer_version.pyjwt_layer.arn]

  depends_on = [
    aws_iam_role_policy_attachment.authentication_logs_attach,
    aws_iam_role_policy_attachment.authentication_secrets_attach,
    aws_lambda_layer_version.pyjwt_layer,
  ]
}

# ROLES ( WHO AM I?)
resource "aws_iam_role" "authentication" {
  name = "authentication-${var.environment}-role"

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
    Name        = "authentication-role"
    Component   = "authentication"
    Environment = var.environment
  }
}

# POLICIES -> ( WHAT CAN I DO?)
data "aws_caller_identity" "current" {}
resource "aws_iam_policy" "authentication_secrets_policy" {
  name   = "authentication_secrets_policy-${var.environment}"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = [
          aws_secretsmanager_secret.jwt_secret.arn, # JWT SECRET
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.client_secret_prefix}*" #
        ]
      }
    ]
  })
}
resource "aws_iam_role_policy_attachment" "authentication_secrets_attach" {
  role       = aws_iam_role.authentication.name
  policy_arn = aws_iam_policy.authentication_secrets_policy.arn
}
resource "aws_iam_role_policy_attachment" "authentication_logs_attach" {
  role       = aws_iam_role.authentication.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# PERMISSIONS ( WHO CAN USE ME?)
resource "aws_lambda_permission" "authentication_apigw" {
  statement_id  = "AllowAPIGatewayInvokeAuthentication-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authentication.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/$default/POST/auth/token*"

  depends_on = [
    aws_apigatewayv2_integration.authentication,
    aws_apigatewayv2_route.authenticate_token
  ]

}

