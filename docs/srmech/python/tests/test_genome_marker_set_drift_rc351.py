"""rc351 (task `#T1004`) — the genome MARKER-SET drift ratchet, and the pure-path load it broke.

**What shipped broken.** ``genome.py`` defines fourteen block-kind marker bytes and one
tuple, ``_LEAF_WIDE_BLOCK_MARKERS``, naming the set of them. Four walkers need that set.
Three read the tuple. The fourth — the no-native streaming reader *inside*
:func:`srmech.biology.genome.genome_load`, the one a pure / Pyodide / WASM install runs —
carried an inline hand-copy that stopped at ``CHROMATIN_MARKER``, omitting
``FIBER_CAP_MARKER`` (``0x46``) and ``OCT_FIBER_CAP_MARKER`` (``0x4F``). The C classifier
knew both. So a pure install could **save a fiber-bearing genome and never load it back**:

    GenomeBoundingError: genome body: unrecognised block kind byte 70 at offset 37

The tuple's own comment said it existed "so the two can never drift". A shared name did not
stop a fifth spelling from being written, and the drift was invisible to CI because no cell
ran the suite with ``HAS_NATIVE=False``. Both halves are fixed in rc351; this file holds the
tests for both.

**The three classes of test here.**

1. ``test_pure_*`` — the DEFECT, at the shipped ops (``genome_save`` / ``genome_load``),
   with the native decoder forced off so the pure block-walker is the subject even when a
   native lib is present. These fail on the pre-rc351 tree with or without a native build.
2. ``test_scan_*`` / ``test_genes_*`` / ``test_plan_*`` — the three FURTHER hand-copies that
   had drifted the same way, each pinned at the shipped op that exposes it.
3. ``test_marker_set_ratchet_*`` — the GUARD. An AST check over ``genome.py``: a marker-set
   spelling may live at module level with a name, and nowhere else. It is what makes a fifth
   drift a build failure rather than a field report.

Every test is numpy-free (the module under test is).
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.cascade.one import the_one
from srmech.biology.genome import (
    ELEMENT_TYPE_KLEIN4, ELEMENT_TYPE_OCTONION, ELEMENT_TYPE_Q8, FIBER_CAP_MARKER,
    OCT_FIBER_CAP_MARKER, OCTONION_SECTORS, QUAD, _cap_kind, chromosome,
    genome_add_fiber, genome_add_octonion_fiber, genome_load, genome_read_fiber,
    genome_read_octonion_fiber, genome_save, telomere,
)
from srmech.math.hv import HV
from srmech.biology.q8 import q8_from_one

#: 32, not 16 — an 𝕆 fiber cap 4-bit-packs its holonomy, so `[0x4F] + label + NUL + n_holo`
#: does not fit a 16-byte leaf (the rc325 suite uses 32 for the same reason).
_LD = 32


# ── fixtures ─────────────────────────────────────────────────────────────────
def _q8_one():
    return q8_from_one(the_one(1, 1, 3, 6), _LD)


def _q8_leaf(k):
    return HV.from_sequence(bytes((1 + 2 * k + i) % 8 for i in range(_LD)), sectors=8)


def _q8_fiber_strand(label="chrF"):
    """A Q₈ chromosome carrying the §Q8-FIBER ``0x46`` cap — built with the shipped ops."""
    leaves = [_q8_leaf(k) for k in range(3)]
    strand = chromosome(leaves, _q8_one(), label=label, element_type=ELEMENT_TYPE_Q8)
    return genome_add_fiber(strand)


def _oct_fiber_strand(label="chrO"):
    """A strand carrying the §𝕆-FIBER ``0x4F`` cap (turns in 0..7, valid for both folds)."""
    turns = [HV.from_sequence(bytes((1 + 2 * i + k) % 8 for i in range(_LD)),
                              sectors=OCTONION_SECTORS) for k in range(3)]
    return genome_add_octonion_fiber([telomere(label, dim=_LD)] + turns)


@pytest.fixture
def force_pure(monkeypatch):
    """Force ``genome_load`` down its no-native streaming reader.

    The pure block-walker is the SUBJECT of these tests, so it must run whether or not the
    machine has a native build — otherwise the regression is only observable in a cell that
    happens to lack a ``.so``, which is exactly how it shipped."""
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    return monkeypatch


# ── 1. the defect: the pure reader could not load what the pure writer wrote ──
def test_pure_load_roundtrips_a_q8_fiber_genome(tmp_path, force_pure):
    """``genome_save`` → ``genome_load`` with NO native decoder, on a ``0x46``-bearing body.

    Pre-rc351 this raised ``GenomeBoundingError: unrecognised block kind byte 70``."""
    strand = _q8_fiber_strand()
    one = _q8_one()
    genome_save(strand, str(tmp_path), one, element_type=ELEMENT_TYPE_Q8)
    loaded, _cpl, _lbls = genome_load(str(tmp_path), coupling=one)
    assert [_cap_kind(hv) for hv in loaded] == [_cap_kind(hv) for hv in strand]
    assert genome_read_fiber(loaded)["holonomy"] == genome_read_fiber(strand)["holonomy"]
    assert genome_read_fiber(loaded)["consistent"] is True


def test_pure_load_roundtrips_an_octonion_fiber_genome(tmp_path, force_pure):
    """The ``0x4F`` peer — the same omission, one Cayley-Dickson rung up. The rc325 suite
    never had a save/load row for it, so only the ``0x46`` cap was ever going to be caught."""
    strand = _oct_fiber_strand()
    one = HV.from_sequence(bytes((3 * i + 1) % 8 for i in range(_LD)),
                           sectors=OCTONION_SECTORS)
    genome_save(strand, str(tmp_path), one, element_type=ELEMENT_TYPE_OCTONION)
    loaded, _cpl, _lbls = genome_load(str(tmp_path), coupling=one)
    assert OCT_FIBER_CAP_MARKER in [_cap_kind(hv) for hv in loaded]
    assert (genome_read_octonion_fiber(loaded)["holonomy"]
            == genome_read_octonion_fiber(strand)["holonomy"])


def test_pure_load_carries_both_fiber_caps(tmp_path, force_pure):
    """A strand holding BOTH the ℍ ``0x46`` and 𝕆 ``0x4F`` caps — the pure reader has to
    stride past two markers it did not know, not one."""
    turns = [HV.from_sequence(bytes((1 + 2 * i + k) % 8 for i in range(_LD)),
                              sectors=OCTONION_SECTORS) for k in range(3)]
    strand = genome_add_octonion_fiber(genome_add_fiber([telomere("both", dim=_LD)] + turns))
    one = HV.from_sequence(bytes((3 * i + 1) % 8 for i in range(_LD)),
                           sectors=OCTONION_SECTORS)
    genome_save(strand, str(tmp_path), one, element_type=ELEMENT_TYPE_OCTONION)
    loaded, _cpl, _lbls = genome_load(str(tmp_path), coupling=one)
    kinds = [_cap_kind(hv) for hv in loaded]
    assert FIBER_CAP_MARKER in kinds and OCT_FIBER_CAP_MARKER in kinds


# ── 2. the same drift, three more sites ──────────────────────────────────────
def test_loaded_fiber_cap_keeps_the_carrier_it_was_minted_with(tmp_path, force_pure):
    """``_hv_from_block`` had its own truncated copy, so a fiber cap came back as a
    ``sectors=QUAD`` block while :func:`_pack_fiber_cap` mints it at ``sectors=256``. The
    bytes round-tripped and the carrier did not — a silent difference, since ``HV.__eq__``
    compares buffers only."""
    strand = _q8_fiber_strand()
    one = _q8_one()
    minted = [hv.sectors for hv in strand if _cap_kind(hv) == FIBER_CAP_MARKER]
    genome_save(strand, str(tmp_path), one, element_type=ELEMENT_TYPE_Q8)
    loaded, _cpl, _lbls = genome_load(str(tmp_path), coupling=one)
    got = [hv.sectors for hv in loaded if _cap_kind(hv) == FIBER_CAP_MARKER]
    assert minted == [256] and got == minted
    assert all(hv.sectors == 256 for hv in loaded if _cap_kind(hv) is not None)
    assert all(hv.sectors == QUAD for hv in loaded if _cap_kind(hv) is None)


def test_scan_derived_leaf_count_agrees_with_the_written_manifest(tmp_path):
    """The manifest is a DERIVED cache — rebuilding it by scanning the body must reproduce
    what ``genome_save`` wrote. ``_ScanState.fold`` carried a hand-spelled ``!=`` chain
    missing the two fiber markers, so a fiber cap was counted as a data turn and the
    rebuilt ``leaf_count`` came back one HIGHER than the written one."""
    strand = _q8_fiber_strand()
    one = _q8_one()
    data = genome_save(strand, str(tmp_path), one, element_type=ELEMENT_TYPE_Q8)
    body = (tmp_path / "turns.bin").read_bytes()
    specs, _n_blocks = G._scan_body_to_chrom_specs(body, _LD)
    assert [s[2] for s in specs] == [c["leaf_count"] for c in data["chromosomes"]]
    assert [s[2] for s in specs] == [3]          # three data turns, the fiber cap is not one


def test_genes_does_not_decouple_a_fiber_cap_into_a_gene(tmp_path):
    """``genes`` skipped a hand-spelled FOUR caps, so every later cap family — the §95b
    diploid telomere, the §95a centromere, the §98 chromatin cap and both fiber caps — fell
    through to be DECOUPLED into the current gene's leaves as if it were content."""
    one = _q8_one()
    strand = chromosome(genes=[("gA", [_q8_leaf(0), _q8_leaf(1)]),
                               ("gB", [_q8_leaf(2), _q8_leaf(3)])],
                        coupling=one, label="chrG", element_type=ELEMENT_TYPE_Q8)
    plain = G.genes(strand, one, element_type=ELEMENT_TYPE_Q8)
    fibred = G.genes(genome_add_fiber(strand), one, element_type=ELEMENT_TYPE_Q8)
    assert [(lbl, [h.tolist() for h in lv]) for lbl, lv in fibred] == \
           [(lbl, [h.tolist() for h in lv]) for lbl, lv in plain]


