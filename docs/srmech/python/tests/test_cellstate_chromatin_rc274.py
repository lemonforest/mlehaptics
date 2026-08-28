"""v0.9.0rc274 (§98.1 / G1) — CELL-STATE-CONDITIONAL chromatin (facultative heterochromatin).

Extends the rc269 demand-load-chromatin harness. The ``0x48`` chromatin ACCESS layer is now
cell-state-conditional: an additive ``access_gate_type`` byte after ``den`` (in the cap's existing
NUL padding — same dual-read discipline as the §129 repressor / §135 copy-number) carries an
OPTIONAL gate (klein4 / boolean-DNF / threshold, the SAME gene-gate wire forms) so
``accessible(strand, cell_state)`` is COMPUTED, not stored:

  * CONSTITUTIVE (``access_gate_type == NONE`` — the pre-rc274 default; centromeric / telomeric
    H3K9me3 heterochromatin) → the STATIC stored level, CONSTANT in cell_state.
  * FACULTATIVE (a gate, from ``condense(state={...})`` — the Barr body / H3K27me3-Polycomb
    X-inactivation analog) → the WHEN-OPEN level iff the gate FIRES under cell_state, else (0, 1).

Proven here (the note's 8 shapes):
  T1  constitutive / plain invariance — a plain (no cap), a constitutive (1,1), and a
      constitutive (0,1) region each read the SAME accessible() under every cell_state.
  T2  facultative TRACKS cell_state — klein4 / boolean / threshold facultative regions each read a
      DIFFERENT accessible() under two cell_states differing on a gated bit (the core G1 claim).
  T3  back-compat — a constitutive rc274 cap is BYTE-IDENTICAL to a v15 cap; GENOME_FORMAT_VERSION
      stays 15; tools.total is 456 (the ONE new callable, accessible).
  T4  C↔Python byte-parity — accessible native==pure ∀ cell_state; the facultative cap WRITER
      native==pure (raw bytes); the demand-load PATH plan native==pure on a MIXED genome ∀ cs.
  T5  demand-load skips the right regions per state — a facultative region is in / out of the plan
      as a FUNCTION of cell_state; a state-CLOSED facultative region touches ONLY the chromatin cap.
  T6  save / reload / decondense / integrate survival — round-trips reproduce; decondense restores
      byte-identity (no re-mint); an integrated facultative provirus survives.
  T7  read-only — the strand + turns.bin are byte-identical after accessible / plan / gene_express.
  T8  level composition — a GRADED facultative cap (when-open (1,3), gated on bit1) composes
      MULTIPLICATIVELY with a graded promoter in gene_express_levels iff the gate fires.

No format bump (additive field in existing padding, no new marker); ABI stays 5 (additive
symbols). numpy-free; no abs() (a level / mask / cell_state is a non-negative or Class-K-signed
exact integer, never abs()).
"""
from __future__ import annotations

import pathlib
import tempfile

import pytest

from srmech.biology import genome as G
from srmech import _native

# rc282 — make this tests/ directory importable when this module is collected
# ALONE. ``tests/`` is a package (``__init__.py`` present), so pytest's prepend
# import-mode puts the package PARENT (``python/``) on sys.path, not ``tests/``
# itself, and a bare ``from conftest import ...`` raises ModuleNotFoundError in
# isolation. The project's proven shared-helper path (see test_mcp.py /
# test_immolation.py, rc231 #810).
import os as _os
import sys as _sys
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)

from conftest import BodyReadProbe


LEAF = G.LEAF_CAP
B0, B1, B2, B3 = 1 << 0, 1 << 1, 1 << 2, 1 << 3
ALLB = B0 | B1 | B2 | B3


def _leaves(n, fill=0):
    return [[(fill + i) & 3 for i in range(LEAF)] for _ in range(n)]


def _one_gene_strand(label="chrX", gene="g1", body=6):
    """A single-chromosome, single-gene strand (an always-on plain gene) to condense onto."""
    one = G._default_coupling(LEAF)
    strand = G.chromosome(coupling=one, label=label, genes=[(gene, _leaves(body))])
    return strand, one


def _pure_access(strand, cs):
    """The pure oracle: the first chromatin cap's _chromatin_access, else (1, 1)."""
    for hv in strand:
        if G._cap_kind(hv) == G.CHROMATIN_MARKER:
            return G._chromatin_access(hv, cs)
    return (1, 1)


