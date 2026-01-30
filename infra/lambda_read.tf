data "archive_file" "read_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/build/read.zip"

  source {
    content  = file("${path.module}/../app/read/handler.py")
    filename = "read/handler.py"
  }

  source {
    content  = file("${path.module}/../app/read/persistence.py")
    filename = "read/persistence.py"
  }

  source {
    content  = file("${path.module}/../app/read/errors.py")
    filename = "read/errors.py"
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
# READ LAMBDA
################################

resource "aws_lambda_function" "read" {
  function_name = "read-lambda"
  role          = aws_iam_role.read_lambda_role.arn
  handler       = "read.handler.handler"
  runtime       = "python3.13"

  filename         = data.archive_file.read_lambda_zip.output_path
  source_code_hash = data.archive_file.read_lambda_zip.output_base64sha256

  timeout      = 5
  memory_size = 128

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.events.name
    }
  }


  depends_on = [
    aws_iam_role_policy_attachment.read_logs,
    aws_iam_role_policy_attachment.read_dynamodb,
  ]
}
