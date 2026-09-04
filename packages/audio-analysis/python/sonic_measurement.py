"""Deterministic PCM WAV measurements for Sonic AI V3 OH-M04.

This module intentionally uses only the Python standard library so the initial
measurement contract can run identically in local development and CI.

It does NOT estimate LUFS or true peak. Those quantities remain explicit,
separate, and unavailable until a standards-compliant implementation is added.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import wave
from pathlib import Path
from typing import Iterable

PROFILE_ID = "OH-M04"
PROFILE_VERSION = "1.0.0"
SILENCE_THRESHOLD_DBFS = -60.0
NEAR_FULL_SCALE_THRESHOLD = 0.999


def _dbfs(value: float) -> float | None:
    if value <= 0.0:
        return None
    return 20.0 * math.log10(value)


def _decode_pcm(raw: bytes, sample_width: int) -> list[int]:
    if sample_width == 1:
        return [value - 128 for value in raw]
    if sample_width == 2:
        count = len(raw) // 2
        return list(struct.unpack(f"<{count}h", raw))
    if sample_width == 3:
        values: list[int] = []
        for index in range(0, len(raw), 3):
            chunk = raw[index : index + 3]
            value = int.from_bytes(chunk, byteorder="little", signed=False)
            if value & 0x800000:
                value -= 1 << 24
            values.append(value)
        return values
    if sample_width == 4:
        count = len(raw) // 4
        return list(struct.unpack(f"<{count}i", raw))
    raise ValueError(f"Unsupported PCM sample width: {sample_width} bytes")


def _normalizer(sample_width: int) -> float:
    return float(1 << (sample_width * 8 - 1))


def _full_scale_extrema(sample_width: int) -> tuple[int, int]:
    bits = sample_width * 8
    return -(1 << (bits - 1)), (1 << (bits - 1)) - 1


def _rms(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def _correlation(left: list[float], right: list[float]) -> float | None:
    if not left or len(left) != len(right):
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_centered = [value - left_mean for value in left]
    right_centered = [value - right_mean for value in right]
    left_energy = sum(value * value for value in left_centered)
    right_energy = sum(value * value for value in right_centered)
    denominator = math.sqrt(left_energy * right_energy)
    if denominator == 0.0:
        return None
    value = sum(a * b for a, b in zip(left_centered, right_centered)) / denominator
    return max(-1.0, min(1.0, value))


def measure_pcm_wav(path: str | Path) -> dict:
    """Measure an uncompressed PCM WAV file using OH-M04 v1 deterministic rules."""
    source = Path(path)
    raw_file = source.read_bytes()
    sha256 = hashlib.sha256(raw_file).hexdigest()

    with wave.open(str(source), "rb") as wav:
        if wav.getcomptype() != "NONE":
            raise ValueError("OH-M04 v1 accepts uncompressed PCM WAV only")
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()
        raw_frames = wav.readframes(frame_count)

    integer_samples = _decode_pcm(raw_frames, sample_width)
    expected_samples = frame_count * channels
    if len(integer_samples) != expected_samples:
        raise ValueError(
            f"Decoded sample count mismatch: expected {expected_samples}, got {len(integer_samples)}"
        )

    scale = _normalizer(sample_width)
    normalized = [sample / scale for sample in integer_samples]
    channel_samples = [normalized[index::channels] for index in range(channels)]

    sample_peak_linear = max((abs(value) for value in normalized), default=0.0)
    overall_rms_linear = _rms(normalized)
    sample_peak_dbfs = _dbfs(sample_peak_linear)
    rms_dbfs = _dbfs(overall_rms_linear)
    crest_factor_db = (
        sample_peak_dbfs - rms_dbfs
        if sample_peak_dbfs is not None and rms_dbfs is not None
        else None
    )

    min_int, max_int = _full_scale_extrema(sample_width)
    full_scale_count = sum(
        1 for value in integer_samples if value == min_int or value == max_int
    )
    near_full_scale_count = sum(
        1 for value in normalized if abs(value) >= NEAR_FULL_SCALE_THRESHOLD
    )
    silence_threshold_linear = 10.0 ** (SILENCE_THRESHOLD_DBFS / 20.0)
    silent_sample_count = sum(
        1 for value in normalized if abs(value) <= silence_threshold_linear
    )
    total_samples = len(normalized)

    per_channel = []
    for index, samples in enumerate(channel_samples):
        channel_rms = _rms(samples)
        channel_peak = max((abs(value) for value in samples), default=0.0)
        per_channel.append(
            {
                "channel_index": index,
                "sample_peak_dbfs": _dbfs(channel_peak),
                "rms_dbfs": _dbfs(channel_rms),
                "dc_offset_mean": (sum(samples) / len(samples)) if samples else 0.0,
            }
        )

    if channels == 2:
        correlation = _correlation(channel_samples[0], channel_samples[1])
        correlation_status = "measured" if correlation is not None else "unavailable"
    else:
        correlation = None
        correlation_status = "not_applicable"

    return {
        "profile_id": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "source": {
            "path": source.name,
            "sha256": sha256,
            "container": "wav",
            "codec": "pcm",
        },
        "format": {
            "sample_rate_hz": sample_rate,
            "channels": channels,
            "bit_depth": sample_width * 8,
            "frame_count": frame_count,
            "duration_seconds": frame_count / sample_rate if sample_rate else 0.0,
        },
        "amplitude": {
            "sample_peak_dbfs": sample_peak_dbfs,
            "rms_dbfs": rms_dbfs,
            "crest_factor_db": crest_factor_db,
            "full_scale_sample_count": full_scale_count,
            "full_scale_sample_ratio": full_scale_count / total_samples if total_samples else 0.0,
            "near_full_scale_sample_count": near_full_scale_count,
            "near_full_scale_sample_ratio": near_full_scale_count / total_samples if total_samples else 0.0,
            "silence_threshold_dbfs": SILENCE_THRESHOLD_DBFS,
            "silent_sample_ratio": silent_sample_count / total_samples if total_samples else 0.0,
        },
        "channels": per_channel,
        "stereo": {
            "correlation_status": correlation_status,
            "correlation": correlation,
        },
        "loudness": {
            "integrated_lufs": None,
            "status": "unavailable",
            "reason": "OH-M04 v1 has no standards-compliant BS.1770/R128 loudness implementation",
        },
        "true_peak": {
            "dbtp": None,
            "status": "unavailable",
            "reason": "OH-M04 v1 has no standards-compliant oversampled true-peak implementation",
        },
        "interpretation": {
            "status": "not_performed",
            "reason": "OH-M04 produces deterministic observations only; interpretation belongs to Intelligence Core",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure an uncompressed PCM WAV using Sonic AI V3 OH-M04 v1."
    )
    parser.add_argument("wav", type=Path, help="Path to an uncompressed PCM WAV file")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON",
    )
    args = parser.parse_args()
    result = measure_pcm_wav(args.wav)
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
