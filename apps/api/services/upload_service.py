"""Legacy upload compatibility through the durable, bounded import workflow."""
from fastapi import HTTPException


class UploadService:
    def save_audio(self, file):
        from ..workbench.service import import_asset
        try:
            asset = import_asset(file.filename or "upload", file.file)
            return {"asset_id": asset["id"], "filename": asset["name"], "file_type": asset["name"].rsplit(".", 1)[-1],
                    "sha256": asset["sha256"], **asset["metadata"]}
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None


upload_service = UploadService()
