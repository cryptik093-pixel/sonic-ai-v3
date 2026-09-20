from pathlib import Path
import shutil

from ..utils.audio import get_audio_metadata
from ..services.audio_analysis_service import audio_analysis_service


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

        analysis = audio_analysis_service.analyze(
            str(file_path)
        )

        return {
            **metadata,
            **analysis
        }


upload_service = UploadService()