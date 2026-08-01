"""rc115 (issue #1245 ask (b), UPSTREAM §56) — genome O(1)-AMORTISED append +
non-quadratic pack + the region-chain hash contract (format v4).

rc114 made a data turn 4 Klein-4 symbols/byte (ask (a)); it deliberately kept the
whole-body ``body_sha256`` — which cannot be recomputed in O(1) on append. ask (b)
changes that contract:

  * the manifest gains a ``regions`` array — one {byte_offset, byte_len, sha256}
    per chromosome (its FULL-region digest, == the chromosome's ``.chr`` / AMSC
    provenance unit), so a region hash is the O(1) provenance unit;
  * ``body_sha256`` becomes the REGION CHAIN Hn = sha256(Hn-1 || region_n) seeded
    by H0 = sha256("") — O(1)-maintainable on append (extend the head), yet
    re-verifiable from the file (re-hash each region, re-fold) AND body-derivable
    by a §44 scan (so a rebuild-by-scan reproduces it byte-identically);
  * ``genome_append`` TAIL-EXTENDS turns.bin + updates the manifest in O(1) — it
    never reads / rewrites / re-hashes the whole body; and
  * ``genome_pack`` compacts in a SINGLE pass (linear), not the old O(N²) import.

Proven here: the contract's shape, the O(1)-append invariants (prior entries
byte-identical, chain extension, no whole-body rewrite), the re-verifiability
(a flipped region byte fails), the §44 rebuild==written invariant on v4, the
provenance-unit unification (region sha == the .chr region hash), and pack
round-trip exactness. Timings live in notes/rc114_genome_bitpack_bench.py.

numpy-free per the genome module's discipline.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from srmech.biology import genome as G
from srmech.amsc import _native
from srmech.amsc.format import sha256_bytes
from srmech.math.hdc import klein4_expand

_DIM = 24


def _one():
    return klein4_expand(_DIM, 7)


def _leaves(n, base=0):
    pool = [klein4_expand(_DIM, s + base) for s in range(8)]
    return [pool[i % 8] for i in range(n)]


def _as_lists(xs):
    return [list(x) for x in xs]


# ── the v4 manifest shape + the region chain ────────────────────────────────

def test_save_writes_v4_regions_and_chain(tmp_path):
    """A fresh save RETURNS the current format_version (v12 writer) with the DERIVED
    regions array (one per chromosome, tiling the body) and body_sha256 = the region
    chain. v12: the arrays live in the returned/derived catalog, NOT on disk (the
    manifest is head-only, ADR-0003); the §56/v4 region-chain machinery is unchanged."""
    one = _one()
    strand = G.genome({"a": _leaves(5), "b": _leaves(3, base=10)}, one)
    man = G.genome_save(strand, tmp_path / "g", coupling=one)

    assert man["format_version"] == 19
    assert [r["byte_offset"] for r in man["regions"]] == \
        [c["byte_offset"] for c in man["chromosomes"]]
    # regions tile the body contiguously from 0
    off = 0
    body = (tmp_path / "g" / "turns.bin").read_bytes()
    for r in man["regions"]:
        assert r["byte_offset"] == off
        assert r["sha256"] == sha256_bytes(body[off:off + r["byte_len"]])
        off += r["byte_len"]
    assert off == len(body)
    # body_sha256 IS the chain over the region digests (H0 = sha256(b""))
    acc = sha256_bytes(b"")
    for r in man["regions"]:
        acc = sha256_bytes(bytes.fromhex(acc) + bytes.fromhex(r["sha256"]))
    assert man["body_sha256"] == acc
    # the MPR attestation.response_sha256 IS the chain head (still re-verifiable)
    import json
    rec = json.loads((tmp_path / "g" / "manifest.json").read_text("utf-8"))
    assert rec["attestation"]["response_sha256"] == man["body_sha256"]


# ── O(1) append: prior bytes/entries untouched, chain extended ──────────────

def test_append_is_tail_extend_prior_untouched(tmp_path):
    """Append tail-extends turns.bin (prior bytes an EXACT prefix) and only
    APPENDS a chromosome + region entry + extends the chain — every prior entry
    byte-identical, n_turns grows by the appended block count."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  coupling=one)
    man0 = G.genome_catalog(tmp_path / "g")
    body0 = (tmp_path / "g" / "turns.bin").read_bytes()

    new = _leaves(6, base=20)
    man1 = G.genome_append(tmp_path / "g", "c1", new, one)
    body1 = (tmp_path / "g" / "turns.bin").read_bytes()

    assert body1[:len(body0)] == body0                    # append-only prefix
    region = body1[len(body0):]
    assert man1["chromosomes"][:1] == man0["chromosomes"]  # prior entry identical
    assert man1["regions"][:1] == man0["regions"]          # prior region identical
    assert man1["chromosomes"][1]["byte_offset"] == len(body0)
    assert man1["regions"][1]["sha256"] == sha256_bytes(region)
    # the chain extended in O(1) from the prior head
    assert man1["body_sha256"] == sha256_bytes(
        bytes.fromhex(man0["body_sha256"]) + bytes.fromhex(sha256_bytes(region)))
    assert man1["n_turns"] == man0["n_turns"] + 1 + 6      # 1 cap + 6 turns
    # the appended chromosome reads back leaf-for-leaf
    win = G.genome_window(tmp_path / "g", "c1")
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(new)


