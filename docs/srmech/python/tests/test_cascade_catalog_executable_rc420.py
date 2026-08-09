"""rc420 (`#T1114`) — the cascade catalog becomes EXECUTABLE, and this is
the gate that holds it there.

Through rc419 the 20 ``[cascade]`` descriptors under
``srmech/cascade/catalogs/cascade_catalog/`` were prose records — zero
carried an executable step list, and ADR-0012 §3.4 (clause C6) measured
their ``describe()`` visibility at literally zero. rc420 inverts that,
and this file pins the inversion three ways:

1. **NO THIRD STATE (strict zero, no ceiling).** Every catalog descriptor
   is either EXECUTABLE (declares ≥1 ``[[cascade.chain]]``) or an explicit
   LEAF (``[cascade.leaf]`` with ``irreducible = true`` AND a non-empty
   machine-readable ``reason``). Silence is not a leaf declaration.
2. **THE EQUIVALENCE IS EXECUTED, NOT ASSERTED IN PROSE.** Every declared
   chain runs through the ADR-0008 §2 engine (schema v2) on every one of
   its authored ``[[cascade.chain.proof_cases]]`` and the output is
   compared BIT-FOR-BIT (a canonical byte encoding — NaN payloads and
   signed zeros distinguish) against the shipped op, on the PURE
   projection. Pure on purpose, twice over: (a) several shipped ops
   dispatch whole-transform C kernels whose parity to the Python
   composition is a DOCUMENTED tolerance, not bit-exactness (the
   ``autocorrelation.toml`` parity field says "FFT round-off tolerance
   (~1e-12; NOT bit-exact)"), so a native-projection bit-compare would be
   asserting something the tree explicitly does not promise; (b) the
   chains' claim is about the CASCADE — the composition the descriptor
   documents — and the pure path IS that composition (each projection's
   own native parity is gated by its op's existing differential tests,
   ADR-0009).
3. **BOUNDARY-CASE COVERAGE.** Every key of an executable descriptor's
   ``[cascade.boundary_cases]`` block is either covered by a proof case
   (``covers = "<key>"``) or listed in :data:`WRAPPER_LAYER_BOUNDARIES`
   with a stated reason (a guard that RAISES at the wrapper, a native
   dispatch note, a runtime affordance — things a value-equivalence run
   cannot express). The exclusion dict is enumerated HERE, in the open,
   so it cannot silently grow: it is pinned per-descriptor, key by key.

Plus the ADR-0008 Phase-2 instrument this rc lands the Accepted status
on: :func:`test_closed_form_ops_scheme_gap_ratchet` pins the `#T1114`
rung-4 scheme census — the closed_form_ops modules that still need the
scan / fuel-bounded-consume forms — as a DOWN-ONLY named population
(the ``CEIL_WIRE_GLUE_GAPS`` shape: tight on both sides, drained one
module at a time as the forms land).
"""

from __future__ import annotations

import struct
from contextlib import contextmanager
from pathlib import Path

import pytest

import srmech._native as _native
from srmech import cascade
from srmech.cascade import compose as _compose
from srmech.dsl import get_descriptor, load_catalog
from srmech.dsl._cascade_chain import (
    cascade_catalog_status,
    cascade_chain_specs,
    descriptor_status,
)
from srmech.math.laplacian import schur_complement


# ── the pinned population (drift here must be conscious) ───────────────

#: The three explicit leaves — the atoms nothing lower-level composes.
EXPECTED_LEAVES = frozenset({"chiral_flip", "pin_slot_at_zero", "reorient"})

#: The seventeen executable descriptors.
EXPECTED_EXECUTABLE = frozenset({
    "autocorrelation", "best_rational_signed", "chiral_dual",
    "cyclic_gcd", "cyclic_mod_add", "cyclic_mod_inv", "cyclic_mod_mul",
    "cyclic_mod_mul_wide", "cyclic_mod_pow", "encode_loe_content",
    "kuramoto_step", "magnitude", "net_chirality", "octonion_dft",
    "parallel_sector_dispatch", "quaternion_dft", "schur_complement",
})

