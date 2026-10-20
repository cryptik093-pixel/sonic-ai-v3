# Known issues and acceptance limits

- CPU qualification has failed on the development laptop; the final measured values and gate state are in TEST_REPORT.md. No real-time deadline or dropout guarantee is claimed. Evaluate Eco with reduced voices/larger buffers until profiling and controlled reference testing resolve this gate.
- Full FL Studio scan/play/automation/project recall/export remains NOT_TESTED. Native tests are separate.
- Factory sounds and morph quality need human listening approval.
- Automated editor lifecycle/scaling and visible capture do not cover every mouse gesture, file dialog, focus edge case or DAW automation interaction. G09 remains pending.
- Only stereo 32-bit host audio is supported; mono bus arrangements and 64-bit samples are intentionally rejected. The adapter accepts 8-384 kHz; tested subsets are recorded in reports.
- Patch text names/descriptions and active voice phase are not native sound-state fields. All 15 sound parameters persist. Export JSON to retain patch labels.
- Meter values require the host to forward output parameter changes. Trait visualization is not an audio spectrum.
- Setup is unsigned and requests administrator access for the documented system VST3 location. Its non-admin payload fixture can be tested automatically; actual elevated UAC/Windows Installed Apps behavior remains untested unless separately recorded.
- Existing installation bundles are preserved rather than overwritten. The guarded uninstaller refuses a modified/unfamiliar bundle. Export user patches outside the installed bundle.
- Build reproduction requires free MSVC Build Tools and Windows SDK. Exact reproduction commands and pinned SDK archive are provided; the final report records the actual clean-build outcome. External dependency provenance review remains separate; an archive hash is not a Git submodule pin.
