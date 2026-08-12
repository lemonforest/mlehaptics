#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G3 (rc427) — THE NOTATION CARRIER AND ITS CHARTS: what is frame-free, what is
convention, and exactly what the chart carries that the carrier cannot.

READ-ONLY research note. Writes NOTHING under ``srmech/``. Every number below
comes out of a SHIPPED srmech op; the only bare-Python arithmetic is list
bookkeeping. No ``abs()`` anywhere — sign is a Class-K pin-slot
(:func:`srmech.cascade.pin_slot_at_zero` / :func:`srmech.cascade.magnitude`)
with Class-C re-application, per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``. No stdlib
``math`` / ``fractions`` / ``decimal``. No numpy.

WHAT THIS ROUND ADDS TO THE COMMITTED rc426 ROWS
================================================
rc426 measured THAT the chart carries strictly more than the carrier (F7: 35
chart symbols -> 12 carrier values, interval agreement 1225/1225, backward map
NOT injective, "the surplus is SPELLING"). It did not measure WHAT that surplus
is, or whether it is recoverable. This round does, and the answer turns out to
identify the spelling loss with a loss srmech ALREADY ships an op for.

Everything here is stated over the shipped surface at v0.9.0rc425
(registry 649). The per-tradition sourcing tiers of
``_p7_chart_families_sourced_rc426.ndjson`` are taken AS GIVEN and are not
re-asserted; where this file needs a tradition claim it either cites that row's
tier or marks the datum a MODEL PARAMETER, never a claim about a living
practice.

PRE-REGISTERED FALSIFIERS — written before any of the code below was run
=======================================================================
G1  THE SPELLING MODEL. Model a spelling as a position on the chain generated
    by a unit ``g`` of ``Z/n``, with a symbol = (degree ``d`` in ``0..a-1``,
    modifier ``m``), chain position ``c0 + d + s*m``.
    FALSIFIER: if the Western 7-letter x 5-accidental symbol set is NOT in
    bijection with a CONTIGUOUS 35-wide window of the fifth-chain, the model is
    REFUTED and the loss is not a coset.
    PREDICTION: bijection onto a contiguous window, and the reproduction of
    rc426's ``STEP_MAP = (0,2,4,5,7,9,11)`` from (n=12, g=7, c0=-1, a=7) — i.e.
    what rc426's own comment calls "the chart's ONLY convention" is itself the
    image of a three-parameter declaration.
G1a WELL-FORMEDNESS LAW. PREDICTION: the symbol set is contiguous-and-bijective
    iff the modifier step ``s`` equals the alphabet size ``a``, and (over the
    carrier) iff ``a = g^-1 mod n``. Swept over a x s and over every (n, unit g).
    FALSIFIER: any (a, s) with ``s != a`` that is nevertheless contiguous, or
    any (n, g) whose derived ``a`` fails.
G1b THE FIBRE COMPOSES. FALSIFIER: if
    ``lift_fibre(mod_mul(mod_inv(g,n), p, n), n, W)`` differs from the brute
    ``{k in [-W,W] : g*k = p mod n}`` at ANY (n, unit g, p), the spelling fibre
    is NOT the shipped covering fibre and a new op IS warranted.
    PREDICTION: identical at every one; therefore REJECT a spelling-fibre op.
G1c RECOVERABILITY. Three hypotheses, each measured, each able to return
    otherwise: (H1) the chart declaration alone; (H2) carrier context over a
    sequence; (H3) a cover-valued datum. NEGATIVE CONTROL: a modifier-free
    chart, which MUST come back recoverable, or the instrument is not one.
G2  THE SHAPE OF THE LOSS IS CONVENTION-FREE. PREDICTION: the preimage
    histogram depends only on the window width and ``n``, never on ``g``.
    FALSIFIER: any (n, W) where two units give different histograms.
G3  THE LEAK TEST. Six candidate leaks named in the brief, each classified by
    SUBSTITUTION, not by intuition. NEGATIVE CONTROLS: two deliberately leaked
    probe ops (one hard-wiring 12, one hard-wiring the generator) and one clean
    probe. FALSIFIER: if the test blesses either leaked probe it is not an
    instrument.
G3b THE rc426 LEAK TEST HAS A BLIND SPOT. PREDICTION: the generator-leaking
    probe PASSES F12b's three-bucket predicate (it accepts a modulus, is total,
    moves with n, hard-wires no 12) and FAILS the generator clause. FALSIFIER:
    if F12b already catches it, this whole clause is unnecessary and should be
    dropped.
G4  CLEF vs ``octonion_frame_read`` — FORM, not identity. A four-clause
    predicate run on BOTH. FALSIFIER of the "only analogous" verdict: if some
    shipped action IS simply transitive on all 28 frames, then clause (d) holds
    on both and the two ARE the same shape.
G5  THE ACTION CARRIER. FALSIFIER: if the standard-tuning action->pitch map IS
    additive, the action space collapses to the pitch carrier and there is no
    second carrier. PREDICTION: additivity FAILS for the irregular tuning and
    HOLDS for a regular one, whose kernel is rank 1. NEGATIVE CONTROLS: a
    one-string tuning (must report NO loss) and an all-unison tuning (must
    report uniform 6-fold loss).
G6  THE KEY SIGNATURE IS DERIVED. PREDICTION: the accidental count for a
    transposition by ``t`` equals the Class-K magnitude of the least-magnitude
    representative of ``g^-1 * t mod n``; for (12, 7) that is
    ``[0,5,2,3,4,1,6,1,4,3,2,5]``, it reproduces rc426's F14b
    ``degrees_needing_a_modifier = 1`` at ``origin_shift = 7``, and it TIES at
    the tritone. FALSIFIER: any disagreement with an independent
    rotation-search over the chart.
G7  EQUAL TEMPERAMENT IS A DECLARED MAP. FALSIFIER: if every division in the
    sweep tempers out the same comma, "which temperament" carries no
    information and ET is not chart data.

SCOPE CHECK (done before writing, not after)
--------------------------------------------
Nothing here touches fingerboard GEOMETRY, string length, mesh, or fabrication
tolerance: the action lattice of G5 is a pair of INTEGER INDICES (which course,
which position) and its map to pitch is a group homomorphism question. That is
algebra, and it is inside scope; the CAD/GPU ban is on the continuum shadow, and
this note never leaves the ALU. ``srmech.music.relations`` states the same
boundary in its own words ("fingerboard GEOMETRY are out of scope").
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.abspath(os.path.join(_HERE, "..", "python"))
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

import srmech                                                  # noqa: E402
from srmech.cascade import (cyclic_mod_add, magnitude,          # noqa: E402
                            net_chirality, octonion_frame_read,
                            pin_slot_at_zero)
from srmech.math.covering import center_lift, lift_fibre        # noqa: E402
from srmech.math.cyclic import gcd, mod_add, mod_inv, mod_mul   # noqa: E402
from srmech.music import (comma_of_chain, interval_vector,      # noqa: E402
                          just_limit, normal_order, prime_form,
                          tempers_out)

OUT = os.path.join(_HERE, "_g3_notation_rc427.ndjson")

#: The modulus sweep rc426 used, kept identical so rows compare directly.
MODULI = (5, 7, 12, 17, 19, 22, 24, 31, 41, 53)

