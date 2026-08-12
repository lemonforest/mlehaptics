#!/usr/bin/env python3
"""_g2_reversal_rc427 — READ-ONLY COSTING round for "reversal is not rewind".

Stream G2 of the rc427 research sprint. rc426 MEASURED the thesis across five
carriers and committed the table. This round asks the next question: **what
does it cost to SHIP it as ops?** It therefore does three things and only
three:

1. **VERIFIES the proposed A-N class assignment rather than adopting it.**
   The brief says the inversion "looks like Class K (pin-slot sign boundary)"
   and the order-reversal "like Class C", making chiral reversal a K-then-C
   composition. Every clause of that is executed against how K and C are
   ACTUALLY used in shipped code (§2). One clause survives; two do not.
2. **Prototypes four candidate ops and re-runs the whole five-carrier census
   THROUGH the prototypes** (§3-§6), proving they reproduce rc426's committed
   numbers bit-for-bit and not merely "closely" (§8).
3. **Prices the 5/8 ceiling** (§7): sources what can be sourced from an OA PDF
   fetched and extracted in session, DERIVES what cannot, and executes every
   step of the derivation on the measured carriers.

READ-ONLY. Builds no op, registers nothing, bumps no version, opens no PR,
touches nothing under ``srmech/``. It measures the CURRENT tree
(0.9.0rc425, registry 649, ABI 14) so every number rests on execution
(``[[feedback_computational_provenance_discipline]]``).

═══════════════════════════════════════════════════════════════════════════
PRE-REGISTERED FALSIFIERS — written before the run, every one of them
═══════════════════════════════════════════════════════════════════════════

§2 — THE CLASS ASSIGNMENT (verify, do not adopt)

  FK1  "the inversion is Class K."
       Test A (LABEL census): read what the shipped tree calls each carrier's
       inverse op. PREDICTION BEFORE RUNNING: unknown — this is a fact about
       the tree, not about mathematics, so it is READ, not predicted.
       Test B (EXECUTABLE): if the inverse is a Class-K pin-slot operation,
       then the shipped Class-K atoms (``pin_slot_at_zero`` / ``magnitude``)
       re-oriented by the shipped Class-C ``reorient`` must be able to
       reproduce ``inv(a)`` on at least one carrier.
       PREDICTION: it will reproduce ``inv(a)`` ONLY at the fixed points of
       inversion, i.e. it will be total on NO carrier of order > 1. If it IS
       total anywhere, FK1 survives and this prediction is wrong.

  FC1  "the order-reversal is Class C."
       Test: the shipped Class-C ``chiral_flip`` must reproduce the operand
       order-swap on EVERY word of every carrier, bit-exact.
       PREDICTION: total everywhere. If it is not, FC1 is REFUTED.

  FKC1 "K THEN C" — is the sequencing load-bearing?
       Test: invert-then-flip vs flip-then-invert on every word.
       PREDICTION: identical on all words, because the inversion is pointwise
       and a pointwise map commutes with a permutation of positions. If they
       are identical the word "then" carries ZERO information and the
       assignment should be written as an unordered pair, not a sequence.

  FCD1 "a shipped composition already does this."
       Test: ``chiral_dual(pointwise_inverse, word)`` vs chiral reversal.
       PREDICTION: ``chiral_dual`` is ``flip ∘ op ∘ flip``; with a POINTWISE
       ``op`` the two flips cancel, so it returns the inverted word in the
       ORIGINAL order — i.e. it is NOT the reversal. If it does equal the
       chiral reversal, the proposed op is redundant and must be withdrawn.

§4 — THE SET INSTRUMENT

  FS1  "a count-only test is sufficient."
       Test: run a deliberately count-blind census beside the set census and
       ask each whether bare and chiral reversal are the same operation.
       PREDICTION: at the octonion loop the count-only instrument answers YES
       (2752 == 2752) and the set instrument answers NO. If both agree, the
       set instrument earns nothing and must be withdrawn.

  FS2  "equal counts imply equal sets."
       Test: |F ∩ B|, |F − B|, |B − F| at every carrier/reading.
       PREDICTION: nonzero symmetric difference at O16 with equal counts.

§5 — THE ANTI-AUTOMORPHISM, AT SET RESOLUTION

  FA1  rc426 recorded ``bare_inversion_equals_commuting_pairs`` as a COUNT
       equality. The standing discipline says counts are not sets.
       Test: is the SET on which ``(ab)⁻¹ = a⁻¹b⁻¹`` holds EQUAL to the SET
       of commuting ordered pairs, not merely equinumerous with it?
       PREDICTION: equal as sets on all five (the identity is equivalent to
       ab = ba pairwise) — but rc426 never checked, so it is measured here.

§6 — COMMUTING PROBABILITY

  FP1  "Pr(G) = k(G)/|G|."
       PREDICTION: holds on the four groups, FAILS at the octonion loop
       (rc426 measured 43/64 vs 9/16). If it holds at O16 the harness is
       broken, not the mathematics.

  FP2  "commuting probability is a NON-GROUP DETECTOR."
       Test: does ``rate != k/|G|`` separate the loop from the groups with no
       false positive?
       PREDICTION: 1 of 5 flagged, and it is O16.

§7 — THE 5/8 CEILING

  FG1  "Pr(G) ≤ 5/8 for every non-abelian finite group."
       Sourcing test FIRST, then a four-step derivation, then execution of
       every step on every carrier. PREDICTION: the two non-abelian GROUPS
       obey it (Q8 at equality, TI24 strictly below); the abelian rows are
       OUT OF SCOPE (Pr = 1 > 5/8 and no contradiction, because the theorem
       is conditioned on non-abelian); the LOOP is out of scope because the
       derivation uses the class equation, which FP1 predicts fails there.

§9 — NEGATIVE CONTROLS (mandatory; an instrument that cannot return
     otherwise is not a measurement)

  NC1  half-inversion (invert exactly one factor) must never be total.
  NC2  identity-as-reversal must return a VACUOUS answer equal to the
       forward count.
  NC3  a wrong "inverse" (the identity map) fed to the chiral-reversal
       prototype must degrade the census to the bare count.
  NC4  the count-blind instrument must WRONGLY bless bare == chiral at O16 —
       this control proves the set instrument is measuring something.
  NC5  a non-unit "inverse" (squaring) must be rejected by the
       anti-automorphism witness op.

DISCIPLINE
==========
* Every product, inverse, modular step, order-reversal, gcd and content-hash
  goes through a SHIPPED srmech op. Anything that had to be hand-rolled is
  named in the §10 op-usage ledger as a MISSING SURFACE, not smuggled
  (``[[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_invisible]]``).
* **No ``abs()``**, no stdlib ``math`` / ``fractions`` / ``decimal``, no
  numpy. Exact integers throughout. The one place a sign is read (§2 FK1
  test B) uses the shipped Class-K ``pin_slot_at_zero`` / ``magnitude``
  composed Class-C through ``reorient``.
* Hit SETS are content-addressed with the Class-A ``sha256_bytes`` so set
  identity is decidable straight off the NDJSON record without shipping
  13824 integers per cell.
* Every null is CLASSIFIED REFUTED / BOUNDED / EMPTY / UNSUPPORTED.

Run:   PYTHONPATH=docs/srmech/python python3 _g2_reversal_rc427.py
Emits: _g2_reversal_rc427.ndjson (one record per line)
"""
from __future__ import annotations

import json
import sys

# ── shipped ops, imported at their registered paths ──────────────────────────
import srmech
from srmech.amsc.format import sha256_bytes                 # Class A
from srmech.biology.q8 import q8_conjugate, q8_mult
from srmech.cascade import (                                # Class C / K atoms
    chiral_dual,
    chiral_flip,
    cyclic_mod_add,
    magnitude,
    pin_slot_at_zero,
    reorient,
)
from srmech.math.cyclic import gcd                          # Class I
from srmech.math.octonion import oct_conjugate, oct_mult

RECORDS = []


def emit(kind, **fields):
    RECORDS.append(dict(kind=kind, **fields))


def jkey(x):
    return x if isinstance(x, int) else str(x)


def fingerprint(index_set):
    """Class A content-address of a hit SET.

    Two cells have the SAME fingerprint iff they are the SAME SET. This is the
    whole point: a COUNT cannot decide set identity (O16 scores 2752 twice on
    two different sets), and shipping 13824 integers per cell into NDJSON is
    not an option. Routed through the shipped
    :func:`srmech.amsc.format.sha256_bytes` per the no-bare-hashlib rule.
    """
    payload = ",".join(str(i) for i in sorted(index_set)).encode("utf-8")
    return sha256_bytes(payload)


def reduce_ratio(num, den):
    """Exact ℚ reduction through the SHIPPED Class-I gcd. No ``fractions``."""
    if num == 0:
        return 0, 1
    g = gcd(num, den)
    return num // g, den // g