def test_plan_strides_a_fiber_cap_at_the_leaf_width(tmp_path):
    """The express-plan walk strode any unrecognised block at the PACKED-turn width. A fiber
    cap is stored verbatim at ``leaf_dim`` (32 here vs a 9-byte klein4 packed turn), so every
    byte offset the plan emitted after one was wrong by the difference — the same failure the
    rc340 comment in that function describes, one marker family over.

    The invariant: a plan span is a byte RANGE into ``turns.bin``, so both ends must land on
    real block boundaries. The boundary set comes from the shipped walker
    ``_walk_region_blocks``, not a hand-rolled strider — the hand-rolled strider is the thing
    under test. Pre-rc351 the trailing gene's span ended at byte 141, which is inside a block."""
    one = HV.from_sequence(bytes(i % QUAD for i in range(_LD)), sectors=QUAD)
    lv = [HV.from_sequence(bytes((i + k) % QUAD for i in range(_LD)), sectors=QUAD)
          for k in range(4)]
    strand = chromosome(genes=[("gA", lv[:2]), ("gB", lv[2:])],
                        coupling=one, label="chrP", element_type=ELEMENT_TYPE_KLEIN4)
    fibred = genome_add_fiber(strand)
    genome_save(fibred, str(tmp_path), one, element_type=ELEMENT_TYPE_KLEIN4)
    body = (tmp_path / "turns.bin").read_bytes()

    boundaries, at = {0}, 0
    for raw, _decoded in G._walk_region_blocks(body, _LD, context="rc351 oracle"):
        at += len(raw)
        boundaries.add(at)
    assert at == len(body)

    plan = G._gene_express_plan_strand(fibred, one, 0, element_type=ELEMENT_TYPE_KLEIN4)
    assert plan, "the fixture has expressed genes"
    for label, start, length in plan:
        assert body[start] in G._GENE_MARKERS, (
            f"gene {label!r} span starts at byte {start} = {body[start]:#04x}, not a gene cap")
        assert start + length in boundaries, (
            f"gene {label!r} span [{start}, {start + length}) ends INSIDE a block — the walk "
            f"mis-strode a cap (block boundaries: {sorted(boundaries)})")


