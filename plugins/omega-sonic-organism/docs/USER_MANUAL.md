# OMEGA SONIC ORGANISM — 1.0.0-rc.2 unqualified candidate

Windows x64 VST3 instrument. Everything needed for sound generation is embedded.
No login, samples, server, network or paid framework is required during playback.
This candidate does not carry a commercial release or FL Studio certification.

## Install and play

Run `Omega-Sonic-Organism-1.0.0-rc.2-Windows-x64-Setup.exe`. Keep its default destination,
`C:\Program Files\Common Files\VST3`. Windows will request administrator access
for that system folder. It refuses to overwrite an existing installation.
In FL Studio open **Options > Manage plugins**, enable **Verify plugins**, and
click **Find installed plugins**. Add **OMEGA SONIC ORGANISM** as an instrument,
and route keyboard or Piano Roll MIDI notes to it. The plugin has a stereo output
and no audio input. Start with a moderate listening level.

The Morph rail continuously changes synthesis traits across Bass, Bells, Lead,
Synth and Percussion. You can move it while holding notes. Anchor buttons set
exact family positions. Energy changes drive, brightness and impact. Motion
controls profile-dependent modulation. Material changes inharmonicity and noise.
Space adds stereo ambience; zero is dry. Output is −24 to +6 dB.

The patch menu contains the 30 configurations from the supplied sound-design
brief. Selecting one sends ordinary parameter edits to the host. Active host
automation retains control: stop playback or disable the relevant automation
when you want to audition a patch unchanged. Modified settings display
**Session / Modified**. Native host project state saves all 15 sound parameters;
JSON patch names/descriptions are independent of native parameter recall.

Use Advanced for envelope scales, mono glide, voice count, Eco/HQ, bend range,
tempo sync, motion rate and mono legato. Glide applies to mono legato passages.
HQ uses 2× oversampled drive and costs more CPU. Both modes report 15 samples
of algorithmic latency. This excludes audio interface and DAW buffering.

Drag knobs vertically. Shift-drag makes fine changes. Ctrl-click restores the
contract default. Value boxes accept exact physical values (dB, ms, Hz or scale).
Tab and arrow keys navigate and adjust the standard controls. Resize maintains
the layout's aspect ratio between 80% and 150%, where the host permits it.
The trait-field drawing represents synthesis controls, not a measured spectrum.
Output level, voice count and last MIDI note/velocity use host-routed meter
parameters. A host that does not relay output parameters may not update meters.

## Save your sound

Save your DAW project for normal recall. LOAD imports a schema-1 Organism JSON
patch. SAVE exports the current parameters using the patch-name field. Invalid
or incomplete JSON is rejected before any sound parameter changes. Factory
JSON files are also included in `presets/factory-v1` for inspection and exchange.
The native file dialog handles destination selection and overwrite prompts.

To remove the Setup-installed copy, use Windows Installed apps or run
`Uninstall.exe` inside its VST3 bundle. Portable script installations use
`tools/uninstall-user.ps1`. It checks the
installation receipt and every file hash before removal, and refuses modified
or unfamiliar bundles. Exported patches and DAW projects remain outside the
installed bundle. The portable ZIP also includes the complete VST3 bundle;
keep its `Contents` directory intact when copying it. The scripts can accept
`-Directory` for a different folder. The scripts default to the per-user VST3
location; for FL Studio use its documented system VST3 folder instead.

Image-Line's installation and verified-scan instructions:
https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_externalplugins.htm

## Evidence and limits

See `evidence` and `COMPLETION_REPORT.md` in the delivery for the actual binary
identity, executed checks, performance conditions and unresolved acceptance
gates. Numerical calibration is not a musical listening review. FL Studio
playback, project reload and export remain unverified until exercised in FL.
