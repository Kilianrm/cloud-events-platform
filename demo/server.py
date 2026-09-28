"""
Local demo server for the Cloud Events Platform.

Runs the real deployment (Terraform), the real test suites (pytest) and real
traffic against the deployed API, and streams everything that happens to the
browser over Server-Sent Events so the UI can animate it.
"""
import asyncio
import json
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import boto3
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import resources
import scenarios
from pytest_live import MARKER

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
TF_DIR = ROOT / "infra" / "envs" / "dev"
ENV_FILE = ROOT / ".env"
RECORDINGS = DEMO / "recordings"
TF = ["terraform", f"-chdir={TF_DIR}"]

# Terraform output name -> .env key (same file run.sh writes)
ENV_KEYS = {
    "api_base_url": "API_BASE_URL",
    "table_name": "TABLE_NAME",
    "aws_region": "AWS_REGION",
    "queue_url": "QUEUE_URL",
    "dlq_url": "DLQ_URL",
}

TEST_SUITES = {
    "pre_deploy": {"path": "tests/pre_deploy", "needs_deploy": False},
    "post_deploy": {"path": "tests/post_deploy", "needs_deploy": True},
}

PIPELINE = ["pre_tests", "deploy", "post_tests"]


# =============================================================================
# EVENT HUB: shared state + fan-out to every connected browser
# =============================================================================
class Hub:
    def __init__(self):
        self.loop: asyncio.AbstractEventLoop | None = None
        self.clients: set[asyncio.Queue] = set()
        self.recording = None
        self.scenario_recordings = {}
        self.state = {
            "deployed": None,  # None while the initial Terraform state read is running
            "outputs": {},
            "resources": {},  # addr -> {node, status, action, name}
            "job": None,
            "phases": {p: "idle" for p in PIPELINE},
            "tests": {},  # nodeid -> {group, name, status, duration, detail}
            "metrics": None,
            "identity": None,
        }

    def emit(self, type_, **data):
        """Thread-safe: scenarios run in worker threads."""
        evt = {"type": type_, "ts": time.time(), **data}
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is self.loop:
            self._dispatch(evt)
        else:
            self.loop.call_soon_threadsafe(self._dispatch, evt)

    def _dispatch(self, evt):
        if not evt.get("replay"):
            self._reduce(evt)
            self._record(evt)
        for queue in list(self.clients):
            queue.put_nowait(evt)

    def _record(self, evt):
        if evt["type"] == "metrics":
            return
        # Traffic scenarios get a recording of their own, so they can be replayed separately.
        run_id = evt.get("run_id")
        if run_id:
            if evt["type"] == "scenario_start":
                self.scenario_recordings[run_id] = self._open_recording(f"traffic-{evt['scenario']}")
            file = self.scenario_recordings.get(run_id)
            if file:
                file.write(json.dumps(evt) + "\n")
                if evt["type"] == "scenario_end":
                    self.scenario_recordings.pop(run_id).close()
        elif self.recording:
            self.recording.write(json.dumps(evt) + "\n")

    def _reduce(self, evt):
        s, t = self.state, evt["type"]
        if t == "resource":
            s["resources"][evt["addr"]] = {k: evt[k] for k in ("node", "status", "action", "name")}
        elif t == "resources_reset":
            s["resources"] = evt["resources"]
        elif t == "deployment":
            s["deployed"], s["outputs"] = evt["deployed"], evt["outputs"]
        elif t == "job":
            s["job"] = evt["job"]
        elif t == "phase":
            s["phases"][evt["phase"]] = evt["status"]
        elif t == "tests_reset":
            s["tests"] = {}
        elif t == "test":
            s["tests"].setdefault(evt["nodeid"], {}).update(
                {k: v for k, v in evt.items() if k not in ("type", "ts")}
            )
        elif t in ("metrics", "identity"):
            s[t] = evt["data"]

    @staticmethod
    def _open_recording(name):
        RECORDINGS.mkdir(exist_ok=True)
        path = RECORDINGS / f"{datetime.now():%Y%m%d-%H%M%S}-{name.replace(':', '-')}.jsonl"
        return path.open("w", encoding="utf-8")

    def start_recording(self, name):
        self.recording = self._open_recording(name)

    def stop_recording(self):
        if self.recording:
            self.recording.close()
            self.recording = None


hub = Hub()


# =============================================================================
# PROCESS HELPERS
# =============================================================================
class Runner:
    """Only one long-running job (deploy / destroy / tests / pipeline) at a time."""

    def __init__(self):
        self.task: asyncio.Task | None = None
        self.proc: asyncio.subprocess.Process | None = None
        self.cancelled = False

    def busy(self):
        return self.task is not None and not self.task.done()


runner = Runner()


