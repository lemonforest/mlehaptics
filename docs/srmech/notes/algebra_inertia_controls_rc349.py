#!/usr/bin/env python3
"""The CONTROLS behind the rc349 inertia-signature numbers (`#T987` / `#T968`).

Committed per the computational-provenance discipline: every load-bearing count
quoted in the CHANGELOG for ``srmech.amsc.cascade.inertia_signature`` ships with
the code that produced it. Emits NDJSON (one record per control) on stdout; a
human summary goes to stderr. Exit 0 iff every control passed.

    python3 docs/srmech/notes/algebra_inertia_controls_rc349.py

WHAT IS AND IS NOT BEING CLAIMED
--------------------------------
The Hurwitz loss ladder — ℝ→ℂ ordering, ℂ→ℍ commutativity, ℍ→𝕆 associativity —
is the **classical result: definitional, textbook, forced**. Nothing here
discovers it, and the ladder rows below are a CHECK on the instrument, not a
finding. What is new is the INSTRUMENT and its behaviour on inputs the theorem
does not cover, which is why the controls are the content:

  C1  split octonions — the discriminating pin. Split-𝕆 must NOT answer with
      𝕆's signature. An audit this rc found a mechanism scoring 200/200 on 𝕆,
      split-𝕆 and a random table alike, because it took no algebra input at
      all; separating those three is therefore the pass condition.
  C2  ≥100 random structure-constant tables of matched shape (monomial and
      general), every witness re-verified against the table it came from.
  C3  a NO-NEGATIVE-DIRECTION control. A witness-finder that can never return
      "none" is not measuring anything.
  C4  THE CEILING, measured rather than conceded: the family the op provably
      CANNOT separate from 𝕆, and the neighbouring family it can.
  C5  the coordinate-form pathology, measured: why Re(x·x) is summed from the
      structure constants and never as a² − |v|².

WHAT THIS OP DOES NOT MEASURE (C4 is the evidence)
--------------------------------------------------
It reads the inertia of ONE quadratic form. ``n₋ == 0`` is NOT "orderable" —
split-ℂ answers (2,0,0) and has zero divisors (1+j)(1−j) = 0, so it is provably
not orderable. And a table with 𝕆's diagonal and a scrambled imaginary
off-diagonal answers (1,7,0) identically while being 0/200 associative. The op
certifies nothing about composition, alternativity, associativity or division.

Plus an INDEPENDENT exact oracle for the signature (Faddeev–LeVerrier
characteristic polynomial + Descartes' rule of signs, which is exact rather
than an upper bound because a real symmetric Gram has only real eigenvalues),
sharing no code with the congruence elimination under test.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from fractions import Fraction

# SHADOW GUARD (same reason as tools/verify_cd_rungs.py): say out loud which
# srmech answered, so a stale installed wheel cannot quietly "prove" the tree.
_PKG_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python")
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

import srmech  # noqa: E402

from srmech.amsc import _native  # noqa: E402
from srmech.amsc.cascade import inertia_signature  # noqa: E402
from srmech.qm.octonion import octonion_mult_table  # noqa: E402
from srmech.qm.quaternion import quaternion_mult_table  # noqa: E402


# ── the generalized Cayley–Dickson doubling (the control fixtures) ───────────
# (a, b)(c, d) = (a c + γ d̄ b, d a + b c̄); γ = −1 is the standard definite
# doubling srmech ships, γ = +1 makes that level SPLIT.

def cd_table(dim, gammas):
    def conj(a):
        n = len(a)
        if n == 1:
            return a
        m = n >> 1
        return conj(a[:m]) + tuple(-x for x in a[m:])

    def mul(a, b):
        n = len(a)
        if n == 1:
            return (a[0] * b[0],)
        m = n >> 1
        gamma = gammas[len(gammas) - (n.bit_length() - 1)]
        a1, a2 = a[:m], a[m:]
        b1, b2 = b[:m], b[m:]
        left = tuple(p + gamma * q for p, q in zip(mul(a1, b1), mul(conj(b2), a2)))
        right = tuple(p + q for p, q in zip(mul(b2, a1), mul(a2, conj(b1))))
        return left + right

    def basis(i):
        return tuple(1 if k == i else 0 for k in range(dim))

    return [[list(mul(basis(i), basis(j))) for j in range(dim)]
            for i in range(dim)]


def random_monomial_table(dim, rng):
    out = []
    for _ in range(dim):
        row = []
        for _ in range(dim):
            cell = [0] * dim
            cell[rng.randrange(dim)] = rng.choice((1, -1))
            row.append(cell)
        out.append(row)
    return out


def random_general_table(dim, rng):
    return [[[rng.choice((-1, 0, 0, 1)) for _ in range(dim)]
             for _ in range(dim)] for _ in range(dim)]


def diagonal_pinned_table(dim, rng, allow_real_offdiagonal=False):
    """𝕆's diagonal, everything else scrambled. With the off-diagonal drawn
    from the IMAGINARY directions only, every off-diagonal real part is zero
    and the trace-form Gram is EXACTLY 𝕆's — the family the ceiling is about."""
    low = 0 if allow_real_offdiagonal else 1
    table = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            if i == j:
                table[i][j][0] = 1 if i == 0 else -1
            else:
                table[i][j][rng.randrange(low, dim)] = rng.choice((1, -1))
    return table


