"""Bounded format validation for imported assets, never musical inference.

Untrusted binary media must match its declared container. These checks do not
claim a full decode or prove that a preset is safe to load into a DAW.
"""
import json
import struct
import wave
import zipfile
from pathlib import Path

import soundfile as sf

from .forge_core import ArchiveRejected


def validate_formats(source: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            suffix = Path(entry.filename).suffix.lower()
            with archive.open(entry) as stream:
                head = stream.read(16)
            valid = True
            if suffix == ".wav":
                valid = head[:4] == b"RIFF" and head[8:12] == b"WAVE"
                if valid:
                    try:
                        with archive.open(entry) as stream, wave.open(stream) as audio:
                            frames = audio.getnframes()
                            width = audio.getsampwidth() * audio.getnchannels()
                            valid = frames > 0 and audio.getframerate() > 0
                            count = 0
                            while block := audio.readframes(16384):
                                count += len(block)
                            valid = valid and count == frames * width
                    except wave.Error as exc:
                        # IEEE float WAV is supported by the native audio stack.
                        valid = "unknown format" in str(exc)
                    except (EOFError, struct.error):
                        valid = False
            elif suffix in {".aif", ".aiff"}:
                valid = head[:4] == b"FORM" and head[8:12] in {b"AIFF", b"AIFC"}
            elif suffix == ".flac":
                valid = head.startswith(b"fLaC")
            elif suffix == ".ogg":
                valid = head.startswith(b"OggS")
            elif suffix == ".mp3":
                valid = head.startswith(b"ID3") or (len(head) > 1 and head[0] == 255 and head[1] & 224 == 224)
            elif suffix in {".mid", ".midi"}:
                valid = head.startswith(b"MThd\x00\x00\x00\x06")
            elif suffix in {".fxp", ".fxb"}:
                valid = head.startswith(b"CcnK")
            elif suffix == ".nki":
                raise ArchiveRejected("NKI validation is not implemented; remove presets before import.")
            elif suffix == ".png":
                valid = head.startswith(b"\x89PNG\r\n\x1a\n")
            elif suffix in {".jpg", ".jpeg"}:
                valid = head.startswith(b"\xff\xd8\xff")
            elif suffix == ".webp":
                valid = head[:4] == b"RIFF" and head[8:12] == b"WEBP"
            elif suffix == ".pdf":
                valid = head.startswith(b"%PDF-")
            elif suffix in {".txt", ".json"}:
                # Bound structured/text metadata independently of media limits.
                if entry.file_size > 2 * 1024 * 1024:
                    raise ArchiveRejected("Text metadata exceeds 2 MiB limit")
                try:
                    text = archive.read(entry).decode("utf-8")
                    valid = "\x00" not in text
                    if suffix == ".json":
                        json.loads(text)
                except (UnicodeError, ValueError, RecursionError):
                    valid = False
            if not valid:
                raise ArchiveRejected("Invalid or spoofed media format: " + entry.filename)
            if suffix in {".wav", ".flac", ".aif", ".aiff", ".mp3", ".ogg"}:
                try:
                    with archive.open(entry) as stream, sf.SoundFile(stream) as audio:
                        if audio.frames <= 0 or audio.channels > 32 or audio.samplerate <= 0:
                            raise ArchiveRejected("Invalid audio dimensions")
                        count = 0
                        while len(block := audio.read(16384, dtype="float32", always_2d=True)):
                            count += len(block)
                            if count * audio.channels > 128 * 1024 * 1024:
                                raise ArchiveRejected("Decoded audio exceeds sample budget")
                        if count != audio.frames:
                            raise ArchiveRejected("Truncated audio stream")
                except (RuntimeError, ValueError, OSError) as exc:
                    if isinstance(exc, ArchiveRejected):
                        raise
                    raise ArchiveRejected("Audio cannot be decoded: " + entry.filename) from None
