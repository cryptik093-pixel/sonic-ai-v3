"""Authenticated local Forge workflow: atomic revisions, audit, immutable output."""
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import defer

from ..database import SessionLocal
from ..repositories.forge_repository import ForgeArtifact, ForgeCommand, ForgeEvent, ForgePack
from ..workbench.forge_core import (
    ArchivePolicy, ForgeError, approve_edits, export_reviewed_pack,
    export_shopify_draft_csv, inventory_pack,
)
from ..workbench.forge_core.core import Asset, Manifest
from ..workbench.format_validation import validate_formats
from ..workbench.models import Run, WorkEvent, OWNER, WORKSPACE
from ..workbench.service import now

MAX_UPLOAD_BYTES = 32 * 1024 * 1024
POLICY = ArchivePolicy(max_file_bytes=32 * 1024 * 1024, max_total_bytes=128 * 1024 * 1024)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(raw: str) -> Manifest:
    doc = json.loads(raw)
    doc["assets"] = [Asset(**a) for a in doc["assets"]]
    return Manifest(**doc)


def view(pack: ForgePack) -> dict:
    return {"id": pack.id, "status": pack.status, "manifest_revision": pack.revision,
            "run_id": pack.run_id, "owner_id": OWNER, "workspace_id": WORKSPACE,
            "approved_revision": pack.approved_revision, "approved_by": pack.approved_by,
            "manifest": json.loads(pack.manifest), "errors": [], "evidence_refs": []}


def owned(session, pack_id: str, owner: str) -> ForgePack:
    pack = session.scalar(select(ForgePack).options(defer(ForgePack.source)).where(ForgePack.id == pack_id, ForgePack.owner == owner))
    if pack is None:
        raise HTTPException(404, "Pack not found")
    return pack


