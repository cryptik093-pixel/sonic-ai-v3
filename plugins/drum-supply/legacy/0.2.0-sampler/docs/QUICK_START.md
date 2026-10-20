# Drum Supply Headquarters — engineering candidate

1. Use a new disposable DAW project for evaluation. This Windows x64 bundle is unsigned and commercial/host acceptance is still pending. Keep the 0.1.0 synthesis version and its original sessions separately; the same plugin identity is intentionally preserved.
2. Add Omega Drum Supply as an instrument. Play GM notes (kick 36, snare 38, hats 42/44/46, cymbal 49, tom 45, percussion 37, clap 39), or MIDI 60 for the selected slot. The seven starter sounds are embedded and need no library location.
3. Click a pad to select and audition it. Drop one WAV/AIFF onto a pad or use LOAD / RELINK SAMPLE. Loading is asynchronous. If it fails, the previous sound remains playable and the status line explains the error.
4. Shape the selected sample using tune, gain, pan, start/end, attack/release, low-pass, reverse, mute and solo. BODY, CHARACTER and SPACE affect the whole kit. Output gain is in dB; the peak meter and CLIP warning refer to the actual output. PANIC releases voices and clears the clipping latch.
5. Double-click the kit name to rename. EDITED indicates changes. SAVE KIT writes a `.dhpreset` that references the managed local sample cache; LOAD KIT accepts that file or a portable `.dhkit`. STARTER resets both comparison banks to the factory kit.
6. A/B keeps two complete kits, including sample assignments and parameters. Switching banks preserves edits in the bank you leave. Both banks are included in host state and kit files.
7. Save your DAW project normally. Imported samples are copied into `%APPDATA%/OmegaHouse/DrumSupply/Samples`; leave that folder intact. A missing cached sample appears as MISSING and plays silence until explicitly relinked.
8. To move a kit to another computer, EXPORT PORTABLE. Confirm you have redistribution permission for every sample in both banks. The exported container includes the referenced personal sample files; factory IDs resolve from the plugin itself. A DAW project alone does not carry the sample cache.

Factory samples are supplied by the creator with redistribution authorization recorded in `Assets/origin-manifest.json`. Musical approval and the provisional slot classifications still need the creator's listening review. No online account, Sonic service or internet connection is required by the audio path.