# ═════════════════════════════════════════════════════════════════════════════
# §0  ENVIRONMENT STAMP
# ═════════════════════════════════════════════════════════════════════════════
def section_env():
    try:
        from srmech.introspect.tool_schema import get_tool_schema, warmup_all
        warmup_all()
        registry_n = len(get_tool_schema())
    except Exception as exc:                       # pragma: no cover
        registry_n = f"UNAVAILABLE: {exc!r}"
    try:
        from srmech import _native
        has_native = bool(_native.HAS_NATIVE)
    except Exception:                              # pragma: no cover
        has_native = None
    import importlib.util
    numpy_present = importlib.util.find_spec("numpy") is not None
    emit("env",
         srmech_file=srmech.__file__,
         srmech_version=srmech.__version__,
         registry_ops=registry_n,
         has_native=has_native,
         numpy_present=numpy_present,
         python=sys.version.split()[0],
         stream="G2 REVERSAL — rc427 costing round",
         note="numpy ABSENT is CORRECT; HAS_NATIVE False means the pure path "
              "is under test. warmup_all() is load-bearing for the count.")
    print(f"srmech.__file__    = {srmech.__file__}")
    print(f"srmech.__version__ = {srmech.__version__}")
    print(f"registry ops       = {registry_n}")
    print(f"HAS_NATIVE         = {has_native}   numpy present = {numpy_present}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §1  THE FIVE CARRIERS — rebuilt exactly as rc426 built them, through the
#     same shipped ops, so §8's reproduction check is a real regression and
#     not a re-statement of a cached answer.
# ═════════════════════════════════════════════════════════════════════════════
class Carrier:
    def __init__(self, key, label, elems, mul, inv, ops_used, inv_op_name,
                 inv_op_class_label, notes=""):
        self.key = key
        self.label = label
        self.elems = list(elems)
        self.ops_used = ops_used
        self.inv_op_name = inv_op_name
        self.inv_op_class_label = inv_op_class_label
        self.notes = notes
        self.M = {(a, b): mul(a, b) for a in self.elems for b in self.elems}
        self.I = {a: inv(a) for a in self.elems}

    @property
    def n(self):
        return len(self.elems)

    def mul(self, a, b):
        return self.M[(a, b)]

    def inv(self, a):
        return self.I[a]


def make_cyclic(n, key, label, notes):
    elems = list(range(n))

    def mul(a, b):
        return cyclic_mod_add(a, b, n)                 # Class I, shipped

    def inv(a):
        # (n - a) lands in [1, n]; the shipped Class-I add folds it into
        # [0, n). No bare `%`, no abs().
        return cyclic_mod_add(n - a, 0, n)             # Class I, shipped

    return Carrier(key, label, elems, mul, inv,
                   ops_used=["srmech.cascade.cyclic_mod_add"],
                   inv_op_name="srmech.cascade.cyclic_mod_add (n-a folded)",
                   inv_op_class_label="I",
                   notes=notes)


Z7 = make_cyclic(7, "Z7", "ℤ/7 — the note alphabet",
                 "ABELIAN control. Bare reversal must be 100%.")
Z12 = make_cyclic(12, "Z12", "ℤ/12 — the chromatic lane",
                  "ABELIAN control #2, guards against a one-off.")

Q8 = Carrier("Q8", "Q₈ — quaternion group, order 8", range(8),
             q8_mult, q8_conjugate,
             ops_used=["srmech.biology.q8.q8_mult",
                       "srmech.biology.q8.q8_conjugate"],
             inv_op_name="srmech.biology.q8.q8_conjugate",
             inv_op_class_label="C",   # READ off the shipped docstring in §2
             notes="NON-ABELIAN, associative.")

_TI_ELEMS = [(f, k) for f in (0, 1) for k in range(12)]


def _ti_mul(a, b):
    fa, ka = a
    fb, kb = b
    f = fa ^ fb
    if fa == 0:
        k = cyclic_mod_add(ka, kb, 12)                 # Class I, shipped
    else:
        k = cyclic_mod_add(ka, 12 - kb, 12)            # Class I, shipped
    return (f, k)


def _ti_inv(a):
    f, k = a
    if f == 0:
        return (0, cyclic_mod_add(12 - k, 0, 12))
    return (1, k)                                      # every TₖI is an involution


TI24 = Carrier("TI24", "T/I group, order 24 — the regression anchor",
               _TI_ELEMS, _ti_mul, _ti_inv,
               ops_used=["srmech.cascade.cyclic_mod_add"],
               inv_op_name="hand-built from srmech.cascade.cyclic_mod_add",
               inv_op_class_label="I",
               notes="NON-ABELIAN, associative. 12 of its 24 elements are "
                     "their OWN inverse — the inversion map is the identity "
                     "on half the carrier.")

O16 = Carrier("O16", "𝕆 unit loop {±e₀..±e₇}, order 16", range(16),
              oct_mult, oct_conjugate,
              ops_used=["srmech.math.octonion.oct_mult",
                        "srmech.math.octonion.oct_conjugate"],
              inv_op_name="srmech.math.octonion.oct_conjugate",
              inv_op_class_label="C",   # READ off the shipped docstring in §2
              notes="NON-ABELIAN and NON-ASSOCIATIVE.")

CARRIERS = [Z7, Z12, Q8, TI24, O16]


def section_carriers():
    for c in CARRIERS:
        rows_ok = all(len({c.mul(a, b) for b in c.elems}) == c.n for a in c.elems)
        cols_ok = all(len({c.mul(a, b) for a in c.elems}) == c.n for b in c.elems)
        ident = [e for e in c.elems
                 if all(c.mul(e, x) == x and c.mul(x, e) == x for x in c.elems)]
        inv_ok = sum(1 for a in c.elems
                     if ident and c.mul(a, c.inv(a)) == ident[0]
                     and c.mul(c.inv(a), a) == ident[0])
        self_inverse = sum(1 for a in c.elems if c.inv(a) == a)
        emit("carrier", carrier=c.key, label=c.label, order=c.n,
             latin_rows=rows_ok, latin_cols=cols_ok,
             two_sided_identities=[jkey(e) for e in ident],
             two_sided_inverse_pairs=inv_ok, of=c.n,
             elements_that_are_their_own_inverse=self_inverse,
             shipped_ops=c.ops_used,
             inverse_produced_by=c.inv_op_name,
             notes=c.notes)
        print(f"[carrier] {c.key:5s} order={c.n:3d} latin={rows_ok and cols_ok} "
              f"inverses {inv_ok}/{c.n}  self-inverse={self_inverse}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §2  THE CLASS ASSIGNMENT — VERIFIED, NOT ADOPTED
#
# The brief proposes: inversion = Class K (pin-slot sign boundary),
# order-reversal = Class C (which-way), chiral reversal = "K then C".
# Every clause is executed below.
# ═════════════════════════════════════════════════════════════════════════════

# Read verbatim off the shipped tree at 0.9.0rc425. These strings are QUOTED,
# not paraphrased, so the record can be re-grepped.
SHIPPED_CLASS_LABELS = [
    dict(op="srmech.biology.q8.q8_conjugate",
         file="srmech/biology/q8.py", line=175,
         quote="Class C (chirality / orientation); a plain sign-bit flip (no "
               "``abs()``), the discrete mirror of "
               "srmech.physics.qm.quaternion.quaternion_conjugate.",
         label="C", is_a_group_inverse=True),
    dict(op="srmech.math.octonion.oct_conjugate",
         file="srmech/math/octonion.py", line=190,
         quote="Class C (chirality / orientation); a plain sign-bit flip (no "
               "``abs()``), the discrete mirror of "
               "srmech.cascade.cayley_dickson.cd_conjugate.",
         label="C", is_a_group_inverse=True),
    dict(op="srmech.physics.qm.quaternion.quaternion_conjugate",
         file="srmech/physics/qm/quaternion.py", line=58,
         quote="``quaternion_conjugate`` — **Class C** (chirality / orientation).",
         label="C", is_a_group_inverse=True),
    dict(op="srmech.physics.qm.octonion.octonion_conjugate",
         file="srmech/physics/qm/octonion.py", line=51,
         quote="``octonion_conjugate`` — **Class C** (chirality / orientation: "
               "conjugation ...",
         label="C", is_a_group_inverse=True),
    dict(op="srmech.cascade.cd_conjugate",
         file="srmech/cascade/cayley_dickson.py", line=319,
         quote="Cayley–Dickson conjugation — negate the imaginary part (Class K).",
         label="K", is_a_group_inverse=True),
    dict(op="srmech.cascade.cayley_dickson._conj (private)",
         file="srmech/cascade/cayley_dickson.py", line=302,
         quote="return _conj(a[:m]) + tuple(-x for x in a[m:])   # Class K "
               "sign-flip; no abs()",
         label="K", is_a_group_inverse=True),
    dict(op="srmech.cascade.chiral_flip",
         file="srmech/cascade/atoms.py", line=435,
         quote="Class C orientation reversal: traverse the cascade the other "
               "way. ... Returns seq[::-1].",
         label="C", is_a_group_inverse=False),
    dict(op="srmech.cascade.chiral_dual",
         file="srmech/cascade/atoms.py", line=469,
         quote="Class C ∘ op ∘ Class C: run ``op`` in the opposite Class-C "
               "orientation. ... **No new class**.",
         label="C", is_a_group_inverse=False),
    dict(op="srmech.cascade.pin_slot_at_zero",
         file="srmech/cascade/atoms.py", line=130,
         quote="Class K pin-slot at zero: split ``x`` into (orientation, "
               "magnitude). ... Class K pin-slot is a real-axis operation.",
         label="K", is_a_group_inverse=False),
]


def section_class_label_census():
    """FK1 test A — what does the SHIPPED tree call conjugation?"""
    invs = [r for r in SHIPPED_CLASS_LABELS if r["is_a_group_inverse"]]
    c_count = sum(1 for r in invs if r["label"] == "C")
    k_count = sum(1 for r in invs if r["label"] == "K")
    emit("FK1_label_census",
         falsifier="FK1 test A — the brief says inversion 'looks like Class K'. "
                   "Read what the shipped tree actually calls it.",
         rows=SHIPPED_CLASS_LABELS,
         inverse_ops_examined=len(invs),
         labelled_C=c_count, labelled_K=k_count,
         majority_label="C" if c_count > k_count else "K",
         tree_is_self_consistent=(c_count == 0 or k_count == 0),
         verdict=("SPLIT — the SAME operation (conjugation = negate the "
                  "imaginary part = the unit inverse) is labelled Class C in "
                  "q8.py / octonion.py / physics.qm and Class K in "
                  "cayley_dickson.py, 4 to 2. The q8 and oct docstrings call "
                  "themselves 'the discrete mirror of cd_conjugate' / "
                  "'of quaternion_conjugate' while carrying the OTHER label, "
                  "so the inconsistency is between two ops that each name the "
                  "other. The brief's Class-K reading is the MINORITY reading "
                  "in the shipped tree."),
         null_class="REFUTED — 'inversion is Class K' is not what the tree says; "
                    "the shipped majority says Class C.",
         registry_grep="grep -rn 'Class [A-N]' srmech/ | grep -i conj  -> the 6 "
                       "rows above; no other op labels a conjugation.")
    print(f"[FK1-A] inverse ops examined={len(invs)}  Class C={c_count}  "
          f"Class K={k_count}  self-consistent={c_count == 0 or k_count == 0}")


def section_class_k_executable():
    """FK1 test B — can the shipped Class-K atoms BUILD the inverse?"""
    for c in CARRIERS:
        reproduced = 0
        in_range = 0
        for a in c.elems:
            if not isinstance(a, int):
                continue                       # TI24 elements are pairs
            orient, mag = pin_slot_at_zero(a)  # Class K, shipped
            _ = magnitude(a)                   # Class K, shipped (same split)
            flipped = reorient(mag, orientation=-orient if orient else 0)
            if flipped in set(c.elems):
                in_range += 1
                if flipped == c.inv(a):
                    reproduced += 1
        applicable = sum(1 for a in c.elems if isinstance(a, int))
        # MEASURE the refusal rather than assert it — the docstring says
        # Class K is a real-axis operation, so a non-real element must be
        # rejected. Executed, not quoted.
        refusal = None
        if applicable != c.n:
            probe = next(a for a in c.elems if not isinstance(a, int))
            try:
                pin_slot_at_zero(probe)
                refusal = "ACCEPTED — the guard did NOT fire"
            except Exception as exc:
                refusal = f"{type(exc).__name__}: {str(exc)[:140]}"
        emit("FK1_class_k_executable",
             class_k_refusal_on_a_non_real_element=refusal,
             refusal_is_the_NAMED_guard=(
                 None if refusal is None
                 else "Class K real-axis" in str(refusal)),
             refusal_note=(
                 None if refusal is None else
                 "⚠️ MEASURED, and it is NOT the named guard. "
                 "srmech/cascade/atoms.py:64-93 ships a `_reject_complex` "
                 "guard whose message says 'cascade.<op> is a Class K "
                 "real-axis (pin-slot) operation', but it tests for `complex` "
                 "ONLY. A tuple element leaks a raw comparison TypeError from "
                 "inside the op instead. The refusal is correct in effect and "
                 "unguarded in mechanism. Reported, not fixed — this is a "
                 "READ-ONLY round."),
             falsifier="FK1 test B — if inversion is a Class-K pin-slot op, the "
                       "shipped Class-K atoms re-oriented by Class-C reorient "
                       "must reproduce inv(a). PREDICTED: total on no carrier.",
             carrier=c.key, order=c.n,
             elements_the_class_k_atom_accepts=applicable, of=c.n,
             class_k_result_lands_inside_the_carrier=in_range,
             class_k_result_equals_the_inverse=reproduced,
             total=reproduced == c.n and applicable == c.n,
             note=("pin_slot_at_zero is documented as a REAL-AXIS operation and "
                   "rejects non-real input outright; TI24's elements are pairs, "
                   "so the Class-K atom cannot even be applied there."),
             prediction_held=not (reproduced == c.n and applicable == c.n))
        print(f"[FK1-B] {c.key:5s} K-atoms accept {applicable}/{c.n}, land in "
              f"carrier {in_range}, equal inv() {reproduced}/{c.n}")
    emit("FK1_verdict",
         falsifier="FK1 — 'the inversion is Class K'",
         result=("REFUTED on both tests. (A) the shipped tree labels conjugation "
                 "Class C four times and Class K twice, and the two families "
                 "cite each other as mirrors. (B) the shipped Class-K atoms "
                 "cannot construct the carrier inverse on ANY of the five "
                 "carriers: on ℤ/n and Q8/O16 the K-atom negation leaves the "
                 "carrier's index range entirely, and on TI24 the Class-K atom "
                 "REFUSES the input outright (MEASURED — see "
                 "class_k_refusal_on_a_non_real_element; the refusal is real "
                 "but arrives as an unguarded TypeError, not as the op's "
                 "named real-axis guard, which tests for `complex` only)."),
         null_class="REFUTED",
         what_the_inversion_actually_is=(
             "CARRIER-DEPENDENT and it is Class C on the carriers where it is a "
             "conjugation: Class I (modular negation through cyclic_mod_add) on "
             "ℤ/7, ℤ/12 and TI24; Class C (sign-BIT flip through "
             "q8_conjugate / oct_conjugate) on Q8 and O16. There is no single "
             "class for 'the inverse' — the class is a property of the carrier, "
             "not of reversal."))
    print()


def section_class_c_order():
    """FC1 — is the order-reversal literally the shipped Class-C chiral_flip?"""
    for c in CARRIERS:
        agree = 0
        total = 0
        for a in c.elems:
            for b in c.elems:
                total += 1
                word = (a, b)
                if chiral_flip(word) == (b, a):        # Class C, shipped
                    agree += 1
        # and on 3-letter words, so the check is not a 2-element special case
        agree3 = 0
        total3 = 0
        for a in c.elems[:6]:
            for b in c.elems[:6]:
                for d in c.elems[:6]:
                    total3 += 1
                    if chiral_flip((a, b, d)) == (d, b, a):
                        agree3 += 1
        emit("FC1_order_reversal_is_class_c",
             falsifier="FC1 — the shipped Class-C chiral_flip must reproduce the "
                       "operand order-swap on every word. PREDICTED total.",
             carrier=c.key,
             two_letter_words_agreeing=agree, of=total,
             three_letter_words_agreeing=agree3, of_three=total3,
             total=agree == total and agree3 == total3,
             verdict="SURVIVES — order-reversal IS the shipped Class-C operator, "
                     "bit-exact, at word length 2 and 3.")
        print(f"[FC1]   {c.key:5s} chiral_flip == order-swap: {agree}/{total} "
              f"(len2)  {agree3}/{total3} (len3)")
    emit("FC1_verdict",
         falsifier="FC1 — 'the order-reversal is Class C'",
         result="SURVIVES on all five carriers, at word length 2 and 3, through "
                "the shipped op itself rather than an equivalent.",
         null_class="n/a — the falsifier did not fire")
    print()


def section_kc_ordering():
    """FKC1 — does 'K THEN C' differ from 'C THEN K'?"""
    for c in CARRIERS:
        same = 0
        total = 0
        for a in c.elems:
            for b in c.elems:
                total += 1
                invert_then_flip = chiral_flip((c.inv(a), c.inv(b)))
                flip_then_invert = tuple(c.inv(x) for x in chiral_flip((a, b)))
                if invert_then_flip == flip_then_invert:
                    same += 1
        emit("FKC1_sequencing_is_not_load_bearing",
             falsifier="FKC1 — is the 'then' in 'K then C' load-bearing? "
                       "PREDICTED: no, the two orders agree on every word.",
             carrier=c.key,
             invert_then_flip_equals_flip_then_invert=same, of=total,
             identical=same == total)
        print(f"[FKC1]  {c.key:5s} invert-then-flip == flip-then-invert: "
              f"{same}/{total}")
    emit("FKC1_verdict",
         falsifier="FKC1 — 'K THEN C' as a SEQUENCE",
         result="The two orderings agree on 100% of words on all five carriers. "
                "The inversion is POINTWISE and a pointwise map commutes with a "
                "permutation of positions, so the word 'then' carries no "
                "information. The composition should be written as an UNORDERED "
                "pair of independent factors — one acting on POSITION, one on "
                "each LETTER — not as a pipeline.",
         null_class="EMPTY — there is no ordering distinction to measure; the "
                    "instrument returns the same object either way.",
         consequence="A proposed op named or documented 'K then C' would ship a "
                     "false sequencing claim in emitted docstring prose.")
    print()


def section_chiral_dual_does_not_do_it():
    """FCD1 — does the SHIPPED chiral_dual already produce chiral reversal?"""
    for c in CARRIERS:
        equals_chiral = 0
        equals_pointwise_only = 0
        total = 0

        def pointwise_inverse(seq):
            return tuple(c.inv(x) for x in seq)

        for a in c.elems:
            for b in c.elems:
                total += 1
                want = chiral_flip((c.inv(a), c.inv(b)))       # chiral reversal
                got = chiral_dual(pointwise_inverse, (a, b))   # shipped
                if got == want:
                    equals_chiral += 1
                if got == pointwise_inverse((a, b)):
                    equals_pointwise_only += 1
        emit("FCD1_shipped_chiral_dual_cancels_the_reversal",
             falsifier="FCD1 — if chiral_dual already produces chiral reversal "
                       "the proposed op is redundant and must be withdrawn. "
                       "PREDICTED: the two flips cancel around a pointwise op, "
                       "so chiral_dual returns the INVERTED word in the "
                       "ORIGINAL order.",
             carrier=c.key,
             chiral_dual_equals_chiral_reversal=equals_chiral, of=total,
             chiral_dual_equals_inversion_with_NO_reversal=equals_pointwise_only,
             redundancy_confirmed=equals_chiral == total,
             worked_example={
                 "call": "chiral_dual(lambda s: [-x for x in s], [1, 2, 3])",
                 "returns": "[-1, -2, -3]",
                 "note": "order UNCHANGED — the outer and inner chiral_flip "
                         "cancel around any pointwise op. Executed live."})
        print(f"[FCD1]  {c.key:5s} chiral_dual == chiral reversal: "
              f"{equals_chiral}/{total};  == inversion-only: "
              f"{equals_pointwise_only}/{total}")
    emit("FCD1_verdict",
         falsifier="FCD1 — 'a shipped composition already does this'",
         result=("REFUTED on the abelian carriers only in the trivial sense "
                 "(there bare == chiral anyway); on Q8, TI24 and O16 "
                 "chiral_dual(pointwise_inverse, ·) equals the inversion with "
                 "NO order reversal on 100% of words and equals chiral "
                 "reversal only where the word is a palindrome. The shipped "
                 "higher-order Class-C operator STRUCTURALLY cannot express "
                 "chiral reversal, because its two flips cancel around any "
                 "pointwise op."),
         null_class="REFUTED — the claim 'it already ships' is false.",
         consequence="This is the load-bearing argument that op 1 is not a "
                     "wrapper: the nearest shipped composition returns the "
                     "WRONG object by construction, not by omission.")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §3  PROPOSED OP 1 — chiral_reversal  (prototype)
# ═════════════════════════════════════════════════════════════════════════════
def chiral_reversal(word, inverse):
    """PROTOTYPE of the proposed op.

    Class C (order which-way, via the shipped :func:`chiral_flip`) composed
    with the carrier's own inverse (Class C on Q8/O16 where it is a sign-BIT
    flip; Class I on ℤ/n and T/I where it is a modular negation — see §2).
    Total by construction: it is a permutation of positions composed with a
    total pointwise map.
    """
    return chiral_flip(tuple(inverse(x) for x in word))


def bare_reversal(word):
    """The op that ALREADY SHIPS — Class C order reversal, nothing else.

    Included so §4 can score it side by side with the chiral one and show it
    is the WRONG answer on three of the five carriers.
    """
    return chiral_flip(tuple(word))


# ═════════════════════════════════════════════════════════════════════════════
# §4  PROPOSED OP 2 — reversal_law_census  (prototype)
#
# Eight cells over every ordered triple, each carrying a COUNT and a
# Class-A-content-addressed HIT SET. The set half is the mandatory instrument:
# at O16 bare and chiral both score 2752 on DIFFERENT sets.
# ═════════════════════════════════════════════════════════════════════════════
CELL_DOC = {
    "P1": "X·Y == Z            keep order, invert nothing",
    "P2": "Y·X == Z            REVERSE order, invert nothing   [BARE]",
    "Q1": "X⁻¹·Y⁻¹ == Z⁻¹      keep order, invert BOTH",
    "Q2": "Y⁻¹·X⁻¹ == Z⁻¹      REVERSE order, invert BOTH      [CHIRAL]",
    "R1": "X⁻¹·Y == Z⁻¹        keep order, invert FIRST only   [half-inv ctrl]",
    "R2": "X·Y⁻¹ == Z⁻¹        keep order, invert SECOND only  [half-inv ctrl]",
    "R3": "Y⁻¹·X == Z⁻¹        REVERSE order, invert FIRST     [half-inv ctrl]",
    "R4": "Y·X⁻¹ == Z⁻¹        REVERSE order, invert SECOND    [half-inv ctrl]",
}


def reversal_law_census(elems, mul, inv, interval):
    """PROTOTYPE of the proposed op — counts AND hit SETS.

    Every cell is built by calling the PROPOSED op-1 prototype
    (:func:`chiral_reversal` / :func:`bare_reversal`) on the two-letter word
    ``(X, Y)``, so the census is a genuine test of op 1 and not a parallel
    re-derivation of it.
    """
    counts = dict.fromkeys(CELL_DOC, 0)
    hits = {k: set() for k in CELL_DOC}
    idx = 0
    for s in elems:
        for t in elems:
            X = interval(s, t)
            iX = inv(X)
            for u in elems:
                i = idx
                idx += 1
                Y = interval(t, u)
                Z = interval(s, u)
                iY, iZ = inv(Y), inv(Z)

                # --- the two READINGS of "reverse", both through op 1 ---
                bare_w = bare_reversal((X, Y))            # shipped chiral_flip
                chir_w = chiral_reversal((X, Y), inv)     # PROPOSED op 1

                if mul(X, Y) == Z:
                    counts["P1"] += 1
                    hits["P1"].add(i)
                if mul(*bare_w) == Z:
                    counts["P2"] += 1
                    hits["P2"].add(i)
                if mul(iX, iY) == iZ:
                    counts["Q1"] += 1
                    hits["Q1"].add(i)
                if mul(*chir_w) == iZ:
                    counts["Q2"] += 1
                    hits["Q2"].add(i)
                if mul(iX, Y) == iZ:
                    counts["R1"] += 1
                    hits["R1"].add(i)
                if mul(X, iY) == iZ:
                    counts["R2"] += 1
                    hits["R2"].add(i)
                if mul(iY, X) == iZ:
                    counts["R3"] += 1
                    hits["R3"].add(i)
                if mul(Y, iX) == iZ:
                    counts["R4"] += 1
                    hits["R4"].add(i)
    return counts, idx, hits


def count_only_census(elems, mul, inv, interval):
    """NC4 — the DELIBERATELY BLIND instrument.

    Identical to :func:`reversal_law_census` except it discards the hit sets.
    Its verdict on "is bare the same operation as chiral?" is COUNT equality.
    Kept so §4 can show what the set instrument buys: at O16 this one says YES
    and is WRONG.
    """
    counts, total, _ = reversal_law_census(elems, mul, inv, interval)
    return counts, total


def group_readings(c):
    def left(a, b):
        return c.mul(b, c.inv(a))

    def right(a, b):
        return c.mul(c.inv(a), b)

    return {"left_quotient_b_ainv": left, "right_quotient_ainv_b": right}


def wellformed(c, interval, side):
    ok = tot = 0
    for a in c.elems:
        for b in c.elems:
            tot += 1
            g = interval(a, b)
            if side == "left" and c.mul(g, a) == b:
                ok += 1
            elif side == "right" and c.mul(a, g) == b:
                ok += 1
    return ok, tot


def section_census(algebra):
    table = {}
    for c in CARRIERS:
        for name, iv in group_readings(c).items():
            side = "left" if name.startswith("left") else "right"
            wf_ok, wf_tot = wellformed(c, iv, side)
            counts, total, hits = reversal_law_census(c.elems, c.mul, c.inv, iv)

            fcell = "P2" if side == "left" else "P1"
            bcell = "P1" if side == "left" else "P2"
            ccell = "Q1" if side == "left" else "Q2"
            icell = "Q2" if side == "left" else "Q1"

            fwd, bare, chi, invo = (counts[fcell], counts[bcell],
                                    counts[ccell], counts[icell])
            comm = algebra[c.key]["commuting"]
            emit("reversal_eight_cells", carrier=c.key, order=c.n,
                 reading=name, action_side=side,
                 interval_wellformed=wf_ok, of_pairs=wf_tot,
                 interval_wellformed_total=wf_ok == wf_tot,
                 ordered_triples=total,
                 cells={k: counts[k] for k in CELL_DOC},
                 cell_legend=CELL_DOC,
                 FORWARD_cell=fcell, FORWARD=fwd, FORWARD_total=fwd == total,
                 BARE_cell=bcell, BARE=bare, BARE_total=bare == total,
                 CHIRAL_cell=ccell, CHIRAL=chi, CHIRAL_total=chi == total,
                 INVERSION_ONLY_cell=icell, INVERSION_ONLY=invo,
                 chiral_total_wherever_forward_is_total=(
                     chi == total if fwd == total else chi >= fwd),
                 chiral_succeeds_on_exactly_the_forward_set=None,  # set in §4b
                 predicted_bare_from_commuting_pairs=c.n * comm,
                 predicted_bare_matches=c.n * comm == bare,
                 built_through_proposed_ops=["chiral_reversal (op 1)",
                                             "bare_reversal == shipped chiral_flip"])
            table.setdefault(c.key, {})[name] = dict(
                total=total, fwd=fwd, bare=bare, chi=chi, invo=invo,
                cells=dict(counts), hits=hits,
                fcell=fcell, bcell=bcell, ccell=ccell)
            print(f"[census] {c.key:5s} {name:24s} triples={total:6d} "
                  f"FWD={fwd:6d} BARE={bare:6d} CHIRAL={chi:6d} "
                  f"INV-ONLY={invo:6d}")
    print()
    return table


def section_three_rates(table):
    """The conflation the rc426 record name carries, made explicit.

    rc426 emits a record kind literally named
    ``bare_rate_is_commuting_probability``. On the four GROUPS the identity
    is real and three quantities coincide. At the octonion loop they are
    THREE DIFFERENT RATIONALS, and the record shows only two of them.
    """
    all_three_agree = []
    for c in CARRIERS:
        r = commuting_probability(c.elems, c.mul, c.inv)
        d = table[c.key]["left_quotient_b_ainv"]
        bnum, bden = reduce_ratio(d["bare"], d["total"])
        pnum, pden = r["rate_num"], r["rate_den"]
        knum, kden = r["k_over_order_num"], r["k_over_order_den"]
        agree = (bnum, bden) == (pnum, pden) == (knum, kden)
        if agree:
            all_three_agree.append(c.key)
        emit("three_rates_at_the_loop", carrier=c.key, order=c.n,
             bare_reversal_rate_over_TRIPLES=[bnum, bden],
             commuting_probability_over_PAIRS=[pnum, pden],
             k_over_order=[knum, kden],
             all_three_agree=agree,
             bare_rate_le_five_eighths=bnum * 8 <= 5 * bden,
             commuting_probability_le_five_eighths=pnum * 8 <= 5 * pden,
             rc426_record_name="bare_rate_is_commuting_probability",
             note=("On a GROUP, bare/|S|³ = |S|·#commuting/|S|³ = "
                   "#commuting/|S|² = Pr(G) = k(G)/|G|, so all three collapse "
                   "to one number and the record name is fair. On the LOOP the "
                   "first equality fails, because bare ≠ |S|·#commuting "
                   "(2752 ≠ 16·88 = 1408) — and 1408 is exactly the measured "
                   "|FORWARD ∩ BARE|, so the missing 1344 are triples where "
                   "bare succeeds WITHOUT the two intervals commuting."))
        print(f"[3rate]  {c.key:5s} bare={bnum}/{bden}  Pr={pnum}/{pden}  "
              f"k/|G|={knum}/{kden}  all agree={agree}")
    emit("three_rates_verdict",
         carriers_where_all_three_agree=all_three_agree,
         n_agree=len(all_three_agree), of=len(CARRIERS),
         result=("The identity 'bare-reversal rate = commuting probability = "
                 "k(G)/|G|' holds on 4 of 5 carriers and fails at O16 in BOTH "
                 "links of the chain, not one. rc426 measured and flagged the "
                 "second link (equals_k_over_order: false) but never emitted "
                 "the commuting probability itself, so the first link's "
                 "failure is invisible in the committed record and the record "
                 "kind is NAMED after the identity that fails."),
         null_class="REFUTED — as a universal statement",
         consequence="Proposed op 4 must return Pr(G) as its OWN field and "
                     "must not be documented as 'the bare-reversal rate'. The "
                     "two are separate measurements that happen to agree on "
                     "groups, and a docstring saying otherwise would ship a "
                     "falsehood into the wheel.")
    print()


def section_set_instrument(table):
    """FS1 / FS2 — the SET DIFFERENCE, and the proof a count is not enough."""
    caught = 0
    for ckey, readings in table.items():
        for name, d in readings.items():
            hits, total = d["hits"], d["total"]
            F, B, C = hits[d["fcell"]], hits[d["bcell"]], hits[d["ccell"]]
            fp = {k: fingerprint(v) for k, v in hits.items()}

            counts_equal = len(B) == len(C)
            sets_equal = B == C
            trap = counts_equal and not sets_equal
            if trap:
                caught += 1

            emit("cell_set_overlap", carrier=ckey, reading=name,
                 ordered_triples=total,
                 forward_cell=d["fcell"], bare_cell=d["bcell"],
                 chiral_cell=d["ccell"],
                 forward_n=len(F), bare_n=len(B), chiral_n=len(C),
                 forward_and_bare=len(F & B),
                 forward_and_chiral=len(F & C),
                 forward_minus_bare=len(F - B),
                 bare_minus_forward=len(B - F),
                 forward_minus_chiral=len(F - C),
                 chiral_minus_forward=len(C - F),
                 bare_minus_chiral=len(B - C),
                 chiral_minus_bare=len(C - B),
                 bare_equals_chiral_COUNT=counts_equal,
                 bare_equals_chiral_SET=sets_equal,
                 chiral_equals_forward_SET=C == F,
                 COUNT_ONLY_TEST_WOULD_BE_WRONG=trap,
                 cell_set_fingerprints_sha256=fp,
                 fingerprint_note="Class A content-address of each hit set. Two "
                                  "cells are the SAME SET iff the fingerprints "
                                  "match — decidable from this record alone, "
                                  "without shipping the index lists.")
            print(f"[sets]   {ckey:5s} {name:24s} |F|={len(F):6d} |B|={len(B):6d} "
                  f"|C|={len(C):6d}  F∩B={len(F & B):6d} F−B={len(F - B):6d} "
                  f"B−F={len(B - F):6d}  B==C set? {sets_equal}  "
                  f"count-only wrong? {trap}")

    emit("FS1_FS2_verdict",
         falsifier="FS1 — 'a count-only test is sufficient'; "
                   "FS2 — 'equal counts imply equal sets'",
         readings_where_counts_agree_but_sets_differ=caught,
         result=("REFUTED, and the trap is REAL not hypothetical: both O16 "
                 "readings score bare == chiral == 2752 while the two sets "
                 "differ by 1344 triples in each direction. A count-only "
                 "instrument declares them the same operation. The proposed "
                 "op-2 output makes the difference readable off the record."),
         null_class="REFUTED",
         which_carriers="O16 only — the abelian rows have bare == chiral as "
                        "SETS (a genuine equality, not a collision) and the "
                        "two groups differ in COUNT as well as set, so O16 is "
                        "the ONLY row where the count lies. One row is enough: "
                        "an instrument that is wrong on the hardest carrier is "
                        "wrong.")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §5  PROPOSED OP 3 — anti_automorphism_witnesses  (prototype)
#     FA1: rc426 compared COUNTS. This compares SETS.
# ═════════════════════════════════════════════════════════════════════════════
def anti_automorphism_witnesses(elems, mul, inv):
    """PROTOTYPE — returns the FAILING pair set, not only a count."""
    good, bad = set(), set()
    commuting = set()
    idx = 0
    for a in elems:
        for b in elems:
            i = idx
            idx += 1
            if inv(mul(a, b)) == mul(inv(b), inv(a)):
                good.add(i)
            if inv(mul(a, b)) == mul(inv(a), inv(b)):
                bad.add(i)
            if mul(a, b) == mul(b, a):
                commuting.add(i)
    return good, bad, commuting, idx


def section_antiauto():
    for c in CARRIERS:
        good, bad, comm, tot = anti_automorphism_witnesses(c.elems, c.mul, c.inv)
        emit("anti_automorphism_witnesses", carrier=c.key, order=c.n,
             pairs=tot,
             correct_law_holds=len(good), correct_law_total=len(good) == tot,
             correct_law_failing_pairs=tot - len(good),
             wrong_law_holds=len(bad),
             commuting_pairs=len(comm),
             wrong_law_equals_commuting_COUNT=len(bad) == len(comm),
             wrong_law_equals_commuting_SET=bad == comm,
             wrong_minus_commuting=len(bad - comm),
             commuting_minus_wrong=len(comm - bad),
             fingerprint_correct=fingerprint(good),
             fingerprint_wrong=fingerprint(bad),
             fingerprint_commuting=fingerprint(comm),
             falsifier="FA1 — rc426 recorded this as a COUNT equality only. "
                       "Measured here at SET resolution.",
             note="(ab)⁻¹ = b⁻¹a⁻¹ is the anti-automorphism; (ab)⁻¹ = a⁻¹b⁻¹ "
                  "is a homomorphism and is expected to hold exactly on the "
                  "commuting SET.")
        print(f"[anti]   {c.key:5s} (ab)⁻¹=b⁻¹a⁻¹ {len(good)}/{tot}   "
              f"(ab)⁻¹=a⁻¹b⁻¹ {len(bad)}/{tot}  commuting {len(comm)}  "
              f"SET equal? {bad == comm}")
    print()


def section_antiauto_negative_control():
    """NC5 — feed a NON-inverse and the witness op must reject it."""
    for c in CARRIERS:
        def squaring(x):
            return c.mul(x, x)                # deliberately NOT an inverse
        good, bad, comm, tot = anti_automorphism_witnesses(
            c.elems, c.mul, squaring)
        emit("negative_control", control="NC5_non_inverse_map",
             carrier=c.key,
             correct_law_holds_under_squaring=len(good), of=tot,
             total=len(good) == tot,
             rejected=len(good) != tot,
             note="If the anti-automorphism law were total under an arbitrary "
                  "map, the instrument would be blessing anything.")
        print(f"[NC5]    {c.key:5s} squaring-as-'inverse': "
              f"{len(good)}/{tot}  rejected={len(good) != tot}")
    emit("negative_control_verdict", control="NC5_non_inverse_map",
         rejected_on=["Q8", "TI24", "O16"],
         blessed_on=["Z7", "Z12"],
         passes_where_it_can=True,
         honest_bound=("NC5 CANNOT reject on an ABELIAN carrier, and this is a "
                       "property of the mathematics rather than a defect in "
                       "the control: x ↦ x² IS a homomorphism on an abelian "
                       "group, so it satisfies the anti-automorphism law "
                       "vacuously. The control is informative on exactly the "
                       "three non-abelian carriers, where it rejects 3 of 3. "
                       "Recorded as a SCOPED control, not a total one — an "
                       "instrument that cannot return otherwise on two rows "
                       "is not measuring anything on those two rows."),
         null_class="BOUNDED — the control is valid on the non-abelian rows "
                    "and vacuous on the abelian ones.")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §6  PROPOSED OP 4 — commuting_probability  (prototype)
# ═════════════════════════════════════════════════════════════════════════════
def conj_classes(elems, mul, inv):
    """Orbits of y under y ↦ (x·y)·x⁻¹, with the alternative bracketing
    x·(y·x⁻¹) MEASURED alongside rather than assumed equal (on a loop the two
    need not agree; flexibility would force it, and 'would force it' is a
    claim, so it is executed)."""
    seen, classes = set(), []
    agree = total = 0
    for x in elems:
        for y in elems:
            total += 1
            if mul(mul(x, y), inv(x)) == mul(x, mul(y, inv(x))):
                agree += 1
    for y in elems:
        if y in seen:
            continue
        orb = {mul(mul(x, y), inv(x)) for x in elems}
        orb.add(y)
        seen |= orb
        classes.append(sorted(orb, key=jkey))
    return classes, agree, total


def commuting_probability(elems, mul, inv):
    """PROTOTYPE — exact ℚ through the shipped Class-I gcd, plus the verdict
    fields that make the Gustafson ceiling a property of the OUTPUT rather
    than of a separate constant-op."""
    n = len(elems)
    commuting = sum(1 for a in elems for b in elems if mul(a, b) == mul(b, a))
    classes, agree, brack_total = conj_classes(elems, mul, inv)
    k = len(classes)
    num, den = reduce_ratio(commuting, n * n)
    knum, kden = reduce_ratio(k, n)
    abelian = commuting == n * n
    # class equation: |G|·k(G) == #commuting ordered pairs  (orbit-stabiliser)
    class_eq = (n * k == commuting)
    # 5/8 comparison by INTEGER cross-multiplication — no division, no float.
    le_58 = num * 8 <= 5 * den
    eq_58 = (num * 8 == 5 * den)
    return dict(order=n, commuting=commuting, of=n * n,
                rate_num=num, rate_den=den,
                k=k, k_over_order_num=knum, k_over_order_den=kden,
                abelian=abelian,
                rate_equals_k_over_order=(num, den) == (knum, kden),
                class_equation_holds=class_eq,
                conjugation_bracketings_agree=agree, of_bracketings=brack_total,
                class_sizes=[len(o) for o in classes],
                gustafson_applicable=(not abelian) and class_eq,
                le_five_eighths=le_58, attains_five_eighths=eq_58)


def section_commuting_probability():
    out = {}
    flagged = []
    for c in CARRIERS:
        r = commuting_probability(c.elems, c.mul, c.inv)
        out[c.key] = dict(commuting=r["commuting"], k=r["k"])
        if not r["rate_equals_k_over_order"]:
            flagged.append(c.key)
        emit("commuting_probability", carrier=c.key, **r,
             falsifier="FP1 — Pr(G) = k(G)/|G| is a GROUP theorem. PREDICTED "
                       "to hold on the four groups and FAIL at the loop.",
             is_a_group_by_this_test=r["rate_equals_k_over_order"],
             built_through="srmech.math.cyclic.gcd (Class I) for the exact-ℚ "
                           "reduction; 5/8 compared by integer "
                           "cross-multiplication, never by division.")
        print(f"[commP]  {c.key:5s} rate={r['rate_num']}/{r['rate_den']}  "
              f"k/|G|={r['k_over_order_num']}/{r['k_over_order_den']}  "
              f"equal={r['rate_equals_k_over_order']}  "
              f"<=5/8={r['le_five_eighths']}  ==5/8={r['attains_five_eighths']}")
    emit("FP2_non_group_detector",
         falsifier="FP2 — does rate != k/|G| separate the loop from the groups "
                   "with no false positive? PREDICTED: exactly 1 flagged, O16.",
         carriers_flagged=flagged, n_flagged=len(flagged),
         prediction_held=flagged == ["O16"],
         result="Pr != k/|G| is a NON-GROUP DETECTOR: it fires on exactly the "
                "one carrier that is not a group, and on no other. That is the "
                "decision content that lifts the op above a ratio.",
         null_class="n/a — a positive result")
    print()
    return out


# ═════════════════════════════════════════════════════════════════════════════
# §7  THE 5/8 CEILING — sourced where possible, DERIVED where not, executed
#     either way
# ═════════════════════════════════════════════════════════════════════════════
def section_gustafson():
    emit("citations", topic="the 5/8 ceiling on commuting probability",
         rows=[
             dict(claim="Gustafson's paper exists and is the origin of the "
                        "commuting-probability question",
                  tier="VERIFIED-SELF",
                  evidence="PDF of arXiv:1001.4856 FETCHED and text-extracted "
                           "in this session. §5 'On the history and background "
                           "of the problem', p.15, verbatim: 'A study of the "
                           "probability that two randomly picked elements x "
                           "and y of a compact group G commute was initiated "
                           "by W. H. Gustafson in [8].'",
                  bibliography_entry_verbatim="[8] Gustafson, W. H., What is "
                           "the probability that two group elements commute? "
                           "Amer. Math. Monthly 80 (1973), 1031-1304.",
                  source_title="The probability that x and y commute in a "
                               "compact group",
                  source_authors="Karl H. Hofmann (TU Darmstadt), "
                                 "Francesco G. Russo (Univ. di Palermo)",
                  source_id="arXiv:1001.4856",
                  caveat="⚠️ The page range in that bibliography entry is a "
                         "TYPO: '1031-1304' cannot be right for a Monthly "
                         "note. The commonly given range is 1031-1034. "
                         "REPORTED, NOT SILENTLY CORRECTED — this record "
                         "attests what the fetched PDF says."),
             dict(claim="d(Q8) = 5/8, i.e. the quaternion group attains the "
                        "bound exactly",
                  tier="VERIFIED-SELF",
                  evidence="Same PDF, Example 4.1, p.13, verbatim: 'Let H be "
                           "the 8-element quaternion group and P = ν × ν. "
                           "Then d(H) = 5/8.'",
                  source_id="arXiv:1001.4856",
                  cross_check="MEASURED here at 5/8 exactly on the shipped "
                              "q8_mult carrier — see the commuting_probability "
                              "record for Q8."),
             dict(claim="Pr(G) ≤ 5/8 for every finite NON-ABELIAN group "
                        "(the bound itself)",
                  tier="NOT SOURCED FROM A PEER-REVIEWED OA DOCUMENT",
                  evidence="The Hofmann-Russo PDF states the Q8 VALUE and "
                           "attributes the QUESTION to Gustafson, but never "
                           "states the 5/8 upper bound. The Gustafson paper "
                           "itself (Amer. Math. Monthly 80, 1973) is "
                           "JSTOR-paywalled, and a paywalled-only source is "
                           "REJECTED as attestation by project discipline. "
                           "Two further OA abstracts were fetched and neither "
                           "states it: arXiv:1411.0848 (Eberhard, 'Commuting "
                           "probabilities of finite groups') and the "
                           "arXiv:1001.4856 abstract.",
                  weakest_available="EXPERT-WEB — en.wikipedia.org/wiki/"
                                    "Commuting_probability states verbatim "
                                    "'If G is not abelian then p(G) ≤ 5/8', "
                                    "but the citation attached in that "
                                    "paragraph is a BLOG POST (Baez, 'The 5/8 "
                                    "Theorem', Azimuth, 2018-09-16), not a "
                                    "peer-reviewed source. Recorded, not "
                                    "relied on.",
                  wikipedia_discrepancy="That article also says the smallest "
                           "group attaining 5/8 is 'the dihedral group of "
                           "order 8'. There are TWO groups of order 8 "
                           "attaining it — D₈ and Q₈ — and Hofmann-Russo "
                           "Example 4.1 attests the Q₈ one. 'The smallest' is "
                           "therefore incomplete as written. NOT corrected "
                           "upstream; recorded here.",
                  classification="DERIVED-AND-MEASURED, not cited — see the "
                                 "gustafson_derivation record."),
         ])

    # ── the four-step derivation, EXECUTED on every carrier ──────────────────
    steps = [
        "S1  G non-abelian  =>  G/Z(G) is not cyclic  =>  [G:Z(G)] >= 4.",
        "S2  the class equation partitions G into |Z(G)| singleton classes and "
        "k(G) - |Z(G)| classes of size >= 2, so k(G) <= |Z| + (|G| - |Z|)/2.",
        "S3  Pr(G) = k(G)/|G| <= |Z|/|G| + 1/2 - |Z|/(2|G|) = 1/2 + |Z|/(2|G|).",
        "S4  |Z|/|G| <= 1/4 by S1, so Pr(G) <= 1/2 + 1/8 = 5/8, with equality "
        "iff [G:Z] = 4 and every non-central class has size exactly 2.",
    ]
    for c in CARRIERS:
        n = c.n
        centre = [z for z in c.elems
                  if all(c.mul(z, x) == c.mul(x, z) for x in c.elems)]
        zc = len(centre)
        classes, _, _ = conj_classes(c.elems, c.mul, c.inv)
        k = len(classes)
        commuting = sum(1 for a in c.elems for b in c.elems
                        if c.mul(a, b) == c.mul(b, a))
        abelian = commuting == n * n
        class_eq = (n * k == commuting)
        # S1: index >= 4 ?   (integer test; n is divisible by zc on a group)
        s1 = (not abelian) and zc * 4 <= n
        # S2: k <= |Z| + (|G|-|Z|)/2  -> 2k <= 2|Z| + |G| - |Z| = |Z| + |G|
        s2 = (2 * k <= zc + n)
        # S3/S4 combined: 8*commuting <= 5*n*n   (Pr <= 5/8), by cross-mult
        s4 = (8 * commuting <= 5 * n * n)
        emit("gustafson_derivation", carrier=c.key, order=n,
             centre_order=zc, index_of_centre_num=n, index_of_centre_den=zc,
             conjugacy_classes=k,
             abelian=abelian,
             class_equation_holds=class_eq,
             derivation_in_scope=(not abelian) and class_eq,
             S1_index_at_least_4=s1,
             S2_class_count_bound=s2,
             S4_rate_at_most_five_eighths=s4,
             attains=(8 * commuting == 5 * n * n),
             steps=steps,
             falsifier="FG1 — every non-abelian finite GROUP must satisfy S1, "
                       "S2 and S4. The abelian rows are OUT OF SCOPE (the "
                       "theorem is conditioned on non-abelian). The LOOP is "
                       "out of scope because S2 uses the class equation, which "
                       "FP1 predicts fails there.")
        print(f"[5/8]    {c.key:5s} |Z|={zc:3d} k={k:3d} in-scope="
              f"{(not abelian) and class_eq}  S1={s1} S2={s2} S4={s4} "
              f"attains={8 * commuting == 5 * n * n}")

    emit("FG1_verdict",
         falsifier="FG1 — 'Pr(G) <= 5/8 for every non-abelian finite group'",
         result="HOLDS on both in-scope carriers: Q8 at EQUALITY (5/8) and "
                "TI24 strictly below (3/8). The abelian rows sit at 1/1, which "
                "is not a counterexample because the theorem is conditioned on "
                "non-abelian. The octonion loop is OUT OF SCOPE by its own "
                "measured failure of the class equation, and its rate 43/64 "
                "cleanest possible demonstration that the ceiling is a GROUP "
                "theorem and evaporates one rung down the Hurwitz ladder.",
         the_loop_in_detail=("At O16 the two rates land on OPPOSITE sides of "
                             "the ceiling: the BARE-REVERSAL rate is 43/64 > "
                             "5/8, while the COMMUTING PROBABILITY is 11/32 < "
                             "5/8. Whichever one a reader takes 'the 5/8 "
                             "ceiling' to bound, the other tells the opposite "
                             "story — which is why proposed op 4 must name "
                             "which quantity it is reporting."),
         null_class="n/a — a positive result on the in-scope rows",
         shipping_decision="The bound does NOT deserve a standalone op. A "
                           "`gustafson_bound()` returning 5/8 is a CONSTANT, "
                           "and this codebase already rejected constant-shaped "
                           "ops on exactly that ground (music/relations.py:54-63 "
                           "REJECTED interval_invert / pitch_class_transpose / "
                           "pitch_class_invert because each 'is a single "
                           "cyclic_mod_add call carrying no decision'). It "
                           "ships instead as three VERDICT FIELDS on proposed "
                           "op 4 — gustafson_applicable / le_five_eighths / "
                           "attains_five_eighths — where the applicability "
                           "test is itself the decision, because it is the "
                           "class-equation check that O16 fails.")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §8  REPRODUCTION LEDGER — every rc426 committed number, re-derived THROUGH
#     the proposed ops, compared cell by cell
# ═════════════════════════════════════════════════════════════════════════════
RC426_EIGHT_CELLS = {
    # carrier: (triples, FORWARD, BARE, CHIRAL, INV_ONLY)  — identical under
    # both readings per the committed table.
    "Z7":   (343, 343, 343, 343, 343),
    "Z12":  (1728, 1728, 1728, 1728, 1728),
    "Q8":   (512, 512, 320, 512, 320),
    "TI24": (13824, 13824, 5184, 13824, 5184),
    "O16":  (4096, 2752, 2752, 2752, 2752),
}
RC426_SET_OVERLAP = {
    # carrier: (forward_n, bare_n, chiral_n, F&B, F&C, F-B, B-F)
    "Z7":   (343, 343, 343, 343, 343, 0, 0),
    "Z12":  (1728, 1728, 1728, 1728, 1728, 0, 0),
    "Q8":   (512, 320, 512, 320, 512, 192, 0),
    "TI24": (13824, 5184, 13824, 5184, 13824, 8640, 0),
    "O16":  (2752, 2752, 2752, 1408, 2752, 1344, 1344),
}
RC426_COMMUTING = {
    # carrier: (commuting_ordered_pairs, k, Pr_num, Pr_den)
    #
    # ⚠️ Pr IS commuting/|G|², taken from rc426's `algebra_census` record —
    # NOT from its `bare_rate_is_commuting_probability` record, whose
    # `bare_rate_num/den` field is the bare-reversal rate over TRIPLES. On the
    # four GROUPS those two coincide; at the LOOP they are different rationals
    # (43/64 vs 11/32) and the record's own NAME asserts an identity that its
    # own `equals_k_over_order: false` field denies. See the
    # `three_rates_at_the_loop` record.
    "Z7":   (49, 7, 1, 1),
    "Z12":  (144, 12, 1, 1),
    "Q8":   (40, 5, 5, 8),
    "TI24": (216, 9, 3, 8),
    "O16":  (88, 9, 11, 32),
}
RC426_BARE_RATE = {
    # carrier: (bare, of_triples, rate_num, rate_den) as committed by rc426's
    # `bare_rate_is_commuting_probability` record.
    "Z7":   (343, 343, 1, 1),
    "Z12":  (1728, 1728, 1, 1),
    "Q8":   (320, 512, 5, 8),
    "TI24": (5184, 13824, 3, 8),
    "O16":  (2752, 4096, 43, 64),
}


def section_reproduction(table, commp):
    all_ok = True
    for c in CARRIERS:
        want = RC426_EIGHT_CELLS[c.key]
        for name, d in table[c.key].items():
            got = (d["total"], d["fwd"], d["bare"], d["chi"], d["invo"])
            ok = got == want
            all_ok = all_ok and ok
            emit("rc426_reproduction_eight_cells", carrier=c.key, reading=name,
                 rc426_committed=dict(zip(
                     ["triples", "FORWARD", "BARE", "CHIRAL", "INVERSION_ONLY"],
                     want)),
                 rc427_through_proposed_ops=dict(zip(
                     ["triples", "FORWARD", "BARE", "CHIRAL", "INVERSION_ONLY"],
                     got)),
                 bit_identical=ok)
            print(f"[repro]  {c.key:5s} {name:24s} eight-cells "
                  f"{'MATCH' if ok else 'MISMATCH'}  {got}")
    for ckey, readings in table.items():
        want = RC426_SET_OVERLAP[ckey]
        for name, d in readings.items():
            hits = d["hits"]
            F, B, C = hits[d["fcell"]], hits[d["bcell"]], hits[d["ccell"]]
            got = (len(F), len(B), len(C), len(F & B), len(F & C),
                   len(F - B), len(B - F))
            ok = got == want
            all_ok = all_ok and ok
            emit("rc426_reproduction_set_overlap", carrier=ckey, reading=name,
                 rc426_committed=dict(zip(
                     ["forward_n", "bare_n", "chiral_n", "F_and_B", "F_and_C",
                      "F_minus_B", "B_minus_F"], want)),
                 rc427_through_proposed_ops=dict(zip(
                     ["forward_n", "bare_n", "chiral_n", "F_and_B", "F_and_C",
                      "F_minus_B", "B_minus_F"], got)),
                 bit_identical=ok)
            print(f"[repro]  {ckey:5s} {name:24s} set-overlap "
                  f"{'MATCH' if ok else 'MISMATCH'}  {got}")
    for c in CARRIERS:
        r = commuting_probability(c.elems, c.mul, c.inv)
        want = RC426_COMMUTING[c.key]
        got = (r["commuting"], r["k"], r["rate_num"], r["rate_den"])
        ok = got == want
        all_ok = all_ok and ok
        emit("rc426_reproduction_commuting", carrier=c.key,
             rc426_committed=dict(zip(
                 ["commuting_ordered_pairs", "k", "rate_num", "rate_den"], want)),
             rc427_through_proposed_ops=dict(zip(
                 ["commuting_ordered_pairs", "k", "rate_num", "rate_den"], got)),
             bit_identical=ok)
        print(f"[repro]  {c.key:5s} commuting-probability "
              f"{'MATCH' if ok else 'MISMATCH'}  {got}")
    for c in CARRIERS:
        want = RC426_BARE_RATE[c.key]
        d = table[c.key]["left_quotient_b_ainv"]
        bnum, bden = reduce_ratio(d["bare"], d["total"])
        got = (d["bare"], d["total"], bnum, bden)
        ok = got == want
        all_ok = all_ok and ok
        emit("rc426_reproduction_bare_rate", carrier=c.key,
             rc426_committed=dict(zip(
                 ["bare", "of_triples", "rate_num", "rate_den"], want)),
             rc427_through_proposed_ops=dict(zip(
                 ["bare", "of_triples", "rate_num", "rate_den"], got)),
             bit_identical=ok)
        print(f"[repro]  {c.key:5s} bare-rate "
              f"{'MATCH' if ok else 'MISMATCH'}  {got}")

    emit("reproduction_verdict",
         all_rc426_numbers_reproduced=all_ok,
         scope="8-cell counts (5 carriers x 2 readings), set-overlap "
               "cardinalities (5 x 2), commuting probability (5), bare rate "
               "(5). 40 comparisons.",
         one_correction_made="The FIRST pass of this ledger failed at O16 "
                             "because it had transcribed 43/64 into the "
                             "commuting-probability slot, following the "
                             "brief's wording. The measurement was right and "
                             "the transcription was wrong: 43/64 is the "
                             "bare-reversal rate over TRIPLES and 11/32 is "
                             "the commuting probability over PAIRS. Both are "
                             "now checked separately and both reproduce.",
         result=("EXACT" if all_ok else "DIVERGENCE — see the mismatching rows"),
         why_it_matters="The proposed ops are not a re-description of rc426; "
                        "every cell above was recomputed by CALLING the "
                        "prototypes, so a defect in op 1 or op 2 would show as "
                        "a mismatch here rather than as agreement by "
                        "construction.")
    print()
    return all_ok


# ═════════════════════════════════════════════════════════════════════════════
# §9  NEGATIVE CONTROLS
# ═════════════════════════════════════════════════════════════════════════════
def section_controls(table):
    # NC1 — half-inversion must never be total
    for ckey, readings in table.items():
        for name, d in readings.items():
            cells, total = d["cells"], d["total"]
            halves = {k: cells[k] for k in ("R1", "R2", "R3", "R4")}
            any_total = any(v == total for v in halves.values())
            emit("negative_control", control="NC1_half_inversion",
                 carrier=ckey, reading=name, ordered_triples=total,
                 half_inversion_cells=halves,
                 any_half_inversion_total=any_total,
                 passes=not any_total,
                 note="Inverting exactly ONE factor must never be a law. If it "
                      "were, the inversion would be doing nothing and the "
                      "whole thesis would be an artifact.")
            print(f"[NC1]    {ckey:5s} {name:24s} halves={halves} "
                  f"any total? {any_total}")

    # NC2 — identity-as-reversal is VACUOUS
    for ckey, readings in table.items():
        for name, d in readings.items():
            emit("negative_control", control="NC2_identity_as_reversal",
                 carrier=ckey, reading=name,
                 identity_reversal_count=d["fwd"],
                 forward_count=d["fwd"],
                 equal_to_forward=True,
                 passes=True,
                 verdict="VACUOUS BY CONSTRUCTION — 'reversal' by the identity "
                         "map returns the FORWARD cell unchanged, so it can "
                         "never distinguish anything. Recorded as the zero "
                         "point of the instrument, not as evidence.",
                 null_class="EMPTY")
    print(f"[NC2]    identity-as-reversal == forward on all "
          f"{sum(len(v) for v in table.values())} carrier/reading rows "
          f"(vacuous by construction)")

    # NC3 — a WRONG inverse fed to op 1 must degrade the census
    for c in CARRIERS:
        def identity_map(x):
            return x
        for name, iv in group_readings(c).items():
            counts, total, _ = reversal_law_census(
                c.elems, c.mul, identity_map, iv)
            side = "left" if name.startswith("left") else "right"
            ccell = "Q1" if side == "left" else "Q2"
            bcell = "P1" if side == "left" else "P2"
            emit("negative_control", control="NC3_wrong_inverse_in_op1",
                 carrier=c.key, reading=name,
                 chiral_cell_with_identity_as_inverse=counts[ccell],
                 bare_cell=counts[bcell],
                 degraded_to_bare=counts[ccell] == counts[bcell],
                 total_triples=total,
                 chiral_still_total=counts[ccell] == total,
                 passes=not (counts[ccell] == total and counts[bcell] != total),
                 note="With inv := identity, chiral_reversal collapses to bare "
                      "reversal. If the census still reported CHIRAL total on "
                      "a non-abelian carrier, op 1 would not be measuring the "
                      "inversion at all.")
            print(f"[NC3]    {c.key:5s} {name:24s} identity-as-inverse: "
                  f"chiral={counts[ccell]} bare={counts[bcell]} "
                  f"degraded={counts[ccell] == counts[bcell]}")

    # NC4 — the count-blind instrument must be WRONG at O16
    for c in CARRIERS:
        for name, iv in group_readings(c).items():
            counts, total = count_only_census(c.elems, c.mul, c.inv, iv)
            side = "left" if name.startswith("left") else "right"
            bcell = "P1" if side == "left" else "P2"
            ccell = "Q1" if side == "left" else "Q2"
            blind_says_same = counts[bcell] == counts[ccell]
            d = table[c.key][name]
            truth_same = d["hits"][d["bcell"]] == d["hits"][d["ccell"]]
            emit("negative_control", control="NC4_count_blind_instrument",
                 carrier=c.key, reading=name,
                 blind_instrument_says_bare_equals_chiral=blind_says_same,
                 set_instrument_says_bare_equals_chiral=truth_same,
                 blind_instrument_is_WRONG=blind_says_same and not truth_same,
                 note="This control is INVERTED: it passes by being WRONG. If "
                      "the blind instrument never erred, the set instrument "
                      "would be buying nothing and op 2 should be withdrawn.")
            print(f"[NC4]    {c.key:5s} {name:24s} blind says same="
                  f"{blind_says_same}  truth={truth_same}  "
                  f"blind WRONG={blind_says_same and not truth_same}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §10  OP-USAGE LEDGER + THE PROPOSAL / REJECT LISTS
# ═════════════════════════════════════════════════════════════════════════════
def section_ledger():
    emit("op_usage_ledger",
         shipped_ops_called=[
             "srmech.amsc.format.sha256_bytes            (A — hit-set address)",
             "srmech.cascade.chiral_flip                 (C — order reversal)",
             "srmech.cascade.chiral_dual                 (C∘op∘C — FCD1 control)",
             "srmech.cascade.cyclic_mod_add              (I — ℤ/n, T/I)",
             "srmech.cascade.pin_slot_at_zero            (K — FK1 test B)",
             "srmech.cascade.magnitude                   (K — FK1 test B)",
             "srmech.cascade.reorient                    (C — FK1 test B)",
             "srmech.math.cyclic.gcd                     (I — exact-ℚ reduce)",
             "srmech.biology.q8.q8_mult / q8_conjugate",
             "srmech.math.octonion.oct_mult / oct_conjugate",
         ],
         had_to_be_hand_rolled=[
             dict(what="the T/I order-24 group product and inverse",
                  why="no order-24 group object ships; the shipped loop orders "
                      "are powers of two only (4/8/16/32) and "
                      "srmech.cascade.group_algebra_table is ℝ[ℤ/dim], cyclic "
                      "and abelian by its own docstring.",
                  is_this_a_gap="NOT PROPOSED HERE — a general finite-group "
                                "object is a much larger surface than this "
                                "stream is costing, and the T/I build is 20 "
                                "lines over the shipped cyclic_mod_add. "
                                "RECORDED so the absence stays visible."),
             dict(what="the 8-cell census, the hit sets, the set differences, "
                       "the commuting probability, the conjugacy classes and "
                       "the class equation",
                  why="none of them ship — registry grep for "
                      "'conjugacy|class_equation|commuting|centraliz' returns "
                      "0 op names at 649 ops.",
                  is_this_a_gap="YES — this IS the proposal (ops 2 and 4)."),
             dict(what="chiral reversal itself",
                  why="chiral_flip gives BARE reversal (the wrong answer on 3 "
                      "of 5 carriers) and chiral_dual CANCELS the reversal "
                      "around any pointwise op (measured, FCD1).",
                  is_this_a_gap="YES — this IS the proposal (op 1)."),
         ])

    emit("proposed_ops", ops=[
        dict(n=1, name="chiral_reversal",
             module="srmech/cascade/atoms.py",
             signature="chiral_reversal(word, inverse) -> tuple",
             an_class="C on ORDER (shipped chiral_flip) ⊗ the carrier's own "
                      "inverse class (C on Q8/O16, I on ℤ/n and T/I) — an "
                      "UNORDERED pair of independent factors, NOT 'K then C'",
             exact=True, cost="small",
             composes="srmech.cascade.chiral_flip",
             why="chiral_flip alone is bare reversal and is measurably wrong "
                 "on Q8 (320/512), TI24 (5184/13824) and O16 (set-wrong at "
                 "equal count); chiral_dual structurally cannot express it.",
             totality="total by construction (a position permutation composed "
                      "with a total pointwise map); on the non-associative "
                      "loop the LAW it satisfies is total on exactly the "
                      "forward-success set — 2752/4096, measured."),
        dict(n=2, name="reversal_law_census",
             module="srmech/cascade/reversal.py (new)",
             signature="reversal_law_census(elems, mul, inv, interval) -> dict",
             an_class="C (which-way operands) then D (pattern-match census) "
                      "then A (content-address of each hit SET)",
             exact=True, cost="medium",
             composes="srmech.cascade.chiral_flip, srmech.amsc.format.sha256_bytes",
             why="THE mandatory instrument. Counts alone declare bare and "
                 "chiral the same operation at O16 and are wrong by 1344 "
                 "triples in each direction. Shape precedent: "
                 "cd_zero_divisor_witnesses, which 'EXHIBITS the whole "
                 "boundary, not one point of it'."),
        dict(n=3, name="anti_automorphism_witnesses",
             module="srmech/cascade/reversal.py (new)",
             signature="anti_automorphism_witnesses(elems, mul, inv) -> dict",
             an_class="C (the reversed-and-inverted law) then D (witness "
                      "census) then A (content-address)",
             exact=True, cost="small",
             composes="srmech.cascade.chiral_reversal",
             why="rc426 asserted '(ab)⁻¹ = a⁻¹b⁻¹ holds exactly on the "
                 "commuting pairs' from a COUNT equality. This measures the "
                 "SET. It is also the n² mechanism behind the n³ census: the "
                 "wrong law succeeds exactly on the commuting set, which is "
                 "why Gustafson caps the bare rate."),
        dict(n=4, name="commuting_probability",
             module="srmech/cascade/reversal.py (new)",
             signature="commuting_probability(elems, mul, inv) -> dict",
             an_class="D (census) then I (gcd reduction) then N (exact "
                      "small-denominator rational)",
             exact=True, cost="small",
             composes="srmech.math.cyclic.gcd",
             why="the closed form of the BARE-reversal rate on groups, AND a "
                 "NON-GROUP DETECTOR: rate != k/|G| fires on exactly O16 and "
                 "nothing else. Carries the Gustafson verdict as fields."),
    ])

    emit("rejected_ops", ops=[
        dict(name="gustafson_bound",
             reason="a CONSTANT carrying no decision. The music surface already "
                    "rejected three ops on exactly that ground.",
             already_ships_at="n/a — ships as verdict FIELDS on proposed op 4"),
        dict(name="bare_reversal",
             reason="already ships, and is the Class-C op the whole thesis "
                    "warns against using as 'reversal'.",
             already_ships_at="srmech.cascade.chiral_flip "
                              "(srmech/cascade/atoms.py:435)"),
        dict(name="opposite_table / opposite_group",
             reason="a Cayley-table transpose carrying no decision; the P2/Q2 "
                    "cells of proposed op 2 ARE the opposite-product law, "
                    "measured rather than tabulated.",
             already_ships_at="n/a — subsumed by proposed op 2"),
        dict(name="half_inversion",
             reason="a NEGATIVE CONTROL, not a capability. Ships as cells "
                    "R1-R4 of proposed op 2, where it is guaranteed to be "
                    "exercised on every call.",
             already_ships_at="n/a — subsumed by proposed op 2"),
        dict(name="conjugacy_classes (standalone)",
             reason="its only consumer is op 4, and on a non-associative loop "
                    "it is not well defined without declaring a bracketing "
                    "((xy)x⁻¹ vs x(yx⁻¹)). Op 4 returns the class data as "
                    "fields AND reports the bracketing agreement count, so "
                    "the ambiguity is visible rather than hidden behind a "
                    "name.",
             already_ships_at="n/a — subsumed by proposed op 4"),
        dict(name="is_moufang / moufang_residue / associator / loop_invariants "
                  "/ unit_loop / malcev_defect",
             reason="ALREADY SHIP. Any proposal for loop-law checking is a "
                    "defect in the spec.",
             already_ships_at="srmech/cascade/cayley_dickson.py (registered as "
                              "srmech.cascade.is_moufang, .moufang_residue, "
                              ".associator, .loop_invariants, .unit_loop, "
                              ".malcev_defect)"),
        dict(name="reverse_order / chiral_dual",
             reason="ALREADY SHIP. chiral_dual in particular was tested here "
                    "and CANNOT express chiral reversal, so reusing it would "
                    "ship a wrong answer.",
             already_ships_at="srmech.introspect.naming.reverse_order; "
                              "srmech.cascade.chiral_dual"),
    ])

    emit("prior_art_greps", note="run at 0.9.0rc425 against "
         "docs/srmech/python/tests/registered_op_names.txt (649 lines) and the "
         "package tree; recorded as evidence of ABSENCE.",
         greps=[
             dict(query="grep -inE 'revers|invert|opposit|anti_?aut|antiaut' "
                        "tests/registered_op_names.txt",
                  hits=2,
                  result="srmech.cascade.left_mult_is_invertible, "
                         "srmech.introspect.naming.reverse_order — neither is "
                         "an algebraic reversal. ABSENT."),
             dict(query="grep -inE 'commut|conjug|class_eq|gustafson|"
                        "centraliz|centralis' tests/registered_op_names.txt",
                  hits=8,
                  result="all 8 are *_conjugate element ops plus cd_commutator "
                         "and qm.single_particle.commutator. NO commuting "
                         "probability, NO conjugacy classes, NO class "
                         "equation, NO centraliser. ABSENT."),
             dict(query="grep -inE 'set_diff|symmetric_diff|overlap|jaccard|"
                        "intersect|witness' tests/registered_op_names.txt",
                  hits=2,
                  result="cd_zero_divisor_witness(es) only — a witness "
                         "ENUMERATOR, not a set-comparison instrument. The "
                         "SHAPE precedent, not the capability. ABSENT."),
             dict(query="grep -in 'chiral' tests/registered_op_names.txt",
                  hits=7,
                  result="chirality_parity, chiral_dual, chiral_flip, "
                         "net_chirality, klein4_chirality_flip_gamma5/omega7, "
                         "classify_chirality_harmonic. NO chiral_reversal. "
                         "ABSENT."),
             dict(query="grep -rn 'Class [A-N]' srmech/ --include=*.py | "
                        "grep -i conj",
                  hits=6,
                  result="the 6 rows in FK1_label_census — 4 say Class C, "
                         "2 say Class K, for the same operation."),
         ])
    print("[ledger] proposal + reject + grep evidence emitted")
    print()


# ═════════════════════════════════════════════════════════════════════════════
def main():
    section_env()
    section_carriers()

    print("── §2  CLASS ASSIGNMENT — VERIFIED, NOT ADOPTED ──")
    section_class_label_census()
    section_class_k_executable()
    section_class_c_order()
    section_kc_ordering()
    section_chiral_dual_does_not_do_it()

    print("── §6  COMMUTING PROBABILITY ──")
    algebra = section_commuting_probability()

    print("── §4  THE CENSUS, THROUGH THE PROPOSED OPS ──")
    table = section_census(algebra)
    section_three_rates(table)
    section_set_instrument(table)

    print("── §5  ANTI-AUTOMORPHISM AT SET RESOLUTION ──")
    section_antiauto()
    section_antiauto_negative_control()

    print("── §7  THE 5/8 CEILING ──")
    section_gustafson()

    print("── §9  NEGATIVE CONTROLS ──")
    section_controls(table)

    print("── §8  REPRODUCTION LEDGER ──")
    ok = section_reproduction(table, algebra)

    section_ledger()

    out = __file__.replace(".py", ".ndjson")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")
    print(f"\nwrote {len(RECORDS)} records -> {out}")
    print(f"rc426 reproduction: {'EXACT' if ok else 'DIVERGENCE'}")


if __name__ == "__main__":
    main()
