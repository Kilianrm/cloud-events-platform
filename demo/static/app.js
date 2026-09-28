"use strict";

/* =============================================================================
   Architecture model — mirrors docs/architecture/aws-service-mapping.md
   ============================================================================= */
const W = 176, H = 66;

const NODES = {
  client:     { x: 90,  y: 350, title: "Client",          sub: "demo harness",       svc: "client", external: true },
  apigw:      { x: 280, y: 350, title: "API Gateway",     sub: "HTTP API",           svc: "api" },
  authn:      { x: 500, y: 110, title: "Authentication",  sub: "Lambda · JWT issuer", svc: "lambda" },
  authz:      { x: 500, y: 220, title: "Authorizer",      sub: "Lambda authorizer",  svc: "lambda" },
  layer:      { x: 740, y: 60,  title: "PyJWT layer",     sub: "Lambda layer",       svc: "lambda" },
  secrets:    { x: 740, y: 165, title: "Secrets Manager", sub: "credentials · key",  svc: "secret" },
  cloudwatch: { x: 975, y: 140, title: "CloudWatch",      sub: "logs · metrics",     svc: "watch" },
  validation: { x: 500, y: 350, title: "Validation",      sub: "Lambda · contract",  svc: "lambda" },
  sqs:        { x: 740, y: 350, title: "Event queue",     sub: "SQS · 3 retries",    svc: "queue" },
  ingestion:  { x: 975, y: 350, title: "Ingestion",       sub: "Lambda · consumer",  svc: "lambda" },
  dlq:        { x: 740, y: 455, title: "DLQ",             sub: "dead-letter queue",  svc: "queue" },
  read:       { x: 500, y: 575, title: "Read",            sub: "Lambda · GET",       svc: "lambda" },
  dynamodb:   { x: 975, y: 575, title: "DynamoDB",        sub: "events table",       svc: "db" },
};

const DESCRIPTIONS = {
  client: "The demo harness on this laptop. It calls the real API over HTTPS, exactly like an internal client would.",
  apigw: "Single HTTP API. /auth/token is public; /events routes are protected by the Lambda authorizer. Throttling: 50 req/s, burst 100.",
  authn: "POST /auth/token. Looks the client up in Secrets Manager, checks the secret and signs a JWT carrying its scopes.",
  authz: "REQUEST authorizer on every /events route. Verifies the JWT signature and returns an Allow/Deny policy by scope (read → GET, write → POST).",
  layer: "Shared PyJWT dependency, built locally by Terraform (null_resource + build_layer.sh) and published as a Lambda layer.",
  secrets: "Client credentials (auth/client/*) and the JWT signing key (auth/jwt_secret).",
  cloudwatch: "Structured JSON logs for every Lambda and the API Gateway, plus metric filters for accepted / rejected / security events.",
  validation: "Checks the event contract (UUID id, type, source, timestamp within 30 days, payload ≤ 256 KB), enqueues it and answers 202 immediately.",
  sqs: "Decouples the API from persistence. Delivers batches of 10 to the ingestion Lambda; a failed message is redelivered up to 3 times.",
  ingestion: "Consumes SQS batches and writes with a conditional put, so duplicates are ignored (idempotency). Reports partial batch failures.",
  dlq: "Messages that fail 3 deliveries land here instead of being lost.",
  read: "GET /events/{id}: strongly consistent read from DynamoDB.",
  dynamodb: "Immutable event store keyed by event_id.",
};

const EDGES = [
  ["client", "apigw"],
  ["apigw", "authn"], ["apigw", "authz"], ["apigw", "validation"], ["apigw", "read"],
  ["authn", "secrets"], ["authz", "secrets"],
  ["validation", "sqs"], ["sqs", "ingestion"], ["sqs", "dlq"],
  ["ingestion", "dynamodb"], ["read", "dynamodb"],
  ["ingestion", "cloudwatch", "dotted"],
];

const ZONES = [
  { x: 402, y: 26,  w: 442, h: 236, label: "Identity & access" },
  { x: 872, y: 26,  w: 206, h: 236, label: "Observability" },
  { x: 402, y: 290, w: 676, h: 218, label: "Write path · asynchronous" },
  { x: 402, y: 532, w: 676, h: 90,  label: "Read path & storage" },
];

const SVC_COLOR = {
  lambda: "--svc-lambda", api: "--svc-api", queue: "--svc-queue", db: "--svc-db",
  secret: "--svc-secret", watch: "--svc-watch", client: "--svc-client",
};

