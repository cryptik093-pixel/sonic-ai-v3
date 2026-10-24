#!/usr/bin/env python3
"""Read-only Omega House VST3 repository/toolchain preflight.

Examples:
  python scripts/preflight.py --repo C:/path/to/project
  py -3 scripts/preflight.py --repo . --output preflight.json
No downloads, writes to the inspected repository, imports, or shell builds.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def tool_version(name, arg="--version"):
    executable = shutil.which(name)
    if executable is None:
        return {"installed": False, "path": None}
    try:
        result = subprocess.run([executable, arg], capture_output=True, text=True, timeout=6, check=False)
        first = (result.stdout or result.stderr).splitlines()
        return {"installed": True, "path": executable, "version": first[0] if first else "unknown"}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"installed": True, "path": executable, "version_error": str(error)}


def git_status(repo):
    executable = shutil.which("git")
    if not executable:
        return {"available": False}
    args = [executable, "-C", str(repo), "status", "--short", "--branch"]
    try:
        outcome = subprocess.run(args, capture_output=True, text=True, timeout=8, check=False)
        return {"available": outcome.returncode == 0, "output": outcome.stdout.strip() if outcome.returncode == 0 else None}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": False, "error": str(error)}


def discover(repo):
    markers = ["CMakeLists.txt", "*.jucer", "AGENTS.md", "*.sln", "*.vcxproj", "*.vst3", "SKILL.md", "LICENSE*", "*.cpp", "*.h"]
    hits = {}
    for marker in markers:
        matches = list(repo.glob(marker)) + list(repo.glob("*/" + marker))
        hits[marker] = [str(path.relative_to(repo)) for path in matches[:30] if path.is_file()]
    return hits


def run(repo):
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        raise ValueError("Repository directory not found: " + str(repo))
    data = {
        "schema_version": 1,
        "read_only": True,
        "platform": {"system": platform.system(), "release": platform.release(), "architecture": platform.machine()},
        "repository": str(repo),
        "git": git_status(repo),
        "toolchain": {name: tool_version(name) for name in ["cmake", "git", "ninja", "cl", "clang++", "g++", "python", "py"]},
        "top_level_markers": discover(repo),
        "windows_host_hint": {"FL_STUDIO_PATH": os.environ.get("FL_STUDIO_PATH"), "VST3_SYSTEM_PATH": os.environ.get("CommonProgramFiles")},
        "warnings": []
    }
    if not data["top_level_markers"]["CMakeLists.txt"] and not data["top_level_markers"]["*.jucer"]:
        data["warnings"].append("No build manifest detected in root or immediate subdirectories; inspect deeper or locate existing plugin source.")
    if platform.system() != "Windows":
        data["warnings"].append("This is not a Windows/FL Studio runtime. A Linux preflight does not validate a Windows VST3 build or DAW load.")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Optional JSON destination; no project changes unless explicitly set inside it")
    args = parser.parse_args()
    try:
        result = run(args.repo)
    except ValueError as error:
        parser.error(str(error))
    content = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
