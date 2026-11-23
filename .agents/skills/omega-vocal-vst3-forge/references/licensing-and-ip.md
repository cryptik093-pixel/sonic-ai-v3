# Licensing and IP controls (research reviewed October 23, 2026)

Source references (verify current terms at implementation/release):
- Steinberg VST3 SDK >=3.8 MIT, some VSTGUI material BSD-like: https://steinbergmedia.github.io/vst3_dev_portal/pages/VST%2B3%2BLicensing/VST3%2BLicense
- iPlug2 zlib-like licence and VST3/CMake: https://github.com/iPlug2/iPlug2 ; out-of-source template https://github.com/iPlug2/iPlug2OOS
- JUCE 9 EULA June 17 2026: https://juce.com/legal/juce-9-licence/
- Signalsmith Stretch MIT: https://github.com/Signalsmith-Audio/signalsmith-stretch
- Rubber Band GPL2+ or separate paid commercial licence: https://github.com/breakfastquay/rubberband
- Roland harmony-generation patent US10937447B2 status: https://patents.google.com/patent/US20200105294A1

## Choose framework from verified repo and business facts
1. **Existing build wins.** Preserve an already compiling and legally licensable adlib93 stack instead of migrating for convenience.
2. **JUCE 9** may be fastest for a fresh plugin; its Starter licence is free up to $20,000 annual revenue or funding *across the legal entity and affiliates*, with upgrade requirement upon exceeding threshold. Confirm exact commercial eligibility before selecting it. Educational licence is not permitted for commercial sales. No paid purchase without user authorization.
3. **iPlug2/iPlug2OOS** is preferred when avoiding the revenue-based JUCE condition; pin dependency revisions and verify licences of bundled support libraries. CMake/Windows builds are documented by upstream.
4. Direct **Steinberg VST3 SDK** is an alternative when framework independence outweighs startup speed.

## DSP software
- `Signalsmith Stretch` MIT is a candidate to benchmark for pitch shift. A robust monophonic pitch correction engine is not included automatically.
- Do not embed `Rubber Band` into a proprietary binary without a compatible commercial licence or an explicitly approved GPL strategy.
- Run a bill-of-materials and transitive licence review before distribution. Preserve third-party notices.

## Manufacturer intellectual property
- Clean-room behavioral reimplementation only: no Roland/BOSS source/firmware, DSP binaries, artwork, patches/presets, manual graphics, product naming or logos. Original Omega House graphics and UI.
- A related Roland active US patent, US10937447B2, includes instrument-performance-derived chord/harmony behavior. Architecture changes do not by themselves prove non-infringement. Obtain claim-by-claim freedom-to-operate legal review before commercializing a potentially covered guitar-guided harmony system. MIDI/key-guided harmony can be prototyped but must also be evaluated against the actual claims before release.
- Do not claim exact hardware emulation absent physical hardware comparison and rights to market the claim.

## Cost policy
No paid licence, hosting, signing service, DAW/plugin, third-party API, cloud execution, or subscription without approval. A local VST3 does not need a network AI inference API for core audio processing.