#: Boundary-case keys a VALUE-equivalence run cannot express, with the
#: reason each one is wrapper-layer. STRICT: a key here must exist in the
#: descriptor, and a descriptor key must be covered or listed here.
WRAPPER_LAYER_BOUNDARIES = {
    "best_rational_signed": {
        "invalid_kwargs": "guard RAISES at the Python dispatch layer "
                          "before any cascade step runs",
        "bool_kwargs": "a native-vs-pure DISPATCH note (bool rejected by "
                       "the C type gate), not a value contract",
    },
    "net_chirality": {
        "out_of_int8": "native-dispatch fallback note (which projection "
                       "runs), not a value contract",
        "generator": "native-dispatch fallback note; the chain's fold "
                     "walks any iterable the same way the pure op does",
        "mixed_types": "native-dispatch fallback note",
    },
    "kuramoto_step": {
        "length_mismatch": "guard RAISES at the Python dispatch layer",
        "adjacency_shape": "guard RAISES at the Python dispatch layer",
        "pin_length": "guard RAISES at the Python dispatch layer",
        "generalized_defaults": "a ROUTING claim (defaults select the "
                                "simple native path bit-for-bit) — gated "
                                "by the shipped kuramoto differential "
                                "tests, not by chain equivalence",
        "aliasing": "a C-buffer contract; the Python chain always "
                    "allocates fresh lists",
        "non_numeric": "native-dispatch fallback note",
    },
    "autocorrelation": {
        "aliasing": "a C-buffer contract; the chain allocates fresh lists",
        "non_numeric": "native-dispatch fallback note",
    },
    "parallel_sector_dispatch": {
        "cap_at_4": "guard RAISES (n_sectors > 4) at the op boundary",
        "n_sectors_lower": "guard RAISES (n_sectors < 1) at the op "
                           "boundary",
        "concurrency": "a runtime affordance (thread overlap), not a "
                       "value contract",
        "verify_kwarg": "verify=True re-runs the serial cross-check — a "
                        "self-test flag, not a distinct value path",
        "collapse_lattice": "a structural property of body symmetry "
                            "classes, exercised by the shipped parallel "
                            "tests, not an input case",
    },
    "cyclic_gcd": {
        "negative_input": "guard RAISES at the primitive (uint64 domain)",
        "out_of_uint64": "guard RAISES at the primitive",
        "bool_input": "a native-vs-pure DISPATCH note, not a value "
                      "contract",
    },
    "cyclic_mod_add": {
        "zero_modulus": "guard RAISES at the primitive",
        "out_of_uint64": "guard RAISES at the primitive",
        "bool_input": "guard RAISES at the primitive (isinstance gate)",
    },
    "cyclic_mod_mul": {
        "zero_modulus": "guard RAISES at the primitive",
        "out_of_uint64": "guard RAISES at the primitive",
        "bool_input": "guard RAISES at the primitive (isinstance gate)",
    },
    "cyclic_mod_pow": {
        "zero_modulus": "guard RAISES at the primitive",
        "out_of_uint64": "guard RAISES at the primitive",
    },
    "cyclic_mod_inv": {
        "no_inverse": "guard RAISES (gcd(a, n) != 1)",
        "degenerate_modulus": "guard RAISES (n >= 2 required)",
    },
    "cyclic_mod_mul_wide": {
        "zero_modulus": "guard RAISES at the primitive",
        "negative_operand": "guard RAISES at the primitive",
        "native_absent": "the equivalence gate runs EXACTLY this "
                         "projection — the note is the gate's own "
                         "operating condition, not an input case",
    },
    "schur_complement": {
        "singular_interior": "guard RAISES (no harmonic extension)",
        "exact_vs_float": "a dispatch/precision note (the float path is "
                          "the numpy [scientific] extra); chain and op "
                          "share whichever path the environment selects",
    },
}

#: ADR-0008 Phase-2 scope, pinned as a population (the rung-4 scheme
#: census, re-derivable from
#: ``docs/srmech/notes/t1114_rung4_scheme_census_rc419_20260809.ndjson``):
#: the closed_form_ops modules NOT declarable after the indexed map lands,
#: by missing recursion scheme. scan = mapAccumL (out[k] depends on carried
#: state — same totality class as fold); fuel-bounded consume = every
#: ``while`` in the 41-module corpus advances a strictly-decreasing fuel
#: measure (the predicate-only unbounded while is EMPTY in shipped code).
#: DOWN-ONLY on both sides: landing a form drains its set in the same
#: commit; a new module needing a missing form may not be added silently.
SCHEME_GAP_SCAN = frozenset({
    "allpass", "arithmetic_coding", "hdc_truncation", "huffman", "iir",
    "lz77", "mlse", "viterbi",
})
SCHEME_GAP_FUEL_CONSUME = frozenset({"huffman", "lz77", "rle"})


# ── the pure projection (see the module docstring for why) ─────────────

@contextmanager
def _pure_projection():
    saved = (_native.HAS_NATIVE, _native.LIB)
    _native.HAS_NATIVE, _native.LIB = False, None
    try:
        yield
    finally:
        _native.HAS_NATIVE, _native.LIB = saved


