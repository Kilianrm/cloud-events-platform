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
resource "aws_cloudwatch_log_metric_filter" "ingestion_accepted_filter" {
  name           = "IngestionAcceptedFilter"
  log_group_name = aws_cloudwatch_log_group.ingestion_logs.name
  pattern        = "{ $.status = \"accepted\" }"

  metric_transformation {
    name      = "RequestsAccepted"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "ingestion_rejected_filter" {
  name           = "IngestionRejectedFilter"
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
resource "aws_cloudwatch_log_metric_filter" "read_accepted_filter" {
  name           = "ReadAcceptedFilter"
  log_group_name = aws_cloudwatch_log_group.read_logs.name
  pattern        = "{ $.status = \"accepted\" }"

  metric_transformation {
    name      = "RequestsAccepted"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "read_rejected_filter" {
  name           = "ReadRejectedFilter"
  log_group_name = aws_cloudwatch_log_group.read_logs.name
  pattern        = "{ $.status = \"rejected\" }"

  metric_transformation {
    name      = "RequestsRejected"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

## AUTHORIZATION 
resource "aws_cloudwatch_log_metric_filter" "authorization_allow_filter" {
  name           = "AuthorizationAllowFilter"
  log_group_name = aws_cloudwatch_log_group.authorization_logs.name
  pattern        = "{ $.status = \"authorized\" && $.effect = \"Allow\" }"

  metric_transformation {
    name      = "AuthorizationAllow"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "authorization_deny_filter" {
  name           = "AuthorizationDenyFilter"
  log_group_name = aws_cloudwatch_log_group.authorization_logs.name
  pattern        = "{ $.status = \"denied\" }"

  metric_transformation {
    name      = "AuthorizationDeny"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

## AUTHENTICATION
resource "aws_cloudwatch_log_metric_filter" "authentication_success_filter" {
  name           = "AuthenticationSuccessFilter"
  log_group_name = aws_cloudwatch_log_group.authentication_logs.name
  pattern        = "{ $.status = \"validated\" }"

  metric_transformation {
    name      = "AuthenticationSuccess"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "authentication_rejected_filter" {
  name           = "AuthenticationRejectedFilter"
  log_group_name = aws_cloudwatch_log_group.authentication_logs.name
  pattern        = "{ $.status = \"rejected\" }"

  metric_transformation {
    name      = "AuthenticationRejected"
    namespace = "MyApp/Lambda"
    value     = "1"
    unit      = "Count"
  }
}