"""Evaluate the unchanged G07 reference workload; never discard outliers."""
import hashlib
import json
import math
import sys
from pathlib import Path


def evaluate(benchmark):
    errors = []
    for field, expected in (("sampleRate", 48000), ("frames", 256), ("voices", 16)):
        if benchmark.get(field) != expected:
            errors.append(f"Wrong reference {field}; expected {expected}")
    seconds = benchmark.get("secondsPerMode", 0)
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 30:
        errors.append("At least 30 seconds of measured workload per quality is required")
    modes = benchmark.get("modes", [])
    if [mode.get("quality") for mode in modes] != ["Eco", "HQ"]:
        errors.append("Both Eco and HQ must be measured")
    results = []
    for mode in modes:
        values = [mode.get(key) for key in ("medianMs", "p95Ms", "p99Ms", "maximumMs")]
        valid = all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0 for x in values)
        valid = valid and values == sorted(values)
        if not valid:
            errors.append(f"Invalid callback distribution for {mode.get('quality')}")
        callbacks = mode.get("callbacks", 0)
        if not isinstance(callbacks, int) or callbacks < 5625:
            errors.append("Reference callback count is incomplete")
        if isinstance(seconds, (int, float)) and math.isfinite(seconds):
            if callbacks != math.ceil(seconds * 48000 / 256):
                errors.append("Callback count does not match the declared workload")
        checks = dict(
            validDistribution=valid,
            p95Within1ms=valid and values[1] <= 1,
            p99Within2ms=valid and values[2] <= 2,
            zeroDeadlineOverruns=mode.get("overruns") == 0,
            maximumWithinDeadline=valid and values[3] <= 256 / 48000 * 1000,
            zeroNonFiniteFaults=mode.get("nonFiniteFaults") == 0,
        )
        results.append(dict(quality=mode.get("quality"), checks=checks,
                            result="PASS" if all(checks.values()) else "FAIL", measured=mode))
    return dict(gate="G07", result="PASS" if not errors and results and all(r["result"] == "PASS" for r in results) else "FAIL",
                thresholdSource="docs/TEST_RELEASE_GATES.md and docs/V4_SEVEN_SECTORS_AND_COUPLED_MODES_2026-10-21.md",
                p95LimitMs=1, p99LimitMs=2, maximumOverruns=0, deadlineMs=256 / 48000 * 1000,
                validationErrors=errors, modes=results,
                scope="Production-core reference gate; no FL Studio or subjective listening acceptance")


if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:])
    raw = source.read_bytes()
    report = evaluate(json.loads(raw.decode("utf-8-sig")))
    report["benchmarkSha256"] = hashlib.sha256(raw).hexdigest()
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result']} G07: P95 <= 1 ms, P99 <= 2 ms, zero overruns; both qualities, unchanged reference workload")
    sys.exit(report["result"] != "PASS")
