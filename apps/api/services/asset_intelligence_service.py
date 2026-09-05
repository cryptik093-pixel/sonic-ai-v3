from __future__ import annotations

from ..repositories.memory_repository import memory_store
from ..repositories.relevance_repository import relevance_store
from ..schemas.asset import AssetCreate
from ..services.asset_service import asset_service
from ..services.audio_analysis_service import audio_analysis_service
from ..services.creator_dna_service import creator_dna_service


class AssetIntelligenceService:
    """Create a durable asset record and persist its analysis metadata."""

    def process_upload(self, project_id: int, filename: str, filepath: str):
        metadata = audio_analysis_service.analyze(filepath)

        asset = AssetCreate(
            project_id=project_id,
            filename=filename,
            filepath=filepath,
            file_type=metadata.get("file_type") or "unknown",
            duration=metadata.get("duration"),
            bpm=metadata.get("bpm"),
            key=metadata.get("key"),
            sample_rate=metadata.get("sample_rate"),
            channels=metadata.get("channels"),
        )

        stored_asset = asset_service.create_asset(asset)
        asset_service.save_analysis(
            stored_asset.id,
            {
                **metadata,
                "confidence": 0.91,
                "provenance": "audio_analysis",
            },
        )
        return stored_asset

    def build_context_snapshot(self, project_id: int | None, asset_id: int | None):
        asset = asset_service.get_asset(asset_id) if asset_id is not None else None
        analysis = asset_service.get_latest_analysis(asset_id) if asset_id is not None else None
        checkpoint = None
        if asset_id is not None:
            checkpoints = relevance_store.list_checkpoints(project_id=project_id, limit=20)
            checkpoint = next((item for item in checkpoints if item.asset_id == asset_id), None)

        dna = creator_dna_service.build_profile(project_id)
        memories = memory_store.search_relevant(
            f"{asset.filename if asset else ''} {asset.file_type if asset else ''}",
            project_id=project_id,
            limit=6,
        ) if asset else []

        summary = (
            f"Project {project_id} contains an asset named {asset.filename if asset else 'unknown'} "
            f"with {analysis.sample_rate if analysis and analysis.sample_rate else 'unknown'}Hz metadata and "
            f"a relevance decision of {checkpoint.persistence_decision if checkpoint else 'pending'}."
        )

        return {
            "asset": asset.model_dump() if asset else None,
            "analysis": {
                "file_type": analysis.file_type if analysis else None,
                "duration": analysis.duration if analysis else None,
                "sample_rate": analysis.sample_rate if analysis else None,
                "channels": analysis.channels if analysis else None,
                "confidence": analysis.confidence if analysis else None,
                "provenance": analysis.provenance if analysis else None,
            },
            "checkpoint": checkpoint.model_dump() if checkpoint else None,
            "dna": dna,
            "memories": [memory.model_dump() for memory in memories],
            "summary": summary,
        }


asset_intelligence_service = AssetIntelligenceService()