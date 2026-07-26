from datetime import datetime
from uuid import UUID, uuid4

from schemas.asset import AssetCreate, AssetResponse, AnalysisStatus


class InMemoryAssetStore:
    def __init__(self) -> None:
        self._assets: list[AssetResponse] = []

    def list_assets(self) -> list[AssetResponse]:
        return self._assets.copy()

    def list_project_assets(self, project_id: UUID) -> list[AssetResponse]:
        return [
            asset
            for asset in self._assets
            if asset.project_id == project_id
        ]

    def create_asset(self, payload: AssetCreate) -> AssetResponse:
        asset = AssetResponse(
            id=uuid4(),
            project_id=payload.project_id,
            filename=payload.filename,
            original_filename=payload.original_filename,
            content_type=payload.content_type,
            file_size=payload.file_size,
            duration_seconds=None,
            sample_rate=None,
            channels=None,
            analysis_status=AnalysisStatus.PENDING,
            uploaded_at=datetime.utcnow(),
        )

        self._assets.append(asset)

        return asset

    def get_asset(self, asset_id: UUID) -> AssetResponse | None:
        for asset in self._assets:
            if asset.id == asset_id:
                return asset

        return None