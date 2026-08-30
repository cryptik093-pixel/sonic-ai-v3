from fastapi import APIRouter
from ..schemas.asset import AssetCreate
from ..services.asset_service import asset_service


router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


@router.get("/")
def list_assets():
    return asset_service.list_assets()


@router.post("/")
def create_asset(asset: AssetCreate):
    return asset_service.create_asset(asset)