async def run_process(cmd, on_line, env=None, source="shell"):
    hub.emit("log", source=source, level="command", text="$ " + " ".join(str(c) for c in cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=ROOT,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        start_new_session=True,  # so cancel can signal the whole process group
    )
    runner.proc = proc
    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="replace").rstrip()
        if line:
            on_line(line)
    code = await proc.wait()
    runner.proc = None
    return code


def read_env_file() -> dict:
    if not ENV_FILE.exists():
        return {}
    values = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def write_env_file(outputs: dict):
    lines = [f"{env_key}={outputs[tf_key]}" for tf_key, env_key in ENV_KEYS.items() if tf_key in outputs]
    ENV_FILE.write_text("\n".join(lines) + "\n")


def outputs_to_env(outputs: dict) -> dict:
    return {ENV_KEYS[k]: v for k, v in outputs.items() if k in ENV_KEYS}


# =============================================================================
# TERRAFORM
# =============================================================================
async def sync_terraform_state():
    """Reads what is currently deployed so the diagram starts in the right state."""
    addrs, outputs = [], {}

    def collect(line):
        addrs.append(line.strip())

    code = await run_process(TF + ["state", "list"], collect, source="terraform")
    if code != 0:
        hub.emit("log", source="terraform", level="error", text="Could not read Terraform state (did you run init?).")
        hub.emit("deployment", deployed=False, outputs={})
        return

    current = {}
    for addr in addrs:
        node = resources.node_for(addr)
        if node:
            current[addr] = {"node": node, "status": "ready", "action": None, "name": resources.short_name(addr)}
    hub.emit("resources_reset", resources=current)

    raw = []
    await run_process(TF + ["output", "-json"], raw.append, source="terraform")
    try:
        outputs = {k: v["value"] for k, v in json.loads("\n".join(raw)).items()}
    except (ValueError, AttributeError):
        outputs = {}

    deployed = bool(current) and "api_base_url" in outputs
    if deployed:
        write_env_file(outputs)
    hub.emit("deployment", deployed=deployed, outputs=outputs_to_env(outputs))
    hub.emit("log", source="terraform", level="info", text=f"{len(current)} resources currently deployed.")


def handle_tf_json(line, outputs: dict):
    try:
        msg = json.loads(line)
    except ValueError:
        hub.emit("log", source="terraform", level="info", text=line)
        return

    kind = msg.get("type")
    level = msg.get("@level", "info")
    text = msg.get("@message", "")

    if kind == "planned_change":
        change = msg["change"]
        addr = change["resource"]["addr"]
        node = resources.node_for(addr)
        if node:
            hub.emit("resource", addr=addr, node=node, status="planned", action=change["action"],
                     name=resources.short_name(addr))

    elif kind in ("apply_start", "apply_progress", "apply_complete", "apply_errored"):
        hook = msg["hook"]
        addr = hook["resource"]["addr"]
        action = hook.get("action")
        node = resources.node_for(addr)
        status = {
            "apply_start": "in_progress",
            "apply_progress": "in_progress",
            "apply_complete": "deleted" if action == "delete" else "ready",
            "apply_errored": "error",
        }[kind]
        if node:
            hub.emit("resource", addr=addr, node=node, status=status, action=action,
                     name=resources.short_name(addr), elapsed=hook.get("elapsed_seconds"))
        if kind == "apply_errored":
            level = "error"

    elif kind == "change_summary":
        hub.emit("tf_summary", changes=msg["changes"])

    elif kind == "outputs":
        outputs.update({k: v.get("value") for k, v in msg["outputs"].items()})

    elif kind == "diagnostic":
        diag = msg.get("diagnostic", {})
        level = diag.get("severity", level)
        detail = diag.get("detail")
        text = f"{diag.get('summary', text)}" + (f"\n{detail}" if detail else "")

    if text:
        hub.emit("log", source="terraform", level=level, text=text, tf_type=kind)


async def terraform(action: str) -> bool:
    """action: 'apply' or 'destroy'"""
    phase = "deploy" if action == "apply" else "destroy"
    hub.emit("tf_start", action=action)

    code = await run_process(
        TF + ["init", "-input=false", "-no-color"],
        lambda l: hub.emit("log", source="terraform", level="info", text=l),
        source="terraform",
    )
    if code != 0:
        return False

    outputs: dict = {}
    code = await run_process(
        TF + [action, "-auto-approve", "-input=false", "-json"],
        lambda l: handle_tf_json(l, outputs),
        source="terraform",
    )
    if code != 0:
        hub.emit("log", source="terraform", level="error", text=f"terraform {action} failed (exit {code}).")
        return False

    if action == "apply":
        write_env_file(outputs)
        hub.emit("deployment", deployed=True, outputs=outputs_to_env(outputs))
    else:
        ENV_FILE.unlink(missing_ok=True)
        hub.emit("resources_reset", resources={})
        hub.emit("deployment", deployed=False, outputs={})
        hub.emit("metrics", data=None)
    hub.emit("log", source="terraform", level="success", text=f"✔ {phase} finished.")
    return True


