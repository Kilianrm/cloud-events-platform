data "archive_file" "ingestion_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/build/ingestion.zip"

  source {
    content  = file("${path.module}/../app/ingestion/handler.py")
    filename = "ingestion/handler.py"
  }

  source {
    content  = file("${path.module}/../app/ingestion/persistence.py")
    filename = "ingestion/persistence.py"
  }

  source {
    content  = file("${path.module}/../app/ingestion/validation.py")
    filename = "ingestion/validation.py"
  }

  source {
    content  = file("${path.module}/../app/ingestion/errors.py")
    filename = "ingestion/errors.py"
  }

  source {
    content  = file("${path.module}/../app/shared/response.py")
    filename = "shared/response.py"
  }

  source {
    content  = file("${path.module}/../app/shared/serialization.py")
    filename = "shared/serialization.py"
  }

  source {
    content  = file("${path.module}/../app/shared/time.py")
    filename = "shared/time.py"
  }

  
}
################################
# INGESTION LAMBDA
################################

resource "aws_lambda_function" "ingestion" {
  function_name = "ingestion-lambda"
  role          = aws_iam_role.ingestion_lambda_role.arn
  handler       = "ingestion.handler.handler"
  runtime       = "python3.13"

  filename         = data.archive_file.ingestion_lambda_zip.output_path
  source_code_hash = data.archive_file.ingestion_lambda_zip.output_base64sha256

  timeout = 5
  memory_size = 128

  environment {
    variables = {
      TABLE_NAME  = aws_dynamodb_table.events.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.ingestion_logs,
    aws_iam_role_policy_attachment.ingestion_dynamodb,
  ]
}
