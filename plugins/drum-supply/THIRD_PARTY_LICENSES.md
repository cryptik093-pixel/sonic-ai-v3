# Dependency review — local development only

JUCE is reused from the repository's pinned 8.0.16-security archive, SHA-256
`7f75cee28ea4dd216fc49ba6fb57f4baa14729ef97529040d3a99dd04910f166`.
Its checked-in LICENSE.md identifies dual AGPLv3/commercial JUCE licensing.
The VST3 SDK included there identifies MIT licensing; retain notices.
JUCE font/graphics dependencies also require their bundled notices.

Primary sources inspected 2026-10-16:
- https://juce.com/juce-legal/
- https://juce.com/legal/juce-8-licence/
- https://github.com/juce-framework/JUCE/blob/master/LICENSE.md

No licence purchase, fee, commercial-tier eligibility determination, distribution,
contract acceptance, signing or publishing is authorized by this development
milestone. Reuse of the existing local toolchain is not commercial clearance.
Before distribution Danny must settle the applicable JUCE licence, eligibility,
third-party notices and any source-disclosure obligations. Needs legal review.
The preserved standalone synthesis core does not use JUCE or external samples.

## 0.2.0 sample instrument review — October 19, 2026

The existing JUCE stack and pinned archive are retained. Current official sources
were checked again: [JUCE 8 EULA](https://juce.com/legal/juce-8-licence/),
[JUCE legal index](https://juce.com/legal/), and
[Steinberg VST SDK](https://www.steinberg.net/developers/vstsdk/).
The actual included SDK LICENSE.txt identifies the MIT license with 2025
Steinberg copyright. This local text, rather than a generic statement about all
historical VST SDK versions, is the basis for the SDK notice.

| Dependency/content | Local license evidence | Obligation / release state |
|---|---|---|
| JUCE 8.0.16-security | notices/LICENSE.md | Dual AGPLv3/commercial; owner must establish applicable tier/seats and obligations before distribution. PENDING |
| Included VST3 SDK | notices/modules/juce_audio_processors_headless/format_types/VST3_SDK | MIT; retain copyright and permission text |
| HarfBuzz | notices/modules/juce_graphics/fonts/harfbuzz/COPYING | Retain copyright and applicable embedded component notices |
| SheenBidi | notices/modules/juce_graphics/unicode/sheenbidi/LICENSE | Retain included notice |
| PNG/zlib | notices/modules/juce_graphics/image_formats/pnglib/LICENSE and notices/modules/juce_core/zip/zlib/LICENSE | Retain notices; no origin misrepresentation |
| Vorbis codec source compiled with JUCE defaults | notices/modules/juce_audio_formats/codecs/oggvorbis/libvorbis-1.3.7/COPYING | Retain included notice; format is not registered for user import |
| Other embedded JUCE codec/graphics code | Source copyright blocks in the pinned JUCE modules | Final full distribution obligation review PENDING; copied notices are not a legal clearance certificate |
| Seven factory WAVs | Assets/origin-manifest.json | User affirmed ownership and commercial-plugin redistribution authorization in this chat; original bytes retained; listening/category approval PENDING |
| System fonts | Native platform font use; no font files bundled | No downloaded font assets included |

The JUCE EULA's product-owner/tier/seat requirements and products-that-create-products
clause require review in the actual intended distribution context. A sample-file
export is not assumed to be prohibited or cleared by that clause here. No fee,
contract, licence acceptance or distribution action was taken. The implementation
has no activation service, telemetry or paid dependency added by this milestone.