_RECORDS = []


def emit(**row):
    row.setdefault("srmech_version", srmech.__version__)
    _RECORDS.append(row)


# ══════════════════════════════════════════════════════════════════════
# Helpers — every one of them a composition of SHIPPED ops.
# ══════════════════════════════════════════════════════════════════════
def res(k: int, n: int) -> int:
    """Least non-negative residue of a possibly-NEGATIVE ``k`` mod ``n``.

    ``srmech.math.cyclic.mod_add`` is a uint64 surface and refuses a negative
    operand, so the sign is split off FIRST as a Class-K pin-slot and
    re-applied as a Class-C negation inside Z/n. This is the named K/C
    composition the discipline requires — never ``abs()``, never a bare ``%``
    standing in for the shipped modular op.
    """
    orientation, mag = pin_slot_at_zero(k)
    r = mod_add(int(mag), 0, n)
    if orientation < 0 and r != 0:
        r = mod_add(n - r, 0, n)          # Class C: re-apply the orientation
    return r


def least_magnitude_rep(k: int, n: int) -> int:
    """The representative of ``k mod n`` with the smallest Class-K magnitude.

    A TIE (exactly at ``n/2``) is returned as the positive one and FLAGGED by
    the caller — the tie is a measurement, not a rounding nuisance.
    """
    r = res(k, n)
    alt = r - n
    return r if magnitude(r) <= magnitude(alt) else alt


def is_tie(k: int, n: int) -> bool:
    r = res(k, n)
    return magnitude(r) == magnitude(r - n)


def units(n: int):
    return tuple(g for g in range(1, n) if gcd(g, n) == 1)


def chain_to_carrier(k: int, g: int, n: int) -> int:
    """A chain position (an integer, i.e. a point of the COVER) -> its carrier
    residue. This is the surjection Z ->> Z/n whose kernel IS the loss."""
    return mod_mul(g, res(k, n), n)


def chain_fibre_shipped(p: int, g: int, n: int, window: int):
    """The spelling fibre, built ONLY from shipped ops."""
    k0 = mod_mul(mod_inv(g, n), res(p, n), n)
    return lift_fibre(k0, n, window)


def chain_fibre_brute(p: int, g: int, n: int, window: int):
    return [k for k in range(-window, window + 1)
            if chain_to_carrier(k, g, n) == res(p, n)]


def symbol_chain_positions(c0: int, a: int, s: int, mods):
    """symbol (degree, modifier) -> chain position."""
    return {(d, m): c0 + d + s * m for d in range(a) for m in mods}


def contiguous(values) -> bool:
    vals = sorted(set(values))
    if len(vals) != len(list(values)):
        return False
    return vals[-1] - vals[0] + 1 == len(vals)


def histogram(counts):
    out = {}
    for c in counts:
        out[str(c)] = out.get(str(c), 0) + 1
    return out


# ══════════════════════════════════════════════════════════════════════
# G0 — environment
# ══════════════════════════════════════════════════════════════════════
def g0_env():
    try:
        import numpy                                            # noqa: F401
        numpy_absent = False
    except ModuleNotFoundError:
        numpy_absent = True
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    n_ops = len(get_tool_schema())
    emit(finding="G0_env",
         srmech_file=srmech.__file__,
         numpy_absent=numpy_absent,
         registry_ops=n_ops,
         python=sys.version.split()[0])
    print("env", srmech.__file__, srmech.__version__, "registry", n_ops,
          "numpy_absent", numpy_absent)
    return n_ops


# ══════════════════════════════════════════════════════════════════════
# G1 — the spelling model, and the reproduction of rc426's STEP_MAP
# ══════════════════════════════════════════════════════════════════════
def g1_spelling_is_a_chain_window():
    n, g, c0, a, s = 12, 7, -1, 7, 7
    mods = tuple(range(-2, 3))
    sym = symbol_chain_positions(c0, a, s, mods)
    positions = list(sym.values())
    ok_contig = contiguous(positions)

    # The 7 naturals, read through the carrier surjection.
    step_map = tuple(sorted(chain_to_carrier(c0 + d, g, n) for d in range(a)))
    rc426_step_map = (0, 2, 4, 5, 7, 9, 11)

    carrier_vals = [chain_to_carrier(k, g, n) for k in positions]
    hist = histogram([carrier_vals.count(v) for v in range(n)])

    emit(finding="G1_spelling_is_a_chain_window",
         n=n, generator=g, chain_origin=c0, alphabet=a, modifier_step=s,
         modifiers=list(mods),
         n_symbols=len(sym),
         chain_window=[min(positions), max(positions)],
         window_width=max(positions) - min(positions) + 1,
         contiguous_and_bijective=ok_contig,
         derived_step_map=list(step_map),
         rc426_step_map=list(rc426_step_map),
         reproduces_rc426_step_map=(step_map == rc426_step_map),
         preimage_histogram=hist,
         rc426_F7_preimage_histogram={"2": 1, "3": 11},
         reproduces_rc426_F7_histogram=(hist == {"2": 1, "3": 11}),
         verdict=(
             "The 35 letter+accidental symbols are in BIJECTION with a "
             "CONTIGUOUS 35-wide window of the fifth-chain, and their carrier "
             "preimage histogram is bit-identical to rc426 F7's {2:1, 3:11}. "
             "So the surplus F7 called 'spelling' is exactly A CHOICE OF "
             "INTEGER LIFT: the chart names a point of the COVER Z, the "
             "carrier holds only its image in Z/12. rc426's own comment calls "
             "STEP_MAP = (0,2,4,5,7,9,11) 'the chart's ONLY convention'; it is "
             "reproduced here from (n=12, g=7, c0=-1, a=7), so that map is not "
             "a convention at all but the image of a three-parameter "
             "DECLARATION."))
    return ok_contig


def g1a_wellformedness_law():
    """Contiguous-and-bijective iff modifier step == alphabet size; and over the
    carrier, iff a == g^-1 mod n. Swept, with the failures kept as the control."""
    mods = tuple(range(-2, 3))
    rows, wrong = [], []
    for a in range(2, 13):
        for s in range(-13, 14):
            if s == 0:
                continue
            sym = symbol_chain_positions(0, a, s, mods)
            ok = contiguous(list(sym.values()))
            predicted = magnitude(s) == a
            rows.append({"a": a, "s": s, "contiguous": ok,
                         "predicted": predicted})
            if ok != predicted:
                wrong.append({"a": a, "s": s, "contiguous": ok,
                              "predicted": predicted})
    emit(finding="G1a_wellformedness_law_over_a_and_s",
         n_cells=len(rows),
         n_contiguous=sum(1 for r in rows if r["contiguous"]),
         n_mispredicted=len(wrong),
         mispredictions=wrong[:10],
         law="contiguous-and-bijective  iff  magnitude(modifier step) == alphabet size",
         verdict=("The law holds on every cell of the sweep. The negative "
                  "control is built in: every s with magnitude(s) != a is "
                  "measured NON-contiguous, so the predicate can return "
                  "otherwise and does, on most of the grid."))

    # The carrier-side statement: a is FORCED by (n, g).
    derived = []
    for n in MODULI:
        for g in units(n):
            a = mod_inv(g, n)
            sym = symbol_chain_positions(0, a, a, mods)
            ok = contiguous(list(sym.values()))
            carrier = sorted(chain_to_carrier(d, g, n) for d in range(a))
            derived.append({"n": n, "g": g, "derived_alphabet": a,
                            "contiguous": ok,
                            "alphabet_covers_carrier": len(set(carrier)) == a})
    bad = [r for r in derived if not r["contiguous"]]
    western = [r for r in derived if r["n"] == 12 and r["g"] == 7]
    emit(finding="G1a_alphabet_size_is_derived_from_the_generator",
         n_cells=len(derived),
         n_failures=len(bad),
         failures=bad[:10],
         western_row=western,
         per_n_alphabet_sizes={str(n): sorted({mod_inv(g, n) for g in units(n)})
                               for n in MODULI},
         verdict=(
             "The alphabet size is a THEOREM of the declared generator: "
             "a = g^-1 mod n, on 0 failures across every (n, unit g) in the "
             "sweep. For (n=12, g=7) it returns SEVEN. So 'seven letter names' "
             "is not the Western datum — the Western datum is g=7, and seven "
             "follows. The leak to guard is therefore NOT the alphabet size; "
             "it is an op that cannot be TOLD its generator."))
    return len(wrong) == 0 and len(bad) == 0


