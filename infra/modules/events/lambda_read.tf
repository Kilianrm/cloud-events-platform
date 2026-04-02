data "archive_file" "read_zip" {
  type        = "zip"
  output_path = "${path.module}/build/read.zip"

  source {
    content  = file("${var.app_path}/read/handler.py")
    filename = "read/handler.py"
  }

  source {
    content  = file("${var.app_path}/read/persistence.py")
    filename = "read/persistence.py"
  }

  source {
    content  = file("${var.app_path}/read/errors.py")
    filename = "read/errors.py"
  }

  source {
    content  = file("${var.app_path}/shared/response.py")
    filename = "shared/response.py"
  }

  source {
    content  = file("${var.app_path}/shared/serialization.py")
    filename = "shared/serialization.py"
  }

  source {
    content  = file("${var.app_path}/shared/time.py")
    filename = "shared/time.py"
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
################################
# READ LAMBDA
################################
resource "aws_lambda_function" "read" {
  function_name = "read-${var.environment}"
  role          = aws_iam_role.read.arn
  handler       = "read.handler.handler"
  runtime       = "python3.11"

  filename         = data.archive_file.read_zip.output_path
  source_code_hash = data.archive_file.read_zip.output_base64sha256

  timeout     = 5
  memory_size = 128

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.events.name
    }
  }

  tags = {
    Name        = "read"
    Component   = "read"
    Environment = var.environment
  }

  depends_on = [
    aws_iam_role_policy_attachment.read_dynamodb_attach,
    aws_iam_role_policy_attachment.read_logs_attach,
  ]
}
# ROLES ( WHO AM I?)
resource "aws_iam_role" "read" {
  name = "read-${var.environment}-role"

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
    Name        = "read-role"
    Component   = "read"
    Environment = var.environment
  }
}
# POLICIES -> ( WHAT CAN I DO?)
# Custom DynamoDB policy (solo permite GetItem en tabla events)
resource "aws_iam_policy" "read_dynamodb" {
  name        = "read-${var.environment}-dynamodb-policy"
  description = "Allow read Lambda to read events"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem"]
      Resource = aws_dynamodb_table.events.arn
    }]
  })
}

# Attach custom policy
resource "aws_iam_role_policy_attachment" "read_dynamodb_attach" {
  role       = aws_iam_role.read.name
  policy_arn = aws_iam_policy.read_dynamodb.arn
}

# Attach basic logs (AWS managed policy)
resource "aws_iam_role_policy_attachment" "read_logs_attach" {
  role       = aws_iam_role.read.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
# PERMISSIONS ( WHO CAN USE ME?)
resource "aws_lambda_permission" "read_apigw" {
  statement_id  = "AllowAPIGatewayInvokeRead-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.read.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/$default/*/*"

  depends_on = [
    aws_apigatewayv2_integration.read,
    aws_apigatewayv2_route.read_event
  ]

}