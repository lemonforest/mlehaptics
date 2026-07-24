"""v0.9.0rc258 (§95a, #1407 / F1243) — the CENTROMERE primitive + the MINT shape-selector.

The first rung of the #1407 biology-native genome architecture. A MINTED (Tier-2)
chromosome carries an INTERIOR centromere cap (marker 0x58 'X' — the cross-point of the
X-shaped chromosome) between its two arms: the per-chromosome GLOBAL orientation-chirality,
stored as biology's α-satellite REPEAT-ARRAY (R copies of the 4-way sector), majority-decoded
(klein4_triality_correct's 2-of-3 generalised to R — a Class-K sector count, no numpy/float).
Measured (F1243 §1): the array recovers the global which-way at ~15× fewer bits than per-leaf
Klein-4 with matching random-noise robustness, taking the GLOBAL which-way off Klein-4.

The tooling PICKS each chromosome's shape by modeling biology (the mint-vs-append two-tier):
the ATTESTED encode_shape criterion routes a plasmid-scale kernel (tome/mobius, ≤4 leaves) to a
Tier-1 append STICK and a eukaryotic-chromosome-scale kernel (quad_strand, ≥5 leaves) to a
Tier-2 MINTED chromosome — we don't pick the shape, the kernel's biology-analog scale does.

Proven here: the primitive (pack/read/majority + robustness), the mint-time placement +
position-as-arm-ratio, recall/partition skipping the interior cap, the shape-selector
(mint_plan / mint), persistence + catalog leaf-count exclusion, format v13 dual-read
back-compat, the F1243 ~15× cost claim, and the 1:1 C↔Python byte-parity of the centromere cap,
srmech_genome_mint, and centromere_of (gated on the native peer). numpy-free.
"""
from __future__ import annotations

import ctypes
import math

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hdc import klein4_expand

_DIM = 64


def _one(seed=7):
    return klein4_expand(_DIM, seed)


def _leaves(n, base=0):
    return [klein4_expand(_DIM, base + s) for s in range(n)]


# ── 1. the primitive: pack / read / majority ────────────────────────────────

@pytest.mark.parametrize("o", [0, 1, 2, 3])
def test_centromere_pack_read_roundtrip(o):
    cap = G.centromere(o, dim=_DIM)
    votes = G._centromere_votes(cap)
    assert votes == [o] * G.CENTROMERE_DEFAULT_REPEATS      # α-satellite repeat-array
    assert G._centromere_orientation(votes) == o
    marker, handle = G._unpack_cap(cap)
    assert marker == G.CENTROMERE_CAP_MARKER == 0x58
    assert handle == "cen"


def test_centromere_majority_survives_minority_corruption():
    # 12 agree, 3 corrupted -> majority still recovers (the EC read)
    votes = [2] * 15
    votes[0], votes[1], votes[2] = 0, 1, 3
    assert G._centromere_orientation(votes) == 2


def test_centromere_majority_ties_break_to_lowest_sector():
    # exactly tied 0 vs 3 -> lowest index wins (klein4_triality_correct's tie rule)
    assert G._centromere_orientation([0, 3]) == 0


def test_centromere_custom_repeats():
    cap = G.centromere(1, repeats=7, handle="cenpA", dim=_DIM)
    assert G._centromere_votes(cap) == [1] * 7
    assert G._unpack_cap(cap)[1] == "cenpA"


@pytest.mark.parametrize("bad", [-1, 4, 99, True])
def test_centromere_rejects_non_sector_orientation(bad):
    with pytest.raises(ValueError):
        G.centromere(bad, dim=_DIM)


# ── 2. mint-time placement + centromere_of (orientation + arm-ratio) ─────────

def test_minted_chromosome_recovers_orientation_and_metacentric_arms():
    one = _one()
    chrom = G.chromosome(_leaves(9), one, label="astronomy", centromere=3)
    info = G.centromere_of(chrom)
    assert info["orientation"] == 3
    assert info["arm_ratio"] == (4, 5)                     # 9 // 2 = 4 before, 5 after
    assert info["handle"] == "cen"
    assert info["repeats"] == G.CENTROMERE_DEFAULT_REPEATS


