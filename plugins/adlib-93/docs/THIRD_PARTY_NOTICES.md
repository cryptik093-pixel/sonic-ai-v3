# Dependency and distribution review

Internal development/evaluation only. Commercial distribution, signing and
public release are PENDING owner review. No paid license or contractual
commercial terms were accepted by this engineering task.

## JUCE

JUCE 9.0.4, revision `3fb5cbc0340758596dac39f7c8de47d562b4896e` is pinned in
`dependencies.lock.json`; archive SHA-256 is recorded there and checked by
CMake when fetched. Source `LICENSE.md` provides AGPLv3 or applicable commercial
terms. The owner must determine the applicable route and satisfy all associated
obligations before distribution. Do not infer eligibility from compilation.

Retain the exact dependency `LICENSE.md` and `JUCE.spdx.json` inventory, plus the
applicable bundled third-party copyright/license texts with a staged package.
An SPDX inventory is an index; it is not a substitute for required notices.
Source location after the standard fetch is the build's `_deps/juce-src` tree;
a verified local-source override uses the explicit path from CMakeCache.txt.

## Steinberg VST3

The format wrapper uses the SDK bundled with the pinned JUCE source. Review and
retain the actual SDK license and notices from
`modules/juce_audio_processors_headless/format_types/VST3_SDK` or the path present
in that pinned tree. Record its version from source, not a guessed online SDK
version. Trademark/branding usage must be reviewed independently of compilation.

## Validation tools

pluginval and Steinberg validator are external development tools, not embedded
runtime services. Retain their executable identities/hashes, invocation logs
and their own applicable notices when redistributing those tools. Evaluation
packages need not redistribute validator executables.

## Omega House source

Omega House Studio LLC product source and approved specification are preserved.
This document does not assign a new source license or assert that a source
archive alone satisfies a chosen distribution license. Review all resulting
obligations, notices and source availability before public/proprietary release.
