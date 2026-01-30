output "api_base_url" {
  description = "Base URL of the Events API"
  value       = aws_apigatewayv2_api.events_api.api_endpoint
}

output "ingestion_lambda_name" {
  value = aws_lambda_function.ingestion.function_name
}

output "read_lambda_name" {
  value = aws_lambda_function.read.function_name
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.events.name
}
