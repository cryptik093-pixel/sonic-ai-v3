import wave
from pathlib import Path

from mutagen import File


class AudioAnalysisService:
    def _read_wave_fallback(self, path: Path) -> dict:
        try:
            with wave.open(str(path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                duration = frames / float(rate) if rate else None
                return {
                    "duration": duration,
                    "sample_rate": int(rate) if rate else None,
                    "channels": int(channels) if channels else None,
                    "bit_depth": sample_width * 8,
                }
        except Exception:
            return {
                "duration": None,
                "sample_rate": None,
                "channels": None,
                "bit_depth": None,
            }

    def analyze(self, filepath: str):
        path = Path(filepath)

        result = {
            "file_type": path.suffix.replace(".", ""),
            "duration": None,
            "sample_rate": None,
            "channels": None,
            "bpm": None,
            "key": None,
        }

        try:
            audio = File(filepath)

            if audio and audio.info:
                result["duration"] = getattr(audio.info, "length", None)
                result["sample_rate"] = getattr(audio.info, "sample_rate", None)
                result["channels"] = getattr(audio.info, "channels", None)
        except Exception:
            pass

        if path.suffix.lower() == ".wav" and (result["sample_rate"] is None or result["channels"] is None):
            fallback = self._read_wave_fallback(path)
            result["duration"] = result["duration"] if result["duration"] is not None else fallback.get("duration")
            result["sample_rate"] = result["sample_rate"] if result["sample_rate"] is not None else fallback.get("sample_rate")
            result["channels"] = result["channels"] if result["channels"] is not None else fallback.get("channels")

        return result


audio_analysis_service = AudioAnalysisService()