const ICONS = {
  lambda: `<path d="M4 2.5h2.2L12 14h-2.3L7.6 9.6 4.9 14H2.6l3.9-6.3L5.3 5.2" />`,
  api: `<path d="M2 5.5h11M10 2.5l3 3-3 3M14 10.5H3M6 7.5l-3 3 3 3" />`,
  queue: `<rect x="1.5" y="4" width="13" height="8" rx="1.5"/><path d="M5.5 4v8M9.5 4v8"/>`,
  db: `<ellipse cx="8" cy="4" rx="5.5" ry="2"/><path d="M2.5 4v8c0 1.1 2.5 2 5.5 2s5.5-.9 5.5-2V4M2.5 8c0 1.1 2.5 2 5.5 2s5.5-.9 5.5-2"/>`,
  secret: `<circle cx="5.5" cy="8" r="3"/><path d="M8.5 8h6M12.5 8v3M14.5 8v2"/>`,
  watch: `<path d="M1.5 12.5l4-4.5 3 2.5 5.5-6.5"/><path d="M1.5 14.5h13"/>`,
  client: `<rect x="2.5" y="3" width="11" height="7.5" rx="1"/><path d="M1 13h14"/>`,
};

const TEST_GROUP_ORDER = [
  "pre_deploy/unit", "pre_deploy/integration", "pre_deploy/system", "pre_deploy/resilience",
  "post_deploy/smoke", "post_deploy/e2e", "post_deploy/resilience",
];

const JOB_LABELS = {
  deploy: "Deploying with Terraform",
  destroy: "Destroying infrastructure",
  "tests:pre_deploy": "Running pre-deploy tests (local, mocked AWS)",
  "tests:post_deploy": "Running post-deploy tests against AWS",
  pipeline: "Running full pipeline",
  refresh: "Reading Terraform state",
};

const PHASE_LABELS = { pre_tests: "pre-deploy tests", deploy: "terraform apply", post_tests: "post-deploy tests" };

/* =============================================================================
   Client state
   ============================================================================= */
const S = {
  deployed: null,
  outputs: {},
  resources: {},
  job: null,
  phases: {},
  tests: {},
  metrics: null,
  identity: null,
  scenarios: {},
  scenarioStatus: {},  // name -> running | passed | failed
  runs: [],            // inspector entries, newest first
  logs: [],
  logFilter: "all",
  tf: { started: null, changes: null, changed: new Set(), operation: null },
  selected: null,
  replaying: null,
  openTest: null,
  lastLatency: null,
};

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const SVG_NS = "http://www.w3.org/2000/svg";

/* =============================================================================
   Diagram
   ============================================================================= */
const svg = $("#diagram");
const edgeEls = {};
const nodeEls = {};
let packetLayer;

function edgePath(a, b) {
  const A = NODES[a], B = NODES[b];
  if (Math.abs(A.x - B.x) < 5) {
    const dir = B.y > A.y ? 1 : -1;
    return `M${A.x} ${A.y + dir * H / 2} L${B.x} ${B.y - dir * H / 2}`;
  }
  const dir = B.x > A.x ? 1 : -1;
  const x1 = A.x + dir * W / 2, x2 = B.x - dir * W / 2, mx = (x1 + x2) / 2;
  return `M${x1} ${A.y} C${mx} ${A.y} ${mx} ${B.y} ${x2} ${B.y}`;
}

function freePath(a, b) {
  // For hops with no drawn edge (e.g. the test harness writing straight into SQS).
  const A = NODES[a], B = NODES[b];
  const x1 = A.x, y1 = A.y + H / 2, x2 = B.x - W / 4, y2 = B.y + H / 2;
  return `M${x1} ${y1} Q${(x1 + x2) / 2} ${Math.max(y1, y2) + 150} ${x2} ${y2}`;
}

function buildDiagram() {
  let html = "";
  for (const z of ZONES) {
    html += `<g class="zone"><rect x="${z.x}" y="${z.y}" width="${z.w}" height="${z.h}" rx="14"/>
      <text x="${z.x + 4}" y="${z.y - 8}">${esc(z.label)}</text></g>`;
  }
  html += `<g id="edges">`;
  for (const [a, b, style] of EDGES) {
    html += `<path id="edge-${a}-${b}" class="edge ${style || ""}" d="${edgePath(a, b)}"/>`;
  }
  html += `</g><g id="nodes">`;
  for (const [id, n] of Object.entries(NODES)) {
    const color = `var(${SVC_COLOR[n.svc]})`;
    html += `<g class="node" id="node-${id}" data-id="${id}" data-state="absent" transform="translate(${n.x - W / 2} ${n.y - H / 2})">
      <rect class="ring" width="${W}" height="${H}" rx="12"/>
      <rect class="box" width="${W}" height="${H}" rx="12"/>
      <rect class="icon-bg" x="11" y="16" width="34" height="34" rx="9" fill="${color}" fill-opacity=".16"/>
      <g class="icon" transform="translate(16 21) scale(1.5)" fill="none" stroke="${color}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">${ICONS[n.svc]}</g>
      <text class="title" x="54" y="25">${esc(n.title)}</text>
      <text class="sub" x="54" y="41">${esc(n.sub)}</text>
      <text class="status" x="54" y="56"></text>
    </g>`;
  }
  html += `</g><g id="packets"></g>`;
  svg.innerHTML = html;

  for (const [a, b] of EDGES) edgeEls[`${a}-${b}`] = $(`#edge-${a}-${b}`);
  for (const id of Object.keys(NODES)) {
    const el = $(`#node-${id}`);
    nodeEls[id] = el;
    el.addEventListener("mouseenter", () => showNodeCaption(id));
    el.addEventListener("mouseleave", restoreCaption);
    el.addEventListener("click", () => selectNode(id));
  }
  packetLayer = $("#packets");
}

