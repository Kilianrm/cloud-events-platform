resource "aws_sqs_queue" "event_dlq" {
  name                       = "event-dlq-${var.environment}"
  visibility_timeout_seconds = 60
}

resource "aws_sqs_queue" "event_queue" {
  name                       = "event-queue-${var.environment}"
  visibility_timeout_seconds = 60

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.event_dlq.arn
    maxReceiveCount     = 3
  })
}

# WHO CAN CONSUME THE QUEUE
resource "aws_lambda_event_source_mapping" "ingestion" {
  event_source_arn = aws_sqs_queue.event_queue.arn
  function_name    = aws_lambda_function.ingestion.arn

  batch_size       = 10

  function_response_types = ["ReportBatchItemFailures"]
}