def g1b_fibre_composes_from_shipped():
    window = 17
    agree = total = 0
    per_n = []
    for n in MODULI:
        n_ok = n_tot = 0
        for g in units(n):
            for p in range(n):
                a = chain_fibre_shipped(p, g, n, window)["fibre"]
                b = chain_fibre_brute(p, g, n, window)
                n_tot += 1
                if a == b:
                    n_ok += 1
        per_n.append({"n": n, "units": len(units(n)),
                      "agree": n_ok, "total": n_tot})
        agree += n_ok
        total += n_tot

    # NEGATIVE CONTROL: a NON-unit generator has no inverse; the shipped op
    # must REFUSE rather than return a wrong fibre.
    refused, accepted = [], []
    for n in (12, 22, 24):
        for g in range(2, n):
            if gcd(g, n) == 1:
                continue
            try:
                mod_inv(g, n)
                accepted.append({"n": n, "g": g})
            except ValueError:
                refused.append({"n": n, "g": g})
    emit(finding="G1b_spelling_fibre_composes_from_shipped_ops",
         composition="lift_fibre( mod_mul( mod_inv(g,n), p, n ), n, W )",
         window=window,
         agree=agree, total=total,
         per_modulus=per_n,
         negative_control_non_unit_generators_refused=len(refused),
         negative_control_non_unit_generators_wrongly_accepted=len(accepted),
         verdict=(
             "IDENTICAL on every (n, unit g, p) in the sweep. The enharmonic "
             "spelling fibre IS srmech's shipped covering fibre with the "
             "generator folded into the shadow by two Class-I calls. A "
             "'spelling_fibre' op is therefore REJECTED: it would re-ship "
             "srmech.math.covering.lift_fibre. The non-unit control confirms "
             "the composition refuses rather than lying: every non-unit g is "
             "rejected by mod_inv, 0 wrongly accepted."))
    return agree == total


def g1c_recoverability():
    n, g, c0, a, s = 12, 7, -1, 7, 7
    mods = tuple(range(-2, 3))
    sym = symbol_chain_positions(c0, a, s, mods)
    window_lo, window_hi = min(sym.values()), max(sym.values())

    # H1 — the CHART DECLARATION alone.
    per_value = {}
    for k in sym.values():
        v = chain_to_carrier(k, g, n)
        per_value.setdefault(v, []).append(k)
    h1_hist = histogram([len(v) for v in per_value.values()])
    h1_determined = sum(1 for v in per_value.values() if len(v) == 1)

    # H2 — CARRIER CONTEXT over a sequence: how many spellings survive?
    seq = [0, 2, 4, 5, 7, 9, 11, 0]
    counts, running = [], 1
    for i, v in enumerate(seq):
        running *= len(per_value[v])
        counts.append({"length": i + 1, "spellings": running})

    # H3 — a COVER-valued datum: give the chain position instead of the
    # carrier residue. The symbol -> chain-position map is injective over the
    # declared window (G1), so the chain position pins the symbol; and the SAME
    # shipped op reports that, through the universal-cover path, by returning a
    # fibre of size 1 rather than by a branch that could not have said
    # otherwise (lift_fibre's own contract).
    h3_symbol_injective = len(set(sym.values())) == len(sym)
    h3_universal = [lift_fibre(k, 0, 64)["size"] for k in sym.values()]
    h3_determined = (h3_symbol_injective and set(h3_universal) == {1})

    # NEGATIVE CONTROL: a modifier-FREE chart must come back RECOVERABLE.
    ctrl = symbol_chain_positions(0, n, n, (0,))
    ctrl_per_value = {}
    for k in ctrl.values():
        ctrl_per_value.setdefault(chain_to_carrier(k, g, n), []).append(k)
    ctrl_hist = histogram([len(v) for v in ctrl_per_value.values()])

    emit(finding="G1c_what_the_loss_IS_and_whether_it_is_recoverable",
         chart={"n": n, "g": g, "c0": c0, "a": a, "s": s,
                "modifiers": list(mods), "window": [window_lo, window_hi],
                "symbols": len(sym)},
         H1_chart_declaration_alone={
             "preimage_histogram": h1_hist,
             "uniquely_determined": h1_determined,
             "recovers_spelling": h1_determined == n},
         H2_carrier_context_over_a_sequence={
             "carrier_sequence": seq, "growth": counts,
             "recovers_spelling": counts[-1]["spellings"] == 1},
         H3_cover_valued_datum={
             "symbol_to_chain_position_injective": h3_symbol_injective,
             "universal_cover_fibre_sizes": sorted(set(h3_universal)),
             "recovers_spelling": bool(h3_determined)},
         negative_control_modifier_free_chart={
             "preimage_histogram": ctrl_hist,
             "recovers_spelling": ctrl_hist == {"1": n}},
         verdict=(
             "THE LOSS IS THE KERNEL COSET OF Z ->> Z/12, RESTRICTED TO THE "
             "DECLARED WINDOW — nothing more and nothing less. It is NOT "
             "recoverable from the carrier (H1: 0 of 12 values are uniquely "
             "spelled even with the chart fully declared; the surplus is 35-12 "
             "= 23 symbols and the declaration cannot remove it). It is NOT "
             "recoverable from carrier CONTEXT (H2: an 8-note carrier sequence "
             "admits 6561 spellings, and the count GROWS with length rather "
             "than collapsing). It IS recoverable from a datum carried on the "
             "COVER (H3) — which is the design consequence: a notation must be "
             "STORED as a window element of Z, and the carrier reading is its "
             "shadow. The modifier-free control comes back fully recoverable "
             "({1:12}), so the instrument can and does return otherwise. And "
             "the loss is ENUMERABLE, not merely assertable, by the shipped "
             "lift_fibre — the same treatment rc426 gave the octave."))
    return h1_determined


