"""
Live traffic scenarios.

Every scenario sends real requests to the deployed API (or real messages to
SQS) and reports the path each request took as "hops" between diagram nodes.
Synchronous hops are derived from the actual HTTP response; asynchronous hops
(SQS -> ingestion -> DynamoDB, retries, DLQ) are only emitted once AWS confirms
them, by polling DynamoDB, SQS or CloudWatch Logs.
"""
import json
import time
import uuid
from datetime import datetime, timedelta, timezone

import boto3
import jwt
import requests

# Demo clients provisioned in infra/modules/events/secrets-manager.tf
CLIENTS = {
    "client1": "super-secret-pass1",  # scope: read, write
    "client2": "super-secret-pass2",  # scope: read
}

SCENARIOS = {
    "happy_path": {
        "title": "Happy path",
        "description": "Get a JWT, write an event, follow it through SQS into DynamoDB, then read it back.",
    },
    "bad_credentials": {
        "title": "Wrong client secret",
        "description": "Authentication Lambda checks Secrets Manager and refuses to issue a JWT.",
    },
    "missing_token": {
        "title": "No JWT",
        "description": "API Gateway rejects the call before any Lambda runs.",
    },
    "forged_token": {
        "title": "Forged JWT",
        "description": "A token signed with the wrong key is denied by the Lambda authorizer.",
    },
    "read_only_client": {
        "title": "Read-only client writes",
        "description": "client2 only has the 'read' scope, so the authorizer denies POST /events.",
    },
    "invalid_event": {
        "title": "Invalid event",
        "description": "Validation Lambda rejects an event with a timestamp in the future.",
    },
    "duplicate_event": {
        "title": "Duplicate event (idempotency)",
        "description": "The same event_id is sent twice; DynamoDB's conditional write keeps a single copy.",
    },
    "dlq": {
        "title": "Poison message → DLQ",
        "description": "A message that always fails is retried 3 times by SQS and then moved to the DLQ (~1 min).",
    },
}


class Trace:
    """Collects what a scenario does and forwards it to the UI."""

    def __init__(self, emit, scenario: str):
        self.emit = emit
        self.scenario = scenario
        self.run_id = uuid.uuid4().hex[:8]

    def _send(self, type_, **data):
        self.emit(type_, run_id=self.run_id, scenario=self.scenario, **data)

    def hop(self, src, dst, label="", kind="request", ok=True):
        """kind: request | response | async"""
        self._send("hop", src=src, dst=dst, label=label, kind=kind, ok=ok)

    def note(self, text, level="info"):
        self._send("note", text=text, level=level)

    def http(self, **data):
        self._send("http", **data)


class Context:
    def __init__(self, outputs: dict, emit, scenario: str):
        self.api = outputs["API_BASE_URL"].rstrip("/")
        self.table_name = outputs["TABLE_NAME"]
        self.region = outputs.get("AWS_REGION", "us-east-1")
        self.queue_url = outputs["QUEUE_URL"]
        self.dlq_url = outputs["DLQ_URL"]
        self.env = self.table_name.rsplit("-", 1)[-1]  # events-dev -> dev
        self.trace = Trace(emit, scenario)

    # ---------------------------------------------------------------- helpers

    def aws(self, service):
        return boto3.client(service, region_name=self.region)

    def call(self, method, path, token=None, body=None):
        correlation_id = str(uuid.uuid4())
        headers = {"X-Correlation-Id": correlation_id}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        start = time.perf_counter()
        resp = requests.request(method, f"{self.api}{path}", json=body, headers=headers, timeout=20)
        latency_ms = round((time.perf_counter() - start) * 1000)
        self.last_latency_ms = latency_ms

        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        self.trace.http(
            method=method,
            path=path,
            status=resp.status_code,
            latency_ms=latency_ms,
            correlation_id=correlation_id,
            authorization=_redact_token(token),
            request=_redact(body),
            response=_redact(data),
        )
        return resp, data


def _redact_token(token):
    if not token:
        return None
    return f"Bearer {token[:12]}…{token[-6:]}"


