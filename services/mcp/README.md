# Sonic v3.5 MCP

One local stdio server using the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
Pinned v1 API for reproducibility; SDK upgrades require protocol regression tests.
Python 3.12+ recommended. No API key, network listener, API dependency, DB access or external writes.

## Windows setup (repository root)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r services/mcp/requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s services/mcp/tests -v
```

POSIX: `python3 -m venv .venv`, then use `.venv/bin/python` for the same commands.
In a stdio-capable MCP client add the entry below, replacing BOTH paths with absolute
paths to this checkout. Spaces are supported because arguments are separate array entries.
```json
{
  "mcpServers": {
    "sonic-v3-5": {
      "command": "C:/path/to/sonic-ai-v3/.venv/Scripts/python.exe",
      "args": ["C:/path/to/sonic-ai-v3/services/mcp/server.py"]
    }
  }
}
```
This example is not installed client configuration. Keep an older server entry disabled
when testing this one to prevent duplicate tool selection. Rollback: remove this entry.
For HTTP-only clients, remote transport and authentication are a separate open gate.
Do not point a public tunnel at this local process or describe it as connected remotely.

## Contract v1
| Tool | Input | Source of truth | Authority / side effects |
|---|---|---|---|
| sonic_get_state | empty object | docs/status/sonic-state.json | repository read / none |
| sonic_list_agents | empty object | agents/registry.json | repository read / none |

Local OS access is the trust boundary; possession of a client connection permits reading
these two non-secret records. No user/tenant data is exposed. Annotations describe behavior;
the fixed implementation enforces it. There is no write escalation, arbitrary file read,
shell execution or downstream API call. Future domain queries must use authenticated APIs
and producer/workspace scoping before adding tools here.

Results include status, execution_id, trace_id, occurred_at, result, evidence hashes,
entity_refs and warnings. Trace IDs are per call; no workflow propagation yet.
Errors: DEPENDENCY_UNAVAILABLE (missing/unreadable source), INVALID_RECORD (bad JSON,
unsupported schema or oversized record), AUTHORIZATION_DENIED (symlink substitution).
Unknown tools and invalid protocol inputs are handled by the SDK. Error messages contain
no file contents or secrets. Result success means record read, not component health.

Queries may be repeated; no idempotency store is needed and execution IDs differ each time.
Client timeout: 10 seconds; retry at most once for transient process failure. No internal
retries. Partial writes, duplicate delivery and downstream timeouts are inapplicable because
this server has no writes or downstream service. Do not imply durable audit logging:
the returned execution envelope is evidence for the caller to retain.
