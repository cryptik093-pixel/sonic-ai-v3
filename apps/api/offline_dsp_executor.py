"""Bounded offline WAV gain processing with guarded, exclusive publication.

No FL Studio integration, host state mutation, or source overwrites.
"""
import hashlib
import os
import tempfile
import wave
from pathlib import Path

from .session_integrity import IntegrityError, _digest
from .session_transactions import SessionTransactionController

MAX_WAV_BYTES = 512 * 1024 * 1024

def _hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()

def execute_gain(controller: SessionTransactionController, session_id, expected_revision,
                 expected_hash, source_relative, gain, output_dir, output_name):
    if type(gain) not in (int, float) or not (0 <= gain <= 1):
        raise IntegrityError("invalid_operation", "Gain must be a finite scalar between 0 and 1")
    if not isinstance(source_relative, str) or not isinstance(output_name, str):
        raise IntegrityError("invalid_operation", "Source and output names must be strings")
    if Path(output_name).name != output_name or not output_name.lower().endswith(".wav"):
        raise IntegrityError("invalid_operation", "Output must be a plain WAV filename")
    evidence = controller.validate(session_id, expected_revision, expected_hash)
    sources = {f["path"]: f["sha256"] for f in evidence["files"]}
    if source_relative not in sources or not source_relative.lower().endswith(".wav"):
        raise IntegrityError("operation_denied", "Source WAV must be in recorded manifest")
    input_path = (controller.root / source_relative).resolve(strict=True)
    destination_root = Path(output_dir).resolve(strict=True)
    if not destination_root.is_dir() or destination_root == controller.root or destination_root.is_relative_to(controller.root):
        raise IntegrityError("invalid_output", "Output directory must exist outside the source project")
    output = destination_root / output_name
    if output.exists():
        raise IntegrityError("conflict", "Output already exists; overwriting is forbidden")
    if input_path.stat().st_size > MAX_WAV_BYTES:
        raise IntegrityError("invalid_source", "WAV exceeds size limit")
    if _hash(input_path) != sources[source_relative]:
        raise IntegrityError("baseline_mismatch", "Input changed after validation")
    stage = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination_root, prefix=".sonic-stage-", suffix=".wav", delete=False) as temp:
            stage = Path(temp.name)
        with wave.open(str(input_path), "rb") as src:
            if src.getcomptype() != "NONE" or src.getsampwidth() != 2 or src.getnchannels() not in (1, 2):
                raise IntegrityError("unsupported_audio", "Only mono/stereo 16-bit PCM WAV supported")
            with wave.open(str(stage), "wb") as dst:
                dst.setparams(src.getparams())
                remaining = src.getnframes()
                while remaining:
                    data = src.readframes(min(4096, remaining))
                    if not data:
                        raise IntegrityError("invalid_source", "Truncated WAV")
                    remaining -= len(data) // (2 * src.getnchannels())
                    from array import array
                    samples = array("h")
                    samples.frombytes(data)
                    if os.sys.byteorder != "little":
                        samples.byteswap()
                    samples = array("h", (int(sample * gain) for sample in samples))
                    if os.sys.byteorder != "little":
                        samples.byteswap()
                    dst.writeframesraw(samples.tobytes())
        with wave.open(str(input_path), "rb") as src, wave.open(str(stage), "rb") as dst:
            if src.getnframes() != dst.getnframes() or src.getframerate() != dst.getframerate() or src.getnchannels() != dst.getnchannels():
                raise IntegrityError("render_failed", "Rendered WAV parameters mismatch")
        controller.validate(session_id, expected_revision, expected_hash)
        if _hash(input_path) != sources[source_relative]:
            raise IntegrityError("baseline_mismatch", "Input changed before publication")
        # Atomic, no-clobber publication on same-volume Windows NTFS and POSIX.
        os.link(stage, output)
        return {"status": "published_offline_candidate", "path": str(output),
                "sha256": _hash(output), "bytes": output.stat().st_size,
                "source_sha256": sources[source_relative], "revision": expected_revision,
                "host_mutated": False, "approved_render_overwritten": False}
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
