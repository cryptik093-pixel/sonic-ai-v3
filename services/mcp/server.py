"""Sonic v3.5 local, read-only repository context. No live health claims."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

ROOT = Path(__file__).resolve().parents[2]
FILES = {"state": "docs/status/sonic-state.json", "agents": "agents/registry.json"}
mcp = FastMCP("Sonic AI v3.5")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                           idempotentHint=True, openWorldHint=False)


def read_record(kind: Literal["state", "agents"]) -> dict:
    execution_id = str(uuid4())
    envelope = {"status": "failed", "execution_id": execution_id,
                "trace_id": execution_id, "entity_refs": [], "result": {},
                "evidence": [], "warnings": [],
                "occurred_at": datetime.now(timezone.utc).isoformat()}
    relative = FILES[kind]
    path = ROOT / relative
    try:
        # No caller-supplied paths; reject symlink substitution as well.
        if path.resolve() != path.absolute():
            envelope["error"] = {"code": "AUTHORIZATION_DENIED"}
            return envelope
        if path.stat().st_size > 262144:
            envelope["error"] = {"code": "INVALID_RECORD"}
            return envelope
        raw = path.read_bytes()
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("schema_version") != "1.0.0":
            raise ValueError("Unsupported record")
    except OSError:
        envelope["error"] = {"code": "DEPENDENCY_UNAVAILABLE"}
        return envelope
    except (ValueError, UnicodeError):
        envelope["error"] = {"code": "INVALID_RECORD"}
        return envelope
    envelope.update(status="succeeded", result=data,
                    evidence=[{"kind": "repository_record", "ref": relative,
                               "sha256": sha256(raw).hexdigest()}],
                    warnings=["Repository snapshot only; not a live service health check."])
    return envelope


@mcp.tool(annotations=READ_ONLY)
def sonic_get_state() -> dict:
    """Read the versioned repository progress snapshot, not live system health."""
    return read_record("state")


@mcp.tool(annotations=READ_ONLY)
def sonic_list_agents() -> dict:
    """List intended agent roles and permissions; does not start agents."""
    return read_record("agents")


if __name__ == "__main__":
    mcp.run(transport="stdio")
