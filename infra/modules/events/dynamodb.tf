resource "aws_dynamodb_table" "events" {
  name         = "events-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "event_id"

  attribute {
    name = "event_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "events-${var.environment}"
    Component   = "persistence"
    Environment = var.environment
  }
}
