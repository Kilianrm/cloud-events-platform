#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_URL=$(terraform output -raw api_base_url)

generate_event() {
  local id="$1"
  local type="$2"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local payload='{"x": 1}'

  if [[ "$type" == "error" ]]; then
    payload='{"x": "INVALID"}'
  fi

  cat <<EOF
{
  "event_id": "evt-$id",
  "event_type": "TEST",
  "source": "manual-test",
  "timestamp": "$timestamp",
  "payload": $payload
}
EOF
}

send_event() {
  local id="$1"
  local type="$2"

  EVENT_JSON=$(generate_event "$id" "$type")

  echo "➡ Sending event evt-$id"
  echo "$EVENT_JSON" | curl -s -X POST "$API_URL/events" \
    -H "Content-Type: application/json" -d @- | jq .
}

read_event() {
  local id="$1"

  echo "➡ Reading event evt-$id"
  curl -s "$API_URL/events/evt-$id" | jq .
}

while true; do
  echo ""
  echo "===== MENU ====="
  echo "1) Send event"
  echo "2) Read event"
  echo "3) Exit"
  echo "================"

  read -p "Choose an option: " OPTION

  case $OPTION in
    1)
      read -p "Enter ID (e.g. 200): " ID
      send_event "$ID" "normal"
      ;;

    2)
      read -p "Enter existing ID: " ID
      read_event "$ID"
      ;;
    3)
      echo "👋 Exiting..."
      exit 0
      ;;

    *)
      echo "❌ Invalid option"
      ;;
  esac
done