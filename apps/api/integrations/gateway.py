"""SDK-owned MCP protocol transport with a fixed read-only tool registry."""
import asyncio
import sqlite3
from uuid import UUID
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from mcp.server.transport_security import TransportSecuritySettings
from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal, ProjectORM
from ..schemas.project import Project
from .config import ControlConfig


router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/status")
def integration_status(request: Request):
    return request.app.state.control_plane.status()


@router.post("/check")
async def integration_check(request: Request):
    try:
        return await request.app.state.control_plane.check()
    except sqlite3.Error:
        raise HTTPException(503, "audit_persistence_failed") from None


def build_mcp(get_plane):
    config = ControlConfig.from_env()
    hosts = ["127.0.0.1", "localhost", "[::1]", "127.0.0.1:*", "localhost:*", "[::1]:*"]
    if config.oauth_configured:
        hosts.append(urlsplit(config.public_mcp_url).netloc)
    server = FastMCP("Sonic AI V3", stateless_http=True, json_response=True,
        streamable_http_path="/mcp", max_request_body_size=65536,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=[]),
        instructions="Operator tools with timestamped evidence. Read queries are side-effect free. Local output tools create files and run records only; reuse request_id for an identical retry. No Shopify mutation or outbound message capability is exposed.")
    readonly = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)

    @server.tool(annotations=readonly)
    async def sonic_system_status() -> dict:
        """Read current API/database health and cached provider evidence. Does not call external providers or change business data."""
        return await asyncio.to_thread(get_plane().status)

    @server.tool(annotations=readonly)
    async def sonic_integration_status() -> dict:
        """Read normalized integration states, check timestamps and trace IDs; configuration is not live validation."""
        return await asyncio.to_thread(get_plane().status)

    @server.tool(annotations=readonly)
    async def sonic_shopify_status() -> dict:
        """Read cached Shopify authentication and required/requested/granted scope evidence. Never mutates the store."""
        status = await asyncio.to_thread(get_plane().status)
        return next(item for item in status["integrations"] if item["provider"] == "shopify")

    @server.tool(annotations=readonly)
    async def sonic_project_get(project_id: int) -> dict:
        """Read one local operator-owned project by positive integer ID. This installation is single-operator, not multi-tenant."""
        if project_id <= 0:
            raise ToolError("project_id must be positive")
        def read():
            try:
                with SessionLocal() as session:
                    row = session.get(ProjectORM, project_id)
                    if row is None:
                        raise ToolError("Project not found")
                    return Project.model_validate(row, from_attributes=True).model_dump(mode="json")
            except SQLAlchemyError:
                raise ToolError("Project storage unavailable") from None
        return await asyncio.to_thread(read)

    @server.tool(annotations=readonly)
    async def sonic_decision_trace_get(trace_id: str) -> dict:
        """Read an integration check or webhook proposal evidence record by UUID trace ID. Contains no hidden reasoning or provider response bodies."""
        try:
            trace_id = str(UUID(trace_id))
        except ValueError:
            raise ToolError("trace_id must be a UUID") from None
        try:
            record = await asyncio.to_thread(get_plane().store.trace, trace_id)
        except sqlite3.Error:
            raise ToolError("Decision storage unavailable") from None
        if record is None:
            raise ToolError("Trace not found")
        return record

    from ..workbench.mcp_tools import register
    register(server)
    return server