def _redact(data):
    if isinstance(data, dict):
        out = dict(data)
        for key in ("access_token", "client_secret"):
            if isinstance(out.get(key), str):
                out[key] = out[key][:12] + "…"
        return out
    return data


def _new_event(**overrides):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "ORDER_PLACED",
        "source": "demo-ui",
        "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(),
        "payload": {"order_id": uuid.uuid4().hex[:8], "amount_cents": 4250},
    }
    event.update(overrides)
    return event


# ---------------------------------------------------------------- building blocks


def get_token(ctx: Context, client_id: str, secret: str):
    t = ctx.trace
    resp, data = ctx.call("POST", "/auth/token", body={"client_id": client_id, "client_secret": secret})

    t.hop("client", "apigw", "POST /auth/token")
    t.hop("apigw", "authn", "invoke")
    t.hop("authn", "secrets", f"GetSecretValue auth/client/{client_id}")
    t.hop("secrets", "authn", "client record", kind="response")

    if resp.status_code == 200:
        t.hop("authn", "apigw", "JWT signed", kind="response")
        t.hop("apigw", "client", "200 · JWT issued", kind="response")
        return data["access_token"]

    t.hop("authn", "apigw", f"{resp.status_code} invalid_client", kind="response", ok=False)
    t.hop("apigw", "client", f"{resp.status_code} Unauthorized", kind="response", ok=False)
    return None


def _through_authorizer(ctx: Context, resp, token) -> bool:
    """Hops for the JWT-protected part of a route. Returns False if the request was stopped."""
    t = ctx.trace

    if not token:
        t.hop("apigw", "client", f"{resp.status_code} · no Authorization header", kind="response", ok=False)
        return False

    t.hop("apigw", "authz", "verify JWT")
    t.hop("authz", "secrets", "GetSecretValue auth/jwt_secret")
    t.hop("secrets", "authz", "signing key", kind="response")

    if resp.status_code == 403:
        t.hop("authz", "apigw", "policy: Deny", kind="response", ok=False)
        t.hop("apigw", "client", "403 Forbidden", kind="response", ok=False)
        return False

    t.hop("authz", "apigw", "policy: Allow", kind="response")
    return True


def post_event(ctx: Context, token, event):
    t = ctx.trace
    resp, data = ctx.call("POST", "/events", token=token, body=event)

    t.hop("client", "apigw", "POST /events")
    if not _through_authorizer(ctx, resp, token):
        return resp

    t.hop("apigw", "validation", "invoke")
    if resp.status_code == 202:
        t.hop("validation", "sqs", "SendMessage")
        t.hop("validation", "apigw", "202 accepted", kind="response")
        t.hop("apigw", "client", "202 Accepted", kind="response")
    else:
        error = data.get("error", "") if isinstance(data, dict) else ""
        t.hop("validation", "apigw", f"{resp.status_code} {error}".strip(), kind="response", ok=False)
        t.hop("apigw", "client", f"{resp.status_code} {error}".strip(), kind="response", ok=False)
    return resp


def get_event(ctx: Context, token, event_id):
    t = ctx.trace
    resp, _ = ctx.call("GET", f"/events/{event_id}", token=token)

    t.hop("client", "apigw", f"GET /events/{event_id[:8]}…")
    if not _through_authorizer(ctx, resp, token):
        return resp

    t.hop("apigw", "read", "invoke")
    t.hop("read", "dynamodb", "GetItem (strongly consistent)")
    ok = resp.status_code == 200
    if resp.status_code in (200, 404):
        t.hop("dynamodb", "read", "item" if ok else "not found", kind="response")
    else:
        # 5xx: the Lambda failed or timed out, so we don't know what DynamoDB answered.
        t.note(f"Read Lambda failed with {resp.status_code} after {ctx.last_latency_ms} ms "
               "(check /aws/lambda/read logs — a timeout shows 'Status: timeout').", "error")
    t.hop("read", "apigw", str(resp.status_code), kind="response", ok=ok)
    t.hop("apigw", "client", f"{resp.status_code} {'event returned' if ok else ''}".strip(), kind="response", ok=ok)
    return resp


