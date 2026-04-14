# ZIP
data "archive_file" "ingestion_zip" {
  type        = "zip"
  output_path = "${path.module}/build/ingestion.zip"

  source {
    content  = file("${var.app_path}/ingestion/handler.py")
    filename = "ingestion/handler.py"
  }

  source {
    content  = file("${var.app_path}/ingestion/persistence.py")
    filename = "ingestion/persistence.py"
  }

  source {
    content  = file("${var.app_path}/ingestion/validation.py")
    filename = "ingestion/validation.py"
  }

  source {
    content  = file("${var.app_path}/ingestion/errors.py")
    filename = "ingestion/errors.py"
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
# LAMBDA
resource "aws_lambda_function" "ingestion" {
  function_name = "ingestion-${var.environment}"
  role          = aws_iam_role.ingestion.arn
  handler       = "ingestion.handler.handler"
  runtime       = "python3.11"

  filename         = data.archive_file.ingestion_zip.output_path
  source_code_hash = data.archive_file.ingestion_zip.output_base64sha256

  timeout     = 5
  memory_size = 128

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.events.name
    }
  }
  event_source_mapping { # EQUIVALENT TO PERMISSION?
    event_source_arn = aws_sqs_queue.event_queue.arn
    batch_size       = 10
    enabled          = true
  }


  tags = {
    Name        = "ingestion"
    Component   = "ingestion"
    Environment = var.environment
  }

  depends_on = [
    aws_iam_role_policy_attachment.ingestion_dynamodb_attach,
    aws_iam_role_policy_attachment.ingestion_logs_attach,
  ]
}
# ROLES ( WHO AM I?)
resource "aws_iam_role" "ingestion" {
  name = "ingestion-${var.environment}-role"

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
    Name        = "ingestion-role"
    Component   = "ingestion"
    Environment = var.environment
  }
}

# POLICIES -> ( WHAT CAN I DO?)
# Custom DynamoDB policy
resource "aws_iam_policy" "ingestion_dynamodb" {
  name        = "ingestion-${var.environment}-dynamodb-policy"
  description = "Allow ingestion Lambda to write events"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem"]
      Resource = aws_dynamodb_table.events.arn
    }]
  })
}

# Attach custom policy
resource "aws_iam_role_policy_attachment" "ingestion_dynamodb_attach" {
  role       = aws_iam_role.ingestion.name
  policy_arn = aws_iam_policy.ingestion_dynamodb.arn
}

# Attach basic logs (AWS managed policy)
resource "aws_iam_role_policy_attachment" "ingestion_logs_attach" {
  role       = aws_iam_role.ingestion.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
# PERMISSIONS ( WHO CAN USE ME?)
resource "aws_lambda_permission" "ingestion_apigw" {
  statement_id  = "AllowAPIGatewayInvokeIngestion-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/$default/*/*"

  depends_on = [
    aws_apigatewayv2_integration.ingestion,
    aws_apigatewayv2_route.ingest_event
  ]

}