def test_rebuild_by_scan_equals_written_manifest_v4(tmp_path):
    """§44 held across the v4 contract: after several appends, deleting the
    manifest and rebuilding-by-scan reproduces the WRITTEN manifest EXACTLY
    (regions + chain included) — the chain is a pure function of the body."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  coupling=one)
    for k in range(1, 5):
        written = G.genome_append(tmp_path / "g", f"c{k}", _leaves(k + 2, base=k),
                                  one)
    (tmp_path / "g" / "manifest.json").unlink()
    rebuilt = G.genome_catalog(tmp_path / "g", coupling=one)
    assert rebuilt == written


# ── re-verifiability: a flipped region byte fails the integrity bound ────────

def test_flipped_region_byte_fails_integrity(tmp_path):
    """The region chain is re-verifiable: corrupting one body byte fails the
    whole-genome load (a GenomeBoundingError) — the region hash + chain catch it."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  coupling=one)
    G.genome_append(tmp_path / "g", "c1", _leaves(6, base=20), one)
    body = bytearray((tmp_path / "g" / "turns.bin").read_bytes())
    body[-1] ^= 0x01                                       # flip a tail byte
    (tmp_path / "g" / "turns.bin").write_bytes(bytes(body))
    with pytest.raises(G.GenomeBoundingError):
        G.genome_load(tmp_path / "g")


# ── provenance-unit unification: region sha == the .chr region hash ─────────

