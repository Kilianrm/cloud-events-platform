############################
# IAM ROLES FOR LAMBDAS
############################

resource "aws_iam_role" "ingestion_lambda_role" {
  name = "ingestion-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Component = "ingestion"
  }
}

resource "aws_iam_role" "read_lambda_role" {
  name = "read-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Component = "read"
  }
}

############################
# DYNAMODB POLICIES
############################

resource "aws_iam_policy" "ingestion_dynamodb_policy" {
  name        = "ingestion-dynamodb-policy"
  description = "Allow ingestion lambda to write events"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.events.arn
      }
    ]
  })
}

resource "aws_iam_policy" "read_dynamodb_policy" {
  name        = "read-dynamodb-policy"
  description = "Allow read lambda to read events"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.events.arn
      }
    ]
  })
}

############################
# BASIC LOGGING POLICY (AWS MANAGED)
############################

resource "aws_iam_role_policy_attachment" "ingestion_logs" {
  role       = aws_iam_role.ingestion_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "read_logs" {
  role       = aws_iam_role.read_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

############################
# ATTACH DYNAMODB POLICIES
############################

resource "aws_iam_role_policy_attachment" "ingestion_dynamodb" {
  role       = aws_iam_role.ingestion_lambda_role.name
  policy_arn = aws_iam_policy.ingestion_dynamodb_policy.arn
}

resource "aws_iam_role_policy_attachment" "read_dynamodb" {
  role       = aws_iam_role.read_lambda_role.name
  policy_arn = aws_iam_policy.read_dynamodb_policy.arn
}
