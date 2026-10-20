# FL Studio acceptance - PENDING

No FL Studio scan, playback, save/reopen or export is claimed for this candidate. Native integration tests and pluginval do not substitute for the following session.

1. Preserve existing projects and plugin installations. Run the candidate Setup, using `C:\Program Files\Common Files\VST3`. The installer refuses an existing bundle; preserve it before evaluating a new version. Record Setup/DLL SHA-256 and FL Studio version/edition, Windows version, interface driver, rate and buffer.
2. In Options > Manage plugins enable Verify plugins and Find installed plugins. Save the scan result and log. Instantiate OMEGA SONIC ORGANISM as a Generator. Confirm editor branding/version and both stereo outputs.
3. In a new project enter bass notes, a lead phrase, overlapping same-pitch notes, chords, rapid percussion and sustain/bend where routed. Confirm note release, transport-stop behavior, 1/8/16/32 voice modes and all five anchors. Record listening observations.
4. Automate Morph, Energy, Motion, Material and Space over their complete normalized ranges. Exercise all four morph intervals during sustained notes. Confirm GUI follows host automation and mouse edits record host gestures. Test Output and Advanced controls.
5. Select factory patches, modify values, export/import a JSON patch, and open/close/reopen the editor repeatedly. Check value fields, keyboard focus and resizing. Test file-dialog cancellation and host close while a dialog is open. Record any discrepancy.
6. Save a project as `OSO-RC1-acceptance.flp` in a new test directory. Record exact parameters, close FL Studio, reopen and compare every parameter and resulting audio. Native project state retains parameters, not patch text names or active voice phase.
7. Add three instances and repeat the musical passage. Test 44.1/48/88.2/96 kHz and practical 64/128/256/512/1024 buffers as the driver permits. Log underruns and CPU; do not hide failed combinations.
8. Export a full-song 24-bit WAV with plugin effects and tails enabled. Inspect finite/nonzero/bounded signal, silence, clipping, timing and tails; listen for clicks and stuck notes. Preserve project, WAV, scan log, screenshots, parameter record, environment and SHA-256 hashes.

G11 can become PASS only after this acceptance is actually completed on the exact candidate binary and the evidence is retained. Failure requires repair and regression before approval.

Official Image-Line guidance: https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_externalplugins.htm
