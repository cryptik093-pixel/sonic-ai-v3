# Professional VST3 Plugin Engineering Standard — 2026-10-16

**Owner:** Omega House Studio LLC  
**Applies to:** Adlib93, Omega House Melody Maker, Drum Supply Headquarters and subsequent commercial audio plug-ins.  
**Status:** Adopted **documentation and design policy**, **not** proof of implemented DSP, installed build tools, test results, signing, or release approval.

## Authority and provenance
This standard condenses the founder-supplied *Professional VST3 Plugin Field Manual* (October 16, 2026), specifically the supplied excerpt covering platform baseline, frameworks, VST3 architecture, realtime and GUI requirements. The full manual beyond that excerpt has **not** been ingested. Product source, actual host tests, SDK EULAs and current official documentation take priority over unverified claims. Recheck all version-dependent facts at build/release time. Record deviations and rationales.

## Engineering rules (mandatory release gates)
1. **Separation:** DSP is framework-independent C++ with its own tests; model/state schema, plug-in host adapters, GUI/assets, installers, benchmarks and documentation are separate.
2. **Realtime:** Audio callbacks and any realtime-sensitive setup path must not allocate/free, block on mutexes, wait on UI, access disk/network, write logs or perform unbounded operations. Preallocate working memory and use carefully bounded data exchange.
3. **Parameter compatibility:** Publish stable unique parameter IDs, normalized-to-physical unit conversions, smoothing, automation semantics and never silently renumber or repurpose a shipped ID.
4. **State:** Version and validate serialized state and presets; preserve old project recall; test missing/corrupt/newer fields; no migration that silently changes an existing customer's sound.
5. **Host contracts:** Exercise processor/controller separation, accurate latency/PDC, tail reporting, delay-aligned click-safe bypass, enabled/disabled sidechains, supported channel layouts and host transport changes.
6. **Musical events:** For instruments, test note on/off at arbitrary offsets, overlaps, sustain/all-notes-off, note expressions and offline bounce. Sample-offset automation must be accurately supported by the **actual chosen wrapper**; do not assume framework capabilities.
7. **DSP quality:** Test 44.1/48/88.2/96/192 kHz as supported, variable buffer sizes (including 1 and non-powers-of-two), silence, denormals, NaNs/infinities, gain staging/headroom, aliasing, distortion, noise, phase, latency, CPU and memory. Document tolerances and actual pass/fail evidence per algorithm.
8. **GUI:** Support reasonable DPI scaling and resize, accessible labels, readable state, precise adjustment, host automation gestures and meters decoupled from the audio callback (~30–60 Hz UI refresh).
9. **Release:** Maintain tested installer/uninstaller, signed Windows release and Apple Developer ID notarization when supported, trial/licensing behavior, privacy disclosures, EULA/third-party notices, presets, release notes, support and rollback mechanisms. AAX is separate approved scope.
10. **Evidence:** No commercially-ready claim without reproducible builds, automated DSP tests, host smoke tests, scanning/validation, packaging/signing confirmation and human listening/producer acceptance. CI logs and artifact hashes must back release decisions.

## October 2026 stack decision (pending project confirmation)
- Preferred: **JUCE 9 + CMake + standalone C++ DSP** for fast multi-platform commercialization.
- Alternatives: raw Steinberg SDK for precise VST3 features; iPlug2 for lean permissive multi-format; CLAP as an additional target when host demand supports it; Faust/Cmajor for algorithm prototyping.
- Current source excerpt states VST3 SDK 3.8.1 under MIT after 3.8; JUCE 9.0.3 as of Oct 7, 2026. **Reverify** release numbers, JUCE commercial eligibility/EULA and CLAP/sample-accurate abstraction support before shipping.
- VST2 is not a new-product target. AU/AAX/CLAP support is **not** automatically implied by VST3 support.

## Suggested ownership
- **Sonic AI V3:** production assistance, deterministic validation reports, test orchestration and artifact lineage; **no unverified direct access to an active DAW/desktop environment**.
- **Omega House OS:** policy, milestones, commercial release sign-offs, product documentation, licensing and evidence references.
- **Codex/plugin development:** implement against this standard, make minimal targeted edits, build/test promptly, report exact artifacts and blockers instead of repeated speculative redesign.

## Minimum pre-release evidence packet
- Code commit SHA / toolchain versions / dependency license list.
- Parameter ID/state schema, migration fixtures and preset roundtrip report.
- DSP unit/property tests, numerical stress tests, sample-rate and block-size matrix.
- VST3 validator/plugin scanner and DAW load/automation/save-reopen/offline-bounce tests.
- Audio quality measurements plus subjective producer listening notes.
- Signed distributables/install/uninstall evidence, download hash, EULA and support path.
- Explicit verdict: **PASS**, **FAIL**, or **NOT TESTED** for each gate.

This document is an operating requirement; publishing it does not change runtime behavior.