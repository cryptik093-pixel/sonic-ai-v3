from pathlib import Path
from mutagen import File


class AudioAnalysisService:

    def analyze(self, filepath: str):

        path = Path(filepath)

        result = {
            "file_type": path.suffix.replace(".", ""),
            "duration": None,
            "sample_rate": None,
            "channels": None,
            "bpm": None,
            "key": None
        }

        try:
            audio = File(filepath)

            if audio and audio.info:

                result["duration"] = getattr(
                    audio.info,
                    "length",
                    None
                )

                result["sample_rate"] = getattr(
                    audio.info,
                    "sample_rate",
                    None
                )

                result["channels"] = getattr(
                    audio.info,
                    "channels",
                    None
                )

        except Exception:
            pass

        return result


audio_analysis_service = AudioAnalysisService()