def is_associative(table):
    """Lazy scan of every imaginary basis triple; stops at the first failure."""
    dim = len(table)
    for i in range(1, dim):
        for j in range(1, dim):
            for k in range(1, dim):
                a, b, c = ([0] * dim for _ in range(3))
                a[i], b[j], c[k] = 1, 1, 1
                if full_product(table, full_product(table, a, b), c) != \
                        full_product(table, a, full_product(table, b, c)):
                    return False
    return True


def full_product(table, x, y):
    dim = len(table)
    out = [0] * dim
    for i in range(dim):
        if x[i] == 0:
            continue
        for j in range(dim):
            if y[j] == 0:
                continue
            for k, c in enumerate(table[i][j]):
                if c:
                    out[k] += x[i] * y[j] * c
    return out


# ── the independent exact oracle ─────────────────────────────────────────────

def char_poly(gram):
    n = len(gram)
    a = [[Fraction(v) for v in row] for row in gram]
    coeffs = [Fraction(1)]
    m = [[Fraction(1) if i == j else Fraction(0) for j in range(n)]
         for i in range(n)]
    for k in range(1, n + 1):
        if k > 1:
            am = [[sum(a[i][t] * m[t][j] for t in range(n)) for j in range(n)]
                  for i in range(n)]
            m = [[am[i][j] + (coeffs[-1] if i == j else 0) for j in range(n)]
                 for i in range(n)]
        am = [[sum(a[i][t] * m[t][j] for t in range(n)) for j in range(n)]
              for i in range(n)]
        coeffs.append(-sum(am[i][i] for i in range(n)) / k)
    assert all(c.denominator == 1 for c in coeffs)
    return [int(c) for c in coeffs]


def oracle_signature(table):
    dim = len(table)
    gram = [[table[i][j][0] + table[j][i][0] for j in range(dim)]
            for i in range(dim)]
    c = char_poly(gram)
    n_zero = 0
    while c and c[-1] == 0:
        c.pop()
        n_zero += 1
    if not c:
        return (0, 0, dim)

    def changes(seq):
        nz = [v for v in seq if v != 0]
        return sum(1 for x, y in zip(nz, nz[1:]) if x * y < 0)

    alt = [v if (len(c) - 1 - i) % 2 == 0 else -v for i, v in enumerate(c)]
    return (changes(c), changes(alt), n_zero)


# ── the controls ─────────────────────────────────────────────────────────────

