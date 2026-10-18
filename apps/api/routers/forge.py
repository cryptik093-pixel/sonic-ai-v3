"""Forge upload/review/export in Sonic, with no anonymous artifact URLs."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from ..integrations.forge_auth import forge_owner
from ..schemas.forge import ForgeDraft, ForgeMutation, ForgeReview
from ..services.forge_service import MAX_UPLOAD_BYTES, forge_service

router = APIRouter(prefix="/workbench/api/forge", tags=["Forge"])


@router.get("/packs")
def list_packs(owner: str = Depends(forge_owner)):
    return forge_service.list(owner)


@router.post("/packs", status_code=201)
async def upload(request: Request, request_id: UUID, title: str = Query(min_length=1, max_length=100),
                 taxonomy: str = Query(min_length=1, max_length=120), owner: str = Depends(forge_owner)):
    if request.headers.get("content-type", "").split(";")[0].lower() not in {"application/zip", "application/octet-stream"}:
        raise HTTPException(415, "Send the ZIP as the raw request body")
    data = bytearray()
    async for block in request.stream():
        if len(data) + len(block) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "ZIP upload exceeds 32 MiB limit")
        data.extend(block)
    return await run_in_threadpool(forge_service.command, owner, request_id, "upload",
        {"title": title, "taxonomy": taxonomy}, source=bytes(data))


@router.get("/packs/{pack_id}")
def get_pack(pack_id: UUID, owner: str = Depends(forge_owner)):
    return forge_service.get(owner, str(pack_id))


@router.patch("/packs/{pack_id}/review")
def review(pack_id: UUID, payload: ForgeReview, owner: str = Depends(forge_owner)):
    updates = {key: edit.model_dump(exclude_unset=True) for key, edit in payload.updates.items()}
    if any(any(value is None for value in edit.values()) for edit in updates.values()):
        raise HTTPException(422, "Null edits are not supported; omit unchanged fields")
    return forge_service.command(owner, payload.request_id, "review",
        {"expected_revision": payload.expected_revision, "updates": updates}, pack_id=str(pack_id))


@router.post("/packs/{pack_id}/approve")
def approve(pack_id: UUID, payload: ForgeMutation, owner: str = Depends(forge_owner)):
    return forge_service.command(owner, payload.request_id, "approve",
        {"expected_revision": payload.expected_revision}, pack_id=str(pack_id))


@router.post("/packs/{pack_id}/export")
def export(pack_id: UUID, payload: ForgeMutation, owner: str = Depends(forge_owner)):
    return forge_service.command(owner, payload.request_id, "export",
        {"expected_revision": payload.expected_revision}, pack_id=str(pack_id))


@router.post("/packs/{pack_id}/shopify-draft")
def draft(pack_id: UUID, payload: ForgeDraft, owner: str = Depends(forge_owner)):
    return forge_service.command(owner, payload.request_id, "shopify-draft",
        {"expected_revision": payload.expected_revision, "price": payload.price, "sku": payload.sku}, pack_id=str(pack_id))


@router.get("/exports/{artifact_id}")
def download(artifact_id: UUID, owner: str = Depends(forge_owner)):
    data, kind, checksum = forge_service.download(owner, str(artifact_id))
    suffix = "zip" if kind == "export" else "csv"
    return Response(data, media_type="application/zip" if suffix == "zip" else "text/csv",
        headers={"Content-Disposition": f'attachment; filename="forge-{artifact_id}.{suffix}"',
                 "X-Content-SHA256": checksum, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
