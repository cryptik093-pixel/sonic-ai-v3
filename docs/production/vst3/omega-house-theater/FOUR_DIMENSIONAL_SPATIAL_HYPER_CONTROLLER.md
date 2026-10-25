# Omega House Theater — Four-Dimensional Immersive Sound Dial

Status: LOCKED PRODUCT DESIGN REQUIREMENT — not implemented or acoustically validated.
Date: 2026-10-25
Scope: Omega House Theater VST3 receiver series, including Theater SR.001 / SR.0030 concepts; precise model allocation remains subject to existing product specs.

## Founder-approved experience
A four-dimensional immersive sound dial acts as a spatial hyper-controller: visually a morphing geometric sigil, perceptually a shifting psychoacoustic continuum. Its interface features a rotating tesseract or wireframe occult mandala whose facets refract depth and perspective as spatial coordinates change. The control should morph ambisonic fields, phase relationships, Doppler trajectories, and nonlinear reverberation tails, evoking an expansive, continuous spatial horizon.

## Engineering interpretation and limits
- **4D is an artistic control metaphor**, not a claim of physically reproducing four spatial dimensions or infinite acoustic space.
- Define four normalized coordinates (provisional): azimuthal motion, elevation/depth, diffusion, and temporal warp. Final axes, parameter IDs, ranges and mappings require approval before release.
- Map control gestures through bounded, smoothed, deterministic DSP to spatial encoding/decoding or a documented stereo binaural approximation. Do not advertise ambisonics without a real tested implementation and declared channel layouts.
- Doppler effects require bounded delay/resampling and anti-aliasing; phase manipulation requires mono-compatibility and gain checks; nonlinear reverb must be stable and finite with explicit tail/latency reporting.
- Keep geometric animation on the UI thread, decoupled from audio processing; use lightweight vector rendering and capped frame rate, with reduced-motion/fallback modes.
- Preserve existing parameter IDs, state/presets, dry/wet behavior and host automation compatibility. No silent sonic changes to shipped projects.

## Acceptance gates
1. Approved parameter/state schema and documented control-to-DSP mapping.
2. Automation, save/reopen and preset roundtrip tests.
3. DSP stress across supported sample rates, channel layouts and block sizes; no NaNs, runaway feedback, glitches or unbounded CPU/memory.
4. Objective spatial/phase/mono, Doppler and reverb-tail measurements plus listening evaluation in FL Studio.
5. UI scale/accessibility, performance and audio/UI-thread isolation checks.
6. Release remains NOT TESTED until VST3 validation, host tests and signed packaging evidence exist.

Reference: docs/production/PROFESSIONAL_VST3_PLUGIN_STANDARD_2026-10-16.md.
