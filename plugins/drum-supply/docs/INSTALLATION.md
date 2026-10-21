
Close FL Studio. Extract the Windows ZIP. Copy the **complete** `DrumShotSupplyCo.vst3` directory into `C:\Program Files\Common Files\VST3\` (Windows may request administrator permission). Do not copy only its internal module. In FL Studio open Options > Manage plugins, perform a verified scan and add the instrument from the generator/plugin picker. Select a pad and play MIDI note 60 to audition that selection, or use the assigned notes below. Clicking a pad auditions when the host is processing audio.

## Default MIDI notes (numeric)
Kick 36; Snare 38; Closed Hat 42; Cymbal 49; Tom 45; Percussion 56; Clap 39; Open Hat 46. Octave labels vary between hosts. Every slot's MIDI NOTE control is editable. Duplicate assignments trigger all matching slots in index order. Unassigned notes are ignored, except 60 auditions the selected slot. Note-off is ignored intentionally for one-shot drums; CC120 clears immediately, CC123 fades voices over 2 ms.