DUAL_NUMBERS = [[[1, 0], [0, 1]], [[0, 1], [0, 0]]]      # R[eps]/(eps^2)

NAMED = [
    ("R", cd_table(1, []), (1, 0, 0), (1, 0, 0)),
    ("C", cd_table(2, [-1]), (1, 1, 0), (2, 0, 0)),
    ("H", cd_table(4, [-1, -1]), (1, 3, 0), (4, 0, 0)),
    ("O", cd_table(8, [-1, -1, -1]), (1, 7, 0), (8, 0, 0)),
    ("S16", cd_table(16, [-1] * 4), (1, 15, 0), (16, 0, 0)),
    ("split-C", cd_table(2, [+1]), (2, 0, 0), (1, 1, 0)),
    ("split-H", cd_table(4, [-1, +1]), (3, 1, 0), (2, 2, 0)),
    ("split-O", cd_table(8, [-1, -1, +1]), (5, 3, 0), (4, 4, 0)),
    ("dual", DUAL_NUMBERS, (1, 0, 1), (1, 0, 1)),
]


def control_ladder():
    """The ladder + the split peers + a degenerate algebra, in BOTH forms.

    The definite column is TEXTBOOK. On the shipped ladder n₋ is exactly
    dim − 1 (0/1/3/7/15), so reading those rows is reading the dimension —
    graded DEFINITIONAL. The split and degenerate rows are not forced.
    """
    rows = []
    ok = True
    for name, table, expected_q, expected_n in NAMED:
        r = inertia_signature(table)
        agree = (tuple(r["signature"]) == expected_q
                 and tuple(r["norm_signature"]) == expected_n)
        oracle = oracle_signature(table)
        oracle_agree = tuple(r["signature"]) == oracle
        witness_ok = True
        if r["witness"] is not None:
            witness_ok = full_product(table, r["witness"], r["witness"])[0] < 0
        ok = ok and agree and oracle_agree and witness_ok
        rows.append({
            "algebra": name, "dim": r["dim"],
            "trace_signature": list(r["signature"]),
            "norm_signature": list(r["norm_signature"]),
            "expected_trace": list(expected_q),
            "expected_norm": list(expected_n),
            "has_negative_direction": r["has_negative_direction"],
            "witness": r["witness"],
            "witness_real_square": r["witness_real_square"],
            "witness_square": r["witness_square"],
            "witness_certifies_nonorderable":
                r["witness_certifies_nonorderable"],
            "n_minus_equals_dim_minus_1": r["n_minus"] == r["dim"] - 1,
            "oracle": list(oracle), "oracle_agrees": oracle_agree,
            "witness_verified": witness_ok,
        })
    return {
        "control": "ladder_and_split_peers", "ok": ok, "rows": rows,
        "note": ("BOTH forms reported. The literature quotes split-O as (4,4) "
                 "— that is the NORM form; the TRACE form answers (5,3,0). On "
                 "the shipped ladder n_minus == dim-1 exactly, so those rows "
                 "are DEFINITIONAL."),
    }


