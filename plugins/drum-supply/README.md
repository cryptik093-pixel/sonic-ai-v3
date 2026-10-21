# Drum Shot Supply Co. 0.3.0
Omega House Studio LLC / Windows x64 VST3 instrument.

Eight MIDI-triggered synthesized drums using the preserved Drum Supply modal oscillator/noise engine. Factory synthesis works without sample playback. Optional authorized WAV/AIFF layers, full kit state, native resizable editor and 181 host parameters. This is a local evaluation build; see the included QA report for actual validation and outstanding host acceptance.

## Install
Close FL Studio. Extract the Windows ZIP. Copy the **complete** `Drum Shot Supply Co..vst3` directory into `C:\Program Files\Common Files\VST3\` (Windows may request administrator permission). Do not copy only its internal module. In FL Studio open Options > Manage plugins, perform a verified scan and add the instrument from the generator/plugin picker. Select a pad and play MIDI note 60 to audition that selection, or use the assigned notes below. Clicking a pad auditions when the host is processing audio.

## Default MIDI notes (numeric)
Kick 36; Snare 38; Closed Hat 42; FX / Custom 49; Tom 45; Percussion 37; Clap 39; Open Hat 46. Octave labels vary between hosts. Every slot's MIDI NOTE control is editable. Duplicate assignments trigger all matching slots in index order. Unassigned notes are ignored, except 60 auditions the selected slot. Note-off is ignored intentionally for one-shot drums; CC120 clears immediately, CC123 fades voices over 2 ms.

## Kits and samples
Double-click kit name to rename; SAVE KIT writes .dhpreset; LOAD KIT recalls it. A/B retains two complete comparisons. EXPORT PORTABLE writes .dhkit with optional user layers after the user confirms redistribution rights. Factory embedded layers need no external file paths. Imported samples are copied to managed hash storage under the user's application data folder; portable export includes both banks. Sample blend defaults to 0 (pure synthesis). At 1 it selects the optional sample layer alone. Missing optional samples are explicit and never silently substituted.

## Build and test
On Windows x64 install Visual Studio Build Tools with C++ and Windows SDK, CMake >=3.24, Ninja and Python 3. Run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-windows.ps1 -Jobs 1` from the source folder. The script locates MSVC and pins JUCE 8.0.16-security with SHA-256. Internet is needed for the first JUCE dependency fetch; an existing verified sibling cache is optional. Build output: `build/OmegaDrumSupply_artefacts/Release/VST3/Drum Shot Supply Co..vst3`. `ctest --test-dir build --output-on-failure` runs the production DSP/processor checks. `python scripts/run-release-checks.py` retains the exact module and source hashes, renders and editor probes. `python scripts/package-candidate.py` stages and verifies both ZIPs after successful functional tests.

Read docs/MANUAL.md, docs/RECOVERY_AND_COMPATIBILITY.md and Verification/REPORT.md. FL Studio project round trips, human listening, display scaling and clean-machine installation require the named host checks; component tests alone do not establish those results.
