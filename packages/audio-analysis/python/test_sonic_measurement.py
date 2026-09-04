import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from sonic_measurement import measure_pcm_wav


SAMPLE_RATE = 48_000


def write_wav(path: Path, channels: list[list[float]], sample_rate: int = SAMPLE_RATE) -> None:
    channel_count = len(channels)
    frame_count = len(channels[0]) if channels else 0
    if any(len(channel) != frame_count for channel in channels):
        raise ValueError("All channels must have equal frame counts")

    interleaved: list[int] = []
    for frame_index in range(frame_count):
        for channel in channels:
            value = max(-1.0, min(1.0, channel[frame_index]))
            integer = -32768 if value <= -1.0 else int(round(value * 32767.0))
            interleaved.append(integer)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channel_count)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f"<{len(interleaved)}h", *interleaved))


class MeasurementProfileTests(unittest.TestCase):
    def test_mono_sine_reports_known_peak_rms_and_crest(self) -> None:
        frames = SAMPLE_RATE // 10
        signal = [0.5 * math.sin(2.0 * math.pi * 1000.0 * i / SAMPLE_RATE) for i in range(frames)]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mono.wav"
            write_wav(path, [signal])
            result = measure_pcm_wav(path)

        self.assertEqual(result["profile_id"], "OH-M04")
        self.assertEqual(result["format"]["sample_rate_hz"], SAMPLE_RATE)
        self.assertEqual(result["format"]["channels"], 1)
        self.assertAlmostEqual(result["format"]["duration_seconds"], 0.1, places=6)
        self.assertAlmostEqual(result["amplitude"]["sample_peak_dbfs"], -6.0206, places=2)
        self.assertAlmostEqual(result["amplitude"]["rms_dbfs"], -9.0309, places=2)
        self.assertAlmostEqual(result["amplitude"]["crest_factor_db"], 3.0103, places=2)
        self.assertEqual(result["stereo"]["correlation_status"], "not_applicable")
        self.assertIsNone(result["loudness"]["integrated_lufs"])
        self.assertIsNone(result["true_peak"]["dbtp"])

    def test_stereo_correlation_distinguishes_in_phase_and_inverted(self) -> None:
        frames = 1000
        signal = [0.25 * math.sin(2.0 * math.pi * 440.0 * i / SAMPLE_RATE) for i in range(frames)]
        inverted = [-value for value in signal]

        with tempfile.TemporaryDirectory() as temp_dir:
            in_phase_path = Path(temp_dir) / "in_phase.wav"
            inverted_path = Path(temp_dir) / "inverted.wav"
            write_wav(in_phase_path, [signal, signal])
            write_wav(inverted_path, [signal, inverted])

            in_phase = measure_pcm_wav(in_phase_path)
            anti_phase = measure_pcm_wav(inverted_path)

        self.assertAlmostEqual(in_phase["stereo"]["correlation"], 1.0, places=6)
        self.assertAlmostEqual(anti_phase["stereo"]["correlation"], -1.0, places=6)

    def test_full_scale_samples_are_counted_without_claiming_limiter_or_clip_cause(self) -> None:
        signal = [1.0, -1.0, 0.0, 0.25]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "full_scale.wav"
            write_wav(path, [signal])
            result = measure_pcm_wav(path)

        self.assertEqual(result["amplitude"]["full_scale_sample_count"], 2)
        self.assertAlmostEqual(result["amplitude"]["full_scale_sample_ratio"], 0.5)
        self.assertEqual(result["interpretation"]["status"], "not_performed")

    def test_silence_is_represented_without_negative_infinity(self) -> None:
        signal = [0.0] * 256

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "silence.wav"
            write_wav(path, [signal])
            result = measure_pcm_wav(path)

        self.assertIsNone(result["amplitude"]["sample_peak_dbfs"])
        self.assertIsNone(result["amplitude"]["rms_dbfs"])
        self.assertIsNone(result["amplitude"]["crest_factor_db"])
        self.assertEqual(result["amplitude"]["silent_sample_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
