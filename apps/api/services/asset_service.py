from __future__ import annotations

from ..repositories.asset_repository import asset_store
from ..schemas.asset import Asset, AssetCreate


class AssetService:
    def clear(self) -> None:
        asset_store.clear()

    def list_assets(self) -> list[Asset]:
        return asset_store.list_assets()

    def create_asset(self, payload: AssetCreate) -> Asset:
        return asset_store.create_asset(payload)

    def get_asset(self, asset_id: int) -> Asset | None:
        return asset_store.get_asset(asset_id)

    def save_analysis(self, asset_id: int, analysis_payload: dict) -> object:
        return asset_store.save_analysis(asset_id, analysis_payload)

    def get_latest_analysis(self, asset_id: int):
        return asset_store.get_latest_analysis(asset_id)


asset_service = AssetService()