# ── 3. the guard: no second spelling of a marker set ─────────────────────────
_GENOME_SRC = pathlib.Path(inspect.getfile(G))


def _marker_constants(tree):
    """Every module-level ``*_MARKER = <int>`` name in ``genome.py``."""
    out = set()
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id.endswith("_MARKER")
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, int)):
            out.add(node.targets[0].id)
    return out


def _named_marker_sets():
    """The module-level ``*_MARKERS`` collections, resolved from the imported module.

    Reading them off the module (not the AST) means a DERIVED set —
    ``_ACCESS_RESET_MARKERS = _CHROM_BOUNDARY_MARKERS + (KERNEL_HEADER_MARKER,)`` — is
    measured by its VALUE, which is the whole point of deriving it."""
    return {name: frozenset(val)
            for name, val in vars(G).items()
            if name.endswith("_MARKERS") and isinstance(val, tuple) and len(val) >= 2
            and all(isinstance(x, int) for x in val)}


def _inline_spellings(tree, marker_names):
    """Every marker-set spelling that is NOT a module-level named declaration.

    Two syntactic forms count, because both were used in the drifted code: a collection
    literal (``kind in (A, B, C)``) and a chain of comparisons (``x != A and x != B``).
    Yields ``(lineno, {marker names})``."""
    declared_at = {n.lineno for n in tree.body
                   if isinstance(n, ast.Assign) and len(n.targets) == 1
                   and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id.endswith("_MARKERS")}
    seen, out = set(), []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            names = {e.id for e in node.elts
                     if isinstance(e, ast.Name) and e.id in marker_names}
        elif isinstance(node, ast.BoolOp):
            names = set()
            for value in node.values:
                if isinstance(value, ast.Compare):
                    names |= {x.id for x in ast.walk(value)
                              if isinstance(x, ast.Name) and x.id in marker_names}
        else:
            continue
        key = (node.lineno, tuple(sorted(names)))
        if len(names) >= 2 and node.lineno not in declared_at and key not in seen:
            seen.add(key)
            out.append((node.lineno, names))
    return out


