"""
Pytest plugin that streams test progress to the demo server.

Each event is written to the real stdout as a single line prefixed with
MARKER, so the server can tell it apart from pytest's own output.
Loaded with `-p pytest_live` (the demo folder must be on PYTHONPATH).
"""
import json
import sys

MARKER = "@@LIVE@@"


def _emit(kind, **data):
    sys.__stdout__.write(f"{MARKER}{json.dumps({'kind': kind, **data})}\n")
    sys.__stdout__.flush()


def _group(nodeid: str) -> str:
    """tests/pre_deploy/unit/read/test_x.py::test_y -> pre_deploy/unit"""
    parts = nodeid.split("::")[0].split("/")
    if parts and parts[0] == "tests":
        parts = parts[1:]
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0]


def _short_repr(report) -> str:
    text = str(report.longrepr) if report.longrepr else ""
    return text[-4000:]


def pytest_collection_modifyitems(session, config, items):
    _emit(
        "collected",
        tests=[{"nodeid": i.nodeid, "group": _group(i.nodeid), "name": i.name} for i in items],
    )


def pytest_collectreport(report):
    if report.failed:
        nodeid = report.nodeid or "collection"
        _emit(
            "result",
            nodeid=nodeid,
            group=_group(nodeid),
            name=nodeid.split("/")[-1],
            outcome="error",
            duration=0,
            detail=_short_repr(report),
        )


def pytest_runtest_logstart(nodeid, location):
    _emit("start", nodeid=nodeid)


def pytest_runtest_logreport(report):
    # A test's outcome comes from the "call" phase, unless setup failed or skipped it.
    if report.when == "call" or (report.when == "setup" and not report.passed):
        outcome = report.outcome
        if report.when == "setup" and report.failed:
            outcome = "error"
        _emit(
            "result",
            nodeid=report.nodeid,
            outcome=outcome,
            duration=round(report.duration, 3),
            detail=_short_repr(report) if not report.passed else "",
        )


def pytest_sessionfinish(session, exitstatus):
    _emit("finished", exitstatus=int(exitstatus))
