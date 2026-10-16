# ADLIB-93 0.1.0 release verification

Internal evaluation candidate. No commercial-readiness or FL Studio compatibility
claim follows from a successful build or offline test.

## Recovery scope

The approved specification, 24 factory recipes, 70 physical parameter IDs,
plugin/class identity and JUCE 9.0.4 dependency pin are preserved. Existing
recordings, FL Studio projects and Sonic applications were not changed by this
release recovery. Only release-blocking corrections were made:

- Reverb feedback now evaluates its existing RT60 equation with signed floating
  point arithmetic. An unsigned exponent previously silenced the return.
- Manual tempo fallback uses the specified 4/4 bar length when host BPM is absent.
- A finite -60 dB branch level remains distinct from the exact mute endpoint.
- Freeze retrigger preserves the audible playhead during its release fade.
- Pending preset and Clear Tails transitions preserve bounded processing and
  avoid prematurely applying incoming settings to the outgoing engine.
- Optional schema-1 preset baseline data preserves Reset after a modified user
  recipe is saved and reopened. Older states remain readable.
- Native editor Save/Cancel buttons use explicit JUCE KeyPress objects.
- The persistent VST3 host bypass is separated from transient internal bypass
  through JUCE's standard wrapper support. The 70 product IDs remain unchanged;
  the wrapper exports one additional host Bypass parameter.
- The native title uses the actual processor name, and header punctuation uses
  explicit UTF-8 decoding. The original offscreen captures exposed mojibake.

## Executed evidence

The initial integrated core run was 47/50 PASS, **not** a final passing suite.
The failed build and test logs remain under `evidence/`; corrected native Release
build results and integrated acceptance results must supersede them explicitly.

Narrow production-code regressions passed for manual timing, level endpoints and
Freeze retrigger continuity: `evidence/review-regressions/`. Reverb injection and
stereo checks passed at 44.1/48/88.2/96 kHz. All 16 approved mid-band RT60 checks
passed with the original +/-25% tolerance: `evidence/space-regressions/`.
The retained broadband-only results include failures and are not substituted for
the specified mid-band measurement. User-baseline state regression has an actual
pre-correction failure at `evidence/state-preset-baseline-red-current.log`.

Native configure: PASS, `evidence/release-configure-native-corrected.log`.
The optimized clean-start Release build completed with exit 0 at
`evidence/release-build-native-corrected.log`. Its complete source rebuild
superseded the retained failed attempts. After the final two adapter/editor
repairs, the targeted build also completed with exit 0 at
`evidence/release-build-bypass-ui.log`. No framework rebuild was needed.
The optimized build uses
MSVC /O2 /Ob2 /DNDEBUG, with /O1 for JUCE graphics/UI translation units on this
8 GB machine. Remaining compiler diagnostics are warnings, not failed builds.

| Check | Actual result | Evidence |
|---|---|---|
| Integrated core/native CTest | 63/63 PASS, 88.50 s | `evidence/release-tests.log`, `.xml` |
| Final processor/editor rerun after adapter repair | 7/7 PASS, 28.60 s; unchanged core tests not repeated | `evidence/processor-final.log`, `.xml` |
| pluginval strictness 10 | PASS, exit 0, GUI tests enabled; 44.1/48/96 kHz, blocks 64/128/256/512/1024 | `evidence/validation-level10-final/` |
| Official Steinberg validator | PASS, exit 0; 47 tests passed, 0 failed | same directory, `steinberg-stdout.txt` |
| Bundle mutation check | PASS; complete file manifest unchanged by validation | same directory, `validation.json` |
| Native editor construction/render | PASS at 75/100/150%; corrected text visually inspected | `evidence/editor-final/` |
| Production factory renders | 24/24 completed with finite stereo float32 output; generated 2 s mono tone at 44.1 kHz/128 | `evidence/render-analysis.log`, `build/fixtures-release/analysis.json` |
| Two-engine buffers at 96 kHz | 7,572,616 bytes; <=64 MiB PASS | `Realtime.Budget` output in `evidence/release-tests.xml` |
| Reference-duration DSP timing | FAIL, exit 1; 600 s per mode, 225,000 blocks per mode, all output finite | `evidence/benchmark-reference.json`, `benchmark-machine.json` |

CTest includes one intentional unknown-test-name rejection (`WILL_FAIL`), not
an audio capability. The final seven tests relink the same production shared
code as the final VST3. The 56 core tests and renderer remain unchanged by the
host-bypass/editor-only correction. The validator's count includes its reported
unsupported 64-bit sample-processing cases; the actual supported audio sample
format is float32 in a Windows x64 binary. No double-precision DSP claim is made.

The earlier strictness-10 run passed pluginval but failed Steinberg with
46 passed/1 failed (`Parameter Bypass persistence`). It remains in
`evidence/validation-level10/`, with its earlier bundle retained at
`dist/ADLIB93.vst3`. **Do not install that earlier candidate.** The corrected
candidate below is the one that passed both validators.

## Exact verified candidate

- Bundle: `dist/rc1/ADLIB93.vst3`.
- Binary: `Contents/x86_64-win/ADLIB93.vst3`, 4,716,032 bytes, PE machine 0x8664.
- SHA-256: `fe6c2fb05a4742ed2fd71d87c87f66b2148b2cd58b2abe41fa9bb5cf6ab99cd9`.
- Bundle manifest SHA-256:
  `081d1193b337e4e6306c411e09776096666feb628bdddeffb0f5067c112cdccb`.
- Display name ADLIB-93, manufacturer Omega House Studio LLC, version 0.1.0;
  original class IDs and all 70 product parameter IDs preserved.
- `evidence/release-artifact-final.json` records the separate copy; its binary
  bytes equal the compiled build output. Only bundle/binary basenames differ.

