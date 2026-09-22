"""Build a portable Windows app: users need neither Python, Node nor Git."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
    "--name", "Sonic", "--paths", str(root),
    "--collect-all", "webview", "--collect-all", "soundfile", "--collect-all", "_soundfile_data",
    "--collect-submodules", "keyring.backends",
    "--copy-metadata", "mcp", "--copy-metadata", "pydantic", "--copy-metadata", "jsonschema",
    "--add-data", f"{root / 'apps/api/workbench/static'}:apps/api/workbench/static",
    "--hidden-import", "uvicorn.logging", "--hidden-import", "uvicorn.loops.asyncio",
    "--hidden-import", "uvicorn.protocols.http.h11_impl", "--hidden-import", "uvicorn.lifespan.on",
    str(root / "apps/desktop/launcher.py"),
], cwd=root, check=True)
