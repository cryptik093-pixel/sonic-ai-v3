"""Import opt-in FL Studio MIDI scripting observations as unverified host evidence.

Does not mutate FL Studio or claim VST state equivalence.
"""
import json
from pathlib import Path

from .session_integrity import IntegrityError, IntegrityLedger

MAX_BYTES = 1024 * 1024

def import_probe(ledger: IntegrityLedger, session_id, expected_revision, source_path):
    path = Path(source_path).resolve(strict=True)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise IntegrityError("invalid_probe", "Probe must be a JSON file up to 1MB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise IntegrityError("invalid_probe", "Invalid probe JSON") from exc
    if not isinstance(data, dict) or data.get("schema") != "sonic.fl.readonly.v1":
        raise IntegrityError("invalid_probe", "Unexpected FL Studio probe schema")
    for field in ("mixer_tracks", "channels"):
        if not isinstance(data.get(field), list) or len(data[field]) > 128:
            raise IntegrityError("invalid_probe", "Invalid host observation arrays")
    current = ledger.get(session_id)
    state = current["state"]
    if state.get("host") != "FL Studio":
        raise IntegrityError("invalid_probe", "Session is not an FL Studio session")
    state["host_observation"] = {
        "source": "external_midi_script_unverified",
        "file": path.name,
        "reported": data,
        "vst_state_verified": False,
        "routing_verified": False,
        "host_rollback_available": False,
    }
    return ledger.checkpoint(session_id, expected_revision, state)