def wait_until_persisted(ctx: Context, event_id, timeout=25):
    """
    Polls DynamoDB until the ingestion Lambda has written the event.
    Also watches the ingestion logs, so a failing write shows up as a
    failure on the diagram instead of a silent timeout.
    """
    t = ctx.trace
    table = boto3.resource("dynamodb", region_name=ctx.region).Table(ctx.table_name)
    t.note("Waiting for SQS → Ingestion Lambda → DynamoDB (polling DynamoDB)…")

    since_ms = int(time.time() * 1000) - 5000
    start = time.perf_counter()
    next_log_check = start + 3
    while time.perf_counter() - start < timeout:
        if "Item" in table.get_item(Key={"event_id": event_id}, ConsistentRead=True):
            elapsed = round((time.perf_counter() - start) * 1000)
            t.hop("sqs", "ingestion", "batch via event source mapping", kind="async")
            t.hop("ingestion", "dynamodb", "PutItem (conditional)", kind="async")
            t.note(f"Event {event_id[:8]}… confirmed in DynamoDB {elapsed} ms after the 202.", "success")
            return True

        if time.perf_counter() >= next_log_check:
            next_log_check = time.perf_counter() + 3
            errors = find_log_events(ctx, "ingestion", "Unexpected ingestion error", event_id, since_ms=since_ms)
            if errors:
                t.hop("sqs", "ingestion", "batch via event source mapping", kind="async")
                t.hop("ingestion", "cloudwatch", "log: Unexpected ingestion error", kind="async", ok=False)
                t.hop("ingestion", "sqs", "batchItemFailures → retry", kind="response", ok=False)
                t.note(f"Ingestion failed: {_log_error(errors[0])}", "error")
                t.note("SQS will retry the message and move it to the DLQ after 3 failed deliveries.", "warning")
                return False
        time.sleep(0.5)

    t.note(f"Event not found in DynamoDB after {timeout}s.", "error")
    return False


def _log_error(message: str) -> str:
    try:
        return json.loads(message).get("error", message)
    except ValueError:
        return message.strip()


def find_log_events(ctx: Context, function, *terms, since_ms):
    """Returns the messages in a Lambda's log group that contain all the given terms."""
    logs = ctx.aws("logs")
    pattern = " ".join(f'"{term}"' for term in terms)
    messages, kwargs = [], {}
    try:
        while True:
            page = logs.filter_log_events(
                logGroupName=f"/aws/lambda/{function}-{ctx.env}",
                startTime=since_ms,
                filterPattern=pattern,
                **kwargs,
            )
            messages += [e["message"] for e in page.get("events", [])]
            if not page.get("nextToken"):
                return messages
            kwargs["nextToken"] = page["nextToken"]
    except logs.exceptions.ResourceNotFoundException:
        return []


def count_log_matches(ctx: Context, function, *terms, since_ms):
    return len(find_log_events(ctx, function, *terms, since_ms=since_ms))


# ---------------------------------------------------------------- scenarios


def happy_path(ctx: Context):
    token = get_token(ctx, "client1", CLIENTS["client1"])
    if not token:
        return False
    event = _new_event()
    if post_event(ctx, token, event).status_code != 202:
        return False
    if not wait_until_persisted(ctx, event["event_id"]):
        return False
    return get_event(ctx, token, event["event_id"]).status_code == 200


def bad_credentials(ctx: Context):
    return get_token(ctx, "client1", "not-the-password") is None


def missing_token(ctx: Context):
    return post_event(ctx, None, _new_event()).status_code == 401


def forged_token(ctx: Context):
    forged = jwt.encode(
        {"sub": "client1", "scope": ["read", "write"], "exp": int(time.time()) + 600},
        "attacker-key",
        algorithm="HS256",
    )
    ctx.trace.note("Token signed locally with 'attacker-key' instead of the key in Secrets Manager.")
    return post_event(ctx, forged, _new_event()).status_code == 403


def read_only_client(ctx: Context):
    token = get_token(ctx, "client2", CLIENTS["client2"])
    return token is not None and post_event(ctx, token, _new_event()).status_code == 403


def invalid_event(ctx: Context):
    token = get_token(ctx, "client1", CLIENTS["client1"])
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    return post_event(ctx, token, _new_event(timestamp=future)).status_code == 400