# ── T1  constitutive / plain invariance — accessible() is CONSTANT in cell_state ──────
def test_t1_constitutive_and_plain_are_invariant():
    strand, one = _one_gene_strand()
    plain = strand                                            # no chromatin cap → (1, 1)
    open_cap = G.condense(strand, coupling=one, label="chrX", state="open")     # constitutive (1,1)
    cond_cap = G.condense(strand, coupling=one, label="chrX", state="condensed")  # constitutive (0,1)
    grad_cap = G.condense(strand, coupling=one, label="chrX", state=(1, 3))     # constitutive (1,3)
    for cs in range(0, ALLB + 1):
        assert G.accessible(plain, cs) == (1, 1), cs
        assert G.accessible(open_cap, cs) == (1, 1), cs
        assert G.accessible(cond_cap, cs) == (0, 1), cs
        assert G.accessible(grad_cap, cs) == (1, 3), cs


# ── T2  facultative TRACKS cell_state (the core G1 claim) ─────────────────────────────
def test_t2_facultative_tracks_cell_state():
    strand, one = _one_gene_strand()
    klein4 = G.condense(strand, coupling=one, label="chrX", state={"activator": B2})
    boolean = G.condense(strand, coupling=one, label="chrX", state={"dnf": [(B1, 0), (B2, 0)]})
    thresh = G.condense(strand, coupling=one, label="chrX",
                        state={"weights": [0, 1, 1], "threshold": 2})
    # klein4: open iff bit2 present
    assert G.accessible(klein4, 0) == (0, 1) and G.accessible(klein4, B2) == (1, 1)
    assert G.accessible(klein4, B1) == (0, 1)          # a non-gated bit does not open it
    # boolean OR: open iff bit1 OR bit2 present
    assert G.accessible(boolean, 0) == (0, 1)
    assert G.accessible(boolean, B1) == (1, 1) and G.accessible(boolean, B2) == (1, 1)
    # threshold (both weights +1, θ=2): open iff BOTH bit1 AND bit2 present
    assert G.accessible(thresh, B1) == (0, 1) and G.accessible(thresh, B2) == (0, 1)
    assert G.accessible(thresh, B1 | B2) == (1, 1)
    # SAME genome, two cell_states → DIFFERENT open-set
    assert G.accessible(klein4, 0) != G.accessible(klein4, B2)


# ── T3  back-compat: a constitutive cap is byte-identical to a v15 cap; format 15 stays ──
def test_t3_constitutive_cap_byte_identical_and_format_15():
    strand, one = _one_gene_strand()
    for st, exp in [("open", (1, 1)), ("condensed", (0, 1)), ((2, 5), (2, 5))]:
        s = G.condense(strand, coupling=one, label="chrX", state=st)
        cap = [hv for hv in s if G._cap_kind(hv) == G.CHROMATIN_MARKER][0].tobytes()
        nul = cap.find(b"\x00", 1)
        den_end = nul + 2 + 2 * G._CHROMATIN_LEVEL_BYTES
        # everything from den_end (the access_gate_type slot) onward is NUL — the v15 pad default;
        # so a constitutive rc274 cap is byte-identical to a pre-rc274 v15 cap (gate NONE == pad 0).
        assert set(cap[den_end:]) == {0}, (st, cap[den_end:den_end + 4])
        # and the gate decodes as NONE (the pre-rc274 read)
        assert G._chromatin_gate_spec(
            [hv for hv in s if G._cap_kind(hv) == G.CHROMATIN_MARKER][0]) == (G.CHROMATIN_GATE_NONE, None)
    assert G.GENOME_FORMAT_VERSION == 20
    import srmech.introspect as introspect
    assert introspect.describe()["tools"]["total"] == 687


# ── T4  C↔Python byte-parity — accessible + the writer + the demand-load plan ─────────
@pytest.mark.skipif(not _native.has_native_genome_chromatin_access(),
                    reason="native chromatin-access surface not built")
