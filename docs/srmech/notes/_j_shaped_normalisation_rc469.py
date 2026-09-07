"""rc469 (`#T1188`) — the generating code for every number the NORMALISATION
row of ``notes/continuous_math_as_14_class_cascade.md`` quotes.

Per the computational-provenance discipline: a load-bearing number in shipped
prose ships with the code that produced it. The row this file backs makes four
claims, and each one is an EXECUTION here rather than an argument:

  A  the `sqrt` row's own op does NOT answer the question the table was read as
     answering. ``asymptotic_calculus.sqrt`` (= ``srmech.math.rational.sqrt``)
     is the APPROXIMATING Newton path: it returns a ``Q``, and that ``Q``
     squared is not the operand. So the table DID have a row for √ and the row
     MASKED the question rather than answering it.
  B  exact normalisation already ships, privately, twice —
     ``srmech.math.qalg._exact_axis`` for the rational part and ``_inv_sqrt_k``
     for the irrational one — and when ``‖v‖²`` is a rational SQUARE the unit
     vector never leaves ℚ at all. It REFUSES rather than rounding otherwise.
  C  the ``{1, 3, 7}`` restriction is a TABLE limit, not a CARRIER limit:
     √2 is constructed exactly three functions away from where ``_exact_axis``
     refuses a direction for needing it, and ``_inv_sqrt_k``'s k=7 Gauss-sum
     loop runs unchanged for every odd prime tried.
  D  what genuinely does NOT ship is the COMPOSITUM. ``Qalg`` is a SIMPLE
     extension with a ``_same_field`` guard, so two individually-exact unit
     vectors over ``t²−2`` and ``t²−5`` cannot be combined: ONE vector
     normalises, an ORTHONORMAL BASIS does not.

Run (WSL2, numpy-absent)::

    cd docs/srmech/python
    python3 ../notes/_j_shaped_normalisation_rc469.py

It writes ``_j_shaped_normalisation_rc469.ndjson`` beside itself (one record
per claim) and prints the same records. MEASURED at srmech 0.9.0rc469:

  A  ``sqrt(Q(2,1))`` returns ``Q``; ``r*r == Q(2,1)`` is **False**; the
     residue is ``-3292739303401103/81129638414606681695789005144064``.
  B  ``(0,3,4,0)`` → ``k = 1`` and unit weights ``['0','3/5','4/5','0']`` —
     exactly rational, no extension at all, because ``‖v‖² = 25`` is a square.
     ``(0,1,1,1)`` → ``k = 3``; ``(0,1,…,1)`` (8-wide) → ``k = 7``.
     ``(0,1,2,0)`` (``‖v‖² = 5``) and ``(0,1,1,0)`` (``‖v‖² = 2``) → ``None``.
  C  ``(2·cos(2π/8))² == 2`` exactly, on the shipped
     ``qalg.cos_sin_2pi_k_over_n``. The quadratic Gauss sum ``g`` satisfies
     ``g² == p`` for **p = 3, 5, 7, 11, 13, 17, 19, 23** — eight for eight,
     the k=7 loop body unchanged but for the modulus.
  D  ``(1/√2 over Φ₈) * (1/√5 over Φ₅)`` raises ``ValueError: Qalg binary op
     requires equal m``.

WHY THE ROW IS **J-SHAPED**, which is the point the numbers are here to
support. Trig and calculus are N-shaped — one carrier, one dial, converging;
``sin_series_truncate(1, 2, 8)`` returns the EXACT value of the truncation and
``num_terms`` is a precision knob. ``‖v‖`` has no such knob: it is a ROOT OF A
POLYNOMIAL, and its discrete form is a CARRIER ELECTION — factor
``‖v‖² = k·t²`` with ``t`` rational and ``k`` squarefree (Class J), keep ``t``
on ℚ, adjoin only ``√k``. Anyone hunting for the missing row was looking for an
N-shaped op with a precision knob, and there is none to find.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Prepend the package root explicitly: an empty `srmech` namespace directory in
# site-packages otherwise shadows the tree and `srmech.math` vanishes.
_PY = Path(__file__).resolve().parents[1] / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech                                                    # noqa: E402
from srmech.math.q import Q                                      # noqa: E402
from srmech.math import qalg as _qalg                            # noqa: E402
from srmech.math.qalg import Qalg, cos_sin_2pi_k_over_n          # noqa: E402
import srmech.asymptotic_calculus as calculus                    # noqa: E402

_OUT = Path(__file__).resolve().with_suffix(".ndjson")


def _axis(vec):
    """``_exact_axis`` on an integer tuple, rendered for the record."""
    got = _qalg._exact_axis([Q(c, 1) for c in vec])
    if got is None:
        return None
    weights, k = got
    return {"unit_weights": [str(w) for w in weights], "axis_k": k}


def main() -> int:
    records = []

    def rec(**kw):
        kw["srmech_version"] = srmech.__version__
        records.append(kw)
        print(json.dumps(kw, sort_keys=True))

    # ── A. the sqrt row MASKED the question ───────────────────────────
    r = calculus.sqrt(Q(2, 1))
    rec(claim="A_sqrt_row_is_the_approximating_newton_path",
        op="srmech.asymptotic_calculus.sqrt",
        aliases_module=calculus.sqrt.__module__,
        operand="Q(2,1)",
        returned_carrier=type(r).__name__,
        squares_back_to_operand=bool(r * r == Q(2, 1)),
        residue=str(r * r - Q(2, 1)))

    # ── B. exact normalisation already ships, privately ───────────────
    for vec, why in (
            ((0, 3, 4, 0), "norm_sq 25 is a rational SQUARE: never leaves Q"),
            ((0, 1, 1, 1), "the quaternion body diagonal, norm_sq 3"),
            ((0, 1, 1, 1, 1, 1, 1, 1), "the equal-weight octonion axis, norm_sq 7"),
            ((0, 1, 2, 0), "norm_sq 5 -> REFUSES, does not round"),
            ((0, 1, 1, 0), "norm_sq 2 -> REFUSES, does not round"),
    ):
        rec(claim="B_exact_axis",
            op="srmech.math.qalg._exact_axis",
            weights=list(vec),
            norm_sq=sum(c * c for c in vec),
            result=_axis(vec),
            note=why)

    # ── C. {1,3,7} is a TABLE limit, not a CARRIER limit ──────────────
    cos8, _sin8 = cos_sin_2pi_k_over_n(8)
    two_cos = cos8 + cos8                       # 2·cos(2π/8) = √2
    rec(claim="C_sqrt2_is_exactly_constructible_on_a_shipped_op",
        op="srmech.math.qalg.cos_sin_2pi_k_over_n",
        expression="(2*cos_sin_2pi_k_over_n(8)[0])**2",
        equals_two=bool(two_cos * two_cos == Q(2, 1)),
        note="_exact_axis REFUSES (0,1,1,0) for needing exactly this value")

    gauss = {}
    for p in (3, 5, 7, 11, 13, 17, 19, 23):
        index = 4 * p                            # p | index and 4 | index
        omega = Qalg.alpha(_qalg._cyclotomic_m(index))
        zp = omega ** (index // p)
        squares = {(a * a) % p for a in range(1, p)}
        root = None
        for a in range(1, p):                    # Class J: the Legendre sum
            term = zp ** a
            term = term if a in squares else -term   # Class K sign, not abs
            root = term if root is None else root + term
        if p % 4 == 3:
            root = root * (omega ** (index // 4)).inverse()   # g/i
        gauss[p] = bool((root * root).as_rational() == Q(p, 1))
    rec(claim="C_inv_sqrt_k_gauss_loop_generalises_unchanged",
        op="srmech.math.qalg._inv_sqrt_k (k=7 body, modulus varied)",
        g_squared_equals_p=gauss,
        all_hold=all(gauss.values()),
        note="the {1,3,7} restriction is a TABLE limit; DELIBERATELY not widened "
             "in rc469 — reachable is not the same as wanted")

    # ── D. the COMPOSITUM is what genuinely does not ship ─────────────
    w8 = Qalg.alpha(_qalg._cyclotomic_m(8))
    root2 = w8 + w8.inverse()                    # √2 over Φ₈
    w5 = Qalg.alpha(_qalg._cyclotomic_m(5))
    root5 = None
    for a in range(1, 5):                        # √5 over Φ₅, same Gauss sum
        term = w5 ** a
        term = term if a in {1, 4} else -term
        root5 = term if root5 is None else root5 + term
    try:
        root2.inverse() * root5.inverse()
        raised = None
    except ValueError as exc:
        raised = f"{type(exc).__name__}: {exc}"
    rec(claim="D_compositum_is_absent_one_vector_normalises_a_basis_does_not",
        carrier="srmech.math.qalg.Qalg",
        root2_squares_to=str((root2 * root2).as_rational()),
        root5_squares_to=str((root5 * root5).as_rational()),
        cross_field_product=raised,
        note="Qalg is a SIMPLE extension with a _same_field guard; the compositum "
             "needs primitive_element / minimal_polynomial in srmech.math.poly "
             "(Poly.resultant, the hard part, already ships). FILED, not built.")

    _OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                            for r in records), encoding="utf-8", newline="\n")
    print(f"\nwrote {_OUT} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