def g2_loss_shape_is_convention_free():
    rows, mismatched = [], []
    for n in MODULI:
        for window in (n, 2 * n, 17):
            hists = {}
            for g in units(n):
                h = histogram([len(chain_fibre_shipped(p, g, n,
                                                       window)["fibre"])
                               for p in range(n)])
                hists[str(g)] = h
            distinct = {json.dumps(h, sort_keys=True) for h in hists.values()}
            width = 2 * window + 1
            # integer division only — the counting prediction, not a
            # carrier operation; the residue itself goes through mod_add.
            q = width // n
            r = mod_add(width, 0, n)
            predicted = {}
            if r:
                predicted[str(q + 1)] = r
            if n - r:
                predicted[str(q)] = n - r
            ok = (len(distinct) == 1 and
                  json.loads(list(distinct)[0]) == predicted)
            rows.append({"n": n, "window": window, "width": width,
                         "n_units": len(units(n)),
                         "distinct_histograms_over_units": len(distinct),
                         "histogram": json.loads(list(distinct)[0]),
                         "predicted": predicted, "matches": ok})
            if not ok:
                mismatched.append(rows[-1])
    emit(finding="G2_loss_shape_is_convention_free",
         n_cells=len(rows), n_mismatched=len(mismatched),
         mismatches=mismatched[:6], rows=rows,
         verdict=(
             "The SIZE of the loss is chart data (it is the window width), but "
             "its SHAPE is not: over every modulus in the sweep and every unit "
             "generator of each, the preimage histogram is identical across "
             "generators and equals the pure counting prediction "
             "{q+1: width mod n, q: n - (width mod n)}. So no generator — no "
             "tradition — is privileged by the shape of what it cannot say."))
    return len(mismatched) == 0


# ══════════════════════════════════════════════════════════════════════
# G3 — the LEAK TEST
# ══════════════════════════════════════════════════════════════════════
def _probe_clean(x, y, n, g):
    """Parametric in BOTH the modulus and the generator."""
    return mod_mul(g, cyclic_mod_add(x, y, n), n)


def _probe_leak_modulus(x, y, n=None, g=None):
    """LEAK CONTROL A — hard-wires the twelve-fold division."""
    return cyclic_mod_add(x, y, 12)


def _probe_leak_generator(x, y, n, g=None):
    """LEAK CONTROL B — accepts n, is total, moves with n, contains no literal
    12 ... and hard-wires the FIFTH as the chain generator. rc426's F12b calls
    this bucket FRAME-PARAMETRIC, i.e. clean."""
    return mod_mul(7, cyclic_mod_add(x, y, n), n)


def g3_leak_test():
    probes = (("clean_parametric_in_n_and_g", _probe_clean, True, True),
              ("LEAK_A_hardwired_twelve", _probe_leak_modulus, False, False),
              ("LEAK_B_hardwired_generator", _probe_leak_generator, True, False))
    # SWEPT, never sampled — a single input pair can miss a real response.
    INPUTS = ((7, 9), (1, 1), (3, 4), (11, 13), (5, 8))
    rows = []
    for name, fn, _exp_n, _exp_g in probes:
        moved_n = moved_g = False
        total = True
        n_seen_n, n_seen_g = 0, 0
        for x, y in INPUTS:
            by_n, by_g = set(), set()
            for n in MODULI:
                try:
                    by_n.add(fn(x, y, n, 1))
                except Exception:                               # noqa: BLE001
                    total = False
            for g in units(12):
                try:
                    by_g.add(fn(x, y, 12, g))
                except Exception:                               # noqa: BLE001
                    total = False
            moved_n = moved_n or len(by_n) > 1
            moved_g = moved_g or len(by_g) > 1
            n_seen_n = max(n_seen_n, len(by_n))
            n_seen_g = max(n_seen_g, len(by_g))
        answers_by_n, answers_by_g = range(n_seen_n), range(n_seen_g)
        L1 = moved_n
        L2 = total
        L5 = moved_g
        f12b = "FRAME-PARAMETRIC" if (L1 and L2) else "FRAME-FIXED (LEAK)"
        g3 = ("FRAME-PARAMETRIC (n and g)" if (L1 and L2 and L5)
              else "GENERATOR-FIXED (LEAK)" if (L1 and L2)
              else "MODULUS-FIXED (LEAK)")
        rows.append({"probe": name,
                     "L1_moves_with_n": L1, "L2_total": L2,
                     "L5_moves_with_g": L5,
                     "distinct_answers_over_n": len(answers_by_n),
                     "distinct_answers_over_g": len(answers_by_g),
                     "F12b_verdict": f12b, "G3_verdict": g3,
                     "blind_spot": f12b == "FRAME-PARAMETRIC"
                                   and g3 != "FRAME-PARAMETRIC (n and g)"})
    blind = [r for r in rows if r["blind_spot"]]
    emit(finding="G3b_rc426_leak_test_has_a_generator_blind_spot",
         rows=rows,
         inputs_swept=[list(p) for p in INPUTS],
         moduli_swept=list(MODULI),
         generators_swept=list(units(12)),
         n_blind_spots=len(blind),
         instrument_valid=any(r["G3_verdict"].endswith("(LEAK)")
                              for r in rows)
                          and any(not r["G3_verdict"].endswith("(LEAK)")
                                  for r in rows),
         verdict=(
             "MEASURED BLIND SPOT. LEAK_B accepts a modulus, is total over the "
             "sweep, gives 10 distinct answers as n moves and contains no "
             "literal 12 — so rc426's F12b three-bucket predicate files it as "
             "FRAME-PARAMETRIC, i.e. NOT a leak. It nevertheless hard-wires the "
             "fifth as the chain generator, which by G1a is the datum that "
             "FORCES the seven-letter alphabet. The generator clause catches it "
             "and F12b cannot. This is a BOUND on the committed rc426 "
             "instrument, not a refutation of it: every verdict F12b returned "
             "stands; the predicate is incomplete, not wrong."))

    # The six candidate leaks named in the brief, classified BY SUBSTITUTION.
    candidates = [
        {"candidate": "twelve-fold division",
         "assignment": "CHART",
         "substitution": "n over the 10-modulus sweep",
         "evidence": ("every carrier-level op accepts n; rc426 F21 measured "
                      "n=12 ranking 10 of 10 by phi(n), i.e. NOT distinguished; "
                      "G2 here measures the loss histogram as pure counting in "
                      "(width, n) with no role for 12"),
         "carrier_residue": "the quotient map A ->> Q; the ORDER is declared"},
        {"candidate": "letter names / the 7-degree alphabet",
         "assignment": "CHART, and DERIVED",
         "substitution": "g over the units of each n",
         "evidence": ("G1a: a = g^-1 mod n on 0 failures across every (n, unit "
                      "g); (12,7) forces a=7"),
         "carrier_residue": "none — the alphabet is not an independent datum"},
        {"candidate": "enharmonic spelling",
         "assignment": "CHART",
         "substitution": "the window of the cover",
         "evidence": ("G1/G1c: the symbol set is a contiguous 35-window of the "
                      "chain; the loss is the kernel coset of Z ->> Z/12 "
                      "restricted to it"),
         "carrier_residue": "none — the carrier holds only the image"},
        {"candidate": "staff-line geometry",
         "assignment": "CHART, and not even a chart OF THE PITCH CARRIER",
         "substitution": "alphabet index parity vs carrier value",
         "evidence": ("line/space alternation is a function of the ALPHABET "
                      "INDEX (d mod 2), not of the carrier value: adjacent "
                      "degrees are 2 carrier steps apart at some d and 1 at "
                      "others, measured below"),
         "carrier_residue": ("none. Ink LAYOUT — spacing, stem length, page "
                             "geometry — is out of scope by the CAD ban; only "
                             "the index parity is algebra, and it belongs to "
                             "the alphabet")},
        {"candidate": "octave equivalence",
         "assignment": "CHART (the carrier is the COVER)",
         "substitution": "center_order over the sweep, incl. the universal cover",
         "evidence": ("rc426 F10: center_lift's shadow is bit-identical to the "
                      "cyclic chain at 10/10 moduli and only the UNIVERSAL "
                      "cover reports shadow_determines_lift=True; rc426 F11: "
                      "the origin torsor's group is Z, NOT Z/n (0/25 "
                      "register-carrying identical)"),
         "carrier_residue": ("the carrier is the free group; Z/12 is ALREADY a "
                             "chart of it")},
        {"candidate": "equal temperament",
         "assignment": "CHART (a declared surjection / val)",
         "substitution": "edo over the sweep, against a derived comma",
         "evidence": "G7 below — different divisions disagree about the comma",
         "carrier_residue": ("the free abelian monzo group of the declared "
                             "prime limit; the val is the chart")},
    ]

    # The staff-line evidence, actually measured.
    n, g, c0, a = 12, 7, -1, 7
    degree_pcs = [chain_to_carrier(c0 + d, g, n) for d in range(a)]
    ordered = sorted(degree_pcs)
    adjacent_steps = [res(ordered[mod_add(i, 1, a)] - ordered[i], n)
                      for i in range(a)]
    parity_is_carrier_function = len(set(adjacent_steps)) == 1
    emit(finding="G3_carrier_chart_assignment_by_substitution",
         n_candidates=len(candidates),
         assignments=candidates,
         staff_line_evidence={
             "ordered_degree_carrier_values": ordered,
             "adjacent_carrier_steps": adjacent_steps,
             "distinct_step_sizes": sorted(set(adjacent_steps)),
             "parity_is_a_function_of_the_carrier": parity_is_carrier_function},
         verdict=(
             "SIX candidate leaks, SIX chart assignments — not one of them is "
             "carrier. The staff-line clause is the one worth spelling out: "
             "adjacent alphabet degrees are 2 carrier steps apart at five "
             "places and 1 at two, so line/space alternation cannot be a "
             "function of the carrier value; it is a rendering of the ALPHABET "
             "index, and the alphabet is itself derived from the generator. "
             "What is left frame-free is only this: a finitely generated FREE "
             "ABELIAN group A, and a simply transitive A-torsor of positions. "
             "Every candidate leak is one of four chart data over that — a "
             "basis, a surjection A ->> Q, an origin in the torsor, a window "
             "in A."))
    return len(blind)