def test_t4_native_equals_pure_accessible_and_writer(monkeypatch):
    strand, one = _one_gene_strand()
    states = ["condensed", "open", (1, 3),
              {"activator": B2}, {"activator": B2, "repressor": B1},
              {"dnf": [(B1, 0), (B2, 0)]}, {"weights": [0, 1, 1], "threshold": 2},
              {"activator": B1, "open_level": (1, 3)}, {"weights": [3, -1], "threshold": 1}]
    for st in states:
        s = G.condense(strand, coupling=one, label="chrX", state=st)
        cap = [hv for hv in s if G._cap_kind(hv) == G.CHROMATIN_MARKER][0]
        # (a) the facultative WRITER: native cap bytes == the pure _pack_chromatin oracle bytes
        ct, num, den, agt, gf = G._chromatin_state(st)
        blob = G._chromatin_gate_blob(agt, gf)
        pure_cap = G._pack_chromatin(ct, num, den, LEAF, handle="chr", gate_blob=blob).tobytes()
        assert cap.tobytes() == pure_cap, st
        for cs in range(0, ALLB + 1):
            native = _native.genome_chromatin_access_c(cap.tobytes(), LEAF, cs)
            pure = G._chromatin_access(cap, cs)
            assert native == pure, (st, cs, native, pure)
            # (b) the public op with native ON == with native FORCED OFF
            monkeypatch.setattr(_native, "genome_chromatin_access_c", lambda *a, **k: None)
            assert G.accessible(s, cs) == pure, (st, cs)
            monkeypatch.undo()


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome plan surface not built")
def test_t4_demand_load_plan_native_equals_pure(monkeypatch):
    one = G._default_coupling(LEAF)
    spec = [("cA", {"activator": B2}), ("cB", "condensed"),
            ("cC", None), ("cD", {"dnf": [(B0, 0)]}), ("cE", {"weights": [0, 1, 1], "threshold": 2})]
    chrom = [(name, [(name, _leaves(6))]) for name, _ in spec]
    strand = G.genome(coupling=one, chromosomes=chrom)
    for name, st in spec:
        if st is not None:
            strand = G.condense(strand, coupling=one, label=name, state=st)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc274t4_"))
    G.genome_save(strand, tmp, one)
    for cs in range(0, ALLB + 1):
        monkeypatch.setattr(_native, "has_native_genome", lambda: True)
        plan_c = G.gene_express_plan(str(tmp), one, cs)
        monkeypatch.setattr(_native, "has_native_genome", lambda: False)
        plan_py = G.gene_express_plan(str(tmp), one, cs)
        strand_py = G.gene_express_plan(strand, one, cs)
        assert plan_c == plan_py, (cs, plan_c, plan_py)
        assert {p[0] for p in plan_c} == {p[0] for p in strand_py}, (cs, plan_c, strand_py)


# ── T5  demand-load skips the right regions per state (bounded single-seek) ────────────
@pytest.fixture()
def probe(monkeypatch):
    """The bounded-I/O probe, SPLIT into its plan / catalog terms (rc282 — see
    ``conftest.BodyReadProbe``). The old single sum silently omitted the catalog
    derivation's whole-body scan, because that read reached the body through
    ``Path.read_bytes`` rather than the ``_open_body_ro`` seam this probe wraps."""
    return BodyReadProbe().install(monkeypatch)


def test_t5_facultative_region_in_or_out_of_plan_per_cell_state():
    one = G._default_coupling(LEAF)
    # a single facultative-klein4 (bit2) community + an always-on open control
    chrom = [("fac", [("fac", _leaves(6))]), ("ctrl", [("ctrl", _leaves(6))])]
    strand = G.genome(coupling=one, chromosomes=chrom)
    strand = G.condense(strand, coupling=one, label="fac", state={"activator": B2})
    strand = G.condense(strand, coupling=one, label="ctrl", state="open")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc274t5_"))
    G.genome_save(strand, tmp, one)
    # bit2 ABSENT → facultative region SILENCED (out); bit2 PRESENT → in
    off = {p[0] for p in G.gene_express_plan(str(tmp), one, 0)}
    on = {p[0] for p in G.gene_express_plan(str(tmp), one, B2)}
    assert "fac" not in off and "fac" in on, (off, on)
    assert "ctrl" in off and "ctrl" in on              # the constitutive control is unaffected


def test_t5_state_closed_facultative_touches_only_the_chromatin_cap(probe):
    one = G._default_coupling(LEAF)
    # ONE facultative community gated on bit2, a sizeable body — the dramatic-skip case
    strand = G.genome(coupling=one, chromosomes=[("solo", [("solo", _leaves(60))])])
    strand = G.condense(strand, coupling=one, label="solo", state={"activator": B2})
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc274t5b_"))
    G.genome_save(strand, tmp, one)
    full_body = (tmp / G._BODY_NAME).stat().st_size
    # cell_state WITHOUT bit2 → the facultative region is CLOSED → skip reading ONLY its cap
    probe.clear()
    plan = G.gene_express_plan(str(tmp), one, 0)
    probe.assert_live()
    closed_bytes, closed_catalog = probe.plan_bytes, probe.catalog_bytes
    assert plan == []                                  # closed under this cell_state
    # THE GUARANTEE: ONLY the chromatin cap (single-seek); the gene gate is never read.
    assert closed_bytes == LEAF, closed_bytes
    assert closed_bytes < full_body // 2, (closed_bytes, full_body)
    # cell_state WITH bit2 → OPEN → advances to the gene gate (2 caps), region planned
    probe.clear()
    plan_on = G.gene_express_plan(str(tmp), one, B2)
    probe.assert_live()
    on_bytes, on_catalog = probe.plan_bytes, probe.catalog_bytes
    assert {p[0] for p in plan_on} == {"solo"}
    assert on_bytes == 2 * LEAF, on_bytes              # chromatin cap + gene gate cap
    # THE POINT OF THE WHOLE FEATURE, asserted as a CONTRAST rather than two constants:
    # closing the region must genuinely REDUCE the bytes the plan reads.
    assert closed_bytes < on_bytes, (closed_bytes, on_bytes)
    # …while the catalog scan is INDEPENDENT of cell_state — which is exactly why it is
    # a separate term and not part of the bound above.
    assert closed_catalog == on_catalog == full_body, (closed_catalog, on_catalog)


