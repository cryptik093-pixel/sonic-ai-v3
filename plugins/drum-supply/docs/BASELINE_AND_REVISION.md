# Baseline and authoritative revision

Prepared October 19, 2026 from local static inspection. No build, validator, host, or listening checks were rerun for this prompt package.

## Revision

The user now wants a small starter set of prequalified drum one-shots plus user sample loading. This supersedes the earlier exclusively sample-free requirement. The sample instrument is the target; a huge factory library and completion of synthesis engines are outside the revised scope.

## Inspected current code

- plugins/drum-supply/Source/DrumEngine.h: existing synthesis core, preserve as previous work.
- Source/PluginProcessor.cpp and .h: JUCE instrument, mono/stereo output, MIDI input, four parameters, JSON state version 1.
- Source/PluginEditor.cpp and .h: department selector, three macro knobs, audition, text peak display. Heading reads DRUM SUPPLY HEADQUARTERS; default size 900x560.
- Tests/DspTests.cpp and Tests/ProcessorTests.cpp: existing test sources, not freshly executed for this package.
- CMakeLists.txt: C++20, project 0.1.0, pinned JUCE 8.0.16-security, Windows VST3 target.
- scripts/build-windows.ps1: uses a sibling Sonic Pocket script to discover the build environment.
- README.md and evidence/verification.md: historical documentation. Their execution claims differ in recency; neither replaces fresh verification of the current artifact.

Current source supports seven synthesized departments, global body/character/space parameters, selected-department audition on MIDI 60, GM kit routing, and versioned state. Current processor reports one program named Current Sound. The inspected editor has no sample loader, waveform, preset browser, A/B, or export interface. Sample playback and the expanded completion features in this package are requirements, not claims about implemented functionality.

Stable identities: department, body, character, space; manufacturer OmHs; product OhDs; bundle com.omegahousestudio.drumsupply. Changing from synthesis to samples affects sound recall even if those identifiers remain stable. Migration must explicitly address that behavior.

## Snapshot limits

The source-reference directory is an allowlisted copy of plugin source, tests, scripts, CMake, README, third-party notices, and historical verification notes. It intentionally excludes binaries, render folders, sample packs, dependency trees, private configuration, and unrelated repository work. It does not include the sibling Sonic Pocket helper or installed SDKs. It is useful for upload/review, not a verified self-contained build kit.

No factory samples are supplied in this handoff. Suitable assets and their origin/license evidence must be selected or produced during implementation. The proposed seven sounds are a small starting scope; listening approval remains the user's decision.
