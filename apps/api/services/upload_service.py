from pathlib import Path
import shutil

from utils.audio import get_audio_metadata


UPLOAD_DIR = Path("storage")

UPLOAD_DIR.mkdir(exist_ok=True)


class UploadService:

    def save_audio(self, file):

        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        metadata = get_audio_metadata(
            file.filename
        )

        return {
            "filename": file.filename,
            "filepath": str(file_path),
            **metadata
        }


upload_service = UploadService()