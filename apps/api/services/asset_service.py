from models.asset import InMemoryAssetStore
from schemas.asset import AssetCreate, AssetResponse


class AssetService:
    def __init__(self) -> None:
        self._store = InMemoryAssetStore()

    def create_asset(self, payload: AssetCreate) -> AssetResponse:
        return self._store.create_asset(payload)

    def list_assets(self) -> list[AssetResponse]:
        return self._store.list_assets()

    def list_project_assets(self, project_id):
        return self._store.list_project_assets(project_id)

    def get_asset(self, asset_id):
        return self._store.get_asset(asset_id)


asset_service = AssetService()