function nodeResources(id) {
  return Object.entries(S.resources).filter(([, r]) => r.node === id);
}

function nodeState(id) {
  if (NODES[id].external) return { state: "external", label: "you" };
  const rs = nodeResources(id).map(([, r]) => r);
  if (!rs.length) return { state: "absent", label: S.deployed === null ? "…" : "not deployed" };

  const count = (st) => rs.filter((r) => r.status === st).length;
  const total = rs.length;
  const deleting = rs.some((r) => r.action === "delete" && r.status !== "ready");
  const busy = count("in_progress") > 0 || (S.job && count("planned") > 0 && count("planned") < total);

  if (count("error")) return { state: "error", label: `${count("error")} failed` };
  if (count("deleted") === total) return { state: "absent", label: "destroyed" };
  if (busy) {
    if (deleting) return { state: "deleting", label: `deleting ${count("deleted")}/${total}` };
    const updating = rs.some((r) => r.status === "in_progress" && r.action === "update");
    return { state: updating ? "updating" : "creating", label: `${updating ? "updating" : "creating"} ${count("ready")}/${total}` };
  }
  if (count("planned")) {
    const action = rs.find((r) => r.status === "planned").action;
    return { state: "planned", label: `plan: ${action} ×${count("planned")}` };
  }
  return { state: "ready", label: `${count("ready")} resource${count("ready") === 1 ? "" : "s"}` };
}

const prevNodeState = {};
function renderNodes() {
  for (const id of Object.keys(NODES)) {
    const { state, label } = nodeState(id);
    const el = nodeEls[id];
    const before = prevNodeState[id];
    if (before && before !== state && state === "ready" && ["creating", "updating", "planned"].includes(before)) {
      el.classList.remove("just-ready"); void el.getBBox(); el.classList.add("just-ready");
    }
    prevNodeState[id] = state;
    el.dataset.state = state;
    el.querySelector(".status").textContent = label;
    el.classList.toggle("selected", S.selected === id);
  }
  // Edges fade out when either end is not deployed.
  for (const [a, b] of EDGES) {
    const dim = [a, b].some((id) => ["absent"].includes(nodeEls[id].dataset.state));
    edgeEls[`${a}-${b}`].classList.toggle("dim", dim);
  }
}

/* ---------------------------------------------------------------- packets */
const lanes = new Map();

function enqueueHop(evt) {
  const key = evt.run_id || "default";
  if (!lanes.has(key)) lanes.set(key, { queue: [], busy: false });
  const lane = lanes.get(key);
  lane.queue.push(evt);
  if (!lane.busy) pump(lane, key);
}

async function pump(lane, key) {
  lane.busy = true;
  while (lane.queue.length) {
    const hop = lane.queue.shift();
    const hurry = lane.queue.length > 8 ? 0.45 : 1;
    await animateHop(hop, hurry);
  }
  lane.busy = false;
  lanes.delete(key);
}

function hopColor(hop) {
  if (!hop.ok) return cssVar("--err");
  if (hop.kind === "async") return cssVar("--async");
  if (hop.kind === "response") return cssVar("--ok");
  return cssVar("--info");
}

function animateHop(hop, hurry = 1) {
  return new Promise((resolve) => {
    if (!NODES[hop.src] || !NODES[hop.dst]) return resolve();

    let path = edgeEls[`${hop.src}-${hop.dst}`];
    let reverse = false, temp = null;
    if (!path) {
      path = edgeEls[`${hop.dst}-${hop.src}`];
      reverse = !!path;
    }
    if (!path) {
      temp = document.createElementNS(SVG_NS, "path");
      temp.setAttribute("d", freePath(hop.src, hop.dst));
      temp.setAttribute("class", "edge dotted");
      $("#edges").appendChild(temp);
      path = temp;
    }

    const kindClass = `hot-${hop.ok ? hop.kind : "error"}`;
    path.classList.add("hot", kindClass);

    const color = hopColor(hop);
    const g = document.createElementNS(SVG_NS, "g");
    g.setAttribute("class", "packet");
    g.innerHTML = `<circle r="13" fill="${color}" opacity=".22"/><circle class="core" r="6" fill="${color}"/>
      <text y="-16" text-anchor="middle">${esc(hop.label || "")}</text>`;
    packetLayer.appendChild(g);

    setCaption(hop);

    const length = path.getTotalLength();
    const duration = (hop.kind === "async" ? 1100 : 620) * hurry;
    const start = performance.now();
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const e = ease(t);
      const p = path.getPointAtLength((reverse ? 1 - e : e) * length);
      g.setAttribute("transform", `translate(${p.x} ${p.y})`);
      if (t < 1) return requestAnimationFrame(frame);

      g.remove();
      flashNode(hop.dst, hop.ok);
      setTimeout(() => {
        path.classList.remove("hot", kindClass);
        if (temp) temp.remove();
      }, 350);
      resolve();
    }
    requestAnimationFrame(frame);
  });
}

