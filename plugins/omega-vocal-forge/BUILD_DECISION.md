# Gate 0 build decision — 2026-10-23

Chosen: separate native Steinberg 3.8.1 VST3 shell with Win32 GUI, reusing the
installed MSVC/CMake/Ninja/SDK workflow. No existing ADLIB93 source is modified.

| Path | Observed basis | Decision |
| --- | --- | --- |
| Reuse ADLIB93 wrapper | Existing C++ DSP/UI, 70 product parameters plus host bypass; JUCE 9.0.4 pinned at 3fb5cbc0340758596dac39f7c8de47d562b4896e; four existing dirty DSP files; separate rc1 candidate | Preserve. License lock selects open-source development and requires licensing review for proprietary/public distribution; no entitlement evidence found. Migrating or copying its wrapper would risk current work. |
| JUCE 9 Starter | Supplied skill requires entity/affiliate eligibility and accepted terms | Not selected; business eligibility and entitlement unverified; no purchase or new terms accepted. |
| iPlug2/iPlug2OOS | Permissive option in supplied handoff; no inspected existing local build established | Viable fallback, but adds a framework fetch/build/bootstrap compared with the already available native SDK route. |
| Direct Steinberg SDK | Local official 3.8.1 SDK, MSVC 19.51, CMake 4.3.1 and Ninja available after environment setup; MIT notice present | Selected for the narrow gain/bypass Gate 1. Windows GUI avoids another framework and compiler-heavy VSTGUI target. |

Steinberg's current license page confirms that VST3 since 3.8 uses MIT with no
fees or membership: https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/VST3+License.html
The downloaded SDK archive is pinned to SHA256
`64965f1b74e08a6d4087a35af7a716f4dcff5852c66ad7ee13f1c47e79c1ab77`.
`tools/verify-sdk.py` compares actual compiler and build-system inputs with it.

Alternative license references checked during this task:
https://juce.com/legal/juce-9-licence/ and
https://github.com/iPlug2/iPlug2/blob/master/LICENSE.txt .
The OOS template is https://github.com/iPlug2/iPlug2OOS .
These alternatives were reviewed, not downloaded, installed, built or selected.

The initial fresh build was intentionally stopped after SDK compilation had
begun so the available compatible local validator could be reused. Completed
objects were retained. A subsequent compile found a missing COM declaration in
the audio probe; adding `objbase.h` fixed it. Logs retain those attempts and the
successful build. The plugin source compiled without that probe-only repair.

Inspected ADLIB93 CMake, dependency lock, processor, parameter catalogue, README,
tests and existing Character/Cleanup diffs. Its current code is richer than the
historical handoff README; documentation and old binaries alone do not prove
the dirty source passes now. No new claim is made about ADLIB93 validation or
compatibility. Gate 2 can evaluate existing pure C++ DSP for reuse after Gate 1
host acceptance, preserving ADLIB93's identity and state contracts.

Initial branch `dev/sonic-organism-v4-20261023` had extensive unrelated changes.
Created `dev/omega-vocal-gate1-20261023` without resetting or checking out over
files. Work is additive under `plugins/omega-vocal-forge`, the extracted supplied
skill, and one new manually triggered workflow. The packaging ZIP is preserved.

Packaged preflight ran and its two unit tests passed. Its shallow discovery and
initial PATH checks missed the nested plugin/toolchain; Git status hit its
8-second timeout. Those limitations are retained in the original preflight JSON.
Explicit Git inspection and the actual native configure/build supersede those
limited hints; they do not alter the supplied script or fabricate a preflight pass.

The Windows helper initialization/discovery timed out on three attempts,
including reinitialization; the final error was `computer-use request timed out:
list_apps`. FL64.exe is running; installed version is recorded separately.
No existing session, routing, plugin scan path, or installed plugin was changed.