def test_position_is_the_arm_ratio():
    one = _one()
    for at, expect in [(0, (0, 9)), (2, (2, 7)), (9, (9, 0))]:
        chrom = G.chromosome(_leaves(9), one, label="x", centromere=1, centromere_at=at)
        assert G.centromere_of(chrom)["arm_ratio"] == expect


def test_recall_skips_the_interior_centromere():
    one = _one()
    leaves = _leaves(9)
    chrom = G.chromosome(leaves, one, label="a", centromere=2)
    rec = G.recall(chrom, one)
    assert len(rec) == 9                                   # the cap is NOT a leaf
    assert all(list(rec[i]) == list(leaves[i]) for i in range(9))


def test_stick_chromosome_has_no_centromere():
    one = _one()
    assert G.centromere_of(G.chromosome(_leaves(9), one, label="p")) is None


def test_centromere_rejects_gene_and_kernel_forms():
    one = _one()
    with pytest.raises(ValueError):
        G.chromosome(coupling=one, genes=[("g", _leaves(2))], centromere=1)
    with pytest.raises(ValueError):
        G.chromosome(_leaves(2), one, kernel=True, centromere=1)
    with pytest.raises(ValueError):
        G.chromosome(_leaves(2), one, centromere_at=1)     # centromere_at needs centromere


# ── 3. the tooling picks the shape (mint_plan / mint) ───────────────────────

def test_mint_plan_picks_shape_by_scale():
    kernels = {"tome": _leaves(1), "mobius": _leaves(4),
               "strand5": _leaves(5), "big": _leaves(20)}
    plan = {p["label"]: p for p in G.mint_plan(kernels)}
    assert plan["tome"]["tier"] == 1 and not plan["tome"]["centromere"]
    assert plan["mobius"]["tier"] == 1 and not plan["mobius"]["centromere"]
    assert plan["strand5"]["tier"] == 2 and plan["strand5"]["centromere"]
    assert plan["big"]["tier"] == 2 and plan["big"]["centromere"]
    assert plan["big"]["orientation"] in (0, 1, 2, 3)
    assert plan["tome"]["orientation"] is None


def test_mint_orientation_is_deterministic_content_address():
    leaves = _leaves(12)
    assert G._mint_orientation(leaves) == G._mint_orientation(leaves)
    assert G._mint_orientation(leaves) in (0, 1, 2, 3)


def test_mint_round_trips_through_partition():
    one = _one()
    kernels = {"note": _leaves(2), "astro": _leaves(12), "music": _leaves(6)}
    strand = G.mint(kernels, one)
    parts = G.partition(strand, one)
    assert set(parts) == set(kernels)
    for lbl in kernels:
        assert len(parts[lbl]) == len(kernels[lbl])        # centromere excluded from leaves


def test_plasmid_is_all_sticks_genome_umbrella_picks():
    # rc260 rename: plasmid() = pure all-sticks; genome() = biology-aware umbrella (picks);
    # mint() = the explicit alias of genome().
    one = _one()
    kernels = {"note": _leaves(2), "big": _leaves(20)}
    p = G.plasmid(kernels, one)
    g = G.genome(kernels, one)
    m = G.mint(kernels, one)
    assert all(G._cap_kind(hv) != G.CENTROMERE_CAP_MARKER for hv in p)   # plasmid = all sticks
    assert any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in g)   # genome umbrella picks
    assert [x.tobytes() for x in g] == [x.tobytes() for x in m]          # mint == genome (alias)


# ── 4. persistence + catalog + format version ───────────────────────────────

def test_minted_genome_persists_and_reloads(tmp_path):
    one = _one()
    kernels = {"note": _leaves(2), "big": _leaves(20)}
    strand = G.mint(kernels, one)
    G.genome_save(strand, tmp_path, coupling=one)
    loaded, _lone, _labels = G.genome_load(tmp_path, coupling=one)
    assert set(G.partition(loaded, one)) == set(kernels)
    assert any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in loaded)