function flashNode(id, ok) {
  const el = nodeEls[id];
  const cls = ok ? "flash" : "flash-error";
  el.classList.remove("flash", "flash-error");
  void el.getBBox();
  el.classList.add(cls);
}

/* ---------------------------------------------------------------- caption */
let lastCaption = null;

function setCaption(hop) {
  const color = hopColor(hop);
  const kind = hop.ok ? hop.kind : "rejected";
  lastCaption = `<span class="tag" style="color:${color};background:${color}22">${esc(kind)}</span>
    <b>${esc(NODES[hop.src].title)}</b><span class="arrow">→</span><b>${esc(NODES[hop.dst].title)}</b>
    <span class="muted">${esc(hop.label || "")}</span>`;
  $("#caption").innerHTML = lastCaption;
}

function showNodeCaption(id) {
  const n = NODES[id];
  const { label } = nodeState(id);
  $("#caption").innerHTML = `<b>${esc(n.title)}</b><span class="muted">${esc(label)}</span>
    <span>${esc(DESCRIPTIONS[id] || "")}</span>`;
}

function restoreCaption() {
  $("#caption").innerHTML = lastCaption || `<span class="muted">Hover a component for details · click to see its resources</span>`;
}

function selectNode(id) {
  S.selected = S.selected === id ? null : id;
  showTab("deploy");
  render("nodes", "deploy");
  if (S.selected) {
    requestAnimationFrame(() => document.querySelector(`[data-group="${id}"]`)?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
  }
}

/* =============================================================================
   Panels
   ============================================================================= */
function fmtSecs(s) {
  s = Math.max(0, Math.round(s));
  return s >= 60 ? `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, "0")}s` : `${s}s`;
}

const STATUS_ICON = { ready: "✓", planned: "○", error: "✕", deleted: "–", in_progress: "" };

function renderDeploy() {
  const all = Object.entries(S.resources);
  const changed = [...S.tf.changed].map((a) => S.resources[a]).filter(Boolean);
  const done = changed.filter((r) => ["ready", "deleted", "error"].includes(r.status)).length;
  const running = S.job && ["deploy", "destroy", "pipeline"].includes(S.job.name) && S.tf.started;

  let html = "";
  if (S.tf.changes) {
    const c = S.tf.changes;
    const pct = changed.length ? Math.round((done / changed.length) * 100) : 100;
    html += `<div class="summary-row"><span class="muted">terraform ${esc(S.tf.operation || "")}</span>
      <span class="plan"><span class="add">+${c.add}</span><span class="chg">~${c.change}</span><span class="del">-${c.remove}</span></span></div>
      <div class="summary-row"><span class="big">${done}/${changed.length}</span>
      <span class="muted">${running ? "elapsed " + fmtSecs(Date.now() / 1000 - S.tf.started) : "resources changed"}</span></div>
      <div class="progress"><div style="width:${pct}%"></div></div>`;
  } else if (running) {
    html += `<div class="summary-row"><span class="muted">terraform init & plan…</span><span class="muted">elapsed ${fmtSecs(Date.now() / 1000 - S.tf.started)}</span></div>`;
  } else {
    const ready = all.filter(([, r]) => r.status === "ready").length;
    html += `<div class="summary-row"><span class="big">${ready}</span><span class="muted">resources under Terraform management</span></div>`;
  }
  if (S.deployed && Object.keys(S.outputs).length) {
    html += `<div class="outputs">${Object.entries(S.outputs).map(([k, v]) => `<div><span>${esc(k)}=</span>${esc(v)}</div>`).join("")}</div>`;
  }
  $("#deploy-summary").innerHTML = html;

  if (!all.length) {
    $("#resource-groups").innerHTML = `<p class="empty">${S.deployed === null ? "Reading Terraform state…" : "Nothing deployed. Press <b>Deploy</b> to create the platform in AWS."}</p>`;
    return;
  }

  let groups = "";
  for (const id of Object.keys(NODES)) {
    const rs = nodeResources(id).sort(([a], [b]) => a.localeCompare(b));
    if (!rs.length) continue;
    const ready = rs.filter(([, r]) => r.status === "ready").length;
    groups += `<section class="rgroup ${S.selected === id ? "selected" : ""}" data-group="${id}">
      <header><i class="swatch" style="background:var(${SVC_COLOR[NODES[id].svc]})"></i>${esc(NODES[id].title)}
      <span class="count">${ready}/${rs.length}</span></header>
      ${rs.map(([, r]) => `<div class="rrow">
        <span class="st st-${r.status}">${STATUS_ICON[r.status] ?? ""}</span>
        <span class="name" title="${esc(r.name)}">${esc(r.name)}</span>
        ${r.action && r.status !== "ready" ? `<span class="act">${esc(r.action)}</span>` : ""}
        ${r.status === "in_progress" && r.elapsed ? `<span class="el">${r.elapsed}s</span>` : ""}
      </div>`).join("")}
    </section>`;
  }
  $("#resource-groups").innerHTML = groups;
}

const TEST_ICON = { queued: "·", running: "", passed: "✓", failed: "✕", error: "!", skipped: "↷" };

function renderTests() {
  const tests = Object.entries(S.tests);
  const count = (st) => tests.filter(([, t]) => t.status === st).length;
  const passed = count("passed"), failed = count("failed") + count("error"), skipped = count("skipped");
  const running = count("running") + count("queued");
  const duration = tests.reduce((sum, [, t]) => sum + (t.duration || 0), 0);

  const badge = $("#tests-badge");
  if (!tests.length) badge.hidden = true;
  else {
    badge.hidden = false;
    badge.className = "badge " + (failed ? "fail" : running ? "" : "pass");
    badge.textContent = failed ? failed : running ? `${passed}/${tests.length}` : passed;
  }

  if (!tests.length) {
    $("#test-summary").innerHTML = "";
    $("#test-groups").innerHTML = `<p class="empty">No test run yet. <b>Pre-deploy tests</b> run locally with mocked AWS (moto); <b>post-deploy tests</b> hit the real deployment.</p>`;
    return;
  }

  $("#test-summary").innerHTML = `<span class="p">✓ ${passed} passed</span>
    ${failed ? `<span class="f">✕ ${failed} failed</span>` : ""}
    ${skipped ? `<span class="s">↷ ${skipped} skipped</span>` : ""}
    ${running ? `<span class="r">${running} pending</span>` : ""}
    <span class="muted">${duration.toFixed(1)}s</span>`;

  const groups = {};
  for (const [id, t] of tests) (groups[t.group || "other"] ||= []).push([id, t]);
  const order = (g) => { const i = TEST_GROUP_ORDER.indexOf(g); return i < 0 ? 99 : i; };

  $("#test-groups").innerHTML = Object.keys(groups).sort((a, b) => order(a) - order(b) || a.localeCompare(b)).map((g) => {
    const items = groups[g];
    const ok = items.filter(([, t]) => t.status === "passed").length;
    return `<div class="tgroup"><h4>${esc(g.replace("/", " · "))}<span class="gcount">${ok}/${items.length}</span></h4>
      ${items.map(([id, t]) => {
        const failedRow = ["failed", "error"].includes(t.status);
        const file = id.split("::")[0].split("/").pop();
        return `<div class="trow ${failedRow ? "clickable" : ""}" data-test="${esc(id)}" title="${esc(id)}">
          <span class="st st-${t.status}">${TEST_ICON[t.status] ?? ""}</span>
          <span class="name">${esc(t.name || id)} <span class="muted">· ${esc(file)}</span></span>
          ${t.duration ? `<span class="dur">${t.duration < 1 ? Math.round(t.duration * 1000) + "ms" : t.duration.toFixed(1) + "s"}</span>` : ""}
        </div>${failedRow && S.openTest === id ? `<pre class="tdetail">${esc(t.detail || "no details")}</pre>` : ""}`;
      }).join("")}</div>`;
  }).join("");

  const runningRow = document.querySelector(".trow .st-running");
  if (runningRow && !$("#tab-tests").hidden) runningRow.parentElement.scrollIntoView({ block: "nearest" });
}

function renderScenarios() {
  const blocked = !S.deployed || (S.job && ["deploy", "destroy", "pipeline"].includes(S.job.name)) || S.replaying;
  $("#scenarios").innerHTML = Object.entries(S.scenarios).map(([name, sc]) => {
    const st = S.scenarioStatus[name];
    const result = st === "passed" ? `<span class="result" style="color:var(--ok)">✓</span>`
      : st === "failed" ? `<span class="result" style="color:var(--err)">✕</span>`
      : st === "running" ? `<span class="result st-running"></span>` : "";
    return `<div class="scenario ${st === "running" ? "running" : ""}">
      <div><b>${esc(sc.title)}</b><p>${esc(sc.description)}</p></div>
      ${result}
      <button class="btn" data-scenario="${name}" ${blocked || st === "running" ? "disabled" : ""}>Send</button>
    </div>`;
  }).join("") || `<p class="empty">Connecting…</p>`;
}

function renderInspector() {
  if (!S.runs.length) return;
  $("#inspector").innerHTML = S.runs.map((run) => `<div class="run">
    <header>${run.ok === true ? "✓" : run.ok === false ? "✕" : "…"} ${esc(run.title)}
      <span class="when">${new Date(run.ts * 1000).toLocaleTimeString()}</span></header>
    ${run.events.map((e, i) => {
      if (e.type === "note") return `<div class="ev note ${esc(e.level)}">${esc(e.text)}</div>`;
      const open = run.open === i;
      return `<div class="ev http" data-run="${run.id}" data-idx="${i}">
          <span class="code code-${String(e.status)[0]}">${e.status}</span>
          <span>${esc(e.method)} ${esc(e.path)}</span><span class="lat">${e.latency_ms} ms</span>
        </div>${open ? `<div class="ev-detail">${httpDetail(e)}</div>` : ""}`;
    }).join("")}
  </div>`).join("");
}

function httpDetail(e) {
  const line = (k, v) => `<span class="k">${k}:</span> ${esc(v)}\n`;
  return line("X-Correlation-Id", e.correlation_id)
    + (e.authorization ? line("Authorization", e.authorization) : "")
    + (e.request ? `<span class="k">request body:</span>\n${esc(JSON.stringify(e.request, null, 2))}\n` : "")
    + `<span class="k">response:</span>\n${esc(typeof e.response === "string" ? e.response : JSON.stringify(e.response, null, 2))}`;
}

function logLineHtml(l) {
  return `<span class="l ${esc(l.level)}"><span class="src">[${esc(l.source)}]</span>${esc(l.text)}</span>`;
}

function renderLogs() {
  const lines = S.logFilter === "all" ? S.logs : S.logs.filter((l) => l.source === S.logFilter);
  $("#logs").innerHTML = lines.slice(-1500).map(logLineHtml).join("");
  const tab = $("#tab-logs");
  tab.scrollTop = tab.scrollHeight;
}

function appendLog(l) {
  S.logs.push(l);
  if (S.logs.length > 4000) S.logs.splice(0, 1000);
  if (S.logFilter !== "all" && l.source !== S.logFilter) return;
  const tab = $("#tab-logs");
  const nearBottom = tab.scrollHeight - tab.scrollTop - tab.clientHeight < 60;
  $("#logs").insertAdjacentHTML("beforeend", logLineHtml(l));
  if (nearBottom) tab.scrollTop = tab.scrollHeight;
}

function setMetric(id, value) {
  const el = $(id);
  if (el.textContent !== String(value)) {
    el.textContent = value;
    el.classList.remove("bump"); void el.offsetWidth; el.classList.add("bump");
  }
}

function renderMetrics() {
  const m = S.metrics;
  setMetric("#m-queue", m ? `${m.queue_visible} / ${m.queue_inflight}` : "–");
  setMetric("#m-dlq", m ? m.dlq : "–");
  setMetric("#m-stored", m ? m.events_stored : "–");
  setMetric("#m-latency", S.lastLatency != null ? `${S.lastLatency} ms` : "–");
}

function renderChrome() {
  const job = S.job?.name;

  // status pill
  const pill = $("#deploy-pill");
  if (S.replaying) { pill.className = "pill pill-busy"; pill.textContent = "Replay"; }
  else if (job === "deploy" || (job === "pipeline" && S.phases.deploy === "running")) { pill.className = "pill pill-busy"; pill.textContent = "Deploying…"; }
  else if (job === "destroy") { pill.className = "pill pill-busy"; pill.textContent = "Destroying…"; }
  else if (S.deployed === null) { pill.className = "pill pill-unknown"; pill.textContent = "Reading state…"; }
  else if (S.deployed) { pill.className = "pill pill-up"; pill.textContent = "Deployed"; }
  else { pill.className = "pill pill-down"; pill.textContent = "Not deployed"; }

  if (S.outputs.AWS_REGION) $("#env-region").textContent = S.outputs.AWS_REGION;
  if (S.identity) $("#identity").textContent = `${S.identity.user} · ${S.identity.account}`;

  // buttons
  const idle = !job && S.deployed !== null && !S.replaying;
  $("#btn-pipeline").disabled = !idle;
  $("#btn-deploy").disabled = !idle;
  $("#btn-pre").disabled = !idle;
  $("#btn-post").disabled = !idle || !S.deployed;
  $("#btn-destroy").disabled = !idle || !S.deployed;
  $("#btn-cancel").hidden = !job || job === "refresh";

  // pipeline stages
  const trafficRunning = Object.values(S.scenarioStatus).includes("running");
  for (const li of document.querySelectorAll("#stages li")) {
    const stage = li.dataset.stage;
    let status = S.phases[stage] || "idle";
    if (stage === "deploy" && status === "idle" && S.deployed) status = "passed";
    if (stage === "traffic") status = trafficRunning ? "running" : S.deployed ? "ready" : "idle";
    li.dataset.status = status;
  }

  // banner over the diagram
  const banner = $("#job-banner");
  if (S.replaying) {
    banner.hidden = false;
    banner.className = "job-banner replay";
    banner.innerHTML = `<span class="spin"></span>Replaying ${esc(S.replaying)}`;
  } else if (job) {
    banner.hidden = false;
    banner.className = "job-banner";
    let label = JOB_LABELS[job] || job;
    if (job === "pipeline") {
      const current = Object.entries(S.phases).find(([, st]) => st === "running");
      if (current) label += ` · ${PHASE_LABELS[current[0]]}`;
    }
    banner.innerHTML = `<span class="spin"></span>${esc(label)} · ${fmtSecs(Date.now() / 1000 - S.job.started)}`;
  } else {
    banner.hidden = true;
  }
}

/* ---------------------------------------------------------------- render batching */
const dirty = new Set();
let rafPending = false;
function render(...parts) {
  parts.forEach((p) => dirty.add(p));
  if (rafPending) return;
  rafPending = true;
  requestAnimationFrame(() => {
    rafPending = false;
    const d = new Set(dirty); dirty.clear();
    if (d.has("nodes")) renderNodes();
    if (d.has("deploy")) renderDeploy();
    if (d.has("tests")) renderTests();
    if (d.has("scenarios")) renderScenarios();
    if (d.has("inspector")) renderInspector();
    if (d.has("logs")) renderLogs();
    if (d.has("metrics")) renderMetrics();
    renderChrome();
  });
}
const renderAll = () => render("nodes", "deploy", "tests", "scenarios", "inspector", "logs", "metrics");

/* =============================================================================
   Tabs
   ============================================================================= */
function showTab(name) {
  for (const b of document.querySelectorAll(".tabs button")) b.classList.toggle("active", b.dataset.tab === name);
  for (const t of document.querySelectorAll(".tab")) t.hidden = t.id !== `tab-${name}`;
  if (name === "replays") loadRecordings();
  if (name === "logs") renderLogs();
}

/* =============================================================================
   Server events
   ============================================================================= */
function applySnapshot(state) {
  Object.assign(S, {
    deployed: state.deployed,
    outputs: state.outputs || {},
    resources: state.resources || {},
    job: state.job,
    phases: state.phases || {},
    tests: state.tests || {},
    metrics: state.metrics,
    identity: state.identity,
  });
}

function runFor(evt) {
  let run = S.runs.find((r) => r.id === evt.run_id);
  if (!run) {
    run = { id: evt.run_id, title: S.scenarios[evt.scenario]?.title || evt.scenario, ts: evt.ts, events: [], ok: null, open: null };
    S.runs.unshift(run);
    S.runs.length = Math.min(S.runs.length, 15);
  }
  return run;
}

function handle(evt) {
  switch (evt.type) {
    case "snapshot":
      S.scenarios = evt.scenarios || {};
      applySnapshot(evt.state);
      renderAll();
      break;

    case "deployment":
      S.deployed = evt.deployed;
      S.outputs = evt.outputs || {};
      render("nodes", "deploy", "scenarios");
      break;

    case "resources_reset":
      S.resources = evt.resources;
      render("nodes", "deploy");
      break;

    case "resource":
      S.resources[evt.addr] = { node: evt.node, status: evt.status, action: evt.action, name: evt.name, elapsed: evt.elapsed };
      if (evt.status === "planned") S.tf.changed.add(evt.addr);
      render("nodes", "deploy");
      break;

    case "tf_start":
      S.tf = { started: evt.ts, changes: null, changed: new Set(), operation: evt.action };
      showTab("deploy");
      render("deploy");
      break;

    case "tf_summary":
      S.tf.changes = evt.changes;
      S.tf.operation = evt.changes.operation || S.tf.operation;
      render("deploy");
      break;

    case "job":
      S.job = evt.job;
      if (evt.job) {
        const name = evt.job.name;
        if (name.startsWith("tests")) showTab("tests");
        else if (name === "deploy" || name === "destroy") showTab("deploy");
      }
      render("scenarios");
      break;

    case "job_end":
      toast(`${JOB_LABELS[evt.name] || evt.name}: ${evt.status}`, evt.status === "passed" ? "" : "error");
      break;

    case "phase":
      S.phases[evt.phase] = evt.status;
      if (evt.status === "running") showTab(evt.phase === "deploy" ? "deploy" : "tests");
      render();
      break;

    case "tests_reset":
      S.tests = {};
      S.openTest = null;
      render("tests");
      break;

    case "test": {
      const { type, ts, replay, ...rest } = evt;
      S.tests[evt.nodeid] = { ...(S.tests[evt.nodeid] || {}), ...rest };
      render("tests");
      break;
    }

    case "log":
      appendLog(evt);
      break;

    case "metrics":
      S.metrics = evt.data;
      render("metrics");
      break;

    case "identity":
      S.identity = evt.data;
      render();
      break;

    case "scenario_start":
      S.scenarioStatus[evt.scenario] = "running";
      runFor(evt);
      showTab("traffic");
      render("scenarios", "inspector");
      break;

    case "scenario_end":
      S.scenarioStatus[evt.scenario] = evt.ok ? "passed" : "failed";
      runFor(evt).ok = evt.ok;
      render("scenarios", "inspector");
      break;

    case "hop":
      enqueueHop(evt);
      break;

    case "http":
      S.lastLatency = evt.latency_ms;
      runFor(evt).events.push(evt);
      render("inspector", "metrics");
      break;

    case "note":
      runFor(evt).events.push(evt);
      render("inspector");
      break;

    case "replay":
      if (evt.status === "start") {
        S.replaying = evt.name;
        S.resources = {};
        S.tests = {};
        S.phases = {};
        render("nodes", "deploy", "tests");
      } else {
        S.replaying = null;
        fetch("/api/state").then((r) => r.json()).then((st) => { applySnapshot(st); renderAll(); });
      }
      render("scenarios");
      break;
  }
}

function connect() {
  const es = new EventSource("/api/stream");
  es.onopen = () => $("#conn").classList.add("on");
  es.onmessage = (e) => handle(JSON.parse(e.data));
  es.onerror = () => $("#conn").classList.remove("on");
}

/* =============================================================================
   Actions
   ============================================================================= */
async function post(url) {
  try {
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      toast(body.detail || `Request failed (${res.status})`, "error");
    }
  } catch (err) {
    toast(`Server unreachable: ${err.message}`, "error");
  }
}