class ForgeService:
    def list(self, owner):
        with SessionLocal() as session:
            # Never materialize a page of original ZIP BLOBs just to list titles.
            packs = session.execute(select(ForgePack.id, ForgePack.manifest, ForgePack.revision, ForgePack.status)
                .where(ForgePack.owner == owner).order_by(ForgePack.created_at.desc()).limit(100))
            return [{"id": p.id, "title": json.loads(p.manifest)["title"],
                     "manifest_revision": p.revision, "status": p.status} for p in packs]

    def get(self, owner, pack_id):
        with SessionLocal() as session:
            result = view(owned(session, pack_id, owner))
            events = session.scalars(select(ForgeEvent).where(ForgeEvent.pack_id == pack_id, ForgeEvent.owner == owner).order_by(ForgeEvent.id))
            result["events"] = [{"id": e.id, "actor": e.owner, "action": e.action,
                                 "revision": e.revision, "correlation_id": e.request_id,
                                 "timestamp": e.created_at.isoformat() + "Z", "evidence": json.loads(e.evidence)} for e in events]
            result["artifacts"] = [{"id": a.id, "kind": a.kind, "revision": a.revision, "sha256": a.sha256}
                for a in session.execute(select(ForgeArtifact.id, ForgeArtifact.kind, ForgeArtifact.revision, ForgeArtifact.sha256)
                    .where(ForgeArtifact.pack_id == pack_id, ForgeArtifact.owner == owner))]
            return result

    def download(self, owner, artifact_id):
        with SessionLocal() as session:
            a = session.scalar(select(ForgeArtifact).where(ForgeArtifact.id == artifact_id, ForgeArtifact.owner == owner))
            if a is None:
                raise HTTPException(404, "Artifact not found")
            if sha(a.content) != a.sha256:
                raise HTTPException(409, "Artifact integrity check failed")
            return a.content, a.kind, a.sha256

    def command(self, owner, request_id, action, payload, *, pack_id=None, source=None):
        try:
            return self._command(owner, request_id, action, payload, pack_id=pack_id, source=source)
        except (HTTPException, OSError) as exc:
            # The failed transaction has rolled back before recording the failure.
            # Authorization misses are not attached to another owner's resource.
            if pack_id:
                with SessionLocal() as session:
                    pack = session.scalar(select(ForgePack).where(ForgePack.id == pack_id, ForgePack.owner == owner))
                    if pack is not None:
                        detail = exc.detail if isinstance(exc, HTTPException) else "Local storage unavailable"
                        session.add(ForgeEvent(owner=owner, pack_id=pack.id, request_id=str(request_id),
                            action=action + "_failed", revision=pack.revision,
                            evidence=json.dumps({"validation": "failed", "error": detail})))
                        session.commit()
            if isinstance(exc, OSError):
                raise HTTPException(503, "Local storage unavailable; retry with the same request ID") from None
            raise

    def _command(self, owner, request_id, action, payload, *, pack_id=None, source=None):
        request_id = str(request_id)
        fingerprint = sha(json.dumps({"action": action, "pack": pack_id, "payload": payload,
                                     "source": sha(source) if source is not None else None}, sort_keys=True).encode())
        with SessionLocal() as session:
            # Serialize SQLite writers before the idempotency/revision reads.
            # Commit includes source/artifact BLOB + revision + audit + response.
            session.execute(text("BEGIN IMMEDIATE"))
            prior = session.scalar(select(ForgeCommand).where(ForgeCommand.owner == owner, ForgeCommand.request_id == request_id))
            if prior:
                if prior.fingerprint != fingerprint:
                    raise HTTPException(409, "Request ID reused with different inputs")
                return json.loads(prior.response)
            try:
                if action == "upload":
                    with tempfile.TemporaryDirectory(prefix="sonic-forge-") as folder:
                        path = Path(folder) / "source.zip"
                        path.write_bytes(source)
                        manifest = inventory_pack(path, payload["title"], payload["taxonomy"], policy=POLICY)
                        validate_formats(path)
                    run_id = str(uuid4())
                    if session.scalar(select(Run.id).where(Run.owner_id == OWNER, Run.request_id == request_id)):
                        raise HTTPException(409, "Request ID is already used by another Workbench workflow")
                    run = Run(id=run_id, owner_id=OWNER, workspace_id=WORKSPACE, request_id=request_id,
                        request_hash=fingerprint, kind="forge", status="succeeded", created_at=now(),
                        completed_at=now(), request_json=json.dumps(payload), result_json="{}")
                    session.add(run)
                    session.flush()
                    pack = ForgePack(id=str(uuid4()), run_id=run_id, owner=owner, revision=1,
                        status="awaiting_review", manifest=json.dumps(manifest.to_dict()), source=source)
                    session.add(pack)
                    session.flush()
                else:
                    pack = owned(session, pack_id, owner)
                    if pack.revision != payload["expected_revision"]:
                        raise HTTPException(409, "Stale manifest revision; reload before editing")
                    manifest = load_manifest(pack.manifest)
                    if sha(pack.source) != manifest.source_zip_sha256:
                        raise HTTPException(409, "Original source ZIP integrity check failed")
                    if action == "review":
                        manifest = approve_edits(manifest, payload["updates"], policy=POLICY)
                        pack.manifest = json.dumps(manifest.to_dict())
                        pack.revision += 1
                        pack.status = "reviewed" if manifest.status == "reviewed" else "awaiting_review"
                        pack.approved_revision = None
                        pack.approved_by = None
                    elif action == "approve":
                        if manifest.status != "reviewed" or not all(a.review_state == "approved" for a in manifest.assets):
                            raise ForgeError("Review every asset before approving this revision")
                        pack.approved_revision = pack.revision
                        pack.approved_by = owner
                        pack.status = "approved"
                    elif action in {"export", "shopify-draft"}:
                        if pack.approved_revision != pack.revision or pack.approved_by != owner:
                            raise ForgeError("Approve the current manifest revision before exporting")
                        # One ZIP per revision; different request IDs cannot duplicate exports.
                        artifact = session.scalar(select(ForgeArtifact).where(
                            ForgeArtifact.pack_id == pack.id, ForgeArtifact.revision == pack.revision,
                            ForgeArtifact.kind == action)) if action == "export" else None
                        if artifact is None:
                            with tempfile.TemporaryDirectory(prefix="sonic-forge-") as folder:
                                src, dest = Path(folder) / "source.zip", Path(folder) / "output.zip"
                                src.write_bytes(pack.source)
                                if action == "export":
                                    export_reviewed_pack(src, manifest, dest, policy=POLICY)
                                else:
                                    dest = Path(folder) / "draft.csv"
                                    export_shopify_draft_csv(manifest, dest, payload["price"], payload["sku"])
                                content = dest.read_bytes()
                            artifact = ForgeArtifact(id=str(uuid4()), owner=owner, pack_id=pack.id,
                                revision=pack.revision, kind=action, sha256=sha(content), content=content)
                            session.add(artifact)
                        if action == "export":
                            pack.status = "exported"
                    else:
                        raise ForgeError("Unknown Forge command")
            except (ForgeError, zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError) as exc:
                # ZIP/parser failures never expose a temporary path or source bytes.
                detail = str(exc) if isinstance(exc, ForgeError) else "Invalid or unsupported ZIP data"
                raise HTTPException(400, detail) from None
            result = view(pack)
            evidence = {"source_zip_sha256": json.loads(pack.manifest)["source_zip_sha256"],
                        "manifest_sha256": sha(pack.manifest.encode()), "validation": "passed"}
            if action in {"export", "shopify-draft"}:
                result["artifact"] = {"id": artifact.id, "sha256": artifact.sha256, "kind": artifact.kind,
                                      "revision": artifact.revision}
                evidence["artifact_sha256"] = artifact.sha256
            event = ForgeEvent(owner=owner, pack_id=pack.id, request_id=request_id,
                action=action, revision=pack.revision, evidence=json.dumps(evidence))
            session.add(event)
            session.flush()
            result["evidence_refs"] = [event.id]
            result["correlation_id"] = request_id
            run = session.get(Run, pack.run_id)
            run.result_json = json.dumps({"title": json.loads(pack.manifest)["title"],
                "forge_pack_id": pack.id, "manifest_revision": pack.revision,
                "summary": f"Forge ZIP: {pack.status}, revision {pack.revision}.",
                "engine": "forge_core_v1", "artifacts": [],
                "next_action": "Open Forge ZIP review to inspect metadata and download approved exports.",
                "warnings": ["BPM/key estimates are not measured. Rights require operator review."]})
            session.add(WorkEvent(id=str(uuid4()), owner_id=OWNER, workspace_id=WORKSPACE,
                run_id=pack.run_id, type="workbench.forge_" + action, occurred_at=now(),
                payload=json.dumps({"request_id": request_id, "pack_id": pack.id,
                    "manifest_revision": pack.revision, "evidence": evidence})))
            session.add(ForgeCommand(owner=owner, request_id=request_id, fingerprint=fingerprint,
                                     response=json.dumps(result)))
            session.commit()
            return result


forge_service = ForgeService()