def test_marker_set_ratchet_no_inline_copy_of_a_named_set():
    """R1 — a marker set that already has a name may not be re-spelled inline.

    This is the rule the shipped defect broke: ``genome_load`` spelled the leaf-wide set as
    a literal instead of naming ``_LEAF_WIDE_BLOCK_MARKERS``, and once a set can be spelled
    twice it can be spelled twice DIFFERENTLY."""
    tree = ast.parse(_GENOME_SRC.read_text(encoding="utf-8"))
    named = _named_marker_sets()
    violations = []
    for lineno, names in _inline_spellings(tree, _marker_constants(tree)):
        values = frozenset(getattr(G, n) for n in names)
        for set_name, members in named.items():
            if values == members:
                violations.append(
                    f"{_GENOME_SRC.name}:{lineno} re-spells {set_name} inline "
                    f"({len(names)} markers) — use the name")
    assert not violations, "inline copies of a named marker set:\n  " + "\n  ".join(violations)


def test_marker_set_ratchet_no_near_copy_of_a_named_set():
    """R2 — nor a NEAR-copy: a proper subset covering more than half of a named set.

    That is the drift signature. ``genome_load`` held 12 of the 14 leaf-wide markers;
    ``_hv_from_block`` the same 12; ``_ScanState.fold`` 8 of the 10 non-boundary caps. A
    genuinely deliberate small subset (the two-element ``(GENE, REGULATORY)`` gate-type pair)
    sits well under the half-line and passes. If you really want a large subset, declare it
    at module level with a name and a docstring — a reviewed declaration, not a literal
    buried in a branch."""
    tree = ast.parse(_GENOME_SRC.read_text(encoding="utf-8"))
    named = _named_marker_sets()
    violations = []
    for lineno, names in _inline_spellings(tree, _marker_constants(tree)):
        values = frozenset(getattr(G, n) for n in names)
        for set_name, members in named.items():
            if values < members and len(values) * 2 > len(members):
                missing = sorted(members - values)
                violations.append(
                    f"{_GENOME_SRC.name}:{lineno} spells {len(values)} of "
                    f"{set_name}'s {len(members)} markers inline, omitting "
                    f"{[hex(m) for m in missing]} — a drifted copy")
    assert not violations, "near-copies of a named marker set:\n  " + "\n  ".join(violations)


