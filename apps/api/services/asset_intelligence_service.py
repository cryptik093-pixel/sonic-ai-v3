from services.audio_analysis_service import audio_analysis_service
from services.asset_service import asset_service
from schemas.asset import AssetCreate


class AssetIntelligenceService:
    """
    Sonic AI Asset Intelligence Pipeline

    Upload
      ↓
    Analyze
      ↓
    Store Metadata
      ↓
    Create Asset Record
    """

    def process_upload(
        self,
        project_id: int,
        filename: str,
        filepath: str
    ):

        metadata = audio_analysis_service.analyze(filepath)

        asset = AssetCreate(
            project_id=project_id,
            filename=filename,
            filepath=filepath,
            file_type=metadata.get("file_type"),
            duration=metadata.get("duration"),
            bpm=metadata.get("bpm"),
            key=metadata.get("key"),
            sample_rate=metadata.get("sample_rate"),
            channels=metadata.get("channels")
        )

        return asset_service.create_asset(asset)


asset_intelligence_service = AssetIntelligenceService()