def control_c4_ceiling(count, seed):
    """C4 — the family the op provably CANNOT separate from 𝕆, measured.

    Re(x·x) = Σ ε_i x_i² exactly when the off-diagonal real parts vanish. Pin
    the diagonal to 𝕆's and scramble the off-diagonal among the IMAGINARY
    directions: every such table answers (1,7,0) while being non-associative.
    Let the scramble reach e₀ and the real parts no longer cancel, at which
    point the op DOES separate part of the family — so the precise scope is
    "reads exactly the symmetric part of the real slice c_ij0 + c_ji0".
    """
    octonion = tuple(inertia_signature(cd_table(8, [-1, -1, -1]))["signature"])
    rng = random.Random(seed)
    identical_null = 0
    non_associative = 0
    for _ in range(count):
        table = diagonal_pinned_table(8, rng)
        if tuple(inertia_signature(table)["signature"]) == octonion:
            identical_null += 1
        non_associative += 0 if is_associative(table) else 1
    rng = random.Random(seed)
    identical_real = 0
    for _ in range(count):
        table = diagonal_pinned_table(8, rng, allow_real_offdiagonal=True)
        if tuple(inertia_signature(table)["signature"]) == octonion:
            identical_real += 1
    return {
        "control": "C4_measured_ceiling",
        "ok": identical_null == count and non_associative == count,
        "count": count, "seed": seed,
        "octonion_signature": list(octonion),
        "null_offdiagonal_identical_to_octonion": identical_null,
        "null_offdiagonal_non_associative": non_associative,
        "real_offdiagonal_identical_to_octonion": identical_real,
        "note": ("The op CANNOT separate the null-real-off-diagonal family "
                 "from O (%d/%d identical, %d/%d non-associative), so it "
                 "certifies nothing about associativity, alternativity, "
                 "composition or division. It is not blind to the off-diagonal "
                 "REAL slice though: %d/%d when the scramble may reach e0."
                 % (identical_null, count, non_associative, count,
                    identical_real, count)),
    }


def control_c6_open_gap():
    """C6 — the REUSE check, and the gap it leaves OPEN.

    The prescribed repair for the split-ℂ false negative was "test isotropy /
    zero divisors of the norm, to separate split-ℂ from ℚ(√2)". Measured, it
    does not work at this resolution, and neither shipped op can be reused:

      * norm_signature: split-ℂ and ℚ(√2) are IDENTICAL in both forms. A
        signature is a REAL-PLACE statement and a² − 2b² is isotropic over ℝ
        while anisotropic over ℚ.
      * cd_norm_sq: the COORDINATE form Σxᵢ². It reports N([1,−1]) = 2 for a
        genuine null vector of the split norm, so reusing it would reproduce
        the input-blind substitution this rc exists to avoid.
      * sedenion_zero_divisor_witness: takes no dim argument — sedenion-only.

    Separating them needs a RATIONAL zero of the norm form. Not shipped.
    """
    from srmech.amsc.cascade import cd_norm_sq  # the SHIPPED coordinate norm
    import inspect
    split_c = cd_table(2, [+1])
    q_sqrt2 = [[[1, 0], [0, 1]], [[0, 1], [2, 0]]]
    a = inertia_signature(split_c)
    b = inertia_signature(q_sqrt2)
    indistinguishable = (tuple(a["signature"]) == tuple(b["signature"])
                         and tuple(a["norm_signature"]) == tuple(
                             b["norm_signature"]))
    return {
        "control": "C6_reuse_check_and_open_gap",
        "ok": True,                      # a measurement, not a pass/fail gate
        "split_complex": {"trace": list(a["signature"]),
                          "norm": list(a["norm_signature"])},
        "q_sqrt2": {"trace": list(b["signature"]),
                    "norm": list(b["norm_signature"])},
        "signature_separates_them": not indistinguishable,
        "split_complex_rational_null_vector": [1, -1],
        "split_complex_null_product": full_product(split_c, [1, 1], [1, -1]),
        "cd_norm_sq_on_that_null_vector": int(cd_norm_sq([1, -1])),
        "sedenion_witness_parameters": list(
            inspect.signature(
                __import__("srmech.amsc.cascade.cayley_dickson",
                           fromlist=["x"]).sedenion_zero_divisor_witness
            ).parameters),
        "note": ("OPEN GAP, stated rather than closed: the signature does NOT "
                 "separate split-C (zero divisors) from Q(sqrt2) (a genuinely "
                 "ordered field) — identical in BOTH forms. cd_norm_sq is the "
                 "coordinate form and cannot test split isotropy; "
                 "sedenion_zero_divisor_witness takes no dim. A rational zero "
                 "of the norm form would be needed, and is not shipped."),
    }