# =============================================================================
# TESTS
# =============================================================================
async def run_tests(suite: str) -> bool:
    cfg = TEST_SUITES[suite]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "app"), str(DEMO)])
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    if cfg["needs_deploy"]:
        env.update(read_env_file())

    hub.emit("tests_reset", suite=suite)

    def on_line(line):
        # pytest -v does not end its line before the plugin writes, so the marker can appear mid-line.
        text, marker, payload = line.partition(MARKER)
        if text.strip():
            hub.emit("log", source="pytest", level="info", text=text.rstrip())
        if marker:
            evt = json.loads(payload)
            kind = evt.pop("kind")
            if kind == "collected":
                for test in evt["tests"]:
                    hub.emit("test", suite=suite, status="queued", **test)
            elif kind == "start":
                hub.emit("test", nodeid=evt["nodeid"], status="running")
            elif kind == "result":
                hub.emit("test", status=evt.pop("outcome"), **evt)
            elif kind == "finished":
                hub.emit("tests_finished", suite=suite, exitstatus=evt["exitstatus"])

    code = await run_process(
        [sys.executable, "-m", "pytest", cfg["path"], "-p", "pytest_live", "-v", "--color=no",
         "-p", "no:cacheprovider", "--disable-warnings"],
        on_line,
        env=env,
        source="pytest",
    )
    return code == 0


# =============================================================================
# JOBS
# =============================================================================
async def phase(name, coro):
    hub.emit("phase", phase=name, status="running")
    ok = await coro
    if runner.cancelled:
        ok = False
    hub.emit("phase", phase=name, status="passed" if ok else "failed")
    return ok


async def job_deploy():
    return await phase("deploy", terraform("apply"))


async def job_destroy():
    ok = await terraform("destroy")
    if ok:
        for p in PIPELINE:
            hub.emit("phase", phase=p, status="idle")
    return ok


async def job_tests(suite):
    name = "pre_tests" if suite == "pre_deploy" else "post_tests"
    return await phase(name, run_tests(suite))


async def job_pipeline():
    for p in PIPELINE:
        hub.emit("phase", phase=p, status="idle")
    steps = [
        ("pre_tests", lambda: run_tests("pre_deploy")),
        ("deploy", lambda: terraform("apply")),
        ("post_tests", lambda: run_tests("post_deploy")),
    ]
    for name, step in steps:
        if not await phase(name, step()):
            hub.emit("log", source="pipeline", level="error", text=f"Pipeline stopped: {name} failed.")
            return False
    return True


def start_job(name, coro_factory):
    if runner.busy():
        current = (hub.state["job"] or {}).get("name", "the initial state sync")
        raise HTTPException(409, f"Wait: {current} is still running")

    async def wrapper():
        runner.cancelled = False
        hub.start_recording(name)
        hub.emit("job", job={"name": name, "started": time.time()})
        ok = False
        try:
            ok = await coro_factory()
        except Exception as exc:
            hub.emit("log", source="server", level="error", text=f"{type(exc).__name__}: {exc}")
        finally:
            status = "cancelled" if runner.cancelled else ("passed" if ok else "failed")
            hub.emit("job_end", name=name, status=status)
            hub.emit("job", job=None)
            hub.stop_recording()

    runner.task = asyncio.create_task(wrapper())
    return {"started": name}


# =============================================================================
# BACKGROUND: live metrics + identity
# =============================================================================
async def metrics_loop():
    while True:
        await asyncio.sleep(4)
        outputs = hub.state["outputs"]
        if not hub.clients or not hub.state["deployed"] or not outputs:
            continue
        try:
            data = await asyncio.to_thread(read_metrics, outputs)
            hub.emit("metrics", data=data)
        except Exception:
            pass  # resources may be mid-deploy/destroy; next tick will try again


def read_metrics(outputs):
    region = outputs.get("AWS_REGION", "us-east-1")
    sqs = boto3.client("sqs", region_name=region)
    names = ["ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"]
    queue = sqs.get_queue_attributes(QueueUrl=outputs["QUEUE_URL"], AttributeNames=names)["Attributes"]
    dlq = sqs.get_queue_attributes(QueueUrl=outputs["DLQ_URL"], AttributeNames=names)["Attributes"]

    table = boto3.client("dynamodb", region_name=region)
    count, kwargs = 0, {}
    while True:
        page = table.scan(TableName=outputs["TABLE_NAME"], Select="COUNT", **kwargs)
        count += page["Count"]
        if "LastEvaluatedKey" not in page:
            break
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]

    return {
        "queue_visible": int(queue["ApproximateNumberOfMessages"]),
        "queue_inflight": int(queue["ApproximateNumberOfMessagesNotVisible"]),
        "dlq": int(dlq["ApproximateNumberOfMessages"]) + int(dlq["ApproximateNumberOfMessagesNotVisible"]),
        "events_stored": count,
    }


