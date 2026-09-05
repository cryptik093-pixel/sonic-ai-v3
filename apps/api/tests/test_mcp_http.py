"""Real TCP transport using the official MCP client, isolated from user data."""
import asyncio
import os
import socket
import subprocess
import sys
import time

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def test_sdk_client_over_real_http(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, SONIC_DB_PATH=str(tmp_path / "app.db"),
        SONIC_EVENT_DB=str(tmp_path / "events.db"), SONIC_CONTROL_PLANE_TOKEN="test-http-token")
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", str(port)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        with httpx.Client(timeout=2) as client:
            deadline = time.monotonic() + 40
            while True:
                assert process.poll() is None, "API failed to boot"
                try:
                    if client.get(base + "/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                assert time.monotonic() < deadline, "API boot timed out"
                time.sleep(0.2)
            assert client.get(base + "/health").json() == {"healthy": True}
            assert client.post(base + "/mcp").status_code == 401
            assert client.get(base + "/projects/").status_code == 307
            created = client.post(base + "/projects", json={"name": "HTTP fixture", "artist": "Fixture", "genre": "Ambient", "bpm": 100, "key": "C major"})
            assert created.status_code == 201
            project_id = created.json()["id"]

        async def verify():
            async with httpx.AsyncClient(headers={"Authorization": "Bearer test-http-token"}) as client:
                async with streamable_http_client(base + "/mcp", http_client=client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        initialized = await session.initialize()
                        assert initialized.serverInfo.name == "Sonic AI V3"
                        tools = await session.list_tools()
                        assert len(tools.tools) == 5
                        result = await session.call_tool("sonic_system_status", {})
                        assert not result.isError
                        project = await session.call_tool("sonic_project_get", {"project_id": project_id})
                        assert not project.isError and "HTTP fixture" in str(project.content)
        asyncio.run(verify())
    finally:
        process.terminate()
        process.wait(timeout=10)
