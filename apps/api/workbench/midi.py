"""Seeded, scale-aware composition. No external service is needed to make a file."""
import hashlib
import json
import math
import random
import re
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

from .schemas import MidiCommand

TICKS = 480
ROOTS = {k: n for n, k in enumerate(["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"])}
SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "major": [0, 2, 4, 5, 7, 9, 11],
          "dorian": [0, 2, 3, 5, 7, 9, 10], "harmonic_minor": [0, 2, 3, 5, 7, 8, 11]}
TRACKS = [("Melody", 0, 0), ("Chords", 1, 89), ("Bass", 2, 38), ("Drums", 9, 0)]


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")[:70] or "Sonic"


def sha256_file(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def compose(p: MidiCommand) -> list[dict]:
    rng = random.Random(p.seed)
    scale, root = SCALES[p.scale], ROOTS[p.key]

    def degree(n, octave=5):
        return 12 * octave + root + scale[n % 7] + 12 * (n // 7)

    notes = []

    def add(track, pitch, start, duration, velocity):
        # Constrain humanization to the arrangement boundary; every note receives an off.
        start = max(0, min(p.bars * 4 - 0.1, start + rng.uniform(-0.018, 0.018)))
        notes.append({"track": track, "pitch": int(pitch), "start": round(start, 5),
                      "duration": round(min(duration, p.bars * 4 - start), 5),
                      "velocity": max(25, min(120, velocity + rng.randint(-6, 6)))})

    mood_progressions = {
        "dark": [0, 5, 6, 4],
        "hopeful": [0, 3, 4, 0],
        "dreamy": [0, 5, 3, 4],
        "tense": [0, 6, 2, 6],
        "uplifting": [0, 3, 4, 0],
    }
    if p.mood != "neutral":
        progression = mood_progressions[p.mood]
    else:
        progression = [0, 5, 3, 4] if p.scale == "major" else ([0, 3, 5, 4] if p.style == "soul" else [0, 5, 2, 6])
    motifs = {
        "neutral": [0, 2, 1, 4, 2, 1, 0, 2],
        "dark": [0, 3, 2, 6, 5, 3, 2, 0],
        "hopeful": [0, 2, 4, 5, 4, 2, 4, 0],
        "dreamy": [0, 4, 2, 6, 4, 2, 1, 0],
        "tense": [0, 6, 2, 5, 3, 1, 4, 0],
        "uplifting": [0, 2, 4, 6, 5, 4, 2, 0],
    }
    motif = motifs[p.mood]
    if p.seed % 3 == 1:
        motif = [2, 1, 0, 4, 3, 2, 1, 0]
    elif p.seed % 3 == 2:
        motif = [0, 4, 2, 1, 0, 2, 4, 2]
    rhythms = {"sparse": [(0, 1.35), (2.5, 0.7)],
               "balanced": [(0, .7), (.75, .4), (1.5, .8), (3, .7)],
               "busy": [(0, .45), (.5, .4), (1.25, .45), (2, .7), (3, .35), (3.5, .35)]}
    previous = [degree(0), degree(2), degree(4)]
    for bar in range(p.bars):
        chord_degree = progression[(bar // (2 if p.bars >= 8 else 1)) % 4]
        chord = [degree(chord_degree + n, 4) for n in ([0, 2, 4, 6] if p.style == "soul" else [0, 2, 4])]
        candidates = []
        for inversion in range(len(chord)):
            voiced = sorted(chord[inversion:] + [n + 12 for n in chord[:inversion]])
            for shift in (0, 12):
                candidate = [n + shift for n in voiced]
                if min(candidate) >= 45 and max(candidate) <= 79:
                    candidates.append(candidate)
        chosen = min(candidates, key=lambda c: sum(abs(n - previous[min(i, len(previous)-1)]) for i, n in enumerate(c)))
        previous = chosen
        for j, note in enumerate(chosen):
            add("Chords", note, bar * 4 + j * .025, 3.7 - j * .025, 60 if p.style == "cloud" else 70)
        bass_pitch = degree(chord_degree, 2)
        if bass_pitch > 47:
            bass_pitch -= 12
        for beat, length in ([(0, 1.8), (2.5, 1.25)] if p.style == "trap" else [(0, 3.65)]):
            add("Bass", bass_pitch, bar * 4 + beat, length, 88)
        for j, (beat, length) in enumerate(rhythms[p.density]):
            if bar % 4 == 3 and j == 1:
                continue  # Leave a response breath at the end of each phrase.
            d = chord_degree + motif[(j + (bar % 2) * 4) % len(motif)]
            if bar == p.bars - 1 and j == len(rhythms[p.density]) - 1:
                d = 7  # A tonic landing, not a random final note.
            pitch = degree(d, 5)
            while pitch > 88:
                pitch -= 12
            swing = .08 if p.style == "soul" and beat % 1 == .5 else 0
            add("Melody", pitch, bar * 4 + beat + swing, length, 88 if j == 0 else 74)
        for beat in [0, 1.5, 3.25] if p.style == "trap" else [0, 2.5]:
            add("Drums", 36, bar * 4 + beat, .12, 103)
        for beat in [2] if p.style != "soul" else [1, 3]:
            add("Drums", 38, bar * 4 + beat, .12, 94)
        for i in range(8):
            add("Drums", 42, bar * 4 + i * .5, .08, 52 if i % 2 else 66)
        if p.style == "trap" and bar % 4 == 3:
            for beat in [3.25, 3.75]:
                add("Drums", 42, bar * 4 + beat, .06, 48)
    return notes


def conductor(p):
    return [mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(p.bpm)),
            mido.MetaMessage("time_signature", numerator=4, denominator=4)]


def note_track(notes, name, channel, program, end, metadata=()):
    track = mido.MidiTrack([mido.MetaMessage("track_name", name=name), *metadata,
                            mido.Message("program_change", channel=channel, program=program)])
    events = []
    for n in notes:
        if n["track"] != name:
            continue
        on = round(n["start"] * TICKS)
        off = max(on + 1, round((n["start"] + n["duration"]) * TICKS))
        events += [(on, 1, mido.Message("note_on", channel=channel, note=n["pitch"], velocity=n["velocity"])),
                   (off, 0, mido.Message("note_off", channel=channel, note=n["pitch"], velocity=0))]
    last = 0
    for tick, _, message in sorted(events, key=lambda e: (e[0], e[1])):
        track.append(message.copy(time=tick-last))
        last = tick
    track.append(mido.MetaMessage("end_of_track", time=max(0, end-last)))
    return track


def render_preview(notes, bpm, bars, path):
    sr, seconds_per_beat = 22050, 60 / bpm
    signal = np.zeros(int((bars * 4 * seconds_per_beat + .5) * sr), dtype=np.float32)
    rng = np.random.default_rng(0)
    for n in notes:
        length = n["duration"] * seconds_per_beat
        if n["track"] == "Drums":
            length = .22 if n["pitch"] == 36 else .12
        t = np.arange(max(1, int(length * sr))) / sr
        frequency = 440 * 2 ** ((n["pitch"] - 69) / 12)
        if n["track"] == "Drums":
            if n["pitch"] == 36:
                sound = np.sin(2 * np.pi * (48 * t + 7 * (1-np.exp(-t*30)))) * np.exp(-t*20)
            else:
                noise = rng.uniform(-1, 1, len(t))
                sound = (noise - np.roll(noise, 1)) * np.exp(-t * (55 if n["pitch"] == 42 else 25)) * .3
        else:
            attack = np.minimum(t / .012, 1)
            release = np.minimum((length-t) / .05, 1)
            decay = np.exp(-t * (1.8 if n["track"] == "Melody" else .5))
            sound = (np.sin(2*np.pi*frequency*t) + .22*np.sin(4*np.pi*frequency*t)) * attack * release * decay
        start = round(n["start"] * seconds_per_beat * sr)
        end = min(len(signal), start + len(sound))
        gain = {"Melody": .22, "Chords": .075, "Bass": .23, "Drums": .23}[n["track"]]
        signal[start:end] += sound[:end-start] * gain * n["velocity"] / 127
    peak = float(np.max(np.abs(signal)))
    if peak > 0:
        signal *= .85 / peak
    sf.write(str(path), signal, sr, subtype="PCM_16")


def generate(p: MidiCommand, folder: Path, production_brief: dict | None = None):
    notes = compose(p)
    prefix = f"{slug(p.title)}_{p.key.replace('#', 'sharp')}_{p.scale}_{p.bpm}BPM"
    song = mido.MidiFile(type=1, ticks_per_beat=TICKS)
    song.tracks.append(mido.MidiTrack([mido.MetaMessage("track_name", name="Tempo"), *conductor(p),
                                       mido.MetaMessage("end_of_track", time=p.bars*4*TICKS)]))
    for name, channel, program in TRACKS:
        song.tracks.append(note_track(notes, name, channel, program, p.bars*4*TICKS))
        part = mido.MidiFile(type=0, ticks_per_beat=TICKS)
        part.tracks.append(note_track(notes, name, channel, program, p.bars*4*TICKS, conductor(p)))
        part.save(folder / f"{name}.mid")
    song.save(folder / f"{prefix}.mid")
    render_preview(notes, p.bpm, p.bars, folder / "Audition.wav")
    brief = production_brief or {
        "schema_version": "sonic.production-brief/1.0",
        "compiler": "structured_controls_v1",
        "interpretation": "structured_controls",
        "source_prompt": p.prompt,
        "resolved_parameters": {field: getattr(p, field) for field in ("title", "key", "scale", "style", "mood", "bpm", "bars", "density", "seed")},
        "assumptions": [],
        "warnings": [],
    }
    source_id = f"brief:{p.request_id}"
    part_ids = {name: f"{p.request_id}:{name.casefold()}" for name in ("Melody", "Chords", "Bass", "Drums")}
    arrangement_name = f"{prefix}.mid"
    lineage = {
        "standard_id": "OH_METADATA_PACKAGING_LINEAGE_V1",
        "standard_reference": "docs/knowledge/metadata/METADATA_PACKAGING_LINEAGE_V1.md",
        "source": {
            "asset_id": source_id,
            "type": "producer_brief" if p.prompt else "structured_controls",
            "storage": "embedded_in_Composition.json",
            "rights_status": "not_assessed",
        },
        "outputs": [
            {"asset_id": part_ids[name], "artifact": f"{name}.mid", "role": name.casefold(), "created_from": [source_id], "included_in": [f"{p.request_id}:arrangement"]}
            for name in ("Melody", "Chords", "Bass", "Drums")
        ] + [
            {"asset_id": f"{p.request_id}:arrangement", "artifact": arrangement_name, "role": "multitrack_arrangement", "created_from": [source_id], "includes": list(part_ids.values())},
            {"asset_id": f"{p.request_id}:audition", "artifact": "Audition.wav", "role": "synth_audition", "created_from": [f"{p.request_id}:arrangement", source_id]},
        ],
    }
    for asset in lineage["outputs"]:
        path = folder / asset["artifact"]
        asset["bytes"] = path.stat().st_size
        asset["sha256"] = sha256_file(path)
    composition = {
        "schema_version": "sonic.composition/1.0",
        "engine": "local_algorithmic_composition_v2",
        "request_id": str(p.request_id),
        "rights_status": "not_assessed",
        "parameters": {field: getattr(p, field) for field in ("title", "key", "scale", "style", "mood", "bpm", "bars", "density", "seed")},
        "production_brief": brief,
        "lineage": lineage,
        "notes": notes,
    }
    (folder / "Composition.json").write_text(json.dumps(composition, indent=2, allow_nan=False), encoding="utf-8")
    instructions = (f"# {p.title}\n\n{p.bars} bars • {p.bpm} BPM • {p.key} {p.scale.replace('_',' ')}\n\n"
        "Drag the individual Melody.mid, Chords.mid or Bass.mid into an FL Studio instrument's Piano Roll. "
        "Set the project tempo to the BPM above. Open the combined MIDI through File > Import > MIDI file to import all parts. "
        "Drums use GM notes 36 kick, 38 snare, 42 closed hat; map these to your drum instruments.\n\n"
        "Audition.wav is a simple synthesized rhythm/harmony preview, not a finished or mastered recording. "
        "Replace the audition sounds with your instruments. Keep the seed to reproduce notes; change it for a variation.\n")
    (folder / "FL_Studio_Readme.md").write_text(instructions, encoding="utf-8")
    return {"title": p.title, "engine": "local_algorithmic_composition_v2", "bpm": p.bpm, "key": p.key,
            "scale": p.scale, "style": p.style, "mood": p.mood, "bars": p.bars, "seed": p.seed, "density": p.density,
            "parameters": composition["parameters"], "production_brief": brief, "lineage": lineage, "note_count": len(notes),
            "tracks": [t[0] for t in TRACKS], "notes": notes,
            "summary": f"{p.bars} bars in {p.key} {p.scale.replace('_', ' ')} at {p.bpm} BPM: {p.mood} {p.style} melody, voice-led chords, bass and drums.",
            "next_action": "Audition the phrase, then drag Melody.mid into an FL Studio instrument and choose your sound.",
            "warnings": ["Algorithmic composition; aesthetic quality is a listening decision.", "Audition audio uses simple synth sounds.", *brief.get("warnings", [])]}
