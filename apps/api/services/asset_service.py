from ..schemas.asset import AssetCreate, Asset
from datetime import datetime


class AssetService:

    def __init__(self):
        self.assets = []
        self.counter = 1

    def create_asset(self, asset: AssetCreate):
        new_asset = Asset(
            id=self.counter,
            created_at=datetime.utcnow(),
            **asset.model_dump()
        )

        self.assets.append(new_asset)
        self.counter += 1

        return new_asset

    def list_assets(self):
        return self.assets


asset_service = AssetService()