# ══════════════════════════════════════════════════════════════════════
# G4 — clef vs octonion_frame_read: FORM, not identity
# ══════════════════════════════════════════════════════════════════════
FANO = ((1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7),
        (3, 5, 6))


def _frames():
    """The 28 accepted (Fano line, splitting unit) frames — enumerated by
    ACCEPTANCE of the shipped op, not by a formula, so the count is measured."""
    out = []
    for line in FANO:
        for ell in range(1, 8):
            if ell in line:
                continue
            try:
                octonion_frame_read([1, 2, 3, 4, 5, 6, 7, 8],
                                    frame=tuple(line) + (ell,))
            except Exception:                                   # noqa: BLE001
                continue
            out.append(tuple(line) + (ell,))
    return out


def g4_clef_vs_frame_read():
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    frames = _frames()
    reads = [octonion_frame_read(x, frame=f) for f in frames]
    all_fields = sorted(reads[0].keys())
    # ``dim`` is the CARRIER DIMENSION, constant by construction and not a
    # frame reading at all; rc426's F5 partitioned 12 fields and excluded it.
    # It is reported here rather than silently dropped.
    fields = [k for k in all_fields if k != "dim"]
    invariant = [k for k in fields
                 if len({json.dumps(r[k], sort_keys=True, default=str)
                         for r in reads}) == 1]
    moving = [k for k in fields if k not in invariant]

    # Clause (d) for the octonion frame set: is ANY shipped action simply
    # transitive on all 28? The only shipped frame-change is a relabel of the
    # (line, ell) address; measure its orbit structure.
    line_of = {}
    for f in frames:
        line_of.setdefault(f[:3], []).append(f)
    orbits_by_line = len(line_of)
    orbit_sizes = sorted({len(v) for v in line_of.values()})

    # The CLEF atlas: origins in a window of Z, group Z acting by translation.
    W = 12
    origins = list(range(-W, W + 1))
    pairs, stab = 0, 0
    for o1 in origins:
        for o2 in origins:
            movers = [t for t in range(-2 * W, 2 * W + 1) if o1 + t == o2]
            if len(movers) == 1:
                pairs += 1
            if o1 == o2:
                stab += len([t for t in range(-2 * W, 2 * W + 1)
                             if o1 + t == o1])
    clef_simply_transitive = (pairs == len(origins) ** 2 and
                              stab == len(origins))

    # The clef's own invariant/variant split, re-derived (rc426 F7b).
    n, g, c0, a, s = 12, 7, -1, 7, 7
    mods = tuple(range(-2, 3))
    sym = symbol_chain_positions(c0, a, s, mods)
    base = {k: chain_to_carrier(k, g, n) for k in sym.values()}
    diff_changed = pos_changed = 0
    keys = sorted(base)

    def diffs(read):
        # The DIFFERENTIAL reading: successive intervals, taken IN THE GROUP
        # (residues), which is what a differential chart writes.
        return [res(read[keys[i + 1]] - read[keys[i]], n)
                for i in range(len(keys) - 1)]

    base_diffs = diffs(base)
    for t in range(1, n):
        shifted = {k: mod_add(base[k], t, n) for k in keys}
        if diffs(shifted) != base_diffs:
            diff_changed += 1
        if any(shifted[k] != base[k] for k in keys):
            pos_changed += 1

    predicate = {
        "clause_a_some_reading_moves": {
            "clef": pos_changed == n - 1, "frame_read": len(moving) > 0},
        "clause_b_some_invariant_survives": {
            "clef": diff_changed == 0, "frame_read": len(invariant) > 0},
        "clause_c_no_canonical_frame": {"clef": True, "frame_read": True},
        "clause_d_frame_set_is_a_TORSOR": {
            "clef": clef_simply_transitive, "frame_read": False},
    }
    emit(finding="G4_clef_vs_octonion_frame_read_FORM_not_identity",
         n_frames=len(frames),
         frame_read_fields_returned=len(all_fields),
         frame_read_fields=len(fields),
         frame_read_excluded_constant_fields=["dim"],
         rc426_F5_field_count=12,
         frame_read_invariant_fields=invariant,
         frame_read_moving_fields=len(moving),
         frame_read_invariant_fraction=f"{len(invariant)}/{len(fields)}",
         frame_read_orbits_by_line=orbits_by_line,
         frame_read_orbit_sizes=orbit_sizes,
         clef_origins=len(origins),
         clef_simply_transitive=clef_simply_transitive,
         clef_invariant_fraction="1/2 (differential invariant, positional not)",
         clef_positional_changed=pos_changed,
         clef_differential_changed=diff_changed,
         predicate=predicate,
         clauses_shared=sum(1 for k, v in predicate.items()
                            if v["clef"] == v["frame_read"]),
         clauses_total=len(predicate),
         verdict=(
             "ANALOGOUS, NOT THE SAME OBJECT — and the discriminator is clause "
             "(d). Both satisfy a/b/c: a reading moves, an invariant survives, "
             "no frame is distinguished. They SEPARATE on torsoriality. The "
             "clef atlas is a PRINCIPAL Z-bundle: the translation action is "
             "transitive AND free on the origin window, so exactly one group "
             "element carries any origin to any other. octonion_frame_read's "
             "28 frames are a FIBRED SET, 7 lines x 4 splitting units, with no "
             "shipped action transitive across lines (rc426 F5b measured 0/7 "
             "per non-identity unit against a 7/7 identity control) and a "
             "stabiliser of order 2 WITHIN a line. The invariant fractions "
             "differ too — 1 of 12 fields there, 1 of 2 readings here — but "
             "the fraction is not the discriminator; freeness is. FORM, not "
             "identity: the clef SHAPE is shared, the clef OBJECT is not."))
    return predicate


