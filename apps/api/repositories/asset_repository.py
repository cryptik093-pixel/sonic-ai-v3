"""Persistence required by the existing asset service and ORM models."""
import json

from ..database import AssetORM, AssetAnalysisORM, SessionLocal
from ..schemas.asset import Asset, AssetCreate


class AssetRepository:
    def clear(self):
        with SessionLocal.begin() as session:
            session.query(AssetAnalysisORM).delete()
            session.query(AssetORM).delete()

    def list_assets(self):
        with SessionLocal() as session:
            return [Asset.model_validate(row, from_attributes=True)
                    for row in session.query(AssetORM).order_by(AssetORM.id).all()]

    def get_asset(self, asset_id: int):
        with SessionLocal() as session:
            row = session.get(AssetORM, asset_id)
            return Asset.model_validate(row, from_attributes=True) if row else None

    def create_asset(self, payload: AssetCreate):
        with SessionLocal.begin() as session:
            row = AssetORM(**payload.model_dump())
            session.add(row)
            session.flush()
            return Asset.model_validate(row, from_attributes=True)

    def save_analysis(self, asset_id: int, payload: dict):
        fields = {c.name for c in AssetAnalysisORM.__table__.columns} - {"id", "asset_id", "created_at"}
        data = {k: v for k, v in payload.items() if k in fields}
        for key in ("frequency_distribution", "transient_information", "silence_information"):
            if key in data and isinstance(data[key], (dict, list)):
                data[key] = json.dumps(data[key])
        with SessionLocal.begin() as session:
            if session.get(AssetORM, asset_id) is None:
                raise ValueError("Asset not found")
            row = AssetAnalysisORM(asset_id=asset_id, **data)
            session.add(row)
            session.flush()
            session.expunge(row)
            return row

    def get_latest_analysis(self, asset_id: int):
        with SessionLocal() as session:
            return session.query(AssetAnalysisORM).filter_by(asset_id=asset_id).order_by(AssetAnalysisORM.id.desc()).first()


asset_store = AssetRepository()