# ── canonical bit-encoding (floats compare by BITS, not by ==) ─────────

def _bits(x) -> bytes:
    if isinstance(x, float):
        return b"f" + struct.pack("<d", x)
    if isinstance(x, bool):
        return b"b1" if x else b"b0"
    if isinstance(x, int):
        return b"i" + repr(x).encode()
    if isinstance(x, str):
        return b"s" + x.encode("utf-8")
    if isinstance(x, bytes):
        return b"y" + x
    if isinstance(x, tuple):
        return b"t(" + b",".join(_bits(v) for v in x) + b")"
    if isinstance(x, list):
        return b"l[" + b",".join(_bits(v) for v in x) + b"]"
    if isinstance(x, dict):
        return b"d{" + b",".join(
            _bits(k) + b":" + _bits(v) for k, v in sorted(
                x.items(), key=lambda kv: repr(kv[0]))) + b"}"
    if x is None:
        return b"n"
    if hasattr(x, "tolist"):                     # Mat / Vec carriers
        return b"M" + _bits(x.tolist())
    return b"r" + repr(x).encode()


# ── the shipped-op invocation glue, per descriptor/variant ─────────────

#: Per-variant defaults merged UNDER a proof case's inputs, so a TOML case
#: can omit what TOML cannot spell (None) or what the op defaults.
CASE_DEFAULTS = {
    ("kuramoto_step", "general"): {
        "adjacency": None, "alpha": 0.0,
        "pin_anchor": None, "pin_strength": 1.0,
    },
}


def _invoke_op(name: str, variant: str, inp: dict):
    """Call the SHIPPED op the way its wrapper contract expects, from the
    chain's input dict. This is the one place chain-input spelling maps to
    op-call spelling, kept explicit per descriptor."""
    if name == "cyclic_gcd":
        return cascade.cyclic_gcd(inp["a"], inp["b"])
    if name == "cyclic_mod_add":
        return cascade.cyclic_mod_add(inp["a"], inp["b"], inp["n"])
    if name == "cyclic_mod_mul":
        return cascade.cyclic_mod_mul(inp["a"], inp["b"], inp["n"])
    if name == "cyclic_mod_pow":
        return cascade.cyclic_mod_pow(inp["a"], inp["k"], inp["n"])
    if name == "cyclic_mod_inv":
        return cascade.cyclic_mod_inv(inp["a"], inp["n"])
    if name == "cyclic_mod_mul_wide":
        return cascade.cyclic_mod_mul_wide(inp["a"], inp["b"], inp["n"])
    if name == "schur_complement":
        return schur_complement(inp["L"], inp["boundary_idx"])
    if name == "magnitude":
        return cascade.magnitude(inp["x"])
    if name == "best_rational_signed":
        return cascade.best_rational_signed(
            inp["x"], max_denominator=inp["max_denominator"],
            fine_scale=inp["fine_scale"])
    if name == "net_chirality":
        return cascade.net_chirality(inp["orientations"])
    if name == "chiral_dual":
        return cascade.chiral_dual(cascade.autocorrelation, inp["x"])
    if name == "parallel_sector_dispatch":
        return cascade.parallel_sector_dispatch(
            cascade.chiral_flip, inp["x"], n_sectors=inp["n_sectors"],
            combine=inp["combine"])
    if name == "encode_loe_content":
        from srmech.signal_processing.rbs_hdc_instrument import (
            encode_loe_content,
        )
        return encode_loe_content(inp["content"], D=inp["D"],
                                  substrate=inp["substrate"])
    if name == "autocorrelation":
        return cascade.autocorrelation(inp["x"])
    if name == "kuramoto_step":
        if variant == "simple":
            return cascade.kuramoto_step(
                inp["theta"], inp["omega"], coupling=inp["coupling"],
                dt=inp["dt"])
        return cascade.kuramoto_step(
            inp["theta"], inp["omega"], coupling=inp["coupling"],
            dt=inp["dt"], adjacency=inp["adjacency"], alpha=inp["alpha"],
            pin_anchor=inp["pin_anchor"],
            pin_strength=inp["pin_strength"])
    if name == "quaternion_dft":
        return cascade.quaternion_dft(
            inp["x"], form=("left" if inp["left"] else "right"),
            mu_axis=inp["mu_axis"], inverse=inp["inverse"])
    if name == "octonion_dft":
        kw = dict(form=inp["form"], mu_axis=inp["mu_axis"],
                  bracketing=inp["bracketing"], inverse=inp["inverse"])
        if inp["form"] == "two_sided":
            kw["two_sided_right_axis"] = inp["mu_r_axis"]
        return cascade.octonion_dft(inp["x"], **kw)
    raise AssertionError(f"no invocation glue for descriptor {name!r} — "
                         f"a new executable descriptor needs its row here")