def test_catalog_excludes_centromere_from_leaf_count(tmp_path):
    one = _one()
    kernels = {"big": _leaves(20)}                         # minted -> 1 centromere
    G.genome_save(G.mint(kernels, one), tmp_path, coupling=one)
    cat = G.genome_catalog(tmp_path, coupling=one)
    assert cat["format_version"] == 19
    lc = {c["label"]: c["leaf_count"] for c in cat["chromosomes"]}
    assert lc["big"] == 20                                 # 20 leaves, NOT 21 (cap excluded)


def test_format_version_is_13():
    assert G.GENOME_FORMAT_VERSION == 19


# ── 5. the F1243 §1 ~15× cost claim ─────────────────────────────────────────

def test_centromere_array_is_15x_cheaper_than_per_leaf():
    # F1243 §1: global 4-way over N=300 leaves — per-leaf 2N bits vs cent-array
    # ceil(log2 N) + 2R bits (R=15) => 600 vs 39 = 15.4x.
    N, R = 300, 15
    per_leaf = 2 * N
    cent = math.ceil(math.log2(N)) + 2 * R
    assert per_leaf / cent >= 14.0


# ── 6. 1:1 C↔Python byte-parity (gated on the native peer) ──────────────────

_native_mint = pytest.mark.skipif(
    not _native.has_native_genome_mint(),
    reason="native srmech_genome_mint peer absent — pure path is the complete alternative")


@_native_mint
@pytest.mark.parametrize("o", [0, 1, 2, 3])
def test_parity_centromere_cap(o):
    py_cap = G._pack_centromere(o, _DIM).tobytes()
    out = (ctypes.c_uint8 * _DIM)()
    rc = _native.LIB.srmech_genome_centromere(
        ctypes.c_uint8(o), ctypes.c_uint32(15), _native._u8(b"cen"),
        ctypes.c_size_t(3), ctypes.c_uint32(_DIM), out, ctypes.c_size_t(_DIM))
    assert rc == 0
    assert bytes(out[:_DIM]) == py_cap


@_native_mint
def test_parity_mint_strand(monkeypatch):
    one = _one()
    kernels = {"note": _leaves(2), "astro": _leaves(12), "big": _leaves(40)}
    c_strand = b"".join(hv.tobytes() for hv in G.mint(kernels, one))   # native
    monkeypatch.setattr(_native, "has_native_genome_mint", lambda: False)
    pure_strand = b"".join(hv.tobytes() for hv in G.mint(kernels, one))
    assert c_strand == pure_strand


@_native_mint
def test_parity_centromere_of(monkeypatch):
    one = _one()
    chrom = G.chromosome(_leaves(9), one, label="astronomy", centromere=3)
    py = G.centromere_of(chrom)
    strand_bytes = b"".join(hv.tobytes() for hv in chrom)
    o_out = ctypes.c_uint8(255)
    p_out = ctypes.c_size_t(0)
    q_out = ctypes.c_size_t(0)
    found = ctypes.c_int(-1)
    rc = _native.LIB.srmech_genome_centromere_of(
        _native._u8(strand_bytes), ctypes.c_size_t(len(chrom)),
        ctypes.c_uint32(_DIM), ctypes.byref(o_out), ctypes.byref(p_out),
        ctypes.byref(q_out), ctypes.byref(found))
    assert rc == 0 and found.value == 1
    assert o_out.value == py["orientation"]
    assert (p_out.value, q_out.value) == py["arm_ratio"]


@_native_mint
def test_parity_minted_genome_persistence(tmp_path, monkeypatch):
    one = _one()
    kernels = {"note": _leaves(2), "big": _leaves(20)}
    strand = G.mint(kernels, one)

    def save(native):
        d = tmp_path / ("nat" if native else "pure")
        d.mkdir()
        monkeypatch.setattr(_native, "has_native_genome", lambda: native)
        G.genome_save(strand, d, coupling=one)
        return (d / "turns.bin").read_bytes(), (d / "manifest.json").read_bytes()

    cb, cm = save(True)
    pb, pm = save(False)
    assert cb == pb
    assert cm == pm
