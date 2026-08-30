from pathlib import Path


def get_file_extension(filename: str):
    return Path(filename).suffix.lower()


def get_audio_metadata(filename: str):
    extension = get_file_extension(filename)

    return {
        "file_type": extension.replace(".", ""),
        "duration": None,
        "sample_rate": None,
        "channels": None
    }