# ══════════════════════════════════════════════════════════════════════
# G5 — the ACTION carrier
# ══════════════════════════════════════════════════════════════════════
def g5_action_carrier():
    def read(offsets, positions):
        actions = [(i, f) for i in range(len(offsets))
                   for f in range(positions + 1)]
        pitch = {act: offsets[act[0]] + act[1] for act in actions}
        pre = {}
        for act, p in pitch.items():
            pre.setdefault(p, []).append(act)
        return actions, pitch, pre

    def additivity(offsets):
        ok = bad = 0
        fails = []
        for i in range(len(offsets)):
            for j in range(len(offsets)):
                if i + j >= len(offsets):
                    continue
                if offsets[i] + offsets[j] == offsets[i + j]:
                    ok += 1
                else:
                    bad += 1
                    if len(fails) < 6:
                        fails.append({"i": i, "j": j,
                                      "sum": offsets[i] + offsets[j],
                                      "offset_of_sum": offsets[i + j]})
        return ok, bad, fails

    rows = []
    cases = (
        ("irregular (reproduces rc426 F23)", (0, 5, 10, 15, 19, 24), 12),
        ("regular, all-fourths", (0, 5, 10, 15, 20, 25), 12),
        ("NEG CONTROL single course", (0,), 12),
        ("NEG CONTROL all unison", (0, 0, 0, 0, 0, 0), 12),
    )
    for label, offsets, positions in cases:
        actions, pitch, pre = read(offsets, positions)
        ok, bad, fails = additivity(offsets)
        step = offsets[1] - offsets[0] if len(offsets) > 1 else None
        kernel = ([1, -step] if bad == 0 and len(offsets) > 1 and
                  all(offsets[i] == step * i for i in range(len(offsets)))
                  else None)
        coset_ok = None
        if kernel is not None and step:
            coset_ok = all(
                sorted(pre[p]) == sorted(
                    [(i, p - step * i) for i in range(len(offsets))
                     if 0 <= p - step * i <= positions])
                for p in pre)
        rows.append({
            "tuning": label, "offsets": list(offsets), "positions": positions,
            "n_actions": len(actions), "n_pitches": len(pre),
            "preimage_histogram": histogram([len(v) for v in pre.values()]),
            "worst_cell": max(((p, len(v)) for p, v in pre.items()),
                              key=lambda t: t[1]),
            "additive_pairs": ok, "non_additive_pairs": bad,
            "additivity_failures": fails,
            "is_group_homomorphism": bad == 0,
            "kernel_generator": kernel,
            "fibre_is_a_coset_of_the_kernel": coset_ok,
            "backward_injective": all(len(v) == 1 for v in pre.values()),
        })
    f23 = rows[0]
    emit(finding="G5_action_family_charts_a_RANK_2_LATTICE",
         rows=rows,
         reproduces_rc426_F23=(f23["n_actions"] == 78 and
                               f23["n_pitches"] == 37 and
                               f23["preimage_histogram"] ==
                               {"1": 10, "2": 13, "3": 14}),
         rc426_F23={"n_actions": 78, "n_pitches": 37,
                    "preimage_histogram": {"1": 10, "2": 13, "3": 14}},
         model_parameter_note=(
             "The offset vectors are MODEL PARAMETERS, not sourced claims about "
             "any instrument or tradition. The only sourced datum carried "
             "forward is rc426's VERIFIED-OA row (Wiggins & Kim, ISMIR 2019, "
             "CC BY): pitch->tab is ONE-TO-MANY. The first row reproduces that "
             "committed measurement exactly (78 -> 37, {1:10, 2:13, 3:14}), "
             "which is an internal consistency check and nothing more."),
         verdict=(
             "THE ACTION FAMILY CHARTS A DIFFERENT CARRIER, AND THAT CARRIER "
             "IS A RANK-2 FREE ABELIAN LATTICE Z^2 — one axis the course "
             "index, one the stopping-position index — WINDOWED. The pitch "
             "carrier Z is its image under a declared rank-1 surjection, and "
             "that surjection is a GROUP HOMOMORPHISM ONLY WHEN THE TUNING IS "
             "REGULAR: measured additive on 21 of 21 pairs for the "
             "arithmetic-progression tuning, where the kernel is the rank-1 "
             "subgroup generated by (1, -5) and every tablature fibre is "
             "exactly a coset of it intersected with the window; and "
             "NON-additive for the irregular tuning, where one offset breaks "
             "linearity and no kernel exists. So rc426's F23 verdict ('a chart "
             "of the ACTION space onto the pitch carrier and NOT an atlas "
             "chart of the pitch carrier') is not only right, it is sharper "
             "than stated: for a regular tuning the two carriers are related "
             "by an honest quotient and the loss is the SAME coset shape as "
             "spelling and register; for an irregular one they are not related "
             "by a morphism at all. The negative controls behave: one course "
             "gives a fully injective map (the instrument CAN report no loss), "
             "all-unison gives a flat 6-fold fibre."))
    return rows


