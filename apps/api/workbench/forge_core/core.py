"""Deterministic, read-only-input ZIP inventory, operator review and reversible export.

This library is deliberately independent of FastAPI, database, network and Shopify.
It is a staging foundation, not a replacement for Sonic's workbench service.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import unicodedata
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


class ForgeError(ValueError):
    """Failed business, validation or integrity rule."""


class ArchiveRejected(ForgeError):
    """Rejected an unsafe or unsupported archive."""


@dataclass(frozen=True)
class ArchivePolicy:
    max_entries: int = 500
    max_file_bytes: int = 150 * 1024 * 1024
    max_total_bytes: int = 512 * 1024 * 1024
    max_ratio: int = 200
    max_path_length: int = 240
    allowed_suffixes: tuple[str, ...] = (
        ".wav", ".flac", ".aif", ".aiff", ".mp3", ".ogg",
        ".mid", ".midi", ".fxp", ".fxb", ".nki", ".txt", ".pdf", ".json",
        ".png", ".jpg", ".jpeg", ".webp",
    )


AUDIO = {".wav", ".flac", ".aif", ".aiff", ".mp3", ".ogg"}
PERCUSSION_DIRS = {"kicks", "kick", "snares", "snare", "hats", "hihat", "hi-hats", "perc", "percussion", "claps", "clap", "808s"}


def _safe_path(name: str, policy: ArchivePolicy) -> str:
    name = unicodedata.normalize("NFC", name)
    if not name or len(name) > policy.max_path_length or "\\" in name or "\x00" in name:
        raise ArchiveRejected("Invalid archive path (length, slash or NUL).")
    if name.startswith("/") or name.startswith("~") or name.endswith(" "):
        raise ArchiveRejected("Absolute, home-relative or trailing-space archive path.")
    pieces = name.split("/")
    if any(p in ("", ".", "..") or p.startswith(" ") or p.endswith(".") for p in pieces):
        raise ArchiveRejected("Unsafe archive path component.")
    if any(":" in p or any(ord(ch) < 32 for ch in p) for p in pieces):
        raise ArchiveRejected("Invalid control or drive character in archive path.")
    reserved = {"con", "prn", "aux", "nul", "conin$", "conout$"} | {f"{prefix}{n}" for prefix in ("com", "lpt") for n in range(1, 10)}
    if any(p.split(".")[0].casefold() in reserved or p.endswith(" ") or any(c in p for c in '<>"|?*') for p in pieces):
        raise ArchiveRejected("Reserved platform filename.")
    return PurePosixPath(*pieces).as_posix()


def _files(zf: zipfile.ZipFile, policy: ArchivePolicy) -> list[zipfile.ZipInfo]:
    entries = zf.infolist()
    if not entries or len(entries) > policy.max_entries:
        raise ArchiveRejected("Archive empty or exceeds entry-count limit.")
    count, total, seen = 0, 0, set()
    out: list[zipfile.ZipInfo] = []
    for info in entries:
        # Windows ZipInfo normalizes backslashes even when reading malicious
        # headers; orig_filename retains that input (and pre-truncation NULs).
        raw_name = info.orig_filename[:-1] if info.is_dir() else info.orig_filename
        _safe_path(raw_name, policy)
        name = info.filename[:-1] if info.is_dir() else info.filename
        path = _safe_path(name, policy)
        casefold = path.casefold()
        if casefold in seen:
            raise ArchiveRejected("Duplicate case-insensitive member path.")
        seen.add(casefold)
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_IFMT(mode) == stat.S_IFLNK:
            raise ArchiveRejected("Symlink entries are not allowed.")
        if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ArchiveRejected("Special archive entries are not allowed.")
        if info.flag_bits & 1:
            raise ArchiveRejected("Encrypted archive member is not supported.")
        if info.is_dir():
            continue
        count += 1
        if Path(path).suffix.lower() not in policy.allowed_suffixes:
            raise ArchiveRejected("Unsupported file extension: " + Path(path).suffix.lower())
        if info.file_size > policy.max_file_bytes:
            raise ArchiveRejected("Archive member exceeds expanded-size limit.")
        total += info.file_size
        if total > policy.max_total_bytes:
            raise ArchiveRejected("Archive exceeds total expanded-size limit.")
        if info.file_size >= (1 << 20) and info.file_size / max(1, info.compress_size) > policy.max_ratio:
            raise ArchiveRejected("Archive member exceeds compression ratio limit.")
        out.append(info)
    if not count:
        raise ArchiveRejected("Archive contains no supported files.")
    file_names = {_safe_path(i.filename, policy).casefold() for i in out}
    if any('/'.join(name.split('/')[:n]) in file_names for name in seen for n in range(1, len(name.split('/')))):
        raise ArchiveRejected("Archive file/directory path collision.")
    return out


def _sha_stream(zf: zipfile.ZipFile, info: zipfile.ZipInfo, policy: ArchivePolicy) -> str:
    h, length = hashlib.sha256(), 0
    with zf.open(info) as fin:
        while block := fin.read(1 << 20):
            length += len(block)
            if length > policy.max_file_bytes or length > info.file_size:
                raise ArchiveRejected("Expanded member exceeded declared/allowed size.")
            h.update(block)
    if length != info.file_size:
        raise ArchiveRejected("Member size mismatch after decompression.")
    return h.hexdigest()


def _kind(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in AUDIO:
        return "audio"
    if suffix in {".mid", ".midi"}:
        return "midi"
    if suffix in {".fxp", ".fxb", ".nki"}:
        return "preset"
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "artwork"
    return "document"


def _is_percussion(path: str) -> bool:
    return bool(PERCUSSION_DIRS.intersection({p.casefold() for p in PurePosixPath(path).parts[:-1]}))


def _estimate_unavailable(reason: str) -> dict[str, Any]:
    return {"value": None, "confidence": 0.0, "method": "not_measured", "reason": reason}


@dataclass
class Asset:
    asset_id: str
    original_path: str
    proposed_path: str
    sha256: str
    bytes: int
    asset_type: str
    taxonomy: str
    bpm: dict[str, Any]
    key: dict[str, Any]
    rights_state: str = "unverified"
    review_state: str = "pending"
    tags: list[str] = field(default_factory=list)
    audio: dict[str, Any] = field(default_factory=dict)


@dataclass
class Manifest:
    schema_version: str
    pack_id: str
    title: str
    taxonomy: str
    source_zip_sha256: str
    assets: list[Asset]
    status: str = "awaiting_operator_review"
    rights_state: str = "unverified"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while b := stream.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def inventory_pack(source_zip: str | Path, title: str, taxonomy: str, *, policy: ArchivePolicy | None = None) -> Manifest:
    """Inventories without changing the input ZIP; key and BPM remain unmeasured.

    Caller must enforce tenant/owner authorization for uploaded source_zip separately.
    """
    policy = policy or ArchivePolicy()
    source = Path(source_zip)
    if not source.is_file() or not zipfile.is_zipfile(source):
        raise ArchiveRejected("Input must be a readable ZIP file.")
    title, taxonomy = title.strip(), taxonomy.strip()
    if not (1 <= len(title) <= 100 and 1 <= len(taxonomy) <= 120):
        raise ForgeError("Title or taxonomy outside accepted length.")
    source_hash = _file_sha256(source)
    assets = []
    with zipfile.ZipFile(source) as zf:
        for info in _files(zf, policy):
            path = _safe_path(info.filename, policy)
            content_hash = _sha_stream(zf, info, policy)
            ident = hashlib.sha256((content_hash + "\0" + path).encode("utf-8")).hexdigest()[:20]
            percussion = _is_percussion(path)
            reason = "Percussion: tonal key not assumed." if percussion else "Tempo/key estimator has not run; operator review required."
            assets.append(Asset(
                asset_id="oh-asset-" + ident, original_path=path, proposed_path=path,
                sha256=content_hash, bytes=info.file_size, asset_type=_kind(path),
                taxonomy=taxonomy, bpm=_estimate_unavailable("Tempo estimator not run."),
                key=_estimate_unavailable(reason),
            ))
    pack_id = "oh-pack-" + hashlib.sha256((title + "\0" + source_hash).encode("utf-8")).hexdigest()[:20]
    return Manifest(schema_version="omega.forge.manifest/1.0", pack_id=pack_id,
                    title=title, taxonomy=taxonomy, source_zip_sha256=source_hash, assets=assets)


def _validate_paths(manifest: Manifest, policy: ArchivePolicy) -> None:
    names = set()
    for a in manifest.assets:
        name = _safe_path(a.proposed_path, policy)
        if Path(name).suffix.lower() not in policy.allowed_suffixes:
            raise ForgeError("Proposed file extension not permitted.")
        if Path(name).suffix.lower() != Path(a.original_path).suffix.lower():
            raise ForgeError("Cannot change binary media format by renaming extension.")
        key = name.casefold()
        if key in names or key in {"manifest.json", "manifest.csv"}:
            raise ForgeError("Duplicate or reserved proposed export name.")
        names.add(key)
    if any('/'.join(name.split('/')[:n]) in names | {"manifest.json", "manifest.csv"}
           for name in names for n in range(1, len(name.split('/')))):
        raise ForgeError("File/directory export path collision.")


def approve_edits(manifest: Manifest, updates: Mapping[str, Mapping[str, Any]], *,
                  policy: ArchivePolicy | None = None) -> Manifest:
    """Make explicitly approved filename/taxonomy/tag/rights overrides; never modify source."""
    policy = policy or ArchivePolicy()
    new = Manifest(**{**manifest.to_dict(), "assets": [Asset(**asdict(a)) for a in manifest.assets]})
    remaining = set(updates)
    valid_rights = {"unverified", "cleared", "restricted"}
    for asset in new.assets:
        if asset.asset_id not in updates:
            continue
        changes = dict(updates[asset.asset_id])
        remaining.discard(asset.asset_id)
        if not changes or set(changes) - {"proposed_path", "taxonomy", "tags", "rights_state", "bpm_override", "key_override"}:
            raise ForgeError("Unrecognized or empty operator edit.")
        if "proposed_path" in changes:
            asset.proposed_path = str(changes["proposed_path"])
        if "taxonomy" in changes:
            s = str(changes["taxonomy"]).strip()
            if not 1 <= len(s) <= 120:
                raise ForgeError("Invalid taxonomy.")
            asset.taxonomy = s
        if "tags" in changes:
            tags = changes["tags"]
            if not isinstance(tags, list) or len(tags) > 25 or not all(isinstance(x, str) and 0 < len(x) <= 40 for x in tags):
                raise ForgeError("Invalid tags.")
            asset.tags = tags
        if "rights_state" in changes:
            if changes["rights_state"] not in valid_rights:
                raise ForgeError("Invalid rights state.")
            asset.rights_state = changes["rights_state"]
        for override, field_name in (("bpm_override", "bpm"), ("key_override", "key")):
            if override in changes:
                value = changes[override]
                if field_name == "bpm":
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not (30 <= value <= 300):
                        raise ForgeError("BPM override must be 30-300.")
                else:
                    if not isinstance(value, str) or not re.fullmatch(r"(?:[A-G](?:#|b)?)(?: (?:major|minor))?", value):
                        raise ForgeError("Invalid key override.")
                setattr(asset, field_name, {"value": value, "confidence": None,
                                            "method": "operator_override", "reason": "Explicit human decision, not automated measurement."})
        asset.review_state = "approved"
    if remaining:
        raise ForgeError("Operator edits target nonexistent asset IDs.")
    _validate_paths(new, policy)
    new.status = "review_in_progress" if any(a.review_state != "approved" for a in new.assets) else "reviewed"
    new.rights_state = "cleared" if all(a.rights_state == "cleared" for a in new.assets) else "unverified"
    return new


def _manifest_csv(manifest: Manifest) -> bytes:
    target = io.StringIO(newline="")
    columns = ["asset_id", "original_path", "proposed_path", "asset_type", "taxonomy", "bpm", "bpm_method", "key", "key_method", "rights_state", "review_state", "sha256", "bytes", "tags"]
    writer = csv.DictWriter(target, fieldnames=columns)
    writer.writeheader()
    for a in manifest.assets:
        writer.writerow({"asset_id": a.asset_id, "original_path": a.original_path,
                         "proposed_path": a.proposed_path, "asset_type": a.asset_type,
                         "taxonomy": a.taxonomy, "bpm": a.bpm["value"], "bpm_method": a.bpm["method"],
                         "key": a.key["value"], "key_method": a.key["method"],
                         "rights_state": a.rights_state, "review_state": a.review_state,
                         "sha256": a.sha256, "bytes": a.bytes, "tags": ", ".join(a.tags)})
    # Spreadsheet applications interpret these prefixes even in quoted cells.
    rows = list(csv.reader(io.StringIO(target.getvalue())))
    safe = io.StringIO(newline="")
    writer = csv.writer(safe)
    for row in rows:
        writer.writerow(["'" + s if s.lstrip().startswith(("=", "+", "-", "@")) or s.startswith(("\t", "\r")) else s for s in row])
    return safe.getvalue().encode("utf-8")


def export_reviewed_pack(source_zip: str | Path, manifest: Manifest, output_zip: str | Path,
                         *, policy: ArchivePolicy | None = None) -> Path:
    """Exports approved, renamed bytes and manifests; refuses unapproved assets.

    Atomic staging and final-path collision protection prevent accidental overwrites.
    Does NOT assert release approval or publish to Shopify.
    """
    policy = policy or ArchivePolicy()
    src, dest = Path(source_zip), Path(output_zip)
    if not all(a.review_state == "approved" for a in manifest.assets):
        raise ForgeError("Every asset requires explicit operator review before export.")
    _validate_paths(manifest, policy)
    if _file_sha256(src) != manifest.source_zip_sha256:
        raise ForgeError("Original source ZIP changed after inventory.")
    if dest.exists():
        raise ForgeError("Destination already exists; preserving existing file.")
    if src.resolve() == dest.resolve():
        raise ForgeError("Destination cannot overwrite source.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = dest.with_name(dest.name + ".staging")
    if staging.exists():
        raise ForgeError("Staging path exists; refusing overwrite.")
    import os
    try:
        with zipfile.ZipFile(src) as input_zip, zipfile.ZipFile(staging, "x", compression=zipfile.ZIP_DEFLATED) as output_zip_file:
            entries = _files(input_zip, policy)
            lookup = {_safe_path(i.filename, policy): i for i in entries}
            if set(lookup) != {a.original_path for a in manifest.assets}:
                raise ForgeError("Manifest and source archive entries disagree.")
            for a in sorted(manifest.assets, key=lambda x: x.proposed_path):
                original = lookup[a.original_path]
                info = zipfile.ZipInfo(a.proposed_path, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                h, n = hashlib.sha256(), 0
                # Stream between archive handles: bounded memory even for large WAV files.
                with input_zip.open(original) as reader, output_zip_file.open(info, "w") as writer:
                    while chunk := reader.read(1 << 20):
                        n += len(chunk)
                        if n > a.bytes or n > policy.max_file_bytes:
                            raise ForgeError("Expanded archive bytes exceeded manifest or safety limit.")
                        h.update(chunk)
                        writer.write(chunk)
                if n != a.bytes or h.hexdigest() != a.sha256:
                    raise ForgeError("Asset hash mismatch during export.")
            for name, data in (("manifest.json", json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")),
                               ("manifest.csv", _manifest_csv(manifest))):
                output_zip_file.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), data, compress_type=zipfile.ZIP_DEFLATED)
        if dest.exists():
            raise ForgeError("Destination appeared while writing; refusing overwrite.")
        os.link(staging, dest)  # atomic create-if-absent; keeps original safe
    finally:
        if staging.exists():
            staging.unlink()
    return dest


def export_shopify_draft_csv(manifest: Manifest, output_csv: str | Path, price: str, sku: str) -> Path:
    """Offline CSV draft ONLY: no network access, order changes or product creation."""
    if not manifest.assets or not all(a.review_state == "approved" and a.rights_state == "cleared" for a in manifest.assets):
        raise ForgeError("Shopify draft blocked until every asset is approved and rights-cleared.")
    from decimal import Decimal, InvalidOperation
    try:
        p = Decimal(price)
    except InvalidOperation as e:
        raise ForgeError("Invalid price.") from e
    if not p.is_finite() or p < 0 or p > 100000:
        raise ForgeError("Price must be finite and nonnegative.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,63}", sku):
        raise ForgeError("Invalid SKU.")
    dest = Path(output_csv)
    if dest.exists():
        raise ForgeError("CSV output already exists.")
    handle = re.sub(r"[^a-z0-9]+", "-", manifest.title.casefold()).strip("-")[:180]
    if not handle:
        raise ForgeError("Invalid storefront handle.")
    fields = ["Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published", "Status", "Variant SKU", "Variant Price", "Variant Requires Shipping"]
    safe_cell = lambda s: "'" + s if s.lstrip().startswith(("=", "+", "-", "@")) or s.startswith(("\t", "\r")) else s
    with dest.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"Handle": handle, "Title": safe_cell(manifest.title), "Body (HTML)": "Pack draft. Review description, licensing and delivery before publishing.",
                         "Vendor": "Omega House Beats", "Type": "Music Production Pack", "Tags": safe_cell(manifest.taxonomy),
                         "Published": "FALSE", "Status": "draft", "Variant Requires Shipping": "FALSE", "Variant SKU": sku, "Variant Price": str(p.quantize(Decimal("0.01")))})
    return dest
