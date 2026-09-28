# Live demo UI

A local web UI that runs the whole lifecycle of the platform — tests, deployment,
live traffic and teardown — and visualizes it on the architecture diagram.

Nothing is simulated: buttons run the real `terraform` and `pytest` commands and send
real requests to the deployed API. Asynchronous steps (SQS → Lambda → DynamoDB,
retries, DLQ) are only drawn once AWS confirms them (DynamoDB / SQS / CloudWatch Logs).

## Run

From Linux or WSL, at the repository root (same prerequisites as `run.sh`: Terraform,
Python 3.11, AWS credentials, the remote-state S3 bucket):

```bash
./demo/start.sh
```

Then open <http://localhost:8000>. The first start creates `demo/.venv` and installs
the dependencies.

## What you can do

| Area | What it shows |
|------|---------------|
| **Pipeline bar** | Pre-deploy tests → Deploy → Post-deploy tests → Live traffic, or everything with *Run full pipeline* |
| **Diagram** | Every Terraform resource mapped to its component; nodes go *planned → creating → deployed* live during `apply` and back during `destroy` |
| **Deployment tab** | Per-resource progress from `terraform apply -json`, plan summary, outputs |
| **Tests tab** | Each test streamed as it runs, grouped by phase; click a failure for its traceback |
| **Traffic tab** | Scenarios (happy path, bad credentials, forged JWT, read-only client, invalid event, duplicate, poison message → DLQ) animated hop by hop, with the real requests/responses and correlation IDs |
| **Replays tab** | Every job and scenario is recorded to `demo/recordings/` and can be replayed without AWS — a fallback if the network fails |

## Files

- `server.py` — FastAPI server: jobs, Terraform/pytest runners, event stream (SSE)
- `scenarios.py` — live traffic scenarios and how each maps to diagram hops
- `resources.py` — Terraform address → diagram component mapping
- `pytest_live.py` — pytest plugin that streams test progress
- `static/` — the UI (plain HTML/CSS/JS, no build step, works offline)