def test_marker_set_ratchet_named_sets_are_pairwise_distinct():
    """R3 — two names for the same set is the same disease with better manners.

    rc351 found exactly that: ``_CHROM_BOUNDARY_MARKERS`` and ``_REGION_OPEN_MARKERS`` were
    byte-identical four-element tuples declared 2 600 lines apart."""
    named = _named_marker_sets()
    dupes = [(a, b) for i, (a, sa) in enumerate(sorted(named.items()))
             for (b, sb) in sorted(named.items())[i + 1:] if sa == sb]
    assert not dupes, f"duplicate marker sets under two names: {dupes}"


def test_marker_set_ratchet_leaf_wide_set_is_every_cap_marker():
    """The canonical set really is canonical: every ``*_CAP_MARKER`` / cap-family constant
    ``genome.py`` defines is in it, so ``_cap_kind`` classifies all of them. A new cap marker
    that is not added here would make this row red, which is the point — the fiber caps went
    in with three of the five spellings updated."""
    tree = ast.parse(_GENOME_SRC.read_text(encoding="utf-8"))
    turn_markers = {"PACKED_TURN_MARKER", "Q8_PACKED_TURN_MARKER",
                    "OCTONION_PACKED_TURN_MARKER"}
    cap_names = _marker_constants(tree) - turn_markers
    missing = sorted(n for n in cap_names
                     if getattr(G, n) not in G._LEAF_WIDE_BLOCK_MARKERS)
    assert not missing, (
        f"cap markers absent from _LEAF_WIDE_BLOCK_MARKERS: {missing} — every walker "
        f"strides by that tuple, so an omitted marker is an unreadable body")


def test_marker_set_ratchet_c_classifier_knows_the_same_set():
    """The C peer classifies the same fourteen bytes. The pure/native split is a projection
    boundary, not a capability boundary (ADR-0009) — and here the SCRIPTING side was the one
    missing the capability, which is the inversion worth pinning."""
    src = (_GENOME_SRC.parents[3] / "c" / "src" / "srmech_genome.c")
    if not src.exists():                          # a wheel install has no C sources
        pytest.skip("C sources not present in this layout")
    text = src.read_text(encoding="utf-8")
    body = text.split("static int genome_cap_kind", 1)[1].split("\n}", 1)[0]
    tree = ast.parse(_GENOME_SRC.read_text(encoding="utf-8"))
    turn_markers = {"PACKED_TURN_MARKER", "Q8_PACKED_TURN_MARKER",
                    "OCTONION_PACKED_TURN_MARKER"}
    missing = sorted(n for n in _marker_constants(tree) - turn_markers
                     if f"SRMECH_GENOME_{n}" not in body)
    assert not missing, f"genome_cap_kind does not classify: {missing}"
