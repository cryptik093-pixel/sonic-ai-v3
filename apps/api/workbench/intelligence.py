"""Evidence-first compiler from producer language to reproducible composition inputs."""
from __future__ import annotations

import re
from typing import Any

from .schemas import MidiCommand

COMPILER_VERSION = "sonic_producer_intelligence_v1"
MUSICAL_FIELDS = ("key", "scale", "style", "mood", "bpm", "bars", "density", "seed")
DEFAULTS = {
    "key": "C", "scale": "minor", "style": "cloud", "mood": "neutral",
    "bpm": 130, "bars": 8, "density": "balanced", "seed": 93,
}

_ENHARMONICS = {"Db": "C#", "D#": "Eb", "Gb": "F#", "G#": "Ab", "A#": "Bb"}
_ROOTS = {"C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"}


def parse_prompt(prompt: str) -> tuple[dict[str, Any], list[str], dict[str, str]]:
    """Match only supported, explicit musical controls; preserve all source wording."""
    text = prompt.strip()
    lower = text.casefold()
    captured: dict[str, Any] = {}
    warnings: list[str] = []
    evidence: dict[str, str] = {}

    key_pattern = re.compile(
        r"(?<![A-Za-z0-9])(?:(?P<prefix>key\s+(?:of\s+)?|in\s+))?"
        r"(?P<key>[A-G](?:#|b)?)"
        r"(?:\s+(?P<scale>harmonic[\s_-]*minor|natural[\s_-]*minor|minor|major|maj|min|dorian|aeolian))?"
        r"(?![A-Za-z0-9])",
        flags=re.IGNORECASE,
    )

    def negated(match: re.Match) -> bool:
        prefix = text[max(0, match.start() - 22):match.start()].casefold()
        clause = re.split(r"[,;.!?]|\b(?:but|however|instead|rather)\b", prefix)[-1]
        return bool(re.search(r"\b(?:not|no|without|avoid|less)\b[^,;.!?]{0,18}$", clause))

    key_match = next((m for m in key_pattern.finditer(text)
                      if (m.group("scale") or m.group("prefix"))
                      and not negated(m)
                      and not (m.group("prefix") and m.group("prefix").casefold() == "in "
                               and not m.group("scale") and m.group("key") == "a")), None)
    if key_match:
        raw_key = key_match.group("key")
        key = raw_key[0].upper() + raw_key[1:]
        key = _ENHARMONICS.get(key, key)
        if key in _ROOTS:
            captured["key"] = key
            evidence["key"] = key_match.group(0).strip()
            scale = key_match.group("scale")
            if scale:
                normalized = re.sub(r"[\s_-]+", " ", scale.casefold()).strip()
                captured["scale"] = {
                    "maj": "major", "min": "minor", "harmonic minor": "harmonic_minor",
                    "natural minor": "minor", "aeolian": "minor"
                }.get(normalized, normalized)
                evidence["scale"] = scale

    tempo_pattern = re.compile(r"(?<!\d)(\d{2,3})\s*(?:bpm|beats\s+(?:per\s+)?minute)\b")
    tempo = next((m for m in tempo_pattern.finditer(lower) if not negated(m)), None)
    if tempo:
        bpm = int(tempo.group(1))
        if 60 <= bpm <= 200:
            captured["bpm"] = bpm
            evidence["bpm"] = tempo.group(0)
        else:
            warnings.append(f"{bpm} BPM is outside the supported 60–200 range; the selected/default tempo was kept.")

    bars_pattern = re.compile(r"\b(\d{1,2})\s*[- ]?bars?\b")
    bars = next((m for m in bars_pattern.finditer(lower) if not negated(m)), None)
    if bars:
        count = int(bars.group(1))
        if count in (4, 8, 16):
            captured["bars"] = count
            evidence["bars"] = bars.group(0)
        else:
            warnings.append("This composer supports 4, 8 or 16 bars; the selected/default length was kept.")

    style_matches = []
    for pattern, value in (
        (r"\b(cloud(?:\s+rap)?|atmospheric|ambient)\b", "cloud"),
        (r"\b(soul|r\s*&\s*b|rnb)\b", "soul"),
        (r"\b(trap|hip[ -]?hop|drill|rap)\b", "trap"),
    ):
        style_matches.extend((match.start(), value, match.group(0))
                             for match in re.finditer(pattern, lower) if not negated(match))
    if style_matches:
        selected_style = min(style_matches, key=lambda item: item[0])
        captured["style"] = selected_style[1]
        evidence["style"] = text[selected_style[0]:selected_style[0] + len(selected_style[2])]

    mood_matches = []
    for pattern, value in (
        (r"\b(dark|brooding|ominous|menacing)\b", "dark"),
        (r"\b(hopeful|warm|tender)\b", "hopeful"),
        (r"\b(dreamy|lucid|hazy|ethereal|wistful)\b", "dreamy"),
        (r"\b(tense|urgent|uneasy)\b", "tense"),
        (r"\b(uplifting|triumphant|bright)\b", "uplifting"),
    ):
        mood_matches.extend((match.start(), value, match.group(0))
                            for match in re.finditer(pattern, lower) if not negated(match))
    if mood_matches:
        selected_mood = min(mood_matches, key=lambda item: item[0])
        captured["mood"] = selected_mood[1]
        evidence["mood"] = text[selected_mood[0]:selected_mood[0] + len(selected_mood[2])]

    density_matches = []
    for pattern, value in ((r"\b(sparse|minimal|airy|spacious|open\s+space|leave\s+space|leave\s+room|space\s+for\s+(?:the\s+)?(?:vocals?|lead|melody))\b", "sparse"),
                          (r"\b(busy|dense|rapid|packed)\b", "busy"),
                          (r"\b(balanced|moderate)\b", "balanced")):
        density_matches.extend((match.start(), value, match.group(0))
                               for match in re.finditer(pattern, lower) if not negated(match))
    if density_matches:
        selected_density = min(density_matches, key=lambda item: item[0])
        captured["density"] = selected_density[1]
        evidence["density"] = text[selected_density[0]:selected_density[0] + len(selected_density[2])]

    title = re.search(r"\b(?:called|titled|named)\s+['\"“]([^'\"”]{1,100})['\"”]", text, flags=re.IGNORECASE)
    if title:
        captured["title"] = title.group(1).strip()
        evidence["title"] = title.group(0)

    return captured, warnings, evidence