# ── T6  save / reload / decondense / integrate survival ───────────────────────────────
def test_t6_decondense_restores_byte_identity_and_reload_reproduces():
    # gene_label == chrom_label so the gene-granular STRAND plan and the chromosome-granular
    # PATH plan return DIRECTLY comparable label sets (the rc269 harness convention).
    strand, one = _one_gene_strand(label="chrX", gene="chrX")
    before = [hv.tobytes() for hv in strand]
    fac = G.condense(strand, coupling=one, label="chrX", state={"dnf": [(B1, 0), (B2, 0)]})
    restored = G.decondense(fac, coupling=one)
    assert [hv.tobytes() for hv in restored] == before   # NO re-mint — byte-identical to the origin
    # save the facultative genome and reload via the demand-load PATH == the in-memory strand
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc274t6_"))
    G.genome_save(fac, tmp, one)
    for cs in [0, B1, B2, B1 | B2]:
        disk = {p[0] for p in G.gene_express_plan(str(tmp), one, cs)}
        mem = {p[0] for p in G.gene_express_plan(fac, one, cs)}
        assert disk == mem, (cs, disk, mem)


def test_t6_integrate_facultative_provirus_survives():
    one = G._default_coupling(LEAF)
    host = G.genome(coupling=one, chromosomes=[("hostA", [("hostA", _leaves(6))])])
    provirus = G.chromosome(coupling=one, label="prov", genes=[("prov", _leaves(6))])
    provirus = G.condense(provirus, coupling=one, label="prov", state={"activator": B1})
    combined = G.integrate(host, provirus)
    assert combined is not None                          # compatible (shared coupling width)
    parts = G.partition(combined, one)
    assert "hostA" in parts and "prov" in parts          # both chromosomes recover
    # the provirus's facultative chromatin still reads under cell_state on the combined strand
    prov_only = [hv for hv in combined]
    # accessible on the whole combined strand reads the FIRST chromatin cap (the provirus's)
    assert G.accessible(prov_only, 0) == (0, 1)          # bit1 absent → silenced
    assert G.accessible(prov_only, B1) == (1, 1)         # bit1 present → open


# ── T7  read-only — strand + turns.bin byte-identical after every read ────────────────
def test_t7_reads_never_mutate():
    one = G._default_coupling(LEAF)
    strand = G.genome(coupling=one, chromosomes=[("chrX", [("g1", _leaves(6))])])
    strand = G.condense(strand, coupling=one, label="chrX", state={"activator": B2})
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc274t7_"))
    G.genome_save(strand, tmp, one)
    strand_before = [hv.tobytes() for hv in strand]
    body_before = (tmp / G._BODY_NAME).read_bytes()
    G.accessible(strand, B2)
    G.gene_express(strand, one, B2)
    G.gene_express_levels(strand, one, B2)
    G.gene_express_plan(strand, one, B2)
    G.gene_express_plan(str(tmp), one, B2)
    assert [hv.tobytes() for hv in strand] == strand_before
    assert (tmp / G._BODY_NAME).read_bytes() == body_before


# ── T8  level composition — a graded facultative cap composes MULTIPLICATIVELY ────────
def test_t8_graded_facultative_composes_with_graded_promoter():
    one = G._default_coupling(LEAF)
    # a GRADED promoter gene: level = weights·bits / denom = (1/2) when bit2 present, else 0
    gene = ("g", _leaves(6), {"gate": "graded", "weights": [0, 0, 1], "denom": 2})
    strand = G.chromosome(coupling=one, label="chrX", genes=[gene])
    # a GRADED FACULTATIVE chromatin cap: when-open level (1, 3), gated on bit1
    strand = G.condense(strand, coupling=one, label="chrX",
                        state={"activator": B1, "open_level": (1, 3)})

    def level_of(cs):
        out = G.gene_express_levels(strand, one, cs)
        return {lbl: lvl for lbl, _leaves_, lvl in out}

    # bit1 AND bit2 present: access (1,3) × promoter (1,2) = (1, 6) — the multiplicative compose
    assert level_of(B1 | B2).get("g") == (1, 6), level_of(B1 | B2)
    # bit1 present, bit2 absent: promoter level 0 → gene silenced (not in the output)
    assert "g" not in level_of(B1)
    # bit1 absent: the facultative chromatin is CLOSED (access (0,1)) → silenced regardless of promoter
    assert "g" not in level_of(B2)
    assert "g" not in level_of(0)
