"""Allowlisted copy-on-write mutations. This is deterministic, not a LangGraph model."""
import re
from .state import Bitcrusher, StudioState

class CommandError(ValueError):
    pass

def apply_command(session: StudioState, instruction: str) -> tuple[StudioState, str]:
    command = instruction.strip().lower()
    if not command or len(command) > 500:
        raise CommandError("Command must contain 1–500 characters")
    update = session.model_copy(deep=True)
    targets = [t for t in update.tracks if t.id.lower() in command or t.name.lower() in command]
    if not targets:
        for fragment, tid in (("drum", "drums"), ("bass", "bass"), ("synth", "bass")):
            if fragment in command:
                targets = [t for t in update.tracks if t.id == tid]
                break
    if not targets:
        raise CommandError("Specify an existing track, such as drums or bass")
    changed = []
    if re.search(r"\bunmute\b", command):
        for t in targets: t.isMuted = False
        changed.append("unmuted")
    elif re.search(r"\bmute\b", command):
        for t in targets: t.isMuted = True
        changed.append("muted")
    if any(w in command for w in ("quieter", "lower", "turn down", "reduce volume")):
        for t in targets: t.volume = round(max(0, t.volume - 0.2), 3)
        changed.append("volume −0.2")
    elif any(w in command for w in ("louder", "turn up", "increase volume")):
        for t in targets: t.volume = round(min(1, t.volume + 0.1), 3)
        changed.append("volume +0.1")
    if "pan" in command or "left" in command or "right" in command:
        if "left" in command and "right" not in command:
            for t in targets: t.pan = -0.5
            changed.append("pan left 0.5")
        elif "right" in command and "left" not in command:
            for t in targets: t.pan = 0.5
            changed.append("pan right 0.5")
    if any(w in command for w in ("crush", "bitcrush", "bitcrusher")):
        bits = 4 if any(w in command for w in ("hard", "heavy", "crush")) else 8
        for t in targets:
            fx = next((fx for fx in t.pluginChain if fx.type == "bitcrusher"), None)
            if fx is None:
                fx = Bitcrusher(id=f"crush-{t.id}")
                t.pluginChain.append(fx)
            fx.bits = bits
            fx.bypass = False
        changed.append(f"bitcrusher configured to {bits} bits (DSP pending)")
    movement = re.search(r"\b(?:move|shift)\b.*?\b(\d+(?:\.\d+)?)\s*(?:seconds?|sec|s)\s*(later|forward|earlier|back)?", command)
    if movement:
        seconds = float(movement.group(1))
        if seconds > 60: raise CommandError("Move at most 60 seconds in one command")
        sign = -1 if movement.group(2) in ("earlier", "back") else 1
        for t in targets:
            for region in t.regions:
                if region.startTime + sign * seconds < 0:
                    raise CommandError("Cannot move a region before timeline start")
                region.startTime += sign * seconds
        changed.append(f"regions moved {sign * seconds:g}s")
    if not changed:
        raise CommandError("Unsupported command. Try 'mute drums', 'make drums quieter and pan left', 'crush drums hard', or 'move bass 2 seconds later'.")
    update.revision += 1
    return StudioState.model_validate(update.model_dump()), f"{', '.join(changed)}: {', '.join(t.name for t in targets)}"
