#!/usr/bin/env python3
"""Safely stage the verified Omega House Pack Forge ZIP in Sonic AI V3.

Staging is non-destructive; it does not start an API, connect MCP or publish.
"""
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

REQUIRED = {
    "SKILL.md", "README.md", "scripts/pack_forge.py",
    "service/app.py", "service/mcp_server.py", "tests/test_pipeline.py",
    "config/defaults.json", "integrations/AGENT_HANDOFFS.json",
}
PREFIX = "omega-house-pack-forge"
EXPECTED_SHA256 = "b8ad41841c7540cf6cbf008293d35b37902d8910dbe350d8699a522ae6e60b30"
MAX_FILES = 500
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024


def validate_archive(archive: Path):
    paths = set()
    with zipfile.ZipFile(archive) as zin:
        entries = zin.infolist()
        if len(entries) > MAX_FILES:
            raise ValueError("Too many distribution entries")
        if sum(x.file_size for x in entries) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("Distribution exceeds extracted-size limit")
        for item in entries:
            name = item.filename
            if "\\" in name or "\x00" in name or name.startswith("/"):
                raise ValueError("Unsafe archive path")
            p = PurePosixPath(name)
            if not p.parts or p.parts[0] != PREFIX or any(x in (".", "..") for x in p.parts):
                raise ValueError("Unexpected archive location")
            if len(p.parts) == 1 and not item.is_dir():
                raise ValueError("Root must be a folder")
            if (item.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
                raise ValueError("Symlinks are forbidden")
            if item.is_dir():
                continue
            rel = "/".join(p.parts[1:])
            if rel in paths:
                raise ValueError("Duplicate archive entry")
            paths.add(rel)
        if not REQUIRED.issubset(paths):
            raise ValueError("Missing required files: " + ", ".join(sorted(REQUIRED - paths)))
    return len(paths)


def install(archive: Path, repo: Path):
    if not (repo / "AGENTS.md").is_file() or not (repo / "apps/api/main.py").is_file():
        raise ValueError("Target is not the Sonic AI V3 repo root")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Unrecognized distribution hash; exact approved ZIP required")
    count = validate_archive(archive)
    target = repo / "tools" / PREFIX
    if target.exists():
        raise FileExistsError("Pack Forge already installed; refusing overwrite: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".omega-pack-forge-stage-", dir=target.parent) as scratch:
        staged = Path(scratch) / PREFIX
        staged.mkdir()
        with zipfile.ZipFile(archive) as zin:
            for item in zin.infolist():
                if item.is_dir():
                    continue
                relative = Path(*PurePosixPath(item.filename).parts[1:])
                output = staged / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                with zin.open(item) as src, output.open("wb") as dest:
                    while True:
                        buf = src.read(1024 * 1024)
                        if not buf:
                            break
                        dest.write(buf)
        os.replace(staged, target)
    print("Staged", count, "files in", target)
    print("Distribution SHA256:", digest)
    print("STATUS=STAGED_ONLY; runtime, API and ChatGPT integrations are NOT yet verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--repo", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    install(args.zip.resolve(), args.repo.resolve())