function toast(text, kind = "") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = text;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

async function loadRecordings() {
  const list = await fetch("/api/recordings").then((r) => r.json()).catch(() => []);
  $("#recordings").innerHTML = list.length ? list.map((r) => `<div class="rec">
      <span class="name" title="${esc(r.name)}">${esc(r.name.replace(".jsonl", ""))}</span>
      <button class="btn" data-replay="${esc(r.name)}" data-speed="1">1×</button>
      <button class="btn" data-replay="${esc(r.name)}" data-speed="4">4×</button>
      <button class="btn" data-replay="${esc(r.name)}" data-speed="12">12×</button>
    </div>`).join("") : `<p class="empty">No recordings yet — run a job or a scenario first.</p>`;
}

function wireUi() {
  $("#btn-pipeline").onclick = () => post("/api/pipeline");
  $("#btn-deploy").onclick = () => post("/api/deploy");
  $("#btn-pre").onclick = () => post("/api/tests/pre_deploy");
  $("#btn-post").onclick = () => post("/api/tests/post_deploy");
  $("#btn-cancel").onclick = () => post("/api/cancel");
  $("#btn-destroy").onclick = () => {
    if (confirm("Destroy every resource of the dev environment in AWS?")) post("/api/destroy");
  };

  for (const b of document.querySelectorAll(".tabs button")) b.onclick = () => showTab(b.dataset.tab);
  for (const li of document.querySelectorAll("#stages li")) li.onclick = () => showTab(li.dataset.tab);

  $("#scenarios").addEventListener("click", (e) => {
    const b = e.target.closest("[data-scenario]");
    if (b) post(`/api/scenario/${b.dataset.scenario}`);
  });

  $("#inspector").addEventListener("click", (e) => {
    const row = e.target.closest(".ev.http");
    if (!row) return;
    const run = S.runs.find((r) => r.id === row.dataset.run);
    const idx = Number(row.dataset.idx);
    run.open = run.open === idx ? null : idx;
    render("inspector");
  });

  $("#test-groups").addEventListener("click", (e) => {
    const row = e.target.closest(".trow.clickable");
    if (!row) return;
    S.openTest = S.openTest === row.dataset.test ? null : row.dataset.test;
    render("tests");
  });

  $("#log-filters").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    S.logFilter = b.dataset.source;
    for (const x of document.querySelectorAll("#log-filters button")) x.classList.toggle("active", x === b);
    renderLogs();
  });

  $("#recordings").addEventListener("click", (e) => {
    const b = e.target.closest("[data-replay]");
    if (b) post(`/api/replay/${encodeURIComponent(b.dataset.replay)}?speed=${b.dataset.speed}`);
  });

  // Elapsed timers
  setInterval(() => {
    if (S.job) render(S.tf.started && ["deploy", "destroy", "pipeline"].includes(S.job.name) ? "deploy" : "metrics");
  }, 1000);
}

buildDiagram();
wireUi();
renderAll();
connect();
