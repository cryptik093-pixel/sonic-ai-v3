# ADLIB-93 FL Studio acceptance

All rows below are **PENDING** until executed in the named host. The presence
of FL64.exe is not proof of compatibility or Producer edition ownership.

Record date, tester, Windows build, exact FL Studio edition/version, audio
device/driver, sample rate, buffer size, VST3 binary SHA-256 and package hash.
Use a disposable project and generated signals or owner-cleared dry vocals.
Preserve existing projects and recordings. Keep screenshots/logs and hashes of
new test renders and the saved acceptance project as evidence.

| Check | Required observation | Status |
|---|---|---|
| Scan and identity | Native x64 effect named ADLIB-93, correct manufacturer, no duplicates/error | PENDING |
| Main buses | Test every layout actually exposed by FL; document unavailable layouts separately | PENDING |
| No external sidechain | Processing requires only main vocal input, no hidden SC/MIDI routing | PENDING |
| Neutral causal path | Init, limiter off, same-sample impulse and unity dry/blend | PENDING |
| Monitoring | Record while monitoring without crash/stuck state; measure device latency separately | PENDING |
| Automation | Main controls, module enables, timing, routing, Throw/Freeze under playback | PENDING |
| Insert bypass | Smooth dry transition; tails decay; output protection still works | PENDING |
| Send bypass | On a send-only mixer route, no newly introduced dry vocal; tails decay | PENDING |
| Host bypass | Observe actual FL wrapper behavior and distinguish it from internal bypass | PENDING |
| Save/reopen editor closed | Full durable parameter/A-B/lock/UI recall, transient states off | PENDING |
| Recall while processing | No half-applied state, deadlock, new dry in Send or held vocal on restore | PENDING |
| Multiple instances | Independent state, no preset/meter contamination | PENDING |
| Freeze and export end | Hold remains audible when intended; release/clear and deliberate export range respected | PENDING |
| Normal render tails | Choose actual FL tail option; no premature truncation, finite upper bound | PENDING |
| Offline consistency | Compare generated-signal real-time/offline WAV with same settings/schedule | PENDING |
| Editor lifecycle | Open/close during playback; momentary Throw releases on lost focus/destruction | PENDING |
| DPI and scaling | Plugin 75/100/150% at Windows100/150/200%; no essential clipping | PENDING |
| Keyboard/accessibility | Visible focus, tab/keyboard/numeric entry and unambiguous held/listen states | PENDING |
| Restart/rescan | Reopen host and saved disposable project using exact tested bundle | PENDING |

Follow the reusable environment's `engineering/vst3/docs/FL_STUDIO_ACCEPTANCE.md`
for evidence format and installation/upgrade precautions. A native validator
PASS does not complete these host-specific rows. A rendered file does not
complete the listening matrix.