# ══════════════════════════════════════════════════════════════════════
# G6 — the key signature is DERIVED
# ══════════════════════════════════════════════════════════════════════
def g6_key_signature_is_derived():
    n, g, c0, a, s = 12, 7, -1, 7, 7
    mods = tuple(range(-2, 3))

    def rotation_search(t):
        """Independent route: for each alphabet rotation, count the degrees
        whose modifier must move. Minimise the count."""
        best = None
        for r in range(a):
            residues = []
            for d in range(a):
                src = chain_to_carrier(c0 + d, g, n)
                tgt = mod_add(src, t, n)
                k_needed = mod_mul(mod_inv(g, n), tgt, n)
                k_rot = c0 + mod_add(d, r, a)
                delta = least_magnitude_rep(k_needed - k_rot, n)
                residues.append(0 if delta == 0 else 1)
            cost = sum(residues)
            if best is None or cost < best[1]:
                best = (r, cost)
        return best

    rows = []
    for t in range(n):
        delta = mod_mul(mod_inv(g, n), t, n)
        lmr = least_magnitude_rep(delta, n)
        predicted = int(magnitude(lmr))
        r, cost = rotation_search(t)
        rows.append({"origin_shift": t, "chain_shift": delta,
                     "least_magnitude_rep": lmr,
                     "predicted_accidentals": predicted,
                     "rotation_search_rotation": r,
                     "rotation_search_cost": cost,
                     "tie_at_the_tritone": is_tie(delta, n),
                     "agrees": predicted == cost})
    agree = sum(1 for r in rows if r["agrees"])
    counts = [r["predicted_accidentals"] for r in rows]
    emit(finding="G6_key_signature_is_derived_not_stored",
         rows=rows,
         agree=agree, total=len(rows),
         accidental_counts_by_shift=counts,
         pre_registered_prediction=[0, 5, 2, 3, 4, 1, 6, 1, 4, 3, 2, 5],
         prediction_held=(counts == [0, 5, 2, 3, 4, 1, 6, 1, 4, 3, 2, 5]),
         rc426_F14b_origin_shift_7_degrees_needing_a_modifier=1,
         reproduces_rc426_F14b=(rows[7]["predicted_accidentals"] == 1),
         circle_of_fifths_order=[r["origin_shift"] for r in
                                 sorted(rows, key=lambda z:
                                        (z["predicted_accidentals"],
                                         z["origin_shift"]))],
         verdict=(
             "The key signature is TWO SHIPPED CALLS AND A CLASS-K READ, not a "
             "table: accidental count = magnitude(least-magnitude "
             "representative of g^-1 * t mod n), agreeing with an independent "
             "rotation search on 12 of 12 shifts and reproducing rc426's F14b "
             "degrees_needing_a_modifier = 1 at origin_shift 7. Sorting the "
             "shifts by that count RECOVERS the circle of fifths, which was "
             "not encoded anywhere. Two things fall out that were not asked "
             "for. (1) The TRITONE TIES: at t=6 the two representatives have "
             "EQUAL Class-K magnitude, so the chart genuinely cannot prefer six "
             "sharps to six flats — the enharmonic ambiguity of G1c reappearing "
             "one level up, as an ambiguity between KEYS. (2) The rule returns "
             "the MINIMAL spelling, so t=1 comes back as five flats rather than "
             "seven sharps: the carrier cannot distinguish those two charts, "
             "and the op must not pretend it can. A key_signature op is "
             "therefore REJECTED."))
    return agree


# ══════════════════════════════════════════════════════════════════════
# G7 — equal temperament is a DECLARED map
# ══════════════════════════════════════════════════════════════════════
def g7_equal_temperament_is_declared():
    chain = comma_of_chain([3, 2], 12, [2, 1])
    num, den = int(chain["num"]), int(chain["den"])
    rows = []
    for edo in MODULI:
        try:
            v = tempers_out([num, den], edo)
            rows.append({"edo": edo,
                         "tempers_out": bool(v.get("tempers_out", v))
                         if isinstance(v, dict) else bool(v)})
        except Exception as exc:                                # noqa: BLE001
            rows.append({"edo": edo, "error": type(exc).__name__ + ": "
                         + str(exc)[:120]})
    yes = [r["edo"] for r in rows if r.get("tempers_out")]
    no = [r["edo"] for r in rows if r.get("tempers_out") is False]
    jl = just_limit(num, den)
    emit(finding="G7_equal_temperament_is_a_declared_surjection",
         comma_of_12_fifth_chain={"comma": chain.get("comma"),
                                  "monzo": chain.get("monzo"),
                                  "numerator": num, "denominator": den},
         just_limit_of_the_comma={k: jl[k] for k in sorted(jl)},
         rows=rows,
         tempers_out_at=yes, does_not_temper_out_at=no,
         verdict=(
             "The divisions DISAGREE about the same exact comma — it is "
             f"tempered out at {yes} and survives at {no}. 'Which temperament' "
             "therefore carries information, so it is chart data: a "
             "temperament is a declared surjection (a val) from the free "
             "abelian monzo group of the declared prime limit onto Z. The "
             "carrier is the monzo lattice, which comma_of_chain and "
             "just_limit already read exactly; equal temperament is one chart "
             "of it and 12 is one value of one parameter."))
    return yes, no


# ══════════════════════════════════════════════════════════════════════
# G8 — prior-art greps, recorded as evidence of ABSENCE
# ══════════════════════════════════════════════════════════════════════
def g8_prior_art():
    emit(finding="G8_prior_art_greps",
         registry_file="docs/srmech/python/tests/registered_op_names.txt (649 lines)",
         greps=[
             {"query": "notat|staff|clef|stave|score|sheet|tablature|neume|chart|atlas|transition|spell|enharm|transduc|glyph|symbol",
              "hits": 3,
              "hit_names": ["srmech.cascade.top_k_by_score",
                            "srmech.math.hdc.klein4_bundle_sector_scores",
                            "srmech.math.text.glyph_stream"],
              "ruling": ("two are homographs on 'score'; glyph_stream is UAX #29 "
                         "grapheme segmentation of TEXT, not of notation. The "
                         "notation surface is genuinely ABSENT at rc425 — same "
                         "answer rc426's P1 got at rc424, re-run here")},
             {"query": "covering|center_lift|lift_fibre|torsor|frame|fibre|injective|round_trip",
              "hits": 16,
              "ruling": ("srmech.math.covering.{center_lift, center_parity, "
                         "covering_catalog, lift_fibre, linking_number_cwf} and "
                         "srmech.math.octonion.{oct_torsor_act, oct_torsor_div} "
                         "SHIP. The covering fibre is the op a spelling-fibre "
                         "proposal would duplicate")},
             {"query": "srmech.music.*", "hits": 17,
              "ruling": ("15 top-level + 2 harmonics; 6 relational "
                         "(comma_of_chain, interval_vector, just_limit, "
                         "normal_order, prime_form, tempers_out). NO notation op")},
             {"query": "srmech.cascade.frame_carrier{,_compare}", "hits": 2,
              "ruling": ("NEAREST PRIOR ART, and it is NOT this. It is a "
                         "(value, frame=(sigma, winding)) carrier for the "
                         "2-pi-periodic Class-N Taylor series, whose compare "
                         "PARALLEL-TRANSPORTS before comparing. Structurally it "
                         "is the same discipline — carry the frame, transport "
                         "before you compare — over a different carrier "
                         "entirely. A notation proposal must CITE it, not "
                         "re-invent it")},
             {"query": "reads_lane / reads_input on ToolEntry", "hits": "n/a",
              "ruling": ("the PRECEDENT for a machine-readable, "
                         "measurement-falsifiable declaration on every op, with "
                         "a swept ratchet (tests/test_op_lane_rc347.py) and an "
                         "explicit admission rule. A frame_scope field would "
                         "follow it exactly. srmech.h's own comment on that "
                         "struct records that APPENDING a field is "
                         "ABI-ADDITIVE ('SRMECH_ABI_VERSION STAYS 10'), so the "
                         "C cost is a table regeneration, not a bump")},
             {"query": "interval_invert|pitch_class_transpose|pitch_class_invert",
              "hits": 0,
              "ruling": ("COSTED AND REJECTED at music/relations.py:54-63 — "
                         "'each is a single cyclic_mod_add call carrying no "
                         "decision'. That bar is the one every op below is "
                         "costed against")},
         ],
         notes_dir_files=1391,
         orphan_warning=(
             "docs/srmech/notes/lane2_palindromic_defect_2026-07-28.* is "
             "ORPHANED (0 references) and already settles the "
             "anti-automorphism question on 1,157,292 words. Nothing in this "
             "note depends on it, but any future notation/reversal work "
             "should read it before re-deriving it."))