def _executable_cases():
    """(name, variant, spec, covers, inputs) for every proof case."""
    out = []
    for name in sorted(EXPECTED_EXECUTABLE):
        for variant, spec, entry in cascade_chain_specs(name):
            cases = entry.get("proof_cases", [])
            assert cases, (
                f"{name}.{variant}: a declared chain with NO proof cases "
                f"is asserted-in-prose, which is the state rc420 removes")
            for case in cases:
                out.append((name, variant, spec, case.get("covers", ""),
                            dict(case.get("inputs", {}))))
    return out


# ── 1. no third state ──────────────────────────────────────────────────

def test_no_third_state_strict_zero():
    """Every catalog descriptor is executable-and-declared or explicit
    LEAF. STRICT ZERO, no ceiling: 'undeclared' was the 20/20 state
    through rc419 and it does not come back one descriptor at a time."""
    status = cascade_catalog_status()
    undeclared = sorted(n for n, s in status.items() if s == "undeclared")
    assert not undeclared, (
        f"{len(undeclared)} descriptor(s) in the third state: {undeclared}."
        f" Declare an executable [[cascade.chain]] (with proof cases) or "
        f"an explicit [cascade.leaf] with irreducible = true and a reason."
    )


def test_population_witness():
    """The 17/3 split, by NAME — drift is conscious, not incidental."""
    status = cascade_catalog_status()
    assert {n for n, s in status.items() if s == "leaf"} == EXPECTED_LEAVES
    assert {n for n, s in status.items()
            if s == "executable"} == EXPECTED_EXECUTABLE
    assert len(status) == 20, (
        f"catalog holds {len(status)} descriptors; this witness pinned 20 "
        f"at rc420 — update BOTH expected sets consciously")


def test_leaf_reasons_are_machine_readable():
    """A leaf declaration carries its reason IN the descriptor — the gate
    reads it from the shipped TOML, not from a test comment."""
    for name in sorted(EXPECTED_LEAVES):
        desc = get_descriptor(name)
        leaf = desc.get("cascade", {}).get("leaf", {})
        assert leaf.get("irreducible") is True, name
        assert isinstance(leaf.get("reason"), str) and \
            len(leaf["reason"].strip()) > 40, (
            f"{name}: a leaf reason under 40 characters is a marker, not "
            f"a reason")
        assert descriptor_status(desc) == "leaf"


# ── 2. the equivalence, executed ───────────────────────────────────────

@pytest.mark.parametrize(
    "name,variant,spec,covers,inputs",
    [pytest.param(n, v, s, c, i, id=f"{n}.{v}.{c}.{j}")
     for j, (n, v, s, c, i) in enumerate(_executable_cases())],
)
def test_declared_chain_is_bit_identical_to_shipped_op(
        name, variant, spec, covers, inputs):
    """Chain output == op output, BIT-for-bit, on the pure projection —
    per proof case (see the module docstring for the projection rationale).
    """
    merged = dict(CASE_DEFAULTS.get((name, variant), {}))
    merged.update(inputs)
    with _pure_projection():
        chain_out = _compose.run_chain(spec, inputs=merged)
        op_out = _invoke_op(name, variant, merged)
    assert _bits(chain_out) == _bits(op_out), (
        f"{name}.{variant} proof case covers={covers!r}: the DECLARED "
        f"chain diverges from the shipped op.\n  chain: {chain_out!r}\n"
        f"  op   : {op_out!r}\n  inputs: {merged!r}"
    )


def test_equivalence_population_floor():
    """The equivalence parametrization is not vacuous: rc420 authored
    proof cases across all 17 descriptors (18 variants) — a drop below
    the floor means a loader/parametrize seam went quiet, not that the
    catalog shrank."""
    cases = _executable_cases()
    assert len(cases) >= 80, (
        f"only {len(cases)} proof cases collected; rc420 authored >= 80")
    variants = {(n, v) for n, v, _s, _c, _i in cases}
    assert len(variants) == 18, (
        f"{len(variants)} chain variants collected; rc420 shipped 18 "
        f"(17 descriptors, kuramoto_step twice)")


# ── 3. boundary-case coverage ──────────────────────────────────────────

