data "archive_file" "read_lambda_zip" {
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
}

################################
# READ LAMBDA
################################

resource "aws_lambda_function" "read" {
  function_name = "read-lambda-${var.environment}"
  role          = aws_iam_role.read_lambda_role.arn
  handler       = "read.handler.handler"
  runtime       = "python3.11"

  filename         = data.archive_file.read_lambda_zip.output_path
  source_code_hash = data.archive_file.read_lambda_zip.output_base64sha256

  timeout     = 5
  memory_size = 128

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.events.name
    }
  }

  tags = {
    Name        = "read-lambda"
    Component   = "read-lambda"
    Environment = var.environment
  }


  depends_on = [
    aws_iam_role_policy_attachment.read_logs,
    aws_iam_role_policy_attachment.read_dynamodb,
  ]
}
