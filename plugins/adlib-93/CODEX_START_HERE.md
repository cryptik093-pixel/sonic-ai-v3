# ADLIB-93 — Codex execution prompt

Extract the entire handoff archive. Open the intended development repository in Codex. Attach or make accessible both `docs/superpowers/specs/2026-10-15-adlib93-design.md` and `docs/superpowers/plans/2026-10-15-adlib93-implementation.md`. The ZIP contains design documents only, not an installable plugin. Do not paste a `sandbox:` link into Codex as though it were a filesystem path on your Windows computer.

Paste the following prompt once you approve the enclosed implementation plan:

---

Build **Omega House ADLIB-93**, the Windows x64 VST3 vocal multi-effects plugin defined by the attached approved engineering specification and staged implementation plan.

The specification was approved by Daniel Sutton on October 15, 2026. That approval supersedes its historical review-pending status text. This prompt authorizes implementation of the enclosed plan in this Codex workspace, task by task. Preserve the agreed product, 24 exact factory presets and pedal interface. The plan's generated code paths are relative to the ADLIB-93 project root; map them explicitly if this repository already has a suitable structure.

ADLIB-93 processes incoming or recorded human **ad-lib vocal tracks**. It does not generate voices, words or ad-libs. Its visual design is an original 1993-inspired vocal multi-effects pedal: charcoal metal/rubber, bone-white labels, cyan accents, amber display, two rows of five knobs and Bypass/Throw/Freeze controls. It is not a website or a cloud AI service.

First read the complete specification and plan, applicable AGENTS.md instructions and the actual advertised VST/plugin-builder skill if one is available. Use `superpowers:executing-plans` if available for sequential execution. Do not claim a skill exists when it does not, and do not make its absence a blocker when ordinary JUCE/C++ development is possible. Do not dispatch subagents unless separately authorized by the user or applicable repository instructions.

Apply the selected Sonic Chat Orchestrator guidance to preserve scope, resume from concrete checkpoints and report verified outcomes. Apply Codex Coordinator's single-native-task default. If this repository already enables coordination, read its project marker first and follow the installed Coordinator operating instructions before claims/writes; do not create a parallel task board or extra tasks merely because the plugin is installed. Establish any isolated project location before coordinated writers begin; do not switch a shared coordinated branch/worktree. Temporal was reviewed for this handoff: the VST3 runs locally with no durable server workflow requirement, so do not add Temporal SDKs, workers, a server or Temporal Cloud to the audio plugin. Any future offline orchestration service is a separately scoped project, not a dependency of this build.

Inspect repository architecture, git status and available build/runtime tools before editing. Preserve unrelated changes, source sessions, routing, renders and existing plugin IDs. Create an isolated ADLIB-93 directory/branch where needed; do not rebuild Sonic AI, Omega OS, Tribal Network or Shopify as part of this task.

Use C++17, CMake and JUCE, with exact dependency revisions recorded. The plan proposes official JUCE tag 9.0.4 as the new-project baseline, not a dependency already tested on this machine. Inspect any existing framework pin before changing it. Do not install or purchase paid dependencies. Record licensing requirements; do not invent license eligibility.

Start with a reproducible neutral VST3 scan/load/state build and production-DSP test runner. Then implement the plan in its 13 tasks: core schema/routing, output protection, cleanup, character/movement, echo/diffusion, reverb/ducking, Freeze/transitions, 24 factory/user presets, native pedal UI, integrated validation and packaging. Do not stop at a scaffold, mock UI or placeholder effect. Commit meaningful stages without discarding user changes.

Critical engineering rules:

- Support mono→mono, mono→stereo and stereo→stereo. Define effective Insert/Send overrides without destroying stored values.
- Preserve the original input at Mix=0, use a linear blend, and avoid doubling the direct signal in Send mode. Apply wet pan/width once.
- Parameter snapshots are fixed-size and thread-safe. No allocation/free, blocking locks, file/network calls, logging or GUI operations inside the audio callback, including preset selection, Freeze and Clear.
- Allocate both preset-transition engines and buffers during preparation. Clear memory incrementally, coalesce pending requests and keep playing the active engine until the incoming one is ready.
- Target zero added algorithmic through-path latency and report the actual latency. Intentional echo/double delays remain effects. The output limiter is sample-peak protection, not a true-peak/mastering claim.
- Implement the documented Freeze texture capture, Throw modes, tail policy and transient-state recall behavior. Do not serialize captured vocal audio into presets/projects.
- Implement **all 24 exact preset names and recipes** from the spec, including the clarified active diffusion path in Frozen Tail. Factory presets use complete snapshots; unlisted settings cannot leak from previous presets.
- Every visible control must affect its documented parameter. Meter real measurements. No decorative placeholder processing or fabricated sound-quality claims.

Run meaningful test cycles and the acceptance matrix. Validate dry identity, limiter ceiling, delay timing/ping-pong, reverb decay, linked dynamics, feedback stability, Freeze/clear, state restore, automation, irregular block sizes, allocation discipline and render parity. Benchmark on identified hardware. Use Steinberg's VST3 validator and external pluginval, then actual FL Studio testing where available.

Proceed through every independent task possible without repeatedly asking for confirmation. If Windows, FL Studio, dependencies or owner vocal recordings are unavailable, state the precise missing capability and complete work that does not depend on it. Mark affected checks PENDING; a Linux DSP test is not evidence that the Windows VST3 loads. If a design requirement is technically incompatible, explain the evidence and smallest proposed correction rather than silently changing scope.

Deliver source, pinned build instructions, the actual Windows Release `.vst3` bundle when buildable, the 24 preset definitions, dependency notices and a verification report with commands, outcomes, machine details and PASS/FAIL/PENDING status. Package the bundle directory correctly into a downloadable ZIP. Do not install over an existing plugin or publish/sell the product automatically.

Start now by reporting the actual project/toolchain state and implementing Task 1, then continue through the plan. When finished, distinguish implemented features, verified outcomes and remaining host/listening checks clearly.

---
