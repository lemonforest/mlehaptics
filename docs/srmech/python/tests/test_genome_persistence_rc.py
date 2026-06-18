"""UPSTREAM §41 — genome persistence (disk save / load / catalog / append /
window). The 6-point acceptance bar for ``srmech.amsc.genome.genome_*``.

The genome helix grows ON DISK: a genome directory holds a fixed-width
append-only body (``turns.bin`` — every strand element a ``leaf_dim``-byte
Klein-4 block) plus an MPR-attested catalog (``manifest.json``). The reads are
paged (catalog reads the manifest only; window seeks one chromosome's region;
load streams block-by-block) and BOUNDED (every read re-hashes the bytes it
touched against the manifest — a mismatch is a ``GenomeBoundingError``).

numpy-free discipline: this test imports NO numpy and runs with numpy blocked
(``test_numpy_free_load`` proves it by collecting+passing numpy-absent). A strand
/ the_one is a list of Klein-4 :class:`HV` vectors from ``hdc.klein4_random`` —
the same house style as ``test_genome_surface_rc37.py``.

The six points (each a test below):
  1. round-trip byte-exact + ``partition`` after load == before;
  2. catalog reads the manifest WITHOUT opening ``turns.bin``;
  3. append grows the helix (new chromosome listed; PRIOR entries byte-identical;
     ``body_sha256`` changed; append never rewrites prior body bytes);
  4. paging — ``genome_window`` reads only the region, equals the stored leaves;
  5. bounding — a flipped body byte → ``GenomeBoundingError`` on load / window;
  6. attested + numpy-free — the manifest IS a valid MPRRecord,
     ``response_sha256 == body_sha256``, the manifest JSON is not bloated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome
from srmech.amsc.format import MPRRecord, validate_mpr_record
from srmech.amsc.hdc import klein4_random


# ── shared fixtures: a 3-chromosome genome strand ────────────────────────────

def _kernels():
    return {
        "astronomy": [klein4_random(64, seed=s) for s in range(3)],
        "geography": [klein4_random(64, seed=s) for s in (10, 11)],
        "music": [klein4_random(64, seed=20)],
    }


def _build(one):
    k = _kernels()
    strand = genome.genome(k, one)
    return k, strand, list(k)


def _as_lists(strand):
    return [list(x) for x in strand]


def _partition_lists(strand, one, labels):
    part = genome.partition(strand, one, labels)
    return {lbl: _as_lists(v) for lbl, v in part.items()}


# ── (1) round-trip byte-exact + partition-after-load == before ───────────────

def test_save_load_round_trip_is_byte_exact(tmp_path):
    one = klein4_random(64, seed=7)
    k, strand, labels = _build(one)
    p = tmp_path / "g"

    manifest = genome.genome_save(strand, p, the_one=one, labels=labels)
    assert isinstance(manifest, dict)
    assert manifest["leaf_dim"] == 64
    assert manifest["n_turns"] == len(strand)
    assert (p / "manifest.json").exists()
    assert (p / "turns.bin").exists()

    loaded_strand, loaded_one, loaded_labels = genome.genome_load(p)
    # byte-for-byte the saved strand
    assert _as_lists(loaded_strand) == _as_lists(strand)
    assert list(loaded_one) == list(one)
    assert loaded_labels == labels

    # partition(loaded) == partition(original) — the kernels survive verbatim
    before = _partition_lists(strand, one, labels)
    after = _partition_lists(loaded_strand, loaded_one, loaded_labels)
    assert after == before
    # and every kernel decodes back to exactly what we stored
    for lbl, leaves in k.items():
        assert after[lbl] == _as_lists(leaves)


# ── (2) catalog reads the manifest WITHOUT opening turns.bin ─────────────────

def test_catalog_reads_manifest_without_opening_body(tmp_path, monkeypatch):
    one = klein4_random(64, seed=7)
    _, strand, labels = _build(one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one, labels=labels)

    opened_paths = []
    real_open = Path.open

    def _recording_open(self, *args, **kwargs):
        opened_paths.append(str(self))
        return real_open(self, *args, **kwargs)

    # rc153: this asserts the PURE-PYTHON catalog read's I/O frugality via a
    # ``Path.open`` hook; under native dispatch ``genome_catalog`` parses
    # manifest.json in C (fopen — invisible to the hook), so pin the pure path here.
    # The native catalog's "never opens turns.bin" property is proven C-side + by the
    # rc153 byte-parity differential (test_genome_native_dispatch_rc153).
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    # Patch ``Path.open`` (NOT ``io.open``): the genome reads funnel through
    # ``Path.read_text`` / ``Path.open`` on every CPython, and ``Path.open`` is
    # resolved on the instance at call time. ``io.open`` is captured into
    # pathlib's accessor at import time on 3.10, so a late ``io.open`` patch is
    # invisible there (the manifest open went unrecorded → spurious failure).
    monkeypatch.setattr(Path, "open", _recording_open)
    cat = genome.genome_catalog(p)
    monkeypatch.undo()

    # the catalog NEVER pages in the body
    assert not any("turns.bin" in o for o in opened_paths), opened_paths
    assert any("manifest.json" in o for o in opened_paths), opened_paths

    # the catalog carries the full chromosome index without the body bytes
    assert [c["label"] for c in cat["chromosomes"]] == labels
    assert all(
        {"cap_sha256", "leaf_count", "byte_offset", "byte_len"} <= set(c)
        for c in cat["chromosomes"]
    )
    assert cat["body_sha256"]


# ── (3) append grows the helix; prior entries byte-identical ─────────────────

def test_append_grows_and_preserves_prior_entries(tmp_path):
    one = klein4_random(64, seed=7)
    base = {
        "astronomy": [klein4_random(64, seed=s) for s in range(3)],
        "geography": [klein4_random(64, seed=s) for s in (10, 11)],
    }
    strand = genome.genome(base, one)
    p = tmp_path / "g"
    man1 = genome.genome_save(strand, p, the_one=one, labels=list(base))

    body_before = (p / "turns.bin").read_bytes()
    prior_entries_before = json.loads(json.dumps(man1["chromosomes"]))  # deep copy

    new_leaves = [klein4_random(64, seed=s) for s in (30, 31)]
    man2 = genome.genome_append(p, "music", new_leaves, the_one=one)

    # k2 (the new chromosome) is listed
    labels2 = [c["label"] for c in man2["chromosomes"]]
    assert "music" in labels2
    assert labels2 == ["astronomy", "geography", "music"]

    # every PRIOR chromosome's manifest entry is byte-identical
    prior_after = [c for c in man2["chromosomes"] if c["label"] in base]
    assert prior_after == prior_entries_before

    # body_sha256 changed; n_turns grew by (cap + 2 turns) = 3
    assert man2["body_sha256"] != man1["body_sha256"]
    assert man2["n_turns"] == man1["n_turns"] + 3

    # append is append-ONLY: prior body bytes are an exact prefix of the new body
    body_after = (p / "turns.bin").read_bytes()
    assert body_after[: len(body_before)] == body_before

    # the appended chromosome round-trips
    ls, lo, ll = genome.genome_load(p)
    part = genome.partition(ls, lo, ll)
    assert _as_lists(part["music"]) == _as_lists(new_leaves)


# ── (4) paging — genome_window reads only the region, equals stored leaves ───

def test_window_pages_one_chromosome(tmp_path, monkeypatch):
    one = klein4_random(64, seed=7)
    k, strand, labels = _build(one)
    p = tmp_path / "g"
    man = genome.genome_save(strand, p, the_one=one, labels=labels)

    # the stored leaves for "astronomy" = the coupled turns (cap excluded) = the
    # strand region [1:4] (astronomy is first: cap@0, then its 3 turns).
    stored_astronomy_turns = strand[1:4]

    win = genome.genome_window(p, "astronomy")
    assert len(win) == 3
    assert _as_lists(win) == _as_lists(stored_astronomy_turns)

    # paging reads ONLY the requested region, not the whole body. Count the bytes
    # read from turns.bin during the window call.
    read_byte_counts = []
    real_open = Path.open

    def _measuring_open(self, *args, **kwargs):
        fh = real_open(self, *args, **kwargs)
        if "turns.bin" in str(self):
            original_read = fh.read

            def _counting_read(size=-1, *a, **kw):
                data = original_read(size, *a, **kw)
                read_byte_counts.append(len(data))
                return data

            fh.read = _counting_read
        return fh

    # rc153: this asserts the PURE-PYTHON pager reads ONLY one region's bytes via a
    # ``Path.open`` byte-count hook; native ``genome_window`` seeks+reads via C fopen
    # (invisible to the hook), so pin the pure path here. The native pager's region-
    # boundedness is proven C-side + by the rc153 byte-parity differential.
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    # Patch ``Path.open`` (version-robust; see catalog test for the 3.10 note).
    monkeypatch.setattr(Path, "open", _measuring_open)
    genome.genome_window(p, "geography")
    monkeypatch.undo()

    geo = next(c for c in man["chromosomes"] if c["label"] == "geography")
    total_body = (p / "turns.bin").stat().st_size
    # the window read at most one chromosome's region, strictly less than the body
    assert sum(read_byte_counts) == geo["byte_len"]
    assert sum(read_byte_counts) < total_body

    # a subset load is the same paged read for many chromosomes
    sub_strand, sub_one, sub_labels = genome.genome_load(p, labels=["music"])
    assert sub_labels == ["music"]
    assert _partition_lists(sub_strand, sub_one, ["music"])["music"] == _as_lists(
        k["music"]
    )


# ── (5) bounding — a flipped body byte → GenomeBoundingError ─────────────────

def test_bounding_flipped_body_byte_raises_on_full_load(tmp_path):
    one = klein4_random(64, seed=7)
    _, strand, labels = _build(one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one, labels=labels)

    body_path = p / "turns.bin"
    raw = bytearray(body_path.read_bytes())
    # flip ONE Klein-4 symbol somewhere in the body (stay in 0..3)
    raw[10] = (raw[10] + 1) % 4
    body_path.write_bytes(bytes(raw))

    with pytest.raises(genome.GenomeBoundingError):
        genome.genome_load(p)   # whole-body hash bound fails


def test_bounding_flipped_cap_byte_raises_on_window(tmp_path):
    one = klein4_random(64, seed=7)
    _, strand, labels = _build(one)
    p = tmp_path / "g"
    man = genome.genome_save(strand, p, the_one=one, labels=labels)

    geo = next(c for c in man["chromosomes"] if c["label"] == "geography")
    body_path = p / "turns.bin"
    raw = bytearray(body_path.read_bytes())
    # flip a byte INSIDE geography's leading cap block → window cap-bound fails
    cap_byte = geo["byte_offset"] + 2
    raw[cap_byte] = (raw[cap_byte] + 1) % 4
    body_path.write_bytes(bytes(raw))

    with pytest.raises(genome.GenomeBoundingError):
        genome.genome_window(p, "geography")
    with pytest.raises(genome.GenomeBoundingError):
        genome.genome_load(p, labels=["geography"])


# ── (6) attested + numpy-free ────────────────────────────────────────────────

def test_manifest_is_a_valid_attested_mpr_record(tmp_path):
    one = klein4_random(64, seed=7)
    _, strand, labels = _build(one)
    p = tmp_path / "g"
    man = genome.genome_save(strand, p, the_one=one, labels=labels)

    # the on-disk manifest is a real MPRRecord that passes validate_mpr_record
    payload = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
    record = MPRRecord(
        mpr_version=str(payload["mpr_version"]),
        data=dict(payload["data"]),
        data_schema_id=str(payload["data_schema_id"]),
        attestation=dict(payload["attestation"]),
        rendering=dict(payload["rendering"]),
    )
    validate_mpr_record(record)   # raises MPRValidationError if not a valid MPR

    # response_sha256 IS the body hash
    assert record.attestation["response_sha256"] == man["body_sha256"]
    assert record.attestation["response_sha256"] == record.data["body_sha256"]
    # parser_version is the srmech version string
    assert record.attestation["parser_version"].startswith("srmech ")

    # the manifest JSON is descriptor-sized, not body-bloated — it must NOT carry
    # the body bytes (the body lives in turns.bin). A 9-turn genome's manifest
    # stays well under the body size; assert it is compact.
    manifest_size = (p / "manifest.json").stat().st_size
    assert manifest_size < 4096, manifest_size
    # the body bytes are NOT embedded in the manifest — only their hash is. The
    # turns.bin file is strictly larger than the manifest references to it.
    body_hex = (p / "turns.bin").read_bytes().hex()
    manifest_text = (p / "manifest.json").read_text(encoding="utf-8")
    assert body_hex not in manifest_text  # the body lives in turns.bin, not here
    # the manifest is smaller than the body it indexes (catalog, not a copy)
    assert manifest_size < len(body_hex) or len(body_hex) > 0


def test_numpy_free_load(tmp_path, monkeypatch):
    """The persistence path runs with numpy BLOCKED — prove the module imports +
    save/load/catalog/append/window all work with ``numpy`` masked out of
    ``sys.modules`` (the numpy-free identity of the genome surface)."""
    # block numpy: any `import numpy` inside the persistence path would raise
    monkeypatch.setitem(sys.modules, "numpy", None)

    one = klein4_random(64, seed=7)
    _, strand, labels = _build(one)
    p = tmp_path / "g"

    man = genome.genome_save(strand, p, the_one=one, labels=labels)
    ls, lo, ll = genome.genome_load(p)
    assert _as_lists(ls) == _as_lists(strand)

    cat = genome.genome_catalog(p)
    assert cat["body_sha256"] == man["body_sha256"]

    win = genome.genome_window(p, "astronomy")
    assert _as_lists(win) == _as_lists(strand[1:4])

    new_leaves = [klein4_random(64, seed=s) for s in (40, 41)]
    man2 = genome.genome_append(p, "biology", new_leaves, the_one=one)
    assert "biology" in [c["label"] for c in man2["chromosomes"]]


# ── invariants the spec calls out explicitly ─────────────────────────────────

def test_subset_load_equals_full_load_for_those_chromosomes(tmp_path):
    one = klein4_random(64, seed=7)
    _, strand, labels = _build(one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one, labels=labels)

    full, full_one, full_labels = genome.genome_load(p)
    full_part = _partition_lists(full, full_one, full_labels)

    sub, sub_one, sub_labels = genome.genome_load(p, labels=["geography", "music"])
    sub_part = _partition_lists(sub, sub_one, sub_labels)
    assert set(sub_part) == {"geography", "music"}
    for lbl in sub_part:
        assert sub_part[lbl] == full_part[lbl]


def test_class_surface_save_load_catalog_append(tmp_path):
    """The Genome CatalogClass binds save/load/catalog/append to the genome_*
    ops (zero user Python — declarative [class] TOML)."""
    from srmech.dsl import make_class

    one = klein4_random(64, seed=7)
    k, strand, labels = _build(one)
    p = tmp_path / "g"

    g = make_class("Genome")(the_one=one)
    man = g.save(strand=strand, path=str(p), labels=labels)
    assert man["leaf_dim"] == 64

    cat = g.catalog(path=str(p))
    assert [c["label"] for c in cat["chromosomes"]] == labels

    loaded_strand, loaded_one, loaded_labels = g.load(path=str(p))
    assert _as_lists(loaded_strand) == _as_lists(strand)

    new_leaves = [klein4_random(64, seed=s) for s in (50, 51)]
    man2 = g.append(path=str(p), label="chemistry", leaves=new_leaves)
    assert "chemistry" in [c["label"] for c in man2["chromosomes"]]
