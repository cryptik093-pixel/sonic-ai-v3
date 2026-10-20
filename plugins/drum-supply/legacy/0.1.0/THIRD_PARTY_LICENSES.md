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
The standalone synthesis core does not use JUCE or external samples.
