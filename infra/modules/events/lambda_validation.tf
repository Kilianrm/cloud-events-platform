data "archive_file" "validation_zip" {
  type        = "zip"
  output_path = "${path.module}/build/validation.zip"

  source {
    content  = file("${var.app_path}/validation/handler.py")
    filename = "validation/handler.py"
  }

  source {
    content  = file("${var.app_path}/shared/logging_utils.py")
    filename = "shared/logging_utils.py"
  }

  source {
    content  = file("${var.app_path}/validation/errors.py")
    filename = "validation/errors.py"
  }

  source {
    content  = file("${var.app_path}/validation/validators.py")
    filename = "validation/validators.py"
  }

  source {
    content  = file("${var.app_path}/shared/response.py")
    filename = "shared/response.py"
  }
  source {
    content  = file("${var.app_path}/shared/parse_utils.py")
    filename = "shared/parse_utils.py"
  }
}

# LAMBDA
resource "aws_lambda_function" "validation" {
  function_name = "validation-${var.environment}"
  role          = aws_iam_role.validation.arn
  handler       = "validation.handler.handler"
  runtime       = "python3.11"

  filename         = data.archive_file.validation_zip.output_path
  source_code_hash = data.archive_file.validation_zip.output_base64sha256

  timeout     = 5
  memory_size = 128

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.event_queue.url
    }
  }
}


# ROLES ( WHO AM I?)
resource "aws_iam_role" "validation" {
  name = "validation-${var.environment}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}
# POLICIES -> ( WHAT CAN I DO?)
resource "aws_iam_role_policy" "validation_sqs" {
  name = "validation-${var.environment}-sqs-policy"
  role = aws_iam_role.validation.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect = "Allow", Action = ["sqs:SendMessage"], Resource = aws_sqs_queue.event_queue.arn }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "validation_logs_attach" {
  role       = aws_iam_role.validation.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# PERMISSIONS ( WHO CAN USE ME?)
resource "aws_lambda_permission" "validation_apigw" {
  statement_id  = "AllowAPIGatewayInvokeValidation-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.validation.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/$default/*/*"

  depends_on = [
    aws_apigatewayv2_integration.ingestion_validation,
    aws_apigatewayv2_route.ingest_event
  ]

}