def control_c7_order_senses(count, seed):
    """C7 — "ordered" does THREE jobs; this op reads the FIELD one.

    Measured on srmech's OWN shipped ops (cd_add / cd_mult / cd_norm_sq), so
    the claim is about the shipped surface and not about hand-rolled algebra.
    """
    from srmech.amsc.cascade import cd_add, cd_mult, cd_norm_sq
    rng = random.Random(seed)
    add_ok = add_total = 0
    mul_ok = mul_total = 0
    norm_ok = 0
    for _ in range(count):
        x = [rng.randint(-4, 4) for _ in range(2)]
        y = [rng.randint(-4, 4) for _ in range(2)]
        z = [rng.randint(-4, 4) for _ in range(2)]
        if tuple(x) < tuple(y):
            add_total += 1
            add_ok += 1 if (tuple(int(v) for v in cd_add(x, z))
                            < tuple(int(v) for v in cd_add(y, z))) else 0
        if tuple(x) > (0, 0) and tuple(y) > (0, 0):
            mul_total += 1
            mul_ok += 1 if tuple(int(v) for v in cd_mult(x, y)) > (0, 0) else 0
        norm_ok += 1 if (int(cd_norm_sq(cd_mult(x, y)))
                         == int(cd_norm_sq(x)) * int(cd_norm_sq(y))) else 0
    return {
        "control": "C7_which_sense_of_ordered",
        "ok": add_ok == add_total and mul_ok < mul_total,
        "count": count, "seed": seed,
        "lex_order_compatible_with_cd_add": [add_ok, add_total],
        "lex_order_compatible_with_cd_mult": [mul_ok, mul_total],
        "cd_norm_sq_multiplicative": [norm_ok, count],
        "op_reports_order_sense": inertia_signature(
            cd_table(2, [-1]))["order_sense"],
        "note": ("C IS orderable as a SET (trivially) and as an ADDITIVE GROUP "
                 "(measured on cd_add); cd_norm_sq is multiplicative but not a "
                 "TOTAL order (ties are chirality orbits). It fails only as a "
                 "FIELD — (0,1)*(0,1) = (-1,0). The op reads the FIELD sense "
                 "and says so in its payload."),
    }


def control_c5_coordinate_form(count, seed):
    """C5 — why Re(x·x) is never taken as the coordinate form a² − |v|².

    The substitution is INPUT-BLIND. On split-𝕆 the two disagree on almost
    every probe, and the disagreement is not a precision artefact: both sides
    are exact integers here.
    """
    split = cd_table(8, [-1, -1, +1])
    plain = cd_table(8, [-1, -1, -1])
    rng = random.Random(seed)
    agree_plain = 0
    agree_split = 0
    for _ in range(count):
        x = [rng.randint(-4, 4) for _ in range(8)]
        coord = x[0] * x[0] - sum(v * v for v in x[1:])
        agree_plain += 1 if full_product(plain, x, x)[0] == coord else 0
        agree_split += 1 if full_product(split, x, x)[0] == coord else 0
    return {
        "control": "C5_coordinate_form_is_input_blind",
        "ok": agree_plain == count and agree_split < count,
        "count": count, "seed": seed,
        "coordinate_form_agrees_on_octonion": agree_plain,
        "coordinate_form_agrees_on_split_octonion": agree_split,
        "note": ("a² − |v|² matches the true Re(x·x) on O but not on split-O, "
                 "at exact integer precision — a SUBSTITUTION error, not a "
                 "precision one. The op sums Re(x·x) from the structure "
                 "constants and never uses the coordinate form."),
    }


