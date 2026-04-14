################################
# API GATEWAY (HTTP API)
################################

resource "aws_apigatewayv2_api" "events_api" {
  name          = "events-${var.environment}-api"
  protocol_type = "HTTP"

  # NOTE: CORS is not enabled now because there's no browser frontend.
  # If you need frontend access later, add a cors_configuration block.

  tags = {
    Name        = "events-api"
    Component   = "api"
    Environment = var.environment
  }
}
# INTEGRATIONS ( BACKEND)

# Integration for POST /auth/token (Authentication Lambda)
resource "aws_apigatewayv2_integration" "authentication" {
  api_id           = aws_apigatewayv2_api.events_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.authentication.invoke_arn
}

# Integration for POST /events (Write/ Validation + Ingestion Lambda)
resource "aws_apigatewayv2_integration" "ingestion_validation" {
  api_id           = aws_apigatewayv2_api.events_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.validation.invoke_arn

}

# Integration for GET /events/{event_id} (Read Lambda)
resource "aws_apigatewayv2_integration" "read" {
  api_id           = aws_apigatewayv2_api.events_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.read.invoke_arn
}


# Integration for: LAMBDA AUTHORIZER -> Diferent resource used. ################### LAMBDA AUTHORIZER
resource "aws_apigatewayv2_authorizer" "authorization" {
  api_id                            = aws_apigatewayv2_api.events_api.id
  authorizer_type                   = "REQUEST"                                # Lambda Authorizer
  name                              = "events-authorization-lambda-authorizer" # visible in AWS console
  identity_sources                  = ["$request.header.Authorization"]        # takes JWT from Authorization header
  authorizer_uri                    = aws_lambda_function.authorization.invoke_arn
  authorizer_payload_format_version = "1.0"

  # <-- Caching del authorizer -->
  authorizer_result_ttl_in_seconds = 0 # 5 seconds cache


}

################################
# ROUTES
################################

# 1️⃣ POST /auth/token (unprotected)
resource "aws_apigatewayv2_route" "authenticate_token" {
  api_id             = aws_apigatewayv2_api.events_api.id
  route_key          = "POST /auth/token"
  target             = "integrations/${aws_apigatewayv2_integration.authentication.id}"
  authorization_type = "NONE"
}

# 2️⃣ POST /events (JWT-protected)
resource "aws_apigatewayv2_route" "ingest_event" {
  api_id             = aws_apigatewayv2_api.events_api.id
  route_key          = "POST /events"
  target             = "integrations/${aws_apigatewayv2_integration.ingestion_validation.id}"
  authorization_type = "CUSTOM" # protected
  authorizer_id      = aws_apigatewayv2_authorizer.authorization.id

  depends_on = [
    aws_apigatewayv2_integration.ingestion_validation,
    aws_apigatewayv2_authorizer.authorization
  ]

}

# 3️⃣ GET /events/{event_id} (JWT-protected)
resource "aws_apigatewayv2_route" "read_event" {
  api_id             = aws_apigatewayv2_api.events_api.id
  route_key          = "GET /events/{event_id}"
  target             = "integrations/${aws_apigatewayv2_integration.read.id}"
  authorization_type = "CUSTOM" # protected
  authorizer_id      = aws_apigatewayv2_authorizer.authorization.id

  depends_on = [
    aws_apigatewayv2_integration.read,
    aws_apigatewayv2_authorizer.authorization
  ]
}

## STAGE:
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.events_api.id
  name        = "$default"
  auto_deploy = true

  depends_on = [
    aws_apigatewayv2_route.authenticate_token,
    aws_apigatewayv2_route.ingest_event,
    aws_apigatewayv2_route.read_event
  ]

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn

    format = jsonencode({
      requestId         = "$context.requestId"
      extendedRequestId = "$context.extendedRequestId"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      routeKey          = "$context.routeKey"
      path              = "$context.path"
      protocol          = "$context.protocol"
      status            = "$context.status"
      responseLength    = "$context.responseLength"
      responseLatency   = "$context.responseLatency"

      integrationStatus  = "$context.integrationStatus"
      integrationLatency = "$context.integrationLatency"
      integrationError   = "$context.integrationErrorMessage"

      errorMessage      = "$context.error.message"
      errorResponseType = "$context.error.responseType"

      authorizerError = "$context.authorizer.error"

      ip        = "$context.identity.sourceIp"
      userAgent = "$context.identity.userAgent"
    })
  }

  default_route_settings {
    throttling_burst_limit   = 100
    throttling_rate_limit    = 50
    logging_level            = "INFO"
    data_trace_enabled       = true
    detailed_metrics_enabled = true
  }
}