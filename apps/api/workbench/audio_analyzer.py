"""Optional, bounded music descriptors for local imported audio (not neural embeddings)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

PITCHES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
MAX_WINDOW_SECONDS = 90
ANALYSIS_SR = 22050


def _estimated_key(chroma: np.ndarray) -> tuple[str | None, float | None]:
    mean = np.asarray(chroma.mean(axis=1), dtype=np.float64)
    if not np.isfinite(mean).all() or mean.std() < 1e-6:
        return None, None
    scores = []
    for mode, profile in (("major", MAJOR), ("minor", MINOR)):
        for shift in range(12):
            scores.append((float(np.corrcoef(mean, np.roll(profile, shift))[0, 1]), PITCHES[shift], mode))
    scores.sort(reverse=True)
    top, runner_up = scores[0], scores[1]
    if not np.isfinite(top[0]) or top[0] < 0.3 or top[0] - runner_up[0] < 0.025:
        return None, None
    return f"{top[1]} {top[2]}", round(top[0], 3)


def extract_musical_metadata(path: Path) -> dict[str, Any]:
    """Analyze at most the first 90 s. Report estimates, never claim ground truth."""
    # Lazy import keeps the existing, measurement-only workbench usable without the extra.
    try:
        import librosa
    except ImportError as exc:
        raise ValueError("Musical metadata requires the optional librosa dependency.") from exc

    info = sf.info(str(path))
    if info.frames <= 0 or info.channels not in (1, 2) or info.duration > 1200:
        raise ValueError("Choose readable mono/stereo audio under 20 minutes.")
    y, sr = librosa.load(str(path), sr=ANALYSIS_SR, mono=True, duration=MAX_WINDOW_SECONDS)
    if y.size == 0 or not np.isfinite(y).all():
        raise ValueError("Audio could not be analyzed.")
    window = round(len(y) / sr, 2)
    result: dict[str, Any] = {
        "schema_version": "sonic.musical-metadata/1",
        "duration_seconds": round(float(info.duration), 2),
        "analyzed_seconds": window,
        "analysis_limited_to_first_90_seconds": info.duration > MAX_WINDOW_SECONDS,
        "source_sample_rate": info.samplerate,
        "analysis_sample_rate": sr,
        "bpm_estimate": None,
        "key_estimate": None,
        "key_profile_correlation": None,
        "spectral_centroid_hz": None,
        "timbre_hint": "undetermined",
        "dsp_descriptor": None,
        "semantic_embedding": None,
        "notes": ["Tempo and key are hypotheses, especially for isolated drums, vocals, or atonal FX.",
                  "DSP descriptor is not a neural CLAP/text-search embedding."],
    }
    if float(np.max(np.abs(y))) < 1e-5:
        result["timbre_hint"] = "silent"
        return result

    onset = librosa.onset.onset_strength(y=y, sr=sr)
    bpm, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, trim=False)
    tempo = float(np.asarray(bpm).reshape(-1)[0])
    if np.isfinite(tempo) and tempo > 0 and len(beats) >= 3:
        result["bpm_estimate"] = round(tempo, 1)

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    result["key_estimate"], result["key_profile_correlation"] = _estimated_key(chroma)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = float(np.mean(centroid))
    if np.isfinite(brightness):
        result["spectral_centroid_hz"] = round(brightness, 1)
        result["timbre_hint"] = "darker" if brightness < 2000 else "brighter"
    # Handcrafted, reproducible descriptors for future local similarity baselines.
    # This is NOT a semantic audio/text embedding.
    distribution = chroma.mean(axis=1).astype(float)
    distribution /= max(float(distribution.sum()), 1e-9)
    result["dsp_descriptor"] = [round(float(value), 6) for value in distribution]
    return result