def _run_parameters(run: dict[str, Any] | None) -> dict[str, Any]:
    if not run:
        return {}
    result = run.get("result", {})
    parameters = result.get("parameters", {})
    return {key: parameters.get(key, result.get(key)) for key in MUSICAL_FIELDS if parameters.get(key, result.get(key)) is not None}


def compile_brief(
    command: MidiCommand,
    latest_run: dict[str, Any] | None = None,
    kept_run: dict[str, Any] | None = None,
) -> tuple[MidiCommand, dict[str, Any]]:
    """Resolve prompt, explicit controls and requested continuity into one explainable plan."""
    prompt = command.prompt.strip()
    lower = prompt.casefold()
    captured, warnings, prompt_evidence = parse_prompt(prompt)
    values = {**DEFAULTS, "title": command.title}
    sources = {field: "default" for field in (*MUSICAL_FIELDS, "title")}
    used_context: dict[str, Any] | None = None

    refers_to_kept = bool(re.search(r"\b(kept|saved|approved|favorite|favourite)\b", lower))
    wants_full_continuity = bool(re.search(
        r"\b(variation|variant|continue|build on|same as (?:the )?last|like (?:the )?last|same settings)\b", lower
    ))
    same_key = bool(re.search(r"\b(same|keep|use|match)\s+(?:the\s+)?key\b|\bkey\s+(?:from|of)\s+(?:the\s+)?last\b", lower))
    same_tempo = bool(re.search(r"\b(same|keep|use|match)\s+(?:the\s+)?(?:tempo|bpm)\b", lower))
    same_style = bool(re.search(r"\b(same|keep|use|match)\s+(?:the\s+)?(?:style|vibe|feel)\b", lower))
    wants_continuity = wants_full_continuity or same_key or same_tempo or same_style or refers_to_kept

    source_run = kept_run if refers_to_kept else latest_run
    prior = _run_parameters(source_run)
    if wants_continuity and prior:
        if wants_full_continuity:
            for field in MUSICAL_FIELDS:
                if field in prior:
                    values[field] = prior[field]
                    sources[field] = "kept_output" if refers_to_kept else "previous_output"
            values["seed"] = (int(prior.get("seed", values["seed"])) + 1) % 2147483648
            sources["seed"] = "variation_of_saved_output"
        else:
            inherited = set()
            if same_key:
                inherited.update(("key", "scale"))
            if same_tempo:
                inherited.add("bpm")
            if same_style:
                inherited.update(("style", "mood"))
            if refers_to_kept and not inherited:
                inherited.update(("key", "scale", "style", "mood", "bpm", "density"))
            for field in inherited:
                if field in prior:
                    values[field] = prior[field]
                    sources[field] = "kept_output" if refers_to_kept else "previous_output"
        used_context = {
            "run_id": source_run["id"],
            "source": "explicitly_kept_output" if refers_to_kept else "most_recent_successful_midi_run",
            "reused_fields": [field for field, source in sources.items() if source in {"kept_output", "previous_output", "variation_of_saved_output"}],
        }
    elif wants_continuity:
        warnings.append("Continuity was requested, but no matching saved MIDI output is available; defaults and stated controls were used.")

    explicit = set(command.model_fields_set)
    for field, value in captured.items():
        if field not in explicit:
            values[field] = value
            sources[field] = "prompt"
    for field in (*MUSICAL_FIELDS, "title"):
        if field in explicit:
            values[field] = getattr(command, field)
            sources[field] = "operator_control"

    if "title" not in explicit and "title" not in captured:
        if prompt:
            values["title"] = f"{values['key']} {values['scale'].replace('_', ' ')} {values['style']} idea"
        else:
            values["title"] = command.title
        sources["title"] = "derived_label" if prompt else "default"

    if prompt and not set(captured).intersection(MUSICAL_FIELDS):
        warnings.append("No supported musical controls were explicit in this prompt. Sonic preserved it as creative context and used the shown defaults.")

    # Validate inherited historical values against the current public command contract.
    resolved = MidiCommand.model_validate({**command.model_dump(), **values})
    assumptions = []
    for field in ("key", "scale", "style", "mood", "bpm", "bars", "density"):
        if sources[field] == "default":
            assumptions.append(f"{field.replace('_', ' ').capitalize()} defaulted to {values[field]}.")

    brief = {
        "schema_version": "sonic.production-brief/1.0",
        "compiler": COMPILER_VERSION,
        "interpretation": "deterministic_supported_controls",
        "source_prompt": prompt,
        "captured": captured,
        "resolved_parameters": {field: values[field] for field in ("title", *MUSICAL_FIELDS)},
        "field_sources": sources,
        "evidence": [
            {
                "field": field,
                "value": values[field],
                "source": sources[field],
                **({"prompt_excerpt": prompt_evidence[field]} if field in prompt_evidence else {}),
                **({"run_id": used_context["run_id"]} if used_context and sources[field] in {
                    "kept_output", "previous_output", "variation_of_saved_output"
                } else {}),
            }
            for field in ("title", *MUSICAL_FIELDS)
        ],
        "assumptions": assumptions,
        "continuity": {
            "requested": wants_continuity,
            "used": used_context is not None,
            "source_run": used_context,
        },
        "scope": "Only title, key, scale, style, mood, BPM, bar count, density and seed map to MIDI controls. Other wording is preserved as creative context and is not silently converted into musical facts.",
        "warnings": warnings,
    }
    return resolved, brief