def test_boundary_cases_are_covered_or_explicitly_wrapper_layer():
    """Every ``[cascade.boundary_cases]`` key of an executable descriptor
    is claimed by a proof case or listed (with reason) in
    :data:`WRAPPER_LAYER_BOUNDARIES`. STRICT both ways — a stale exclusion
    (key gone from the descriptor) also fails, so the dict cannot rot."""
    covers_by_name: dict = {}
    for name, _v, _s, covers, _i in _executable_cases():
        covers_by_name.setdefault(name, set()).add(covers)
    problems = []
    for name in sorted(EXPECTED_EXECUTABLE):
        desc = get_descriptor(name)
        keys = set(desc.get("cascade", {}).get("boundary_cases", {}))
        excl = WRAPPER_LAYER_BOUNDARIES.get(name, {})
        for key in sorted(keys):
            if key not in covers_by_name.get(name, set()) \
                    and key not in excl:
                problems.append(
                    f"  {name}: boundary case {key!r} has no proof case "
                    f"and no wrapper-layer exclusion")
        for key in sorted(excl):
            if key not in keys:
                problems.append(
                    f"  {name}: exclusion {key!r} names a boundary case "
                    f"the descriptor no longer declares (stale)")
    assert not problems, (
        f"{len(problems)} boundary-coverage problem(s):\n"
        + "\n".join(problems))


# ── 4. ADR-0008 Phase-2 instrument: the scheme-gap ratchet ─────────────

def test_closed_form_ops_scheme_gap_ratchet():
    """The ADR-0008 Phase-2 clauses' instrument (scan + fuel-bounded
    consume), pinned as a DOWN-ONLY named population.

    Landing the scan form means removing its modules from
    :data:`SCHEME_GAP_SCAN` in the same commit (the census gets re-run for
    the drained module — a declared chain replacing its hand-rolled
    iteration is the exit condition); same for the fuel-bounded-consume
    form. The union (9 modules at rc420) is the ``modules_not_closed``
    figure of the rung-4 census, so this test is the census made a
    ratchet rather than a note.
    """
    cfo = (Path(__file__).resolve().parent.parent
           / "srmech" / "signal_processing" / "closed_form_ops")
    assert cfo.is_dir(), f"closed_form_ops not found at {cfo}"
    missing = [m for m in sorted(SCHEME_GAP_SCAN | SCHEME_GAP_FUEL_CONSUME)
               if not (cfo / f"{m}.py").exists()]
    assert not missing, (
        f"scheme-gap module(s) no longer on disk: {missing} — a deleted "
        f"module leaves the ratchet counting ghosts; drain it here in the "
        f"same commit")
    union = SCHEME_GAP_SCAN | SCHEME_GAP_FUEL_CONSUME
    assert len(union) == 9, (
        f"the scheme-gap union is {len(union)}, rc420 pinned 9 "
        f"(the rung-4 census modules_not_closed figure). Down-only: a "
        f"landed form DRAINS its set in the same commit; a new module "
        f"needing a missing form is a conscious widening, not a drift."
    )
    # The exile boundary stays where the census measured it: the corpus
    # carries NO predicate-only unbounded while (every while is
    # fuel-bounded), so neither form would break kernel totality.
    assert SCHEME_GAP_FUEL_CONSUME <= {"huffman", "lz77", "rle"}
    assert SCHEME_GAP_SCAN <= {
        "allpass", "arithmetic_coding", "hdc_truncation", "huffman",
        "iir", "lz77", "mlse", "viterbi"}


# ── 5. the loader itself ───────────────────────────────────────────────

def test_run_cascade_chain_is_the_catalog_made_callable():
    """The public runner executes a descriptor's declared chain end to
    end — the user-facing half of the inversion."""
    from srmech.dsl import run_cascade_chain
    with _pure_projection():
        assert run_cascade_chain("cyclic_gcd", {"a": 12, "b": 18}) == 6
        got = run_cascade_chain("magnitude", x=-3.25)
        assert _bits(got) == _bits(3.25)
        with pytest.raises(ValueError, match="variant"):
            run_cascade_chain("kuramoto_step", {"theta": [], "omega": [],
                                                "coupling": 1.0,
                                                "dt": 0.01})
        got = run_cascade_chain(
            "kuramoto_step",
            {"theta": [0.1], "omega": [0.4], "coupling": 1.0, "dt": 0.01},
            variant="simple")
        assert _bits(got) == _bits(
            cascade.kuramoto_step([0.1], [0.4], coupling=1.0, dt=0.01))
    with pytest.raises(ValueError, match="no \\[\\[cascade.chain\\]\\]"):
        cascade_chain_specs("chiral_flip")


def test_catalog_load_still_clean():
    """The rc420 descriptor additions parse under the shipped loader (the
    lru-cached catalog sees all 20 with their new sections)."""
    catalog = load_catalog()
    assert len(catalog) >= 20
    for name in EXPECTED_EXECUTABLE | EXPECTED_LEAVES:
        assert name in catalog
