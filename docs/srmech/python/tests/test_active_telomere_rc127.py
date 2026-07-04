"""rc127 (UPSTREAM §127, #726) — the ACTIVE TELOMERE: the Hayflick descending
counter that makes the chromosome GENUINELY op⊗operand (turns the #726 lens into a
theorem).

#726 PROVED the genome telomere is a PASSIVE op-SLOT — swapping the cap leaves the
leaves unchanged; the_one governs them, telomere-independent. So "chromosome =
op⊗operand" was a LENS, not a theorem. The ONE build that makes it a THEOREM: make the
telomere ACTIVE — carry an exact counter (the OPERAND) that MODULATES a downstream op
(the OPERATOR). The active telomere = op⊗operand fused in ONE cap: op = the gating rule
(:func:`telomere_tick`'s proceed/senesce decision), operand = the count. Same
``(operand, op)`` pattern as ``op_provenance.carry`` (value, operation) /
``coupling.RecoverableFold`` (lossy_bundle, exact_seed_R) — the proven op-carrying
carrier — but with an ACTIVE op, which is precisely what makes it genuinely op⊗operand.

Attested biology (ONE FACET — telomeres also cap/protect; this is NOT a reduction):
  * Harley, Futcher & Greider 1990, Nature 345(6274):458 "Telomeres shorten during
    ageing of human fibroblasts";
  * Hayflick & Moorhead 1961, Exp Cell Res 25:585 (serial cultivation of human diploid
    cell strains);
  * Hayflick 1965, Exp Cell Res 37(3):614 (the Hayflick Limit).

Proven here (the ask's DoD):
  1. an active telomere with count N allows EXACTLY N divides, then the (N+1)-th REFUSES
     with an honest senescence verdict; the count decrements by EXACTLY 1 each divide;
  2. the chromosome SELF-DESCRIBES its current count by bare-strand scan (no manifest);
  3. plain-telomere back-compat: a plain telomere reads UNCHANGED and is un-gated;
  4. THE DUALITY: the count modulates the op — same divide call, proceed-when-count>0
     vs refuse-when-count==0;
  5. Python==C byte-identical (turns.bin + manifest on a genome with an active telomere;
     the divide op's decrement + senescence verdict identical);
  6. format v6 → v7 additive dual-read; a plain-telomere genome reads identically.

numpy-free per the genome module's discipline; no abs() (the count is an exact
Class-I/N integer, never negated).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hv import HV


def _one(dim=64):
    return G._default_the_one(dim)


def _leaves(n, dim=64, base=0):
    return [HV.from_sequence([(base + i + k) % 4 for k in range(dim)], sectors=4)
            for i in range(n)]


# ── (1) the DoD — N divides then senescence; exact decrement ─────────────────

@pytest.mark.parametrize("N", [0, 1, 3, 7])
def test_n_divides_then_senescence(N):
    """An active telomere of count N allows EXACTLY N divides; the (N+1)-th refuses."""
    one = _one()
    strand = G.chromosome(_leaves(2), one, label="cell", active_count=N)
    cur = strand
    for i in range(N):
        r = G.telomere_tick(cur)
        assert r["status"] == G.TELOMERE_DIVIDED, (i, r)
        assert r["count_before"] == N - i
        assert r["count_after"] == N - i - 1        # decrement by EXACTLY 1
        cur = r["daughter"]
        assert cur is not None
        # the daughter self-describes its shortened count on the bare strand
        assert G._active_telomere_count(cur[0]) == N - i - 1
    # the (N+1)-th tick is honest senescence — no daughter, count stays 0
    r = G.telomere_tick(cur)
    assert r["status"] == G.TELOMERE_SENESCENT
    assert r["count_before"] == 0 and r["count_after"] == 0
    assert r["daughter"] is None


def test_decrement_is_exactly_one_each_step():
    """The count walks N, N-1, …, 1, 0 — no skips, no double-decrements."""
    one = _one()
    N = 10
    cur = G.chromosome(_leaves(1), one, label="c", active_count=N)
    seen = [G._active_telomere_count(cur[0])]
    while True:
        r = G.telomere_tick(cur)
        if r["status"] == G.TELOMERE_SENESCENT:
            break
        cur = r["daughter"]
        seen.append(G._active_telomere_count(cur[0]))
    assert seen == list(range(N, -1, -1))           # N, N-1, …, 1, 0


def test_senescence_forever_at_zero():
    """A senescent cell stays senescent — repeated ticks never resurrect it."""
    one = _one()
    strand = G.chromosome(_leaves(1), one, label="dead", active_count=0)
    for _ in range(4):
        r = G.telomere_tick(strand)
        assert r["status"] == G.TELOMERE_SENESCENT and r["daughter"] is None


# ── (2) bare-strand count self-description (§44; no manifest) ─────────────────

def test_bare_strand_self_describes_count(tmp_path):
    """The chromosome recovers its CURRENT count by SCANNING the strand — no manifest,
    no the_one (the count lives inline in the 0x74 cap)."""
    one = _one()
    strand = G.chromosome(_leaves(3), one, label="k", active_count=42)
    # in-memory bare scan
    cap = next(hv for hv in strand if G._cap_kind(hv) == G.ACTIVE_TELOMERE_MARKER)
    assert G._active_telomere_count(cap) == 42
    assert G._active_telomere_label(cap) == "k"
    # on disk with the manifest DELETED — rebuild-by-scan still finds the count
    p = tmp_path / "g"
    G.genome_save(strand, p, one)
    (p / "manifest.json").unlink()
    strand2, _one2, _labels = G.genome_load(p, the_one=one)
    cap2 = next(hv for hv in strand2 if G._cap_kind(hv) == G.ACTIVE_TELOMERE_MARKER)
    assert G._active_telomere_count(cap2) == 42
    # bytes survive the disk round-trip exactly
    assert cap.tobytes() == cap2.tobytes()


def test_count_layout_and_label_uniform():
    """The count sits AFTER the label's NUL, so the label decode is UNIFORM with every
    other cap kind (_unpack_cap reads it), while the count read is active-specific."""
    one = _one()
    cap = G.active_telomere("mylabel", 5, dim=64)
    assert int(cap[0]) == G.ACTIVE_TELOMERE_MARKER == 0x74
    # _unpack_cap (the generic cap label reader) recovers the label with no special case
    marker, label = G._unpack_cap(cap)
    assert marker == 0x74 and label == "mylabel"
    assert G._active_telomere_count(cap) == 5


# ── (3) plain-telomere back-compat: unchanged + un-gated ─────────────────────

def test_plain_telomere_reads_unchanged_and_is_ungated():
    """A plain telomere is UNCHANGED (still 0x43) and CANNOT be ticked (un-gated —
    telomere_tick only accepts an active telomere)."""
    one = _one()
    plain = G.chromosome(_leaves(2), one, label="plain")          # plain telomere
    assert G._cap_kind(plain[0]) == G.CHROM_CAP_MARKER
    with pytest.raises(ValueError, match="does not open with an active telomere"):
        G.telomere_tick(plain)
    # the leaves recover exactly (a plain chromosome is unaffected by the §127 code)
    assert [list(x) for x in G.recall(plain, one)] == [list(x) for x in _leaves(2)]


def test_active_telomere_disturbs_only_the_cap():
    """The active telomere GOVERNS the leaves WITHOUT decoding them: an active-telomere
    chromosome and the plain one over the SAME leaves differ ONLY in the leading cap —
    every coupled data turn is byte-identical."""
    one = _one()
    lv = _leaves(3, base=2)
    plain = G.chromosome(lv, one, label="c")
    active = G.chromosome(lv, one, label="c", active_count=9)
    assert plain[0].tobytes() != active[0].tobytes()          # only the cap differs
    assert [t.tobytes() for t in plain[1:]] == [t.tobytes() for t in active[1:]]
    # and the divide does not decode/re-couple the leaves — the daughter's turns are
    # byte-identical to the parent's (biology shortens the cap, not the genes)
    r = G.telomere_tick(active)
    assert [t.tobytes() for t in r["daughter"][1:]] == [t.tobytes() for t in active[1:]]


def test_v2_fixture_still_reads(tmp_path):
    """A pre-§127 (v2) genome fixture reads UNCHANGED — the walker gains one branch,
    never breaks an existing genome (dual-read back-compat)."""
    import shutil
    from pathlib import Path
    src = Path(__file__).resolve().parent / "data" / "genome_v2_fixture"
    if not src.exists():
        pytest.skip("v2 fixture not present")
    dst = tmp_path / "v2"
    shutil.copytree(src, dst)
    cat = G.genome_catalog(dst)
    assert cat["format_version"] == 2                          # reading never rewrites
    strand, one, labels = G.genome_load(dst)
    assert set(labels) == {"alpha", "multi", "plain"}


# ── (4) THE DUALITY — the count (operand) modulates the op (operator) ────────

def test_duality_operand_modulates_operator():
    """THE op⊗operand THEOREM: the SAME telomere_tick call yields DIFFERENT operator
    behaviour selected ONLY by the operand (the count) — proceed at count>0, refuse at
    count==0. The op is genuinely modulated by the operand it carries."""
    one = _one()
    lv = _leaves(2)
    # two chromosomes IDENTICAL except the operand (count): 1 vs 0
    alive = G.chromosome(lv, one, label="x", active_count=1)
    dead = G.chromosome(lv, one, label="x", active_count=0)
    # identical strands apart from the count byte in the cap
    assert [t.tobytes() for t in alive[1:]] == [t.tobytes() for t in dead[1:]]
    # SAME call → operator behaviour SELECTED by the operand
    r_alive = G.telomere_tick(alive)
    r_dead = G.telomere_tick(dead)
    assert r_alive["status"] == G.TELOMERE_DIVIDED     # operand 1 → proceed
    assert r_dead["status"] == G.TELOMERE_SENESCENT    # operand 0 → refuse
    # the op⊗operand tie: this is the (operand, op) pattern of op_provenance /
    # RecoverableFold, with an ACTIVE op — documented on active_telomere / telomere_tick
    assert "op_provenance" in G.active_telomere.__doc__
    assert "RecoverableFold" in G.active_telomere.__doc__


# ── (5) disk round-trip + partition of an active-telomere genome ─────────────

def test_active_telomere_genome_saves_partitions_v7(tmp_path):
    """A genome MIXING a plain and an active-telomere chromosome saves at v7, and
    partition recovers BOTH kernels (the active telomere is a chromosome boundary)."""
    one = _one()
    plain = G.chromosome(_leaves(2), one, label="plainC")
    active = G.chromosome(_leaves(2, base=1), one, label="activeC", active_count=5)
    strand = plain + active
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 8                          # the v8 writer stamps 8 (rc128 §128)
    assert [c["label"] for c in man["chromosomes"]] == ["plainC", "activeC"]
    strand2, one2, _ = G.genome_load(p)
    parts = G.partition(strand2, one2)
    assert set(parts) == {"plainC", "activeC"}
    assert [list(x) for x in parts["activeC"]] == [list(x) for x in _leaves(2, base=1)]
    # the active-telomere count survives the whole save/load
    cap = next(hv for hv in strand2 if G._cap_kind(hv) == G.ACTIVE_TELOMERE_MARKER)
    assert G._active_telomere_count(cap) == 5


def test_plain_genome_v7_body_has_no_active_marker(tmp_path):
    """A plain-telomere genome saved by the v7 writer carries NO 0x74 block marker — it
    is byte-identical to the v6 body except the manifest format_version field."""
    one = _one()
    strand = G.genome({"a": _leaves(2), "b": _leaves(3)}, one)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 8
    for raw, _decoded in G._walk_region_blocks((p / "turns.bin").read_bytes(), 64,
                                               context="t"):
        assert raw[0] != G.ACTIVE_TELOMERE_MARKER              # no active telomere used
    # and it still round-trips
    parts = G.partition(*G.genome_load(p)[:2])
    assert set(parts) == {"a", "b"}


# ── (6) error / guard cases ──────────────────────────────────────────────────

def test_count_must_be_nonnegative_int():
    with pytest.raises(ValueError, match="non-negative"):
        G.active_telomere("c", -1)
    with pytest.raises(ValueError, match="exact int"):
        G.active_telomere("c", 1.5)


def test_active_count_mutually_exclusive_with_kernel():
    one = _one()
    with pytest.raises(ValueError, match="single-kernel telomere form"):
        G.chromosome(_leaves(1), one, label="c", active_count=3, kernel=True)


def test_empty_strand_rejected():
    with pytest.raises(ValueError, match="empty strand"):
        G.telomere_tick([])


# ── (5) Python==C byte-identical ──────────────────────────────────────────────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("count", [0, 1, 5, 255, 65537])
def test_python_equals_c_tick(count):
    """The native tick (srmech_genome_telomere_tick) is BYTE-IDENTICAL to pure Python:
    same senescent flag, same count_after, same daughter cap bytes."""
    one = _one()
    cap = G.active_telomere("cell", count, dim=64)
    # native
    sen_c, after_c, newcap_c = _native.genome_telomere_tick_c(cap.tobytes(), 64)
    # pure
    if count == 0:
        assert sen_c is True and after_c == 0 and newcap_c == cap.tobytes()
    else:
        assert sen_c is False and after_c == count - 1
        assert G._active_telomere_count(G._hv_from_block(newcap_c)) == count - 1


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("count", [0, 1, 12])
def test_python_equals_c_genome_save(tmp_path, count):
    """genome_save / genome_load write turns.bin + manifest.json BYTE-IDENTICALLY on a
    genome carrying an active telomere, native-vs-forced-pure."""
    one = _one()
    strand = (G.chromosome(_leaves(2), one, label="p")
              + G.chromosome(_leaves(2, base=1), one, label="a", active_count=count))

    dn = tmp_path / "native"
    G.genome_save(strand, dn, one)
    n_body = (dn / "turns.bin").read_bytes()
    n_man = (dn / "manifest.json").read_bytes()

    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        dp = tmp_path / "pure"
        G.genome_save(strand, dp, one)
        p_body = (dp / "turns.bin").read_bytes()
        p_man = (dp / "manifest.json").read_bytes()
    finally:
        _native.has_native_genome = real

    assert n_body == p_body
    assert n_man == p_man
    # both recover the count
    for d in (dn, dp):
        s, o, _ = G.genome_load(d)
        cap = next(hv for hv in s if G._cap_kind(hv) == G.ACTIVE_TELOMERE_MARKER)
        assert G._active_telomere_count(cap) == count


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
def test_python_equals_c_full_hayflick(tmp_path):
    """End-to-end native: build → save → load → run the whole Hayflick countdown; the
    native and pure ticks agree at every step (same daughters, same senescence)."""
    one = _one()
    N = 6
    strand = G.chromosome(_leaves(3), one, label="cell", active_count=N)
    # native ticks
    cur, native_counts = strand, []
    while True:
        r = G.telomere_tick(cur)                       # native-dispatched
        native_counts.append((r["status"], r["count_after"]))
        if r["status"] == G.TELOMERE_SENESCENT:
            break
        cur = r["daughter"]
    # forced pure ticks
    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        cur, pure_counts = strand, []
        while True:
            r = G.telomere_tick(cur)
            pure_counts.append((r["status"], r["count_after"]))
            if r["status"] == G.TELOMERE_SENESCENT:
                break
            cur = r["daughter"]
    finally:
        _native.has_native_genome = real
    assert native_counts == pure_counts
    assert native_counts == [(G.TELOMERE_DIVIDED, N - 1 - i) for i in range(N)] \
        + [(G.TELOMERE_SENESCENT, 0)]
