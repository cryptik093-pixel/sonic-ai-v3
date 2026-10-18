"""Foundation unit tests. Command: python -m pytest apps/api/tests/test_forge_core_foundation.py -q"""
import hashlib
import io
import json
import stat
import sys
import zipfile
from pathlib import Path

import pytest

# Path is resolved from the test file, so it works after overlay copy into the Sonic repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workbench.forge_core import (
    ArchivePolicy, ArchiveRejected, ForgeError, approve_edits, export_reviewed_pack,
    export_shopify_draft_csv, inventory_pack,
)


def make_zip(tmp_path, files):
    source = tmp_path / "input.zip"
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return source


def test_inventory_is_read_only_and_deterministic(tmp_path):
    src = make_zip(tmp_path, {"Pack/808s/sub.wav": b"raw-audio", "Pack/Melodies/keys.wav": b"second audio"})
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    a = inventory_pack(src, "Rebellion", "hip-hop / trap")
    b = inventory_pack(src, "Rebellion", "hip-hop / trap")
    assert a.to_dict() == b.to_dict()
    assert a.source_zip_sha256 == before == hashlib.sha256(src.read_bytes()).hexdigest()
    assert len(a.assets) == 2
    assert all(x.key["value"] is None and x.bpm["value"] is None for x in a.assets)
    assert next(x for x in a.assets if "/808s/" in x.original_path).key["value"] is None


def test_complete_review_roundtrip_and_hash_lineage(tmp_path):
    original = {"Pack/Loops/a.wav": b"abc123", "Pack/Drums/kick.wav": b"kick bytes"}
    src = make_zip(tmp_path, original)
    m = inventory_pack(src, "Lord of Prudence", "boom bap")
    edits = {}
    for a in m.assets:
        edits[a.asset_id] = {
            "proposed_path": "RELEASE/" + a.original_path,
            "rights_state": "cleared",
            "taxonomy": "boom bap / drums" if "kick" in a.original_path else "boom bap / loop",
        }
    review = approve_edits(m, edits)
    assert review.status == "reviewed"
    dst = export_reviewed_pack(src, review, tmp_path / "out.zip")
    with zipfile.ZipFile(dst) as z:
        assert z.read("RELEASE/Pack/Loops/a.wav") == b"abc123"
        assert z.read("RELEASE/Pack/Drums/kick.wav") == b"kick bytes"
        doc = json.loads(z.read("manifest.json"))
        for asset in doc["assets"]:
            assert hashlib.sha256(z.read(asset["proposed_path"])).hexdigest() == asset["sha256"]
        assert b"rights_state" in z.read("manifest.csv")
    assert src.exists()
    with pytest.raises(ForgeError, match="exists"):
        export_reviewed_pack(src, review, dst)


def test_export_requires_operator_review_and_rights_gate(tmp_path):
    src = make_zip(tmp_path, {"p.wav": b"not real PCM but hashable"})
    m = inventory_pack(src, "P", "hip hop")
    with pytest.raises(ForgeError, match="operator review"):
        export_reviewed_pack(src, m, tmp_path / "out.zip")
    approved = approve_edits(m, {m.assets[0].asset_id: {"tags": ["reviewed"]}})
    dst = export_reviewed_pack(src, approved, tmp_path / "reviewed.zip")
    assert dst.exists()
    with pytest.raises(ForgeError, match="rights-cleared"):
        export_shopify_draft_csv(approved, tmp_path / "draft.csv", "5.00", "OH-FORGE-01")
    cleared = approve_edits(approved, {m.assets[0].asset_id: {"rights_state": "cleared"}})
    csv_path = export_shopify_draft_csv(cleared, tmp_path / "draft.csv", "5.00", "OH-FORGE-01")
    assert "FALSE" in csv_path.read_text()


@pytest.mark.parametrize("bad_name", ["../danger.wav", "/absolute.wav", "a/../../escape.wav", "C:/bad.wav", "folder\\bad.wav"])
def test_reject_zip_slip(tmp_path, bad_name):
    src = make_zip(tmp_path, {bad_name: b"x"})
    # zipfile normalizes Windows separators; put hostile names in raw headers.
    if "\\" in bad_name:
        src.write_bytes(src.read_bytes().replace(bad_name.replace("\\", "/").encode(), bad_name.encode()))
    with pytest.raises(ArchiveRejected):
        inventory_pack(src, "Bad", "trap")


def test_reject_duplicate_casefold(tmp_path):
    src = make_zip(tmp_path, {"Kicks/A.wav": b"a", "kicks/a.wav": b"b"})
    with pytest.raises(ArchiveRejected, match="Duplicate"):
        inventory_pack(src, "Bad", "trap")


def test_reject_symlink(tmp_path):
    src = tmp_path / "input.zip"
    with zipfile.ZipFile(src, "w") as z:
        i = zipfile.ZipInfo("link.wav")
        i.create_system = 3
        i.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(i, b"/etc/passwd")
    with pytest.raises(ArchiveRejected, match="Symlink"):
        inventory_pack(src, "Bad", "trap")


def test_reject_too_many_members(tmp_path):
    src = make_zip(tmp_path, {f"{n}.wav": b"x" for n in range(4)})
    with pytest.raises(ArchiveRejected, match="entry-count"):
        inventory_pack(src, "Bad", "trap", policy=ArchivePolicy(max_entries=3))


def test_reject_bomb_ratio(tmp_path):
    src = make_zip(tmp_path, {"huge.wav": b"\0" * 2_000_000})
    with pytest.raises(ArchiveRejected, match="compression ratio"):
        inventory_pack(src, "Bad", "trap")


def test_reject_unsupported_asset(tmp_path):
    src = make_zip(tmp_path, {"danger.exe": b"x"})
    with pytest.raises(ArchiveRejected, match="Unsupported"):
        inventory_pack(src, "Bad", "trap")


def test_conflicting_output_names_and_extension_renaming(tmp_path):
    src = make_zip(tmp_path, {"a.wav": b"a", "b.wav": b"b"})
    m = inventory_pack(src, "P", "trap")
    with pytest.raises(ForgeError, match="Duplicate"):
        approve_edits(m, {m.assets[0].asset_id: {"proposed_path": "A.wav"},
                          m.assets[1].asset_id: {"proposed_path": "a.wav"}})
    with pytest.raises(ForgeError, match="media format"):
        approve_edits(m, {m.assets[0].asset_id: {"proposed_path": "a.mp3"}})


def test_source_integrity_recheck(tmp_path):
    src = make_zip(tmp_path, {"a.wav": b"a"})
    m = inventory_pack(src, "P", "trap")
    approved = approve_edits(m, {m.assets[0].asset_id: {"tags": ["ok"]}})
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("a.wav", b"tampered")
    with pytest.raises(ForgeError, match="changed"):
        export_reviewed_pack(src, approved, tmp_path / "out.zip")


def test_unknown_asset_cannot_be_modified(tmp_path):
    src = make_zip(tmp_path, {"a.wav": b"a"})
    m = inventory_pack(src, "P", "trap")
    with pytest.raises(ForgeError, match="nonexistent"):
        approve_edits(m, {"fake-id": {"tags": ["bad"]}})


def test_percussion_key_override_is_human_attributed(tmp_path):
    src = make_zip(tmp_path, {"808s/bass.wav": b"raw"})
    m = inventory_pack(src, "P", "trap")
    reviewed = approve_edits(m, {m.assets[0].asset_id: {"key_override": "F# minor"}})
    assert reviewed.assets[0].key["method"] == "operator_override"
    assert reviewed.assets[0].key["confidence"] is None