def test_region_sha_is_the_chr_region_hash(tmp_path):
    """The manifest's per-chromosome region sha256 IS the .chr bundle's region
    hash (the AMSC provenance unit register_attested uses) — one hash, two views."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  coupling=one)
    G.genome_append(tmp_path / "g", "c1", _leaves(6, base=20), one)
    man = G.genome_catalog(tmp_path / "g")
    by_label = {c["label"]: r for c, r in zip(man["chromosomes"], man["regions"])}
    for label in ("c0", "c1"):
        cdata = G.genome_export(tmp_path / "g", label, tmp_path / f"{label}.chr")
        assert cdata["region"]["sha256"] == by_label[label]["sha256"]


# ── non-quadratic pack: single-pass, round-trip EXACT ───────────────────────

def test_pack_single_pass_roundtrip_exact(tmp_path):
    """genome_pack compacts a directory of .chr bundles in one pass; every
    chromosome round-trips leaf-for-leaf and the packed manifest is v4."""
    one = _one()
    kernels = {f"c{k}": _leaves(k + 3, base=k) for k in range(6)}
    G.genome_save(G.genome(kernels, one), tmp_path / "g", coupling=one)
    G.genome_explode(tmp_path / "g", tmp_path / "loose", coupling=one)
    man = G.genome_pack(tmp_path / "loose", tmp_path / "packed", coupling=one)
    assert man["format_version"] == 19
    assert len(man["regions"]) == len(kernels)
    for label, leaves in kernels.items():
        win = G.genome_window(tmp_path / "packed", label, coupling=one)
        assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(leaves)


def test_many_appends_all_read_back(tmp_path):
    """A helix grown by MANY O(1) appends loads back whole, every chromosome
    leaf-for-leaf, and the body integrity bound passes (the chain covers all)."""
    one = _one()
    want = {}
    lv0 = _leaves(4)
    G.genome_save(G.chromosome(lv0, one, label="c000"), tmp_path / "g", coupling=one)
    want["c000"] = _as_lists(lv0)
    for k in range(1, 30):
        lv = _leaves((k % 9) + 2, base=k)
        G.genome_append(tmp_path / "g", f"c{k:03d}", lv, one)
        want[f"c{k:03d}"] = _as_lists(lv)
    strand, lo, labels = G.genome_load(tmp_path / "g")      # verifies the chain
    part = G.partition(strand, lo, labels)                  # decodes leaves inline
    for label, leaves in want.items():
        assert _as_lists(part[label]) == leaves


# ── v12 O(1) append: the manifest is HEAD-ONLY and FIXED-SIZE (F833 wall stays shut) ──

def test_append_is_o1_head_only_fixed_manifest_v12(tmp_path):
    """The deterministic (non-timing) O(1)-append regression guard. v12 writes a
    HEAD-ONLY manifest (no per-chromosome ``chromosomes`` / ``regions`` arrays on
    disk — ADR-0003), so N appends do NOT rewrite an O(n_chromosomes) catalog and
    the O(N^2) wall (F833) stays closed. Proxy for O(1): manifest.json stays
    fixed-size as the chromosome count grows, and the arrays are absent on disk."""
    import json
    one = _one()
    g = tmp_path / "g"
    G.genome_save(G.chromosome(_leaves(2), one, label="seed"), g, coupling=one)

    def on_disk():
        raw = json.loads((g / "manifest.json").read_text("utf-8"))["data"]
        return (g / "manifest.json").stat().st_size, raw

    sz0, d0 = on_disk()
    assert "chromosomes" not in d0 and "regions" not in d0   # head-only from the first save
    assert d0["n_chromosomes"] == 1

    data = G.genome_catalog(g, coupling=one)                  # full derived catalog to thread
    for k in range(200):
        data = G.genome_append(g, f"c{k:04d}", _leaves(2), one, catalog=data)  # O(1) threaded

    sz1, d1 = on_disk()
    assert "chromosomes" not in d1 and "regions" not in d1   # STILL head-only after 200 appends
    assert d1["n_chromosomes"] == 201
    # the head is FIXED WIDTH — it does NOT grow with n_chromosomes (only small ints
    # change; coupling hex + body_sha256 are constant width). This is the O(1) disk write.
    assert sz1 <= sz0 + 64, (sz0, sz1)
    # the threaded in-memory catalog is complete, and equals the cold body-derived one.
    assert len(data["chromosomes"]) == 201
    cold = G.genome_catalog(g, coupling=one)
    assert len(cold["chromosomes"]) == 201
    assert cold["body_sha256"] == data["body_sha256"]        # threaded head == derived head


# ── §95.2 / #1407 ergonomics: the three catalog modes + the {} footgun ───────

def test_catalog_load_resumes_a_streaming_loop(tmp_path):
    """``catalog="load"`` reads the threadable catalog from disk ONCE (the resume-with-
    no-prior-return-in-hand path, §95.2), then threads it — byte-identical to threading a
    catalog derived up front. The two loops append the same chromosomes to two genomes
    and the bodies + region chains match."""
    one = _one()
    ga, gb = tmp_path / "ga", tmp_path / "gb"
    for g in (ga, gb):
        G.genome_save(G.chromosome(_leaves(2), one, label="seed"), g, coupling=one)
    a = G.genome_catalog(ga, coupling=one)                    # thread a derived catalog
    b = "load"                                               # resume with no dict in hand
    for k in range(6):
        a = G.genome_append(ga, f"c{k}", _leaves(2, base=k), one, catalog=a)
        b = G.genome_append(gb, f"c{k}", _leaves(2, base=k), one, catalog=b)
    assert (ga / "turns.bin").read_bytes() == (gb / "turns.bin").read_bytes()
    assert a["body_sha256"] == b["body_sha256"]
    assert a["n_chromosomes"] == b["n_chromosomes"] == 7
    # "load"'s FIRST return is already a threadable dict (carries the per-chromosome arrays)
    assert len(b["chromosomes"]) == 7 and len(b["regions"]) == 7


def test_catalog_empty_dict_is_a_clear_error_not_keyerror(tmp_path):
    """``catalog={}`` (or any dict with no ``leaf_dim``) is NOT a genome catalog — it
    raises a clear ValueError naming the modes, never a bare KeyError (§95.2 footgun)."""
    one = _one()
    g = tmp_path / "g"
    G.genome_save(G.chromosome(_leaves(2), one, label="seed"), g, coupling=one)
    with pytest.raises(ValueError, match="leaf_dim"):
        G.genome_append(g, "x", _leaves(2), one, catalog={})
    with pytest.raises(ValueError, match="load"):
        G.genome_append(g, "x", _leaves(2), one, catalog={"n_turns": 3})


# ── §97 (#1407) — the native append arena must be O(1) RAM, not O(body) ───────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome append needed for the §97 arena-size regression")
def test_native_append_arena_is_o1_not_o_body(tmp_path):
    """§97 regression: the native append arena (`_native._genome_ws`) must stay
    manifest-sized (O(1)), NOT grow with the body. A v12 genome's manifest is
    HEAD-ONLY (no `regions` array — ADR-0003), and the rc115 detection mis-read that
    absence as "legacy" → it sized the shared arena to the WHOLE growing `turns.bin`
    per append, and the arena (grown-to-max, never shrunk) ballooned to a whole-body-
    rebuild size → OOM at corpus scale (95 GB after 3361 bodies). The O(1) tail-extend
    path is now keyed on `format_version >= 4`, so the arena stays O(1)."""
    dim = 256
    one = klein4_expand(dim, 7)

    def body(i, n=25):
        return [klein4_expand(dim, 10_000 + i * n + j) for j in range(n)]

    g = tmp_path / "g"
    G.genome_save(G.chromosome(body(0), one, label="seed"), g, coupling=one)
    cat = G.genome_catalog(g, coupling=one)

    def ws_len():
        return 0 if _native._genome_ws is None else len(_native._genome_ws)

    for k in range(20):
        cat = G.genome_append(g, f"c{k:04d}", body(k + 1), one, catalog=cat)
    ws_early = ws_len()
    for k in range(20, 200):                 # 180 more appends — turns.bin grows ~300 KB
        cat = G.genome_append(g, f"c{k:04d}", body(k + 1), one, catalog=cat)
    ws_late = ws_len()
    turns = (g / "turns.bin").stat().st_size

    # the arena did NOT track the ~turns.bin growth — it is manifest-sized (O(1)).
    # (pre-fix, ws_late grew by ~the turns growth ≫ this margin.)
    assert ws_late <= ws_early + 65_536, (
        f"append arena grew {ws_late - ws_early} B over 180 appends "
        f"(early={ws_early}, late={ws_late}, turns.bin={turns}) — it is tracking the "
        f"body (O(n) RAM), not manifest-sized (§97)")


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome needed for the §97 C-helper arena-size check")
def test_c_helper_sizes_append_arena(tmp_path):
    """§97: the C SSoT ``srmech_genome_append_arena_bytes`` ITSELF (not just the Python
    wrapper) sizes the v12 append arena O(MANIFEST), not O(body). A v12 manifest is
    HEAD-ONLY (fixed-size — no ``regions`` array on disk, ADR-0003), so as turns.bin
    grows by ~300 KB over 180 appends the C helper's returned arena size does NOT track
    it. This proves the v12/legacy classification lives in C: a bare-C host sizes the
    append arena right with no Python (the wrapper only relays this number)."""
    import ctypes

    lib = _native.LIB
    if not hasattr(lib, "srmech_genome_append_arena_bytes"):
        pytest.skip("native lib predates srmech_genome_append_arena_bytes (§97)")

    dim = 256
    one = klein4_expand(dim, 7)

    def body(i, n=25):
        return [klein4_expand(dim, 10_000 + i * n + j) for j in range(n)]

    g = tmp_path / "g"
    G.genome_save(G.chromosome(body(0), one, label="seed"), g, coupling=one)
    cat = G.genome_catalog(g, coupling=one)

    def helper_arena():
        """The raw C helper's arena size for the current on-disk genome (bypass the
        Python wrapper — this exercises the C classification directly)."""
        man_sz = (g / "manifest.json").stat().st_size
        scratch = (ctypes.c_char * (man_sz + 1))()
        out = ctypes.c_size_t(0)
        rc = lib.srmech_genome_append_arena_bytes(
            str(g).encode("utf-8"), ctypes.c_size_t(4096),
            ctypes.cast(scratch, ctypes.c_void_p), ctypes.c_size_t(man_sz + 1),
            ctypes.byref(out))
        assert rc == 0, f"srmech_genome_append_arena_bytes rc={rc}"
        return int(out.value)

    for k in range(20):
        cat = G.genome_append(g, f"c{k:04d}", body(k + 1), one, catalog=cat)
    need_early = helper_arena()
    turns_early = (g / "turns.bin").stat().st_size
    assert need_early > 0

    for k in range(20, 200):                 # 180 more appends — turns.bin grows ~300 KB
        cat = G.genome_append(g, f"c{k:04d}", body(k + 1), one, catalog=cat)
    need_late = helper_arena()
    turns_late = (g / "turns.bin").stat().st_size

    assert turns_late - turns_early > 100_000    # the body genuinely grew
    # the C helper's arena did NOT track that growth — it is O(manifest) (head-only,
    # fixed-size), NOT O(body). (pre-§97 the arena tracked the whole body → OOM.)
    assert need_late - need_early < 65_536, (
        f"C helper append arena grew {need_late - need_early} B while turns.bin grew "
        f"{turns_late - turns_early} B — it is body-scaled, not manifest-scaled (§97)")
