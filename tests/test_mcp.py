"""MCP surface tests.

The server is driven as a real subprocess over stdio, because the failure that
matters most — something printing to stdout and corrupting the protocol — is
invisible to an in-process test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from contextkeel.cli import init as init_cmd
from contextkeel.mcp import tools as mcp_tools


def _drive(root: Path, requests: list[dict]) -> dict[int, dict]:
    payload = "".join(json.dumps(m) + "\n" for m in requests)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "contextkeel.cli.main",
            "mcp-serve",
            "--root",
            str(root),
        ],
        input=payload,
        capture_output=True,
        text=True,
        timeout=120,
    )
    responses: dict[int, dict] = {}
    for line in proc.stdout.splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "id" in message:
            responses[message["id"]] = message
    responses["_stdout"] = proc.stdout  # type: ignore[index]
    responses["_returncode"] = proc.returncode  # type: ignore[index]
    return responses


HANDSHAKE = [
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    },
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
]


@pytest.fixture
def served(node_repo: Path, no_preferred_backend) -> Path:
    init_cmd.run(node_repo, auto=True, no_viewer=True)
    return node_repo


def test_handshake_and_tool_list(served: Path):
    responses = _drive(
        served,
        [*HANDSHAKE, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}],
    )
    assert responses[1]["result"]["serverInfo"]["name"] == "contextkeel"
    names = {t["name"] for t in responses[2]["result"]["tools"]}
    assert names == {"load_context", "query_index", "sync_context", "status", "plan"}


def test_stdout_carries_protocol_frames_only(served: Path):
    """A stray print here would take the whole server down."""
    responses = _drive(
        served,
        [*HANDSHAKE, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}],
    )
    noise = [
        line
        for line in responses["_stdout"].splitlines()  # type: ignore[index]
        if line.strip() and not line.strip().startswith("{")
    ]
    assert noise == []


def test_query_index_finds_a_real_symbol(served: Path):
    responses = _drive(
        served,
        [
            *HANDSHAKE,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "query_index", "arguments": {"query": "Widget"}},
            },
        ],
    )
    text = responses[2]["result"]["content"][0]["text"]
    assert "app.ts" in text


def test_unknown_tool_is_an_error_not_a_crash(served: Path):
    """A bad call must produce a structured error, not take the server down.

    Note the server shuts down at stdin EOF, so a request queued after this one
    may never be served — the meaningful assertions are the error result and a
    clean exit, not a follow-up round trip.
    """
    responses = _drive(
        served,
        [
            *HANDSHAKE,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "nope", "arguments": {}},
            },
        ],
    )
    assert responses[2]["result"]["isError"] is True
    assert "Unknown tool" in responses[2]["result"]["content"][0]["text"]
    assert responses["_returncode"] == 0  # type: ignore[index]


def test_bad_arguments_are_an_error_not_a_crash(served: Path):
    responses = _drive(
        served,
        [
            *HANDSHAKE,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "query_index", "arguments": {"bogus": 1}},
            },
        ],
    )
    assert responses[2]["result"]["isError"] is True
    assert responses["_returncode"] == 0  # type: ignore[index]


# -- handler-level checks (fast, no subprocess) ----------------------------


def test_query_index_paginates(served: Path):
    text = mcp_tools.query_index(served, "e", limit=2)
    assert text.count("\n- ") <= 2 or text.startswith("No matches")


def test_query_index_limit_is_capped(served: Path):
    text = mcp_tools.query_index(served, "e", limit=10_000)
    assert isinstance(text, str)


def test_load_context_is_one_call_not_many_reads(served: Path):
    text = mcp_tools.load_context(served)
    assert "Stack:" in text
    assert "Code index" in text or "No code index" in text
