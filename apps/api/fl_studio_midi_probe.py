"""FL Studio native MIDI scripting probe (opt-in). Never invokes setter APIs.

Install manually as a MIDI controller script for a virtual/dedicated controller
only after testing on a disposable project. No network socket or background thread.
"""
import json
import time
import channels
import mixer
import general

OUTPUT_PATH = r"C:\Users\Public\Documents\sonic_fl_readonly_probe.json"
MAX_TRACKS = 128
MAX_CHANNELS = 128

def _safe(func, *args):
    try:
        return {"status": "available", "value": func(*args)}
    except Exception as exc:
        return {"status": "unavailable", "error": type(exc).__name__}

def capture():
    count = _safe(mixer.trackCount)
    track_count = min(int(count["value"]), MAX_TRACKS) if count["status"] == "available" else 0
    channel_count = _safe(channels.channelCount)
    n_channels = min(int(channel_count["value"]), MAX_CHANNELS) if channel_count["status"] == "available" else 0
    payload = {
        "schema": "sonic.fl.readonly.v1",
        "captured_unix": int(time.time()),
        "source": "fl_studio_midi_scripting",
        "project_title": _safe(general.getProjectTitle),
        "tempo": _safe(mixer.getCurrentTempo),
        "dirty_flag": _safe(general.getChangedFlag),
        "mixer_tracks": [
            {"index": i, "name": _safe(mixer.getTrackName, i),
             "color": _safe(mixer.getTrackColor, i)} for i in range(track_count)
        ],
        "channels": [
            {"index": i, "name": _safe(channels.getChannelName, i),
             "target_fx_track": _safe(channels.getTargetFxTrack, i)}
            for i in range(n_channels)
        ],
        "vst_state": {"status": "unavailable"},
        "mixer_send_routing": {"status": "unavailable"},
        "automation": {"status": "unavailable"},
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True)

def OnInit():
    capture()