Packaging uses `scripts/package.ps1` with that bundle and the final schema-2
validation report. It rechecks tool logs, complete bundle hashes, copied notices
and ZIP contents and writes new archives plus a SHA-256 file under `dist/`.
Packages are explicitly **INTERNAL_EVALUATION_ONLY**. No installation, signing,
public upload or license purchase is performed by staging.

## Executed commands

In `plugins/adlib-93` after process-local toolchain setup:

```powershell
cmake --preset windows-release -DADLIB93_BUILD_PLUGIN=ON '-DCMAKE_CXX_FLAGS_RELEASE=/O2 /Ob2 /DNDEBUG' '-DCMAKE_C_FLAGS_RELEASE=/O2 /Ob2 /DNDEBUG'
cmake --build --preset windows-release --target ADLIB93_VST3 adlib93_processor_tests adlib93_tests adlib93_render adlib93_benchmark
ctest --preset windows-release --output-on-failure --output-junit <absolute-evidence/release-tests.xml>
cmake --build --preset windows-release --target ADLIB93_VST3 adlib93_processor_tests
ctest --preset windows-release -R '^Processor\.' --output-on-failure --output-junit <absolute-evidence/processor-final.xml>
./build/windows-release/adlib93_benchmark.exe --sample-rate 48000 --block-size 128 --seconds 600 --mode both --paced true --report evidence/benchmark-reference.json
```

The two JUnit arguments above abbreviate only this checkout's absolute path.
Editor captures used process-local `ADLIB93_CAPTURE_DIR=evidence/editor-release`
and `evidence/editor-final` resolved to absolute paths in the respective runs.
The initial clean-first attempt and subsequent corrections are retained in the
build logs; the successful corrective commands are shown above.

From repository root:

```powershell
.venv/Scripts/python.exe engineering/vst3/skills/omega-vst-qa/scripts/validate_vst3.py --bundle plugins/adlib-93/dist/rc1/ADLIB93.vst3 --pluginval plugins/sonic-pocket/build/pluginval/pluginval.exe --steinberg plugins/sonic-pocket/build/steinberg-validator/bin/validator.exe --output plugins/adlib-93/evidence/validation-level10-final --strictness 10 --timeout 1800
.venv/Scripts/python.exe plugins/adlib-93/scripts/analyze_character.py --renderer plugins/adlib-93/build/windows-release/adlib93_render.exe --output plugins/adlib-93/build/fixtures-release --all-presets
```

The runner records each validator's exact executable, argument vector, exit
status, positive completion text, log hashes and full before/after bundle hashes.
Results are in the table above; the benchmark exit is 1 (FAIL), not a passing
shell-only invocation.

## Acceptance boundaries

Native processor tests exercise production parameter registration, layouts,
state, bypass, meters, editor construction and concurrent recall. Callback
allocation hooks detect C++ new/delete in those exercised paths; they do not
constitute a complete platform allocator or scheduling proof.

Editor captures are native offscreen renders at 75/100/150%, not evidence of
host embedding, physical DPI behavior or complete keyboard interaction.
Generated signal renders establish numerical processing only, not vocal quality.
The coherent-tone analysis calibrated its DFT amplitude to 0.5000000000000405.
Selected folded-bin indicators for factory recipes 4/14/16 were respectively
-52.7919/-53.2321/-28.5586 dB relative to their fundamental. These are limited
whole-preset measurements, not total alias power or an acceptability threshold;
filtering, blend and other effects contribute. No listening PASS follows.
The benchmark times the production DSP engine; it excludes JUCE wrapper,
correlation metering, host overhead and audio-driver scheduling. Short or unpaced
runs cannot pass the ten-minute reference performance gate.

The completed paced run on Windows 10 Pro / i5-4310U / 8 GB at 48 kHz/128
measured steady p50/p99/max **1.0554/4.572/184.963 ms**, and transitions
**1.235/4.155/63.3739 ms**. Each mode ran 600 wall-clock seconds. The unchanged
limits are p99 <0.5333 ms steady, <1.0667 ms transitions, and max <2.6667 ms.
**This is a failed P1 performance gate, not a missing compiler/dependency.**
No timing threshold was revised, outlier discarded or host performance inferred.
Existing user processes and machine power/priority settings were preserved.

A bounded production-module probe (`evidence/timing-profile.cpp`, `.json`,
`timing-profile-build.log`) measured 1,000 unpaced 128-frame blocks per module.
Median block costs were Cleanup .1594, Character .1753, Movement .1537,
Echo .1832, Space .2203, Output .0261 and whole Transitions .9987 ms.
These isolated inputs differ from the full chain and the probe is explicitly
not an acceptance test. Cost is spread across modules; its timing variation
does not establish a single cause or separate arithmetic cost from OS scheduling.
Further optimization and a passing reference rerun are required before release.
No speculative DSP rewrite was introduced to mask this failure.

## Open commercial gates

- FL Studio loading, routing, automation and save/reopen: NOT VERIFIED.
- Owner listening and factory-preset musical acceptance: PENDING.
- Clean-profile installation and host/DPI interaction: PENDING.
- P1 reference-duration performance acceptance: **FAIL** on the measured machine;
  optimization and a passing rerun are required. Host callback/device scheduling
  remains unverified independently.
- Applicable JUCE distribution route, all notice/source obligations and product
  distribution approval: PENDING owner review. No license was purchased or
  commercial terms accepted by this engineering task.

Use `FL_STUDIO_CHECKLIST.md`, `AUDITION.md` and `THIRD_PARTY_NOTICES.md` for these
remaining checks. Do not publish an internal evaluation package as a commercial
release while these gates remain open.