def duplicate_event(ctx: Context):
    t = ctx.trace
    token = get_token(ctx, "client1", CLIENTS["client1"])
    event = _new_event()
    since_ms = int(time.time() * 1000) - 5000

    post_event(ctx, token, event)
    if not wait_until_persisted(ctx, event["event_id"]):
        return False

    t.note("Sending the exact same event_id again…")
    post_event(ctx, token, event)

    t.note("Waiting for the ingestion Lambda's 'Duplicate event' log line (CloudWatch Logs)…")
    deadline = time.time() + 45
    while time.time() < deadline:
        if count_log_matches(ctx, "ingestion", "Duplicate event", event["event_id"], since_ms=since_ms):
            t.hop("sqs", "ingestion", "batch via event source mapping", kind="async")
            t.hop("ingestion", "dynamodb", "conditional PutItem", kind="async")
            t.hop("dynamodb", "ingestion", "ConditionalCheckFailed", kind="response", ok=False)
            t.hop("ingestion", "cloudwatch", "log: Duplicate event", kind="async")
            t.note("Duplicate detected and acknowledged — not retried, still one item in DynamoDB.", "success")
            return True
        time.sleep(3)

    t.note("Duplicate log line not seen within 45s (CloudWatch can lag).", "warning")
    return False


def dlq(ctx: Context):
    t = ctx.trace
    sqs = ctx.aws("sqs")
    event_id = f"dlq-demo-{uuid.uuid4()}"
    since_ms = int(time.time() * 1000) - 5000

    # Same test hook used by tests/post_deploy/resilience/test_dlq_flow.py
    sqs.send_message(
        QueueUrl=ctx.queue_url,
        MessageBody=json.dumps(
            {"event": {"event_id": event_id, "type": "poison"}, "metadata": {"test": {"force_fail": True}}}
        ),
    )
    t.hop("client", "sqs", "SendMessage (force_fail test hook)")
    t.note("Message injected straight into SQS with a flag that makes the ingestion Lambda fail.")

    attempts, deadline = 0, time.time() + 180
    while time.time() < deadline:
        seen = count_log_matches(ctx, "ingestion", "Unexpected ingestion error", event_id, since_ms=since_ms)
        while attempts < seen:
            attempts += 1
            t.hop("sqs", "ingestion", f"delivery #{attempts}", kind="async")
            t.hop("ingestion", "cloudwatch", "log: Unexpected ingestion error", kind="async", ok=False)
            t.hop("ingestion", "sqs", "batchItemFailures → retry", kind="response", ok=False)
            if attempts < 3:
                t.note(f"Attempt {attempts} failed. Message is invisible for 20s (visibility timeout), then redelivered.", "warning")

        resp = sqs.receive_message(QueueUrl=ctx.dlq_url, MaxNumberOfMessages=10, VisibilityTimeout=2, WaitTimeSeconds=2)
        for msg in resp.get("Messages", []):
            if event_id in msg["Body"]:
                t.hop("sqs", "dlq", "maxReceiveCount=3 exceeded", kind="async", ok=False)
                t.note(f"Message moved to the DLQ after {max(attempts, 3)} failed deliveries. Nothing was lost.", "success")
                return True
        time.sleep(1)

    t.note("Message did not reach the DLQ within 3 minutes.", "error")
    return False


RUNNERS = {
    "happy_path": happy_path,
    "bad_credentials": bad_credentials,
    "missing_token": missing_token,
    "forged_token": forged_token,
    "read_only_client": read_only_client,
    "invalid_event": invalid_event,
    "duplicate_event": duplicate_event,
    "dlq": dlq,
}


def run(name: str, outputs: dict, emit) -> bool:
    ctx = Context(outputs, emit, name)
    ctx.trace._send("scenario_start", title=SCENARIOS[name]["title"])
    try:
        ok = RUNNERS[name](ctx)
    except Exception as exc:  # surface any AWS/HTTP error in the UI instead of failing silently
        ctx.trace.note(f"{type(exc).__name__}: {exc}", "error")
        ok = False
    ctx.trace._send("scenario_end", ok=bool(ok))
    return bool(ok)