def read_identity():
    arn = boto3.client("sts").get_caller_identity()["Arn"]
    account = arn.split(":")[4]
    return {"user": arn.split("/")[-1], "account": f"••••{account[-4:]}"}


async def startup_sync():
    try:
        hub.emit("identity", data=await asyncio.to_thread(read_identity))
    except Exception as exc:
        hub.emit("log", source="aws", level="error", text=f"AWS credentials not usable: {exc}")
    await sync_terraform_state()


# =============================================================================
# HTTP API
# =============================================================================
@asynccontextmanager
async def lifespan(_app):
    hub.loop = asyncio.get_running_loop()
    runner.task = asyncio.create_task(startup_sync())
    metrics = asyncio.create_task(metrics_loop())
    yield
    metrics.cancel()


app = FastAPI(title="Cloud Events Platform — demo", lifespan=lifespan)


@app.get("/")
async def index():
    return FileResponse(DEMO / "static" / "index.html")


@app.get("/api/state")
async def state():
    return hub.state


@app.get("/api/stream")
async def stream():
    queue: asyncio.Queue = asyncio.Queue()
    hub.clients.add(queue)

    async def gen():
        try:
            meta = {"scenarios": scenarios.SCENARIOS}
            yield f"data: {json.dumps({'type': 'snapshot', 'state': hub.state, **meta})}\n\n"
            while True:
                try:
                    evt = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(evt)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            hub.clients.discard(queue)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/deploy")
async def deploy():
    return start_job("deploy", job_deploy)


@app.post("/api/destroy")
async def destroy():
    return start_job("destroy", job_destroy)


@app.post("/api/tests/{suite}")
async def tests(suite: str):
    if suite not in TEST_SUITES:
        raise HTTPException(404, "unknown suite")
    if TEST_SUITES[suite]["needs_deploy"] and not hub.state["deployed"]:
        raise HTTPException(400, "Deploy the platform before running post-deploy tests")
    return start_job(f"tests:{suite}", lambda: job_tests(suite))


@app.post("/api/pipeline")
async def pipeline():
    return start_job("pipeline", job_pipeline)


@app.post("/api/refresh")
async def refresh():
    return start_job("refresh", lambda: sync_terraform_state())


@app.post("/api/cancel")
async def cancel():
    if not runner.busy():
        raise HTTPException(400, "nothing is running")
    runner.cancelled = True
    if runner.proc and runner.proc.returncode is None:
        # SIGINT lets Terraform stop gracefully and release the state.
        os.killpg(runner.proc.pid, signal.SIGINT)
    hub.emit("log", source="server", level="warning", text="Cancellation requested…")
    return {"cancelling": True}


@app.post("/api/scenario/{name}")
async def scenario(name: str):
    if name not in scenarios.RUNNERS:
        raise HTTPException(404, "unknown scenario")
    if not hub.state["deployed"]:
        raise HTTPException(400, "Deploy the platform first")
    job = hub.state["job"]
    if job and job["name"] in ("deploy", "destroy", "pipeline"):
        raise HTTPException(409, "Wait for the infrastructure job to finish")

    outputs = dict(hub.state["outputs"])
    asyncio.create_task(asyncio.to_thread(scenarios.run, name, outputs, hub.emit))
    return {"started": name}


@app.get("/api/recordings")
async def recordings():
    if not RECORDINGS.exists():
        return []
    files = sorted(RECORDINGS.glob("*.jsonl"), reverse=True)
    return [{"name": f.name, "size": f.stat().st_size} for f in files[:30]]


@app.post("/api/replay/{name}")
async def replay(name: str, speed: float = 4.0):
    path = RECORDINGS / Path(name).name
    if not path.exists():
        raise HTTPException(404, "recording not found")
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    async def play():
        hub.emit("replay", status="start", name=name)
        previous = events[0]["ts"] if events else 0
        for evt in events:
            # Keep the original rhythm but never wait more than 1.5s between events.
            await asyncio.sleep(min((evt["ts"] - previous) / speed, 1.5))
            previous = evt["ts"]
            hub.emit(evt.pop("type"), **{**evt, "replay": True})
        hub.emit("replay", status="end", name=name)

    asyncio.create_task(play())
    return {"replaying": name}


app.mount("/static", StaticFiles(directory=DEMO / "static"), name="static")
