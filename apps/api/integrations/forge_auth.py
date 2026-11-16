"""Identity supplied by existing WorkbenchAuth, never the caller."""
from fastapi import HTTPException, Request


def forge_owner(request: Request) -> str:
    identity = getattr(request.state, "workbench_identity", None)
    if not identity:
        raise HTTPException(401, "Authenticated Workbench session required")
    # Existing desktop model is one local owner/workspace, not hosted tenancy.
    return identity["owner_id"] + ":" + identity["workspace_id"]
