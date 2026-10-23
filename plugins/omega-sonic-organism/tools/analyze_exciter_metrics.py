"""High-frequency production EXCITE alias experiment, not general sound approval."""
import array
import json
import math
import sys
from pathlib import Path
from analyze_renders import fft

root = Path(sys.argv[1])
stimulus = json.loads((root / "stimulus.json").read_text())
results = []
failures = []
by_bin = {}
for case in stimulus["cases"]:
    values = array.array("f")
    values.frombytes((root / case["file"]).read_bytes())
    if sys.byteorder != "little":
        values.byteswap()
    assert len(values) == stimulus["frames"] and all(math.isfinite(x) for x in values)
    spectrum = fft(values)
    power = [abs(x) ** 2 for x in spectrum[:len(values) // 2 + 1]]
    fundamental = 2 * power[case["bin"]]
    assert fundamental > 0
    # Every test fundamental lies above half Nyquist, so all higher harmonics
    # are out of band. Exclude DC and compare residual to actual fundamental.
    other = 2 * sum(x for i, x in enumerate(power[1:-1], 1) if i != case["bin"]) + power[-1]
    residual = 10 * math.log10(max(other, 1e-300) / fundamental)
    record = dict(case, residualDb= residual, peak=max(map(abs, values)))
    results.append(record)
    by_bin.setdefault(case["bin"], {})[case["source"]] = residual
for bin_number, modes in by_bin.items():
    for source in ("saw", "pulse"):
        improvement = modes[f"{source}-naive"] - modes[f"{source}-blep"]
        if improvement < stimulus["blepImprovementLimitDb"]:
            failures.append(f"bin {bin_number} {source}: improvement {improvement:.3f} dB < 10 dB")
    if modes["additive"] > stimulus["additiveResidualLimitDb"]:
        failures.append(f"bin {bin_number}: additive residual exceeds -80 dBc")
assert len(by_bin) == 5 and len(results) == 25
report = dict(result="FAIL" if failures else "PASS", stimulus=stimulus, measurements=results, failures=failures,
              criteriaStatus="provisional engineering experiment, declared in stimulus before analysis",
              scope="48 kHz, five coherent high-frequency points; actual production oscillator helper; no filter/drive/room; not all notes, modulation or DAW/listening acceptance")
(root / "analysis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"{report['result']} production EXCITE alias experiment: 25 captures, {len(failures)} failures")
for failure in failures:
    print(failure)
sys.exit(bool(failures))