def control_c1_separation():
    """C1 — the pass condition. 𝕆 / split-𝕆 / random must be THREE answers."""
    rng = random.Random(20260727)
    octonion = cd_table(8, [-1, -1, -1])
    split = cd_table(8, [-1, -1, +1])
    rand = random_monomial_table(8, rng)
    answers = {
        "octonion": tuple(inertia_signature(octonion)["signature"]),
        "split_octonion": tuple(inertia_signature(split)["signature"]),
        "random": tuple(inertia_signature(rand)["signature"]),
    }
    squares = [split[i][i][0] for i in range(8)]
    return {
        "control": "C1_split_octonion_separation",
        "ok": (len(set(answers.values())) == 3
               and answers["octonion"] == (1, 7, 0)
               and answers["split_octonion"] == (5, 3, 0)),
        "answers": {k: list(v) for k, v in answers.items()},
        "distinct_answers": len(set(answers.values())),
        "split_basis_squares": squares,
        "split_imaginary_plus_one": squares[1:].count(1),
        "split_imaginary_minus_one": squares[1:].count(-1),
        "shipped_octonion_table_agrees":
            tuple(inertia_signature(octonion_mult_table())["signature"]) == (1, 7, 0),
        "shipped_quaternion_table_agrees":
            tuple(inertia_signature(quaternion_mult_table())["signature"]) == (1, 3, 0),
    }


def control_c2_random(kind, dim, count, seed):
    """C2 — random structure-constant tables of matched shape."""
    rng = random.Random(seed)
    build = (random_monomial_table if kind == "monomial"
             else random_general_table)
    signatures = {}
    witness_failures = 0
    oracle_failures = 0
    started = time.time()
    for _ in range(count):
        table = build(dim, rng)
        r = inertia_signature(table)
        key = tuple(r["signature"])
        signatures[key] = signatures.get(key, 0) + 1
        if sum(key) != dim:
            witness_failures += 1
        if r["witness"] is None:
            if r["n_minus"] != 0:
                witness_failures += 1
        elif full_product(table, r["witness"], r["witness"])[0] >= 0:
            witness_failures += 1
        if key != oracle_signature(table):
            oracle_failures += 1
    return {
        "control": "C2_random_%s_tables" % kind,
        "ok": witness_failures == 0 and oracle_failures == 0,
        "kind": kind, "dim": dim, "count": count, "seed": seed,
        "distinct_signatures": len(signatures),
        "witness_verification_failures": witness_failures,
        "oracle_disagreements": oracle_failures,
        "octonion_signature_seen": signatures.get((1, 7, 0), 0),
        "split_octonion_signature_seen": signatures.get((5, 3, 0), 0),
        "signature_census": sorted(
            ([list(k), v] for k, v in signatures.items()),
            key=lambda kv: -kv[1]),
        "seconds": round(time.time() - started, 3),
    }


def control_c3_no_negative_direction():
    """C3 — the instrument CAN return "none", and not by reading the dim.

    AND the correction that matters most: "no negative direction" is NOT
    "orderable". split-ℂ answers (2,0,0) yet (1+j)(1−j) = 0 with both factors
    nonzero, so it carries no compatible total order. The op therefore emits
    no orderability key at all.
    """
    split = cd_table(2, [+1])
    real = inertia_signature(cd_table(1, []))
    split_c = inertia_signature(split)
    plain_c = inertia_signature(cd_table(2, [-1]))
    zero_divisor = full_product(split, [1, 1], [1, -1])
    return {
        "control": "C3_no_negative_direction_control",
        "ok": (not real["has_negative_direction"] and real["witness"] is None
               and not split_c["has_negative_direction"]
               and plain_c["has_negative_direction"]
               and "ordered" not in split_c
               and not any(zero_divisor)),
        "real": {"dim": real["dim"], "signature": list(real["signature"]),
                 "has_negative_direction": real["has_negative_direction"],
                 "witness": real["witness"]},
        "split_complex": {
            "dim": split_c["dim"], "signature": list(split_c["signature"]),
            "has_negative_direction": split_c["has_negative_direction"],
            "witness": split_c["witness"]},
        "complex": {"dim": plain_c["dim"],
                    "signature": list(plain_c["signature"]),
                    "has_negative_direction": plain_c["has_negative_direction"],
                    "witness": plain_c["witness"]},
        "split_complex_zero_divisor": {
            "x": [1, 1], "y": [1, -1], "product": zero_divisor},
        "emits_an_orderability_key": "ordered" in split_c,
        "note": ("split-ℂ and ℂ share dim 2 and answer oppositely, so the "
                 "answer cannot come from the dimension. But (1+j)(1−j) = 0 "
                 "with both factors nonzero, so split-ℂ is provably NOT "
                 "orderable while showing no negative direction — reading "
                 "n_minus == 0 as 'ORDERED' would be a FALSE NEGATIVE one rung "
                 "above R. The op emits no such key."),
    }


def control_c_parity(count, seed):
    """C/Python parity in BOTH forms, on the SPLIT algebras too.

    Per ADR-0009 the capability is the invariant across projections, so the
    differential deliberately includes the split algebras, the degenerate one
    and the diagonal-pinned ceiling family — not only the shipped ladder, where
    the answer is forced and agreement proves little.
    """
    from srmech.amsc.cascade import cayley_dickson as cd_mod
    have_native = (_native.HAS_NATIVE and _native.LIB is not None
                   and hasattr(_native.LIB,
                               "srmech_algebra_inertia_signature"))
    if not have_native:
        return {"control": "c_python_parity", "ok": True, "skipped": True,
                "reason": "no libsrmech with the rc349 symbol"}
    rng = random.Random(seed)
    checked = 0
    declined = 0
    mismatches = 0
    split_checked = 0
    named = [(n, t) for n, t, _, _ in NAMED]
    tables = list(named)
    tables += [("random_monomial", random_monomial_table(8, rng))
               for _ in range(count)]
    tables += [("random_general", random_general_table(6, rng))
               for _ in range(count)]
    tables += [("diagonal_pinned", diagonal_pinned_table(8, rng))
               for _ in range(count)]
    for form in ("trace", "norm"):
        for name, table in tables:
            tbl = cd_mod._structure_table(table)
            native = cd_mod._native_inertia(tbl, form)
            pure = cd_mod._congruence_inertia(cd_mod._real_gram(tbl, form))
            if native is None:
                declined += 1
                continue
            checked += 1
            if name.startswith("split"):
                split_checked += 1
            nw = cd_mod._primitive(list(native[3])) if native[3] else None
            pw = cd_mod._primitive(list(pure[3])) if pure[3] else None
            if tuple(native[:3]) != tuple(pure[:3]) or nw != pw:
                mismatches += 1
    return {"control": "c_python_parity", "ok": mismatches == 0,
            "checked": checked, "native_declined": declined,
            "split_algebra_checks": split_checked,
            "forms": ["trace", "norm"],
            "mismatches": mismatches}


def main() -> int:
    print("srmech %s from %s" % (srmech.__version__, srmech.__file__),
          file=sys.stderr)
    print("HAS_NATIVE=%s" % _native.HAS_NATIVE, file=sys.stderr)
    records = [
        control_ladder(),
        control_c1_separation(),
        control_c2_random("monomial", 8, 120, 4242),
        control_c2_random("general", 6, 120, 31337),
        control_c3_no_negative_direction(),
        control_c4_ceiling(200, 8675309),
        control_c5_coordinate_form(4000, 271828),
        control_c6_open_gap(),
        control_c7_order_senses(2000, 1618),
        control_c_parity(100, 11235),
    ]
    all_ok = True
    for rec in records:
        all_ok = all_ok and rec["ok"]
        print(json.dumps(rec, sort_keys=True), flush=True)
        print("  %-34s %s" % (rec["control"], "OK" if rec["ok"] else "FAILED"),
              file=sys.stderr, flush=True)
    print("ALL CONTROLS OK" if all_ok else "CONTROL FAILURES PRESENT",
          file=sys.stderr)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
