# Third-party notices

This Windows candidate uses the official Steinberg VST3 SDK 3.8.1. The inspected
local SDK contains the MIT license reproduced in STEINBERG-LICENSE.txt.
Retain it with any binary containing SDK code. The custom editor links the
same distribution's VSTGUI Windows amalgamation; retain VSTGUI-LICENSE.txt.
No JUCE, paid SDK, samples or online service is required for playback.

The Windows installer is built with NSIS 3.11 using its zlib compressor.
The unmodified official compiler archive has SHA-256
`c7d27f780ddb6cffb4730138cd1591e841f4b7edb155856901cdf5f214394fa1`.
The distribution includes NSIS-LICENSE.txt from the unmodified tool archive.
NSIS license information: https://nsis.sourceforge.io/Docs/AppendixI.html

Official source: https://github.com/steinbergmedia/vst3sdk

Local source provenance: existing SDK distribution archive
`plugins/sonic-pocket/build/steinberg-sdk.zip`, SHA-256
`64965f1b74e08a6d4087a35af7a716f4dcff5852c66ad7ee13f1c47e79c1ab77`.
This archive digest identifies the local distribution; it is not a claim that
a specific Git commit was verified. A recursive official Git revision pin and
dependency provenance review remain pending. A hash-verified portable SDK bootstrap is supplied in tools/reproduce-build.ps1. The build script accepts
an explicit OSO SDK directory through its `SdkRoot` argument.

Omega House source is not relicensed under Steinberg's MIT license.
Copyright, trademarks, distribution terms and brand use must receive final
release review. No SDK endorsement or trademark registration is implied.
