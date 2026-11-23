# OHS-TRIDENT-2026-01 recovery and integration plan

This task owns only `engineering/trident/vst3/`. Existing staged, modified,
untracked, installed plugin, theme and audio files are protected.

1. Capture current Git HEAD, branch, expanded porcelain inventory, remotes,
   worktrees, binary patches and index outside the source tree. Inventory is
   evidence, not an instruction to stage or publish those files.
2. Snapshot current product source into a fresh run directory. Bind the build
   to file hashes as well as HEAD: HEAD alone cannot reproduce dirty source.
3. Reuse the existing process-local Windows x64 toolchain. Build Release with
   one worker, local dependencies, plugin copying/linking disabled and no install.
4. Start with EQ's existing engine, adapter/state and exact-DLL response tests.
   Add deterministic synthetic audio capture against that same DLL. Compare
   repeat runs and the pre-existing binary separately; neither makes the old
   binary an approved sonic golden. Never promote a new golden automatically.
5. Record every command, return code, tool identity, source and bundle hashes.
   Missing host, CPU, design and approved-golden evidence blocks release claims.
6. Qualify ADLIB V1 next using existing wet-send, bypass, tails, state and preset
   tests. Keep existing four-file CPU work and V2 experiments separate. Recover
   the V500 specification before choosing a block; do not equate VE500 with it.
7. Reconcile Organism instrument versus V4 effect and the approved V5 contract
   before altering DSP. Do not treat the separate effect as V5 instrument work.
8. Review open PRs individually against canonical main. Do not wholesale merge
   this divergent recovery branch or duplicate existing FORGE/event/commerce work.
   Continue through the established PR review process; no production migration,
   deployment, store mutation, installed-plugin replacement or theme edits.

No task commit may include the existing index. A later focused integration must
use an isolated development branch and only explicitly reviewed task paths.
