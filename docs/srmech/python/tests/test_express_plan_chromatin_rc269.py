"""v0.9.0rc269 (§98 / #1422 / F1247 / PR#687) — CHROMATIN gates the DEMAND-LOAD PATH plan.

Completes the rc268 deferral. The PATH (variant-b) ``gene_express_plan`` + its C peer
``srmech_genome_gene_express_plan`` now respect the HEAD chromatin cap (``0x48``). The
region-head layout is ``[CHROM cap][chromatin cap?][gene gate cap][data…]`` (exactly where
``condense(region=None)`` splices the marker):

  * HETEROCHROMATIN (condensed / graded level 0) ⇒ the whole region is SKIPPED at plan time
    having touched ONLY the chromatin cap — its gene gate cap is NEVER read (bounded I/O; even
    FEWER bytes than the §134 read).
  * EUCHROMATIN (open / graded level > 0) ⇒ advance one slot and evaluate the gene gate at
    ``off + 2·leaf_dim`` — the unchanged §134 decision (falls through to the promoter).
  * A chromatin-FREE region is BYTE-FOR-BYTE the rc135 read (backward-compat).

Proven here (the ask's DoD):
  (i)   the PATH plan SKIPS condensed / graded-0 regions (whole community excluded), across
        all cell_states + all delivered chromatin states;
  (ii)  BYTES-TOUCHED — a condensed region pages neither its body NOR its gene gate cap
        (only the chromatin cap, one leaf_dim), measured through the ``_open_body_ro`` seam.
        rc282: this is the PER-REGION term. The catalog derivation's whole-body scan is a
        separate, cell_state-independent cost, asserted separately rather than folded into
        (or hidden from) this bound — see ``conftest.BodyReadProbe``;
  (iii) native == pure BYTE-PARITY for the PATH plan on a MIXED genome (condensed + open +
        chromatin-free), every cell_state;
  (iv)  EUCHROMATIN defers to the promoter (open + firing → in; open + not-firing → out);
  (v)   BACKWARD-COMPAT — a chromatin-free genome's PATH plan (and its per-region bytes) is
        unchanged from rc135 (one head cap read; plan == the gene_express community set);
  (vi)  the STRAND plan (rc268) and the PATH plan (rc269) agree on the expressed label set.

No format / ABI change (a READ behavior change): GENOME_FORMAT_VERSION stays 15, no new marker,
no new public callable (tools.total stays 445). numpy-free; no abs() (a level / cell_state is a
non-negative Class-I / Class-N integer, never negated).
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

#: (chrom/gene label, gate — None = always-on 2-tuple / an int = an E1 activator bit,
#:  chromatin state — None chromatin-free / "open" / "condensed" / a (num,den) graded level).
#: SINGLE gene per community with gene_label == chrom_label so the STRAND (gene-granular) and
#: PATH (chromosome-granular) plans return DIRECTLY comparable label sets.
_SPEC = [
    ("free_on",  None, None),         # chromatin-free + always-on   → always in
    ("open_on",  None, "open"),       # euchromatin    + always-on   → always in
    ("cond_on",  None, "condensed"),  # heterochromatin+ always-on   → NEVER in (silences promoter)
    ("grad0_on", None, (0, 1)),       # graded level 0 + always-on   → NEVER in (silenced)
    ("grad_on",  None, (1, 3)),       # graded 1/3     + always-on   → always in (accessible)
    ("open_b0",  B0,   "open"),       # euchromatin    + gated bit0  → in iff bit0 present
    ("free_b1",  B1,   None),         # chromatin-free + gated bit1  → in iff bit1 present
    ("cond_b0",  B0,   "condensed"),  # heterochromatin+ gated bit0  → NEVER in (silenced)
]


def _leaves(n, fill):
    return [[(fill + i) & 3 for i in range(LEAF)] for _ in range(n)]


def _build(tmp, spec=_SPEC, body=6):
    """Build the mixed layout, apply per-chromosome chromatin (by label), save; return
    (in-memory chromatin'd strand, coupling)."""
    one = G._default_coupling(LEAF)
    chrom_list = []
    for name, gate, _chrom in spec:
        gene = (name, _leaves(body, 0)) if gate is None else (name, _leaves(body, 0), gate)
        chrom_list.append((name, [gene]))
    strand = G.genome(coupling=one, chromosomes=chrom_list)
    for name, _gate, chrom in spec:
        if chrom is not None:
            strand = G.condense(strand, coupling=one, label=name, state=chrom)
    G.genome_save(strand, tmp, one)
    return strand, one


def _expected(cs, spec=_SPEC):
    """The communities the PATH plan should include under cell_state ``cs`` — accessible
    (chromatin numerator > 0 / chromatin-free) AND its promoter fires."""
    out = set()
    for name, gate, chrom in spec:
        if chrom == "condensed" or chrom == (0, 1):
            continue                                   # silenced regardless of promoter
        fires = gate is None or (cs & gate) == gate    # always-on OR the activator bit present
        if fires:
            out.add(name)
    return out


@pytest.fixture()
def probe(monkeypatch):
    """The bounded-I/O probe, SPLIT into its two terms (rc282 — see
    ``_genome_io_probe.py``).

    This used to be a single ``sum(cf.n for cf in opened)``. That sum was silently
    incomplete: ``_catalog_data``'s head-only branch reached the body through
    ``Path.read_bytes``, NOT through the ``_open_body_ro`` seam, so the whole-body
    catalog scan every one of these calls performs was invisible. The assertions read
    as bounding the whole call while in fact bounding only the gate loop. rc282 routed
    every body read through the one seam, and these numbers became honest.

    The chromatin guarantee is about the PER-REGION gate reads, so it is asserted on
    ``probe.plan_bytes`` — at exactly the strength it always was. The catalog scan is a
    separate, cell_state-INDEPENDENT cost and is asserted as such."""
    return BodyReadProbe().install(monkeypatch)


# ── (i) the PATH plan SKIPS condensed / graded-0 regions ──────────────────────────
def test_path_plan_skips_condensed_regions():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269i_"))
    _build(tmp)
    one = G._default_coupling(LEAF)
    for cs in range(0, ALLB + 1):
        labels = {p[0] for p in G.gene_express_plan(str(tmp), one, cs)}
        assert labels == _expected(cs), f"cs={cs}: {labels} != {_expected(cs)}"
        # the three silenced communities are NEVER planned, whatever the promoter would do
        assert labels.isdisjoint({"cond_on", "grad0_on", "cond_b0"}), (cs, labels)


# ── (ii) BYTES-TOUCHED: a condensed region pages neither body NOR gene gate cap ──────
def test_condensed_region_touches_only_the_chromatin_cap(probe):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269ii_"))
    # ONE condensed community with a sizeable body — the dramatic-skip case
    _build(tmp, spec=[("solo", None, "condensed")], body=60)
    one = G._default_coupling(LEAF)
    full_body = (tmp / G._BODY_NAME).stat().st_size
    probe.clear()
    plan = G.gene_express_plan(str(tmp), one, 0)
    probe.assert_live()
    assert plan == []                                  # the whole region is skipped
    # THE GUARANTEE (unchanged in strength): ONLY the chromatin cap is read (one leaf_dim)
    # — the gene gate cap is NEVER touched (that would be 2*LEAF) and the body's many
    # turns are never paged.
    assert probe.plan_bytes == LEAF, probe.plan_bytes
    assert probe.plan_bytes < full_body // 2, (probe.plan_bytes, full_body)
    # THE SEPARATE, KNOWN COST: deriving the chromosome table scans the whole body
    # (ADR-0003 — the array is a plaintext TOC and is never stored). Not part of the
    # chromatin bound, and not hidden inside it either.
    assert probe.catalog_bytes == full_body, (probe.catalog_bytes, full_body)


def test_bytes_touched_by_chromatin_state(probe):
    """Per-state cap accounting on a mixed cond/open/free genome: condensed → 1 cap (chromatin
    only), open → 2 caps (chromatin + gene gate), chromatin-free → 1 cap (gene gate)."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269ii2_"))
    spec = [("c", None, "condensed"), ("o", None, "open"), ("f", None, None)]
    _build(tmp, spec=spec, body=40)
    one = G._default_coupling(LEAF)
    full_body = (tmp / G._BODY_NAME).stat().st_size
    probe.clear()
    plan = G.gene_express_plan(str(tmp), one, 0)
    probe.assert_live()
    assert {p[0] for p in plan} == {"o", "f"}          # condensed excluded
    # THE GUARANTEE: the per-region gate reads are exactly 1 + 2 + 1 caps.
    assert probe.plan_bytes == LEAF + 2 * LEAF + LEAF
    assert probe.plan_bytes < full_body // 2, (probe.plan_bytes, full_body)
    assert probe.catalog_bytes == full_body, (probe.catalog_bytes, full_body)


# ── (iii) native == pure BYTE-PARITY for the PATH plan ───────────────────────────
@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built")
def test_native_equals_pure(monkeypatch):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269iii_"))
    _build(tmp)
    one = G._default_coupling(LEAF)
    for cs in range(0, ALLB + 1):
        monkeypatch.setattr(_native, "has_native_genome", lambda: True)
        plan_c = G.gene_express_plan(str(tmp), one, cs)
        monkeypatch.setattr(_native, "has_native_genome", lambda: False)
        plan_py = G.gene_express_plan(str(tmp), one, cs)
        assert plan_c == plan_py, f"plan offsets differ cs={cs}: {plan_c} != {plan_py}"
        # and both equal the ground-truth expected set
        assert {p[0] for p in plan_c} == _expected(cs), cs


# ── (iv) EUCHROMATIN defers to the promoter (unchanged §134) ─────────────────────
def test_euchromatin_defers_to_the_promoter():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269iv_"))
    # an OPEN region gated on bit0 (+ an always-on open control so the genome is non-trivial)
    _build(tmp, spec=[("gate_b0", B0, "open"), ("ctrl", None, "open")])
    one = G._default_coupling(LEAF)
    off_labels = {p[0] for p in G.gene_express_plan(str(tmp), one, 0)}      # bit0 ABSENT
    on_labels = {p[0] for p in G.gene_express_plan(str(tmp), one, B0)}      # bit0 PRESENT
    assert "gate_b0" not in off_labels                                     # open but promoter off → out
    assert "gate_b0" in on_labels                                          # open + promoter on → in
    assert "ctrl" in off_labels and "ctrl" in on_labels                    # always-on stays in


# ── (v) BACKWARD-COMPAT: a chromatin-free genome's plan + bytes are the rc135 read ───
def test_chromatin_free_plan_unchanged(probe):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269v_"))
    # a purely chromatin-free genome (no condense at all)
    spec = [("free_on", None, None), ("free_b1", B1, None), ("free_off", B2, None)]
    _build(tmp, spec=spec, body=20)
    one = G._default_coupling(LEAF)
    full_body = (tmp / G._BODY_NAME).stat().st_size
    catalog_terms = set()
    for cs in [0, B1, B2, B1 | B2, ALLB]:
        probe.clear()
        plan = G.gene_express_plan(str(tmp), one, cs)
        probe.assert_live()
        assert {p[0] for p in plan} == _expected(cs, spec), cs
        # THE GUARANTEE: exactly ONE head cap read per chromosome — no extra chromatin
        # read (== the rc135 read).
        assert probe.plan_bytes == len(spec) * LEAF, (cs, probe.plan_bytes)
        catalog_terms.add(probe.catalog_bytes)
    # The catalog scan is a FIXED cost — the same whatever the cell_state. That is what
    # makes it separable from the bound above rather than noise inside it.
    assert catalog_terms == {full_body}, catalog_terms


# ── (vi) the STRAND plan (rc268) and the PATH plan (rc269) AGREE on the label set ────
def test_strand_and_path_plans_agree():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269vi_"))
    strand, one = _build(tmp)              # strand is the in-memory chromatin'd genome
    for cs in range(0, ALLB + 1):
        strand_labels = {p[0] for p in G.gene_express_plan(strand, one, cs)}   # rc268 STRAND
        path_labels = {p[0] for p in G.gene_express_plan(str(tmp), one, cs)}   # rc269 PATH
        assert strand_labels == path_labels == _expected(cs), (cs, strand_labels, path_labels)


# ── read-only: the strand + turns.bin are byte-identical after the plan ──────────
def test_read_only():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc269ro_"))
    strand, one = _build(tmp)
    strand_before = [list(map(int, hv.tolist())) for hv in strand]
    body_before = (tmp / G._BODY_NAME).read_bytes()
    G.gene_express_plan(strand, one, B0)                  # STRAND variant
    G.gene_express_plan(str(tmp), one, B0)                # PATH variant
    assert [list(map(int, hv.tolist())) for hv in strand] == strand_before
    assert (tmp / G._BODY_NAME).read_bytes() == body_before


# ── no format / ABI / tool-count change (a READ behavior change only) ────────────
def test_no_format_or_abi_or_toolcount_change():
    assert G.GENOME_FORMAT_VERSION == 20
    import srmech.introspect as introspect
    assert introspect.describe()["tools"]["total"] == 679
