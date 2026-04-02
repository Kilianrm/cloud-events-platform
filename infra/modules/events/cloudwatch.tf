####################
# CloudWatch Log Groups
####################
resource "aws_cloudwatch_log_group" "ingestion_logs" {
  name              = "/aws/lambda/ingestion-${var.environment}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "read_logs" {
  name              = "/aws/lambda/read-${var.environment}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/api-gateways/api-gateway-${var.environment}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "authentication_logs" {
  name              = "/aws/lambda/authentication-${var.environment}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "authorization_logs" {
  name              = "/aws/lambda/authorization-${var.environment}"
  retention_in_days = 7
}

####################
# Ingestion Metrics
####################
resource "aws_cloudwatch_log_metric_filter" "ingestion_accepted" {
  name           = "IngestionAccepted"
  log_group_name = aws_cloudwatch_log_group.ingestion_logs.name
  pattern        = "{ $.status = \"accepted\" }"

  metric_transformation {
    name      = "RequestsAccepted"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "ingestion_rejected" {
  name           = "IngestionRejected"
  log_group_name = aws_cloudwatch_log_group.ingestion_logs.name
  pattern        = "{ $.status = \"rejected\" }"

  metric_transformation {
    name      = "RequestsRejected"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

####################
# Read Metrics
####################
resource "aws_cloudwatch_log_metric_filter" "read_accepted" {
  name           = "ReadAccepted"
  log_group_name = aws_cloudwatch_log_group.read_logs.name
  pattern        = "{ $.status = \"accepted\" }"

  metric_transformation {
    name      = "RequestsAccepted"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "read_rejected" {
  name           = "ReadRejected"
  log_group_name = aws_cloudwatch_log_group.read_logs.name
  pattern        = "{ $.status = \"rejected\" }"

  metric_transformation {
    name      = "RequestsRejected"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}
