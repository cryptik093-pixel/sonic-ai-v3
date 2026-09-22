import json
import os
import sys
import traceback
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Windowed executables have no standard streams. Dependencies may still write to them.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

if __name__ == "__main__":
    try:
        from apps.desktop.app import main
        main()
    except Exception as exc:
        smoke = next((flag for flag in ("--smoke-test", "--ui-smoke-test") if flag in sys.argv), None)
        if smoke:
            output = Path(sys.argv[sys.argv.index(smoke) + 1])
            output.write_text(json.dumps({"passed": False, "error": str(exc), "traceback": traceback.format_exc()}, indent=2), encoding="utf-8")
        elif sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Sonic could not open.\n\n{exc}\n\nYour saved outputs remain in your Sonic data folder.", "Sonic", 0x10)
        else:
            traceback.print_exc()
        sys.exit(1)
