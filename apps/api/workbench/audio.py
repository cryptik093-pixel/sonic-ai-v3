"""Bounded, block-based audio measurements with explicit limits on interpretation."""
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

MAX_DURATION = 1200


def inspect_audio(path: Path):
    try:
        info = sf.info(str(path))
    except (RuntimeError, sf.LibsndfileError):
        raise ValueError("This file could not be decoded. Export a WAV or FLAC from your DAW.") from None
    if info.frames <= 0 or info.samplerate <= 0 or info.channels not in (1, 2):
        raise ValueError("Use a non-empty mono or stereo audio file.")
    if info.duration > MAX_DURATION:
        raise ValueError("Analyze audio up to 20 minutes per file.")
    peak = square = dc = silence = near_full = frames = 0
    channel_sum = np.zeros(info.channels)
    channel_square = np.zeros(info.channels)
    cross = 0.0
    for block in sf.blocks(str(path), blocksize=65536, dtype="float64", always_2d=True):
        if not np.isfinite(block).all():
            raise ValueError("Audio contains non-finite samples; re-export it from the DAW.")
        absolute = np.abs(block)
        peak = max(peak, float(absolute.max()))
        square += float(np.square(block).sum())
        silence += int((absolute < 0.0001).all(axis=1).sum())
        near_full += int((absolute >= 0.999).sum())
        channel_sum += block.sum(axis=0)
        channel_square += np.square(block).sum(axis=0)
        if info.channels == 2:
            cross += float((block[:, 0] * block[:, 1]).sum())
        frames += len(block)
    rms = math.sqrt(square / (frames * info.channels))
    corr = None
    if info.channels == 2:
        covariance = cross - channel_sum[0]*channel_sum[1]/frames
        variance = np.maximum(0, channel_square - channel_sum**2/frames)
        denominator = float(np.sqrt(variance[0]*variance[1]))
        if denominator > 1e-12:
            corr = round(max(-1, min(1, covariance / denominator)), 4)
    peak_db = round(20 * math.log10(peak), 2) if peak else None
    rms_db = round(20 * math.log10(rms), 2) if rms else None
    dc = float(np.max(np.abs(channel_sum / frames)))
    observations = []
    if peak == 0:
        observations.append({"severity": "action", "fact": "All decoded samples are silent.", "action": "Check the export selection, mixer routing and mute states before exporting again."})
    if near_full:
        observations.append({"severity": "review", "fact": f"{near_full} channel samples are at or above 0.999 amplitude.", "action": "Inspect loud transients for flattening. This is a near-full-scale warning, not proof of audible clipping."})
    if corr is not None and corr < 0:
        observations.append({"severity": "review", "fact": f"Stereo correlation is {corr}.", "action": "Audition in mono; inspect polarity and stereo widening if the low end disappears."})
    if dc > .01:
        observations.append({"severity": "review", "fact": f"Maximum channel DC offset is {dc:.4f}.", "action": "Remove DC offset before further dynamics processing, then re-check."})
    if silence / frames > .2:
        observations.append({"severity": "review", "fact": f"{silence/frames:.0%} of frames are below -80 dBFS on every channel.", "action": "Check leading/trailing gaps against the intended loop length; preserve intentional rests and reverb tails."})
    if not observations:
        observations.append({"severity": "info", "fact": "No silence, near-full-scale, negative-correlation or DC warning was triggered.", "action": "Audition the loop seam and musical balance before marking the asset ready."})
    return {"duration_seconds": round(info.duration, 4), "sample_rate": info.samplerate,
            "channels": info.channels, "format": info.format, "subtype": info.subtype,
            "sample_peak_dbfs": peak_db, "rms_dbfs": rms_db,
            "crest_factor_db": round(peak_db-rms_db, 2) if peak_db is not None and rms_db is not None else None,
            "near_full_scale_samples": near_full, "dc_offset_max": round(dc, 6),
            "silence_fraction": round(silence/frames, 5), "stereo_correlation": corr,
            "observations": observations, "bpm": None, "key": None,
            "measurement_scope": "Decoded whole-file sample measurements, not true peak or LUFS. Tempo and key are not inferred.",
            "confidence": "High for numerical sample measurements; musical quality requires listening."}


def analyze(path: Path, name: str, folder: Path):
    data = inspect_audio(path)
    result = {"title": name, "engine": "local_measurement_v1", "measurements": data,
              "summary": f"Measured {data['duration_seconds']:.1f}s at {data['sample_rate']} Hz; {len(data['observations'])} review note(s).",
              "next_action": data["observations"][0]["action"], "warnings": [data["measurement_scope"]]}
    (folder / "Audio_Report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [f"# Audio check: {name}", "", result["summary"], "", data["measurement_scope"], ""]
    for key, value in data.items():
        if key not in ("observations", "measurement_scope"):
            lines.append(f"- {key}: {value if value is not None else 'not measured / not defined'}")
    for o in data["observations"]:
        lines += ["", f"**{o['fact']}**", o["action"]]
    (folder / "Audio_Report.md").write_text("\n".join(lines), encoding="utf-8")
    return result
