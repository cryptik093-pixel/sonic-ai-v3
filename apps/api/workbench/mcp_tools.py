"""MCP calls share the very same workflows, validation, persistence and artifacts as the UI."""
import asyncio

from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from ..integrations.config import ControlConfig
from . import service
from .schemas import AnalyzeCommand, FeedbackCommand, FocusCommand, MidiCommand, PackCommand, ReleaseCommand


def register(server):
    read = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    write = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False)

    async def execute(fn, command):
        if ControlConfig.from_env().oauth_requested:
            raise ToolError("Local output creation requires the local operator bearer token. OAuth read scopes cannot create outputs.")
        try:
            result = await asyncio.to_thread(fn, command)
            if result["status"] != "succeeded":
                raise ToolError(result["error"] or "Run did not complete.")
            return result
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=read)
    async def sonic_workbench_runs() -> dict:
        """Read the 40 latest local operator-owned output runs. Does not call AI providers or change state."""
        return {"owner_id": service.OWNER, "workspace_id": service.WORKSPACE, "runs": await asyncio.to_thread(service.list_runs)}

    @server.tool(annotations=read)
    async def sonic_workbench_assets() -> dict:
        """Read imported asset IDs and measured metadata in this operator's workspace. No filesystem paths are returned."""
        return {"assets": await asyncio.to_thread(service.list_assets)}

    @server.tool(annotations=read)
    async def sonic_workbench_run_get(run_id: str) -> dict:
        """Read one output run, its artifacts/checksums, evidence and next action by UUID."""
        try:
            return await asyncio.to_thread(service.get_run, run_id)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=read)
    async def sonic_compile_production_brief(command: MidiCommand) -> dict:
        """Read-only preview of supported prompt signals, explicit controls, saved-run continuity, assumptions and warnings. Creates no files or events."""
        try:
            return await asyncio.to_thread(service.preview_midi, command)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=write)
    async def sonic_generate_midi(command: MidiCommand) -> dict:
        """Compile the producer prompt, then create local melody, chord, bass and drum MIDI, an audition WAV, a provenance brief and Omega House asset lineage. Reuse request_id only to retry identical inputs. No external provider is called."""
        return await execute(service.generate_midi, command)

    @server.tool(annotations=write)
    async def sonic_record_workbench_feedback(run_id: str, command: FeedbackCommand) -> dict:
        """Record the operator's explicit keep/not-for-me decision on a completed MIDI run. Supply a stable request_id to make retries idempotent. A kept output can inform later prompts that refer to it; this does not change MIDI files."""
        if ControlConfig.from_env().oauth_requested:
            raise ToolError("Local feedback recording requires the local operator bearer token. OAuth read scopes cannot write feedback.")
        try:
            return await asyncio.to_thread(service.record_feedback, run_id, command)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=write)
    async def sonic_analyze_audio(command: AnalyzeCommand) -> dict:
        """Measure an already-imported asset by UUID and save JSON/Markdown reports. Does not alter source audio."""
        return await execute(service.analyze_audio, command)

    @server.tool(annotations=write)
    async def sonic_build_pack(command: PackCommand) -> dict:
        """Copy selected workspace assets or a completed MIDI run into a ZIP with manifest/checksums. Originals are preserved. License is only included when supplied."""
        return await execute(service.build_pack, command)

    @server.tool(annotations=write)
    async def sonic_draft_release(command: ReleaseCommand) -> dict:
        """Save inventory-grounded caption drafts and a Shopify CSV with status=draft. Does not publish, message, or mutate Shopify."""
        return await execute(service.release_draft, command)

    @server.tool(annotations=write)
    async def sonic_plan_session(command: FocusCommand) -> dict:
        """Save one bounded next action based on goal, time, energy and completed work. This is a proposed plan, not completed work."""
        return await execute(service.focus_session, command)
