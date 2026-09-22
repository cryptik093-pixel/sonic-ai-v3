import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.desktop.app import main

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        if sys.platform == "win32" and "--smoke-test" not in sys.argv and "--ui-smoke-test" not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Sonic could not open.\n\n{exc}\n\nYour saved outputs remain in your Sonic data folder.", "Sonic", 0x10)
        raise
