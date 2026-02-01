#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

API_URL=$(terraform output -raw api_base_url)
EVENT_ID="evt-3"

echo "📤 Sending event..."
curl -s -X POST "$API_URL/events" \
  -H "Content-Type: application/json" \
  -d @"$SCRIPT_DIR/event.json" \
  | jq .

echo ""
echo "📥 Reading event..."
curl -s "$API_URL/events/$EVENT_ID" | jq .
