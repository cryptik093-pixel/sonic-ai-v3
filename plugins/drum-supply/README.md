# Drum Supply Headquarters 0.2.0

Omega House Studio LLC sample-based Windows x64 VST3 instrument. Local engineering candidate; commercial and FL Studio acceptance are separate gates. The visible editor heading is Drum Supply Headquarters; the stable host/binary product name remains Omega Drum Supply.

Seven embedded starter one-shots, user WAV/AIFF loading, 16 voices, sample shaping, three global macros, cached waveform, A/B kits, v2 state, local kit presets and portable kits are implemented. Execution results and limitations are recorded in `evidence/SAMPLER_VERIFICATION.md`, not inferred from this feature list.

The creator confirmed ownership and commercial-plugin redistribution permission for the supplied source WAVs on October 19, 2026. Exactly seven files are embedded unchanged. Their slot classifications and musical approval are provisional; see `Assets/origin-manifest.json`.

The earlier sample-free synthesis-only requirement is superseded by the supplied revision. Synthesis code and original wrapper sources are preserved in `legacy/0.1.0`; `Source/DrumEngine.h` and its numerical tests remain available. The old source does not run as an additional live mode in 0.2.0. Version-1 state migrates the four controls to the sample starter kit and cannot reproduce the old synthesized sound.

## Use and build

- `docs/QUICK_START.md`: play, load/relink, shape, save and compare.
- `docs/IMPLEMENTATION_CONTRACT.md`: sample limits, threading/lifetime model, automation, MIDI, state migration, container specification and budgets.
- `docs/INSTALLATION.md`: local staging, cache backups, rebuild, upgrade/rollback and removal.
- `docs/FL_STUDIO_ACCEPTANCE.md`: unexecuted native host acceptance matrix.
- `THIRD_PARTY_LICENSES.md` and `notices/`: dependency notices and unresolved release eligibility.

Build: `./scripts/build-windows.ps1 -Jobs 1`. This uses local toolchain discovery, C++20/MSVC/CMake/Ninja and SHA-256-pinned JUCE 8.0.16-security. `-CoreOnly` builds the preserved synthesis checks and new sampler numerical checks without JUCE. Run `python scripts/run-sampler-checks.py` for processor boundary checks, native component snapshots, listening renders and callback percentiles. Validator commands and their exact artifact hashes belong in the verification report.

Runtime audio uses no Sonic API, account, network provider, marketplace or cloud library. Host state and ordinary presets reference managed samples in `%APPDATA%/OmegaHouse/DrumSupply/Samples`; use portable export to move personal samples to another machine. Factory samples are embedded. Portable export requires the user to confirm rights for every sample in both banks.

Do not infer commercial readiness, listening approval, clean-machine installation, native DPI behavior or FL Studio compatibility from a successful compile, screenshot or validator.