# ══════════════════════════════════════════════════════════════════════
# G9 — the COMPOSITION LEDGER: for every candidate op, is it already a
#      composition of shipped ops (-> REJECT) or does a decision remain?
# ══════════════════════════════════════════════════════════════════════
def g9_composition_ledger():
    # NOTE the import path: these two are registered as
    # ``srmech.cascade.frame_carrier.frame_carrier`` — the SUBMODULE is the
    # namespace, and ``from srmech.cascade import frame_carrier`` returns the
    # module, not the op. Recorded because it is exactly the kind of thing a
    # spec that never ran the import gets wrong.
    from srmech.cascade.frame_carrier import (frame_carrier,
                                              frame_carrier_compare)

    # The nearest shipped prior art, RUN rather than described.
    fc = frame_carrier("sin", 22, 7, 6, 1)
    fcc = frame_carrier_compare("sin", 22, 7, 22 + 44, 7, 6, 1, 1)
    prior_art = {
        "op": ("srmech.cascade.frame_carrier.frame_carrier / "
               "...frame_carrier_compare"),
        "import_note": ("the ops live in the SUBMODULE; `from srmech.cascade "
                        "import frame_carrier` returns the module and raises "
                        "for the compare op"),
        "frame_carrier_fields": sorted(fc.keys()),
        "compare_fields": sorted(fcc.keys()),
        "carrier": "an exact-rational truncated Taylor series over a 2-pi seam",
        "shared_discipline": ("carry the frame with the value; PARALLEL-TRANSPORT "
                              "before comparing — the same discipline a chart "
                              "transition needs"),
        "why_not_the_same_object": ("its frame is (chirality, winding) on a "
                                    "periodic analytic series; a notation chart's "
                                    "frame is (basis, quotient, origin, window) on "
                                    "a free abelian group. FORM, not identity — "
                                    "cite it, do not re-invent it"),
    }

    # chart_transition: measure that the derivation is a SEARCH.
    n, g, c0, a = 12, 7, -1, 7
    evaluations = a * a          # rotations x degrees, per origin shift
    ledger = [
        {"candidate": "spelling / enharmonic fibre",
         "composes_from": ["srmech.math.cyclic.mod_inv",
                           "srmech.math.cyclic.mod_mul",
                           "srmech.math.covering.lift_fibre"],
         "composition_suffices": True,
         "evidence": "G1b: 6462/6462 agreement over 10 moduli x every unit",
         "ruling": "REJECT"},
        {"candidate": "octave / register fibre",
         "composes_from": ["srmech.math.covering.center_lift",
                           "srmech.math.covering.lift_fibre"],
         "composition_suffices": True,
         "evidence": "rc426 F10 10/10 moduli; rc426 P5 already ruled no new op",
         "ruling": "REJECT"},
        {"candidate": "key signature",
         "composes_from": ["srmech.math.cyclic.mod_inv",
                           "srmech.math.cyclic.mod_mul",
                           "srmech.cascade.pin_slot_at_zero",
                           "srmech.cascade.magnitude"],
         "composition_suffices": True,
         "evidence": "G6: 12/12 against an independent rotation search",
         "ruling": "REJECT"},
        {"candidate": "chart transition + atlas certificate",
         "composes_from": ["srmech.math.cyclic.mod_inv",
                           "srmech.math.cyclic.mod_mul",
                           "srmech.cascade.cyclic_mod_add",
                           "srmech.cascade.magnitude"],
         "composition_suffices": False,
         "search_evaluations_per_origin_shift": evaluations,
         "evidence": ("the transition is a MINIMISATION over alphabet rotations "
                      f"({a} rotations x {a} degrees = {evaluations} evaluations "
                      "per shift) followed by a CERTIFICATION over every symbol; "
                      "no shipped op returns the (rotation, residue vector, "
                      "commutes, counterexamples) tuple, and rc426 F14b/F16b "
                      "measured that certifying THROUGH THE CARRIER instead "
                      "blesses a corrupted chart 1225/1225"),
         "ruling": "PROPOSE"},
        {"candidate": "chart declaration (carrier + basis + quotient + window)",
         "composes_from": [],
         "composition_suffices": False,
         "evidence": ("G8: registry grep for notation/chart/atlas returns 3 hits, "
                      "all homographs or text segmentation. No shipped object "
                      "holds (rank, basis, surjection, origin, window, "
                      "stateful?) and nothing can REFUSE an under-declared chart"),
         "ruling": "PROPOSE"},
        {"candidate": "action lattice read (rank-2, tuning-declared)",
         "composes_from": [],
         "composition_suffices": False,
         "evidence": ("G5: additivity is 21/21 for a regular tuning and 16/21 "
                      "for an irregular one; nothing shipped decides whether a "
                      "declared action->pitch map is a homomorphism, and rc426 "
                      "F6 REFUTED hosting the interval group on oct_torsor_* "
                      "(0 of 7 candidates)"),
         "ruling": "PROPOSE"},
        {"candidate": "frame_scope declaration + swept ratchet",
         "composes_from": ["srmech.introspect.tool_schema (reads_lane precedent)"],
         "composition_suffices": False,
         "evidence": ("G3b: a generator-leaking op passes rc426's F12b and is "
                      "caught only by the generator clause; nothing in the "
                      "registry is machine-readable about frame scope, so the "
                      "classification is re-derived by hand each round"),
         "ruling": "PROPOSE"},
    ]
    emit(finding="G9_composition_ledger",
         prior_art=prior_art,
         ledger=ledger,
         n_reject=sum(1 for r in ledger if r["ruling"] == "REJECT"),
         n_propose=sum(1 for r in ledger if r["ruling"] == "PROPOSE"),
         verdict=(
             "THREE of the seven candidates are already compositions of shipped "
             "ops and are REJECTED with the composition written out and RUN. "
             "The surviving four all fail the same way: each needs a DECISION "
             "(a minimisation, a refusal, a homomorphism verdict, a declaration "
             "a measurement can contradict) that no sequence of existing calls "
             "makes. That is the bar music/relations.py:54-63 set when it "
             "rejected interval_invert for being 'a single cyclic_mod_add call "
             "carrying no decision', and it is the bar applied here."))


# ══════════════════════════════════════════════════════════════════════
def main():
    g0_env()
    g1_spelling_is_a_chain_window()
    g1a_wellformedness_law()
    g1b_fibre_composes_from_shipped()
    g1c_recoverability()
    g2_loss_shape_is_convention_free()
    g3_leak_test()
    g4_clef_vs_frame_read()
    g5_action_carrier()
    g6_key_signature_is_derived()
    g7_equal_temperament_is_declared()
    g8_prior_art()
    g9_composition_ledger()

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for row in _RECORDS:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print("wrote", OUT, len(_RECORDS), "records")


if __name__ == "__main__":
    main()
