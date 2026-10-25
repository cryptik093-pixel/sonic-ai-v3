# ADLIB93 circular-buffer candidate

This is a tested **core-source patch experiment**, not an integrated or release-qualified VST3. It changes six circular-buffer index expressions in Echo.cpp and Space.cpp, preserving DSP arithmetic, public headers, parameters, presets and state formats.

A fresh Windows MSVC Release core build passed 56/56 CTest tests. All 32 baseline/candidate synthetic render pairs were byte-identical: every existing factory preset at 48 kHz, plus presets 1 and 24 at 44.1/96 kHz with 64/511-frame partitions. Each render includes a 0.1-second synthetic input and five-second tail, exercising the four-second delay wrap.

The retained baseline's sustained 48 kHz/128-frame, 600-second-per-mode test collected 225,000 blocks per mode with finite output and unchanged inputs. Its CPU gate **failed**: steady/transition p99 9.0328/8.5643 ms versus a 2.66667 ms block deadline. This is custom DSP-core wall timing, not an FL Studio callback. Memory use was 89% before and 87% after; this does not establish the cause of stalls.

Four short unpaced ABBA comparisons retain CPU budget PENDING. Candidate medians were lower in both repetitions; tail timings varied and do not qualify sustained/native performance. The candidate has not received a sustained CPU run, native VST3 wrapper build, FL Studio acceptance, approved-golden listening or release approval.

## Source and reproduction boundary

Patch paths are relative to the frozen ADLIB product root. Verify the exact baseline manifest SHA-256 in EVIDENCE.json before applying the patch to a separate source copy. The complete source is the preserved Windows snapshot, not newly reconciled main-branch product source. Do not apply this patch to the protected dirty checkout or installed plugin.

Full source manifests, build commands/logs, JUnit, WAVs, short comparisons and the executed run_candidate.py are retained at:
`C:\Users\david someone\Desktop\OHS-TRIDENT-2026-01\sprint-20261025-0618\`.

Inputs came from `adlib-core-baseline-01/source`, preserved from protected revision ebc308af plus its recorded dirty source. The candidate's complete source manifest and compiler/executable identities are in EVIDENCE.json. This is not clean-clone/CI qualification.

Next: reconcile the complete preserved product source in an isolated branch, apply this exact patch, profile remaining DSP cost, then run sustained native/FL Studio qualification and listening approval. No installation, store change, merge or deployment is part of this experiment.
