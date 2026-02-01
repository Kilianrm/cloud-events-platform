################################
# API GATEWAY (HTTP API)
################################

resource "aws_apigatewayv2_api" "events_api" {
  name          = "events-${var.environment}-api"
  protocol_type = "HTTP"

  tags = {
    Name        = "events-api"
    Component   = "api"
    Environment = var.environment
  }

}

################################
# INTEGRATIONS
################################

resource "aws_apigatewayv2_integration" "ingestion" {
  api_id           = aws_apigatewayv2_api.events_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.ingestion.invoke_arn
}

resource "aws_apigatewayv2_integration" "read" {
  api_id           = aws_apigatewayv2_api.events_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.read.invoke_arn
}

################################
# ROUTES
################################

resource "aws_apigatewayv2_route" "ingest_event" {
  api_id    = aws_apigatewayv2_api.events_api.id
  route_key = "POST /events"
  target    = "integrations/${aws_apigatewayv2_integration.ingestion.id}"
}

resource "aws_apigatewayv2_route" "read_event" {
  api_id    = aws_apigatewayv2_api.events_api.id
  route_key = "GET /events/{event_id}"
  target    = "integrations/${aws_apigatewayv2_integration.read.id}"
}

################################
# STAGE
################################

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.events_api.id
  name        = "$default"
  auto_deploy = true
}

################################
# LAMBDA PERMISSIONS
################################

resource "aws_lambda_permission" "allow_apigw_ingestion" {
  statement_id  = "AllowAPIGatewayInvokeIngestion"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_read" {
  statement_id  = "AllowAPIGatewayInvokeRead"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.read.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.events_api.execution_arn}/*/*"
}

