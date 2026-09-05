"""Class K ∘ L — signed-sum coupling score + the resonant-spectrum closure +
the fractal-spectrum (self-similar) dual.

Three coupling-cascade ops live here:

``signed_sum_squared(sources)``: per-element ``(Σ_sources (2·bit − 1))²`` — the
Class-K bipolar sign-projection ∘ Class-L signed-magnitude-square (a *stack* of
bit-arrays → a coupling-strength score).

``fractal_spectrum(R, branches, *, log_terms)``: the **Ch-2 (quasi-periodic /
fractal) DUAL** of ``resonant_spectrum``. Where ``resonant_spectrum(L)`` reads a
symmetric Laplacian's FLAT eigenspectrum (one eigensolve), ``fractal_spectrum``
reads a self-similar lattice's **SPECTRAL-DECIMATION** structure: the spectrum is
the ITERATED PREIMAGE of the renormalization :class:`~srmech.math.poly.Poly`
``R`` (the decimation map), NOT a flat list. Grounded on the Sierpinski gasket
— on the NORMALIZED Laplacian the decimation is exactly ``R(z)=z(5−4z)``
(measured; Rammal 1984 / Fukushima–Shima 1992). It reads the exact scale
``R'(0)``, the fracton (spectral) dimension ``d_s = 2·log(branches)/log(scale)``
(Class-N), the F974 bit-exact ``|q|``-meter octaves-per-level, and names the full
spectrum (the Julia set of ``R``) the honest operand-IRREPRESENTABLE OPEN. Pure
orchestration over already-C-backed ops (``Poly.derivative`` / ``.eval`` +
Class-N ``log`` / ``best_rational``) — no new numerical kernel, so it ships
**non_compute** (no dedicated C peer; the ``from_bodies`` / ``cooccurrence_edges``
precedent).

``resonant_spectrum(L, *, orders, max_den)``: the **spectral row of the
closure-dispatch** (UPSTREAM §75 / F928). It reads a real-symmetric coupling
Laplacian ``L`` as a *stored* (excitation-free) object:

* its **eigenvalues** (ascending) are the stored **"dark" tension spectrum** —
  the MFO **field** (the composition that exists with *no* pluck/excitation,
  F907). A single driven eigenmode is the **excitation** (matter).
* its **eigenvectors** (columns) are the **excitation modes**.
* the **force-orders** ``[L, L², …, Lᵒ]`` are forces-of-forces — ``L²`` is the
  **biharmonic / tidal** concentration (4th-order dispersive curvature, NOT the
  2nd-order matter curvature). On the DEFAULT (float) route each
  ``Lᵏ = V·diag(Λᵏ)·Vᵀ`` is reconstructed in the eigenbasis from **one**
  eigensolve (Λ raised to ``k``), never by repeated ``L``-matmuls. The
  ``exact=True`` route (rc467, `#T1188`) CANNOT take that reconstruction —
  ``V·diag(Λᵏ)·Vᵀ`` is the cross-field product the ``singular_values_exact``
  precedent refuses — so it takes ``QMat`` matmul powers of the OPERAND
  instead, and says so in the op's Accuracy paragraph.
* the **resonances** are integer/prime ratios of the tensions: each adjacent
  nonzero-tension ratio is read with Class-N :func:`best_rational`, and the
  resulting denominator is prime-coordinate-factorised (Class-J
  :func:`srmech.math.primes.factor` / :class:`srmech.math.qprime.Qprime`) —
  a **small-prime / 2-adic** denominator is a resonance **LOCK** (the Laplace
  ladder), a **large-prime** denominator is **libration** (off-lock).

Every Class-L coupling cascade reduces to these same steps — the op is the
named closure so a coupling read is the default and a hand-rolled eigensolve
the exception.

Pure cascade discipline (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``
+ ``[[feedback_numpy_free_means_zero_numpy_no_bridges]]``): no ``abs()`` (the
sign of a tension is read by comparison, Class-K), no ``import math`` / numpy
(the ``Mat`` / ``Vec`` carriers are float64 by design — the eigensolve IS a
float algorithm — and the rational reading is exact integer arithmetic).

Canonical SSoT:

* the bipolar / spatter-code convention — Kanerva (2009) *Hyperdimensional
  Computing*, Cognitive Computation 1, 139.
* symmetric eigendecomposition — Golub & Van Loan, *Matrix Computations*
  (4th ed., Johns Hopkins, 2013) §8.3 (the symmetric eigenproblem).
* the orbital-resonance / Laplace-lock framing — Murray & Dermott,
  *Solar System Dynamics* (Cambridge, 1999) §8 (resonance & libration).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..math.q import Q  # rc100: the exact-ℚ scalar carrier (fractal_spectrum scale / |q|-meter)
from ..math.rational import sqrt as _rsqrt  # Class-N∘K integer-isqrt root (no libm / no float_pow)
from ..math.vec import Vec  # rc129: the numpy-free 1-D carrier (restores .shape)


def signed_sum_squared(sources: Sequence) -> "Vec":
    """Squared signed-sum coupling score across a stack of bit-arrays.

    Args:
        sources: A non-empty sequence of equal-length 1-D sequences, each
            holding bits in ``{0, 1}``.

    Returns:
        A real :class:`~srmech.math.vec.Vec` (same length as each source;
        ``.shape == (n,)`` + scalar ``v[i]``) — per position,
        ``(Σ_sources (2·bit − 1))²`` — the squared signed-sum, i.e. the
        Class-L magnitude-square of the Class-K bipolar-projected sum.
        Range ``[0, n_sources²]``; ``n_sources²`` = full agreement,
        ``0`` = balanced (equal +1 / −1 across sources). rc129: the carrier is
        a ``Vec``, NOT a bare ``list[int]`` — the small non-negative integer
        scores are exact as float64 doubles (well within the 2⁵³ exact-integer
        range; the buffer carries them losslessly).

    Raises:
        ValueError: empty ``sources``, mismatched lengths, or values
            outside ``{0, 1}``.
    """
    # rc154 (BATCH B10, ``composition_of_c``): this is a pure **Class-K** bipolar
    # sign-projection (``2·bit − 1``) ∘ **Class-L** signed-magnitude-square
    # composition over integer bit-stacks — NOT an irreducible Python kernel. It
    # reaches no non-standalone-ready leaf (all integer arithmetic, no libm, no
    # ``abs()``), so it is trivially C-portable / standalone-ready — the SAME
    # classification as the ``cascade.compose.signed_sum_squared`` twin and the
    # ``mat_dot`` pure-reduction. Value-verified against the exact reference; no
    # new C symbol (the Class-K / Class-L primitives are the C-backed ones).
    if len(sources) == 0:
        raise ValueError(
            "coupling.signed_sum_squared: requires at least one source"
        )
    arrs = [[int(x) for x in s] for s in sources]
    n = len(arrs[0])
    if n == 0:
        raise ValueError("coupling.signed_sum_squared: sources must be non-empty")
    for i, a in enumerate(arrs):
        if len(a) != n:
            raise ValueError(
                f"coupling.signed_sum_squared: source {i} length {len(a)} "
                f"!= {n}"
            )
        for v in a:
            if v not in (0, 1):
                raise ValueError(
                    f"coupling.signed_sum_squared: source {i} must hold bits "
                    f"in {{0, 1}}"
                )
    out: List[int] = []
    for pos in range(n):
        # Class K — bipolar sign-projection {0,1} -> {-1,+1}; sum across sources.
        signed_sum = 0
        for a in arrs:
            signed_sum += 2 * a[pos] - 1
        # Class L — signed-magnitude-squared (no abs(); the square is sign-agnostic).
        out.append(signed_sum * signed_sum)
    # rc129: return the numpy-free 1-D Vec carrier (the small ints are exact as
    # doubles). Iterating it yields scalars; v.tolist() recovers the int values.
    return Vec.from_sequence(out, is_complex=False)


# =====================================================================
# §75 — the resonant-spectrum closure ("the coupling the_one").
# =====================================================================

# The smallest-tension scale below which an eigenvalue is treated as a free /
# bulk (zero) mode, relative to the largest tension. A connected Laplacian has
# exactly one exact-zero mode (the constant vector); float Jacobi puts it at
# ~1e-16·λ_max, so this floor cleanly separates "stored tension" from "free".
_ZERO_TENSION_REL: float = 1e-9

# Scale used to turn a float tension-ratio in (0, 1] into an integer pair for
# the exact Class-N best_rational read. 1e6 resolves a ratio to 6 decimals —
# ample for reading a small-integer lock (4:2:1) vs an off-lock libration.
_RATIO_SCALE: int = 1_000_000


def _tension_is_locked(den_coords: Dict[int, int], *, max_den: int) -> bool:
    """Class-J lock test on a resonance denominator's prime-coordinates.

    A resonance is **LOCKED** when its reduced denominator is **smooth** —
    built only from small primes (≤ a 2-adic-ladder cutoff) — so the ratio sits
    on the integer / 2-adic Laplace ladder. A denominator carrying a **large**
    prime factor (close to ``max_den``) is **libration** (off-lock): the ratio
    is "almost rational" only because the large prime let ``best_rational`` fit
    it, not because it locks.

    The cutoff is the integer square root of ``max_den`` (so e.g. ``max_den=64``
    locks denominators whose every prime is ≤ 8 — i.e. 2, 3, 5, 7 — and calls a
    denominator divisible by 11/13/… a libration). Computed by a pure-integer
    cascade (no ``math.isqrt`` import; ``[[feedback_missing_math_is_added_to_
    srmech_as_cascade_never_imported]]``).
    """
    # Integer sqrt(max_den) by Newton's cascade (pure int; no libm import).
    if max_den < 2:
        cutoff = max_den
    else:
        x = max_den
        y = (x + 1) // 2
        while y < x:
            x = y
            y = (x + max_den // x) // 2
        cutoff = x
    if not den_coords:
        return True  # denominator 1 (the empty product) — an exact integer lock.
    largest_prime = max(den_coords.keys())
    return largest_prime <= cutoff


def _resonances_from_tensions(lam: List[float], max_den: int) -> List[Dict[str, object]]:
    """Adjacent-nonzero-tension resonance read — Class-N ``best_rational`` +
    Class-J prime-coordinate factorisation + the lock/libration verdict.

    ``lam`` is an ASCENDING float tension list; each adjacent nonzero-tension
    ratio (smaller/larger ∈ (0, 1]) is read with :func:`best_rational` and its
    denominator prime-factored, a smooth/2-adic denominator being a resonance
    LOCK and a large-prime denominator a libration (:func:`_tension_is_locked`).
    This is the EXACT logic :func:`resonant_spectrum` uses — factored out so
    :func:`resonant_spectrum_sparse` REUSES the lock/libration read rather than
    reinventing it (both call this one helper, so the verdicts are identical on
    the same tension values). The zero-mode floor is read relative to
    ``lam[-1]`` (the largest tension in the passed list), so a k-extreme list
    that includes the global-max tension floors the same way the full spectrum
    does. No ``abs()`` (signs are read by comparison, Class-K)."""
    from ..math import primes as _primes
    from ..math import rational as _rational

    resonances: List[Dict[str, object]] = []
    n = len(lam)
    if n == 0:
        return resonances
    nz = [i for i in range(n) if lam[i] > lam[-1] * _ZERO_TENSION_REL]
    for a, b in zip(nz, nz[1:]):
        lo, hi = lam[a], lam[b]  # ascending ⇒ lo ≤ hi, both > 0
        num_in = int(round((lo / hi) * _RATIO_SCALE))
        num, den = _rational.best_rational(num_in, _RATIO_SCALE, max_den)
        den_coords = {p: e for p, e in _primes.factor(den)} if den > 1 else {}
        resonances.append({
            "pair": (a, b),
            "ratio": (num, den),
            "den_coords": den_coords,
            "locked": _tension_is_locked(den_coords, max_den=max_den),
        })
    return resonances


# ── the EXACT route (rc467, `#T1188`) — four faculties, four shipped ops ─────
#
# The rc466 census left ONE undeclared silent demoter: resonant_spectrum::L.
# It was deferred as "exact peer ships, deferred" on the grounds that the modes
# faculty "needs eigvec_exact with a caller-supplied IRREDUCIBLE minimal
# polynomial per eigenvalue". That was already false when it was written —
# ``eig_exact`` supplies the irreducible minimal polynomial ITSELF and returns
# ``vectors_qalg`` — and the ``_symmetric_eig_exact`` wrapper landed one commit
# later. Every faculty below is composed from an op that already ships:
#
#   tensions      laplacian._symmetric_eig_exact  -> list[Qalg], ascending
#   modes         the SAME call's Qalg columns    -> list[list[Qalg]]
#   force_orders  QMat.matmul powers of L         -> list[QMat] (entries plain Q)
#   resonances    matrix_cascades.eigvals_exact(return_intervals=True)
#                 + rational.best_rational on BOTH enclosure endpoints
#
# NO cross-field number is ever formed, which is why the SVE precedent — the
# ``singular_values_exact`` refusal to return a combined ``U·Σ·Vᵀ`` because
# assembling ACROSS the per-value fields needs a compositum — does not apply
# here: ``tensions`` is a LIST of per-field ``Qalg`` (never combined), ``modes``
# is per-COLUMN over its own eigenvalue's field, ``force_orders`` lives entirely
# in ``ℚ`` (no field at all), and the resonance read touches only the RATIONAL
# bracket endpoints. The combined dict is returned and the fields are declared
# per column.


def _exact_rows(L) -> List[list]:
    """The RAW rows of ``L``, before any float-carrier coercion.

    ``QMat`` (the exact carrier) via ``.to_lists()``; ``Mat`` / ndarray-like via
    ``.tolist()`` — a ``Mat`` is float64 by construction, so its rows are
    REFUSED by name downstream rather than rounded (that refusal is the point:
    ``Mat.from_rows([[2**53+1, ...]])`` has already lost the low bit)."""
    if hasattr(L, "to_lists"):
        return [list(r) for r in L.to_lists()]
    if hasattr(L, "tolist"):
        return [list(r) for r in L.tolist()]
    return [list(r) for r in L]


def _denominator_lcm(rows) -> int:
    """The Class-I LCM of every entry denominator — ``eig_exact``'s pre-scale
    ``c`` (``B = c·A`` is the INTEGER matrix it actually isolates).

    Load-bearing because :func:`srmech.math.laplacian._symmetric_eig_exact`
    DISCARDS ``eig_exact``'s ``denominator_scale``, so the minimal polynomial
    each ``Qalg`` carries is that of ``c·λ``, not of ``λ``. Any exact read
    against ``λ.m`` — the sign pin and the bracket-containment check below —
    must scale by ``c`` first, and ``c`` is not reachable through the public
    wrapper. ``c == 1`` for an integer operand, so the integer path is
    untouched. Class I (:func:`srmech.math.cyclic.gcd`), not ``math.gcd``."""
    from ..math.cyclic import gcd as _gcd
    c = 1
    for r in rows:
        for v in r:
            d = int(getattr(v, "denominator", 1))
            c = c // _gcd(c, d) * d
    return c


def _int_poly_at(m, x: "Fraction") -> "Fraction":
    """Horner evaluation of an integer polynomial ``m`` (LOW→HIGH, the
    ``eig_exact`` ``min_poly`` convention) at an exact rational ``x``. Exact ℚ
    the whole way — no float, no ``abs()``."""
    s = Fraction(0)
    for coeff in reversed(m):
        s = s * x + coeff
    return s


def _bracket_holds(value, lo, hi, scale: int) -> bool:
    """Does the exact isolating bracket ``[lo, hi]`` hold the eigenvalue
    ``value`` — checked EXACTLY, never through the float embedding.

    A RATIONAL eigenvalue is decided by ``Q`` comparison. An IRRATIONAL one is
    decided by a SIGN CHANGE of its own minimal polynomial across the scaled
    bracket ``[c·lo, c·hi]``: ``m`` is irreducible and the bracket is an
    ISOLATING interval of the characteristic polynomial (it holds exactly one
    distinct root), so ``m`` has at most one root in it and a sign change — or a
    zero at an endpoint — is exactly the containment test. Signs are read by
    comparison (Class K pin-slot), never ``abs()``.

    What this proves, stated so nobody reads more into it: index ``i``'s bracket
    holds a root of index ``i``'s minimal polynomial. Two eigenvalues that are
    Galois conjugates SHARE one ``m``, so for those the check is "a root of the
    shared ``m`` lies here" and the PAIRING follows from both lists being
    ascending over pairwise-disjoint brackets. That is the honest strength of
    the assertion — and it is CHECKED rather than assumed, because the two
    shipped ops isolate independently."""
    r = value.as_rational()
    if r is not None:
        return lo <= r <= hi
    at_lo = _int_poly_at(value.m, Fraction(lo) * scale)
    at_hi = _int_poly_at(value.m, Fraction(hi) * scale)
    if at_lo == 0 or at_hi == 0:
        return True
    return (at_lo > 0) != (at_hi > 0)


def _positive_tension_indices(values, intervals, scale: int) -> List[int]:
    """The Class-K sign pin: the indices whose tension is STRICTLY POSITIVE.

    This replaces the float route's relative floor ``lam[i] > lam[-1]·1e-9``
    (:data:`_ZERO_TENSION_REL`), which is not a zero test at all — on the 3-node
    path Laplacian with weights ``(2**53+1, 1)`` that floor is
    ``1.8e16 · 1e-9 = 1.8e7``, so it discards a tension of ``3/2`` as "free" and
    the resonance list comes back EMPTY. Here the zero mode is ``λ == 0``,
    exactly.

    A bare ``λ != 0`` test would be wrong in the other direction:
    :func:`~srmech.math.rational.best_rational` REFUSES a negative numerator,
    :func:`resonant_spectrum` validates only squareness and ``orders >= 1``, and
    an INDEFINITE real-symmetric matrix is reachable through the public contract
    (``[[1, 2], [2, 1]]`` has tensions ``-1`` and ``3``). The float route never
    trips that because its floor silently drops every non-positive tension;
    keeping the two routes in agreement means the exact test is POSITIVITY, read
    off the exact bracket.

    A bracket that straddles zero is decided in ONE exact step rather than
    refined: the eigenvalue is irrational there (``0`` is rational), so splitting
    the bracket at ``0`` and reading the sign change of ``m`` on ``[c·lo, 0]``
    says which side the root is on."""
    nz: List[int] = []
    for i, v in enumerate(values):
        r = v.as_rational()
        if r is not None:
            if r.numerator > 0:
                nz.append(i)
            continue
        lo, hi = intervals[i]
        if lo > 0:
            nz.append(i)
            continue
        if hi < 0:
            continue
        # The bracket straddles 0. Split it AT 0 and read the sign change.
        at_lo = _int_poly_at(v.m, Fraction(lo) * scale)
        at_zero = Fraction(v.m[0])          # m(0) — the constant term
        if at_zero == 0:
            raise ValueError(
                f"resonant_spectrum(exact=True): eigenvalue {v!r} at index {i} "
                "reports an irreducible minimal polynomial with a zero constant "
                "term (root 0), which would make it rational — eig_exact "
                "inconsistency (upstream bug)")
        if at_lo == 0 or (at_lo > 0) != (at_zero > 0):
            continue                        # the root is in [c·lo, 0] => λ <= 0
        nz.append(i)                        # the root is in (0, c·hi] => λ > 0
    return nz


def _resonances_from_exact_brackets(values, intervals, scale: int,
                                    max_den: int) -> List[Dict[str, object]]:
    """The EXACT peer of :func:`_resonances_from_tensions` — the adjacent
    positive-tension resonance read taken off the exact Sturm brackets.

    A PEER, deliberately not a widening: ``_resonances_from_tensions`` is the one
    lock/libration source of truth SHARED with :func:`resonant_spectrum_sparse`,
    and the sparse op has no exact eigensolver to feed it, so widening the shared
    helper would change the sparse op's contract in the same edit.

    The ratio of two positive tensions is ENCLOSED, not sampled: with
    ``λ_a ∈ [A_lo, A_hi]`` and ``λ_b ∈ [B_lo, B_hi]`` (all positive) the ratio
    lies in ``[A_lo/B_hi, A_hi/B_lo]``, and :func:`best_rational` runs on BOTH
    endpoints. Agreement CERTIFIES the anchor — no rational with denominator
    ``<= max_den`` other than that one lies in the enclosure. Disagreement is
    REPORTED (``certified=False`` plus both anchors), never guessed away. Both
    endpoints are plain ``ℚ``: no cross-field quotient of two ``Qalg`` is ever
    formed (``Qalg`` division across unequal fields refuses by name, correctly).

    ``(0, 1)`` in ``"ratio"`` is the UNDERFLOW SENTINEL — ``best_rational``
    returns it when the ratio is below ``1/max_den`` — and is NOT the integer
    lock that an empty ``den_coords`` otherwise denotes."""
    from ..math import primes as _primes
    from ..math import rational as _rational

    nz = _positive_tension_indices(values, intervals, scale)
    out: List[Dict[str, object]] = []
    for a, b in zip(nz, nz[1:]):
        lo_a, hi_a = intervals[a]
        lo_b, hi_b = intervals[b]
        for idx, lo in ((a, lo_a), (b, lo_b)):
            if not lo > 0:
                raise ValueError(
                    f"resonant_spectrum(exact=True): tension {idx} is positive "
                    f"but its isolating bracket [{lo!r}, ...] does not have a "
                    "strictly positive lower endpoint, so the ratio enclosure "
                    "cannot be formed without dividing by a bracket that reaches "
                    "0. Re-isolate at higher precision "
                    "(srmech.cascade.matrix_cascades.eigvals_exact takes bits=) "
                    "and read the resonances from those brackets.")
        r_lo = Fraction(lo_a) / Fraction(hi_b)      # the ratio's exact floor
        r_hi = Fraction(hi_a) / Fraction(lo_b)      # the ratio's exact ceiling
        n1, d1 = _rational.best_rational(r_lo.numerator, r_lo.denominator, max_den)
        n2, d2 = _rational.best_rational(r_hi.numerator, r_hi.denominator, max_den)
        den_coords = {p: e for p, e in _primes.factor(d1)} if d1 > 1 else {}
        out.append({
            "pair": (a, b),
            "ratio": (n1, d1),
            "den_coords": den_coords,
            "locked": _tension_is_locked(den_coords, max_den=max_den),
            "certified": (n1, d1) == (n2, d2),
            "ratio_enclosure": ((n1, d1), (n2, d2)),
        })
    return out


def _resonant_spectrum_exact(L, orders: int, max_den: int, *, bits: int = 64):
    """The ``exact=True`` route of :func:`resonant_spectrum` — see that
    docstring for the contract, the design decisions and the cost."""
    from ..math import laplacian as _L
    from ..math.qmat import QMat
    from ..cascade.matrix_cascades import eigvals_exact

    rows = _exact_rows(L)
    # Validation + the exact eigensolve, under THIS op's name: the shared
    # laplacian helper takes the caller's name, so a refusal never surfaces
    # another op's identity. SQUARE + EXACT + SYMMETRIC are all refused here —
    # and SYMMETRY is a route asymmetry the default route does not have (it
    # accepts a non-symmetric operand and reads the float Jacobi's answer).
    values, modes = _L._symmetric_eig_exact(rows, "resonant_spectrum", bits=bits)
    n = len(values)

    # ── force-orders, exact: QMat.matmul powers of the OPERAND. ─────────
    # The float route reconstructs Lᵏ = V·diag(Λᵏ)·Vᵀ from the ONE eigensolve.
    # That is exactly the cross-field PRODUCT the SVE precedent refuses — V's
    # columns live in per-eigenvalue fields, Λᵏ in another — so the exact route
    # CANNOT take it and multiplies the OPERAND instead. The algorithm differs
    # by necessity; the VALUE is the one the float route approximates (measured
    # on the 2**53+1 witness: the float reconstruction of L²[0][0] is
    # 1.6225927682921347e+32 against the exact 2·P² whose float is
    # 1.622592768292134e+32 — the eigenbasis reconstruction is itself lossy at
    # that scale).
    A = QMat.from_rows([[v if isinstance(v, Q) else Q(Fraction(v).numerator,
                                                      Fraction(v).denominator)
                         for v in r] for r in rows])
    force_orders: List["QMat"] = []
    power = A
    for k in range(1, orders + 1):
        if k > 1:
            power = power.matmul(A)
        force_orders.append(power)

    # ── resonances, exact: Sturm brackets + best_rational on BOTH endpoints. ─
    scale = _denominator_lcm(rows)

    def _isolate(at_bits: int):
        """The Sturm brackets at ``at_bits``, index-CHECKED against ``values``.

        The two shipped exact ops isolate independently, so the alignment their
        ``pair`` indices rest on is CHECKED, not assumed — every re-isolation
        below is checked again, at the precision it was taken."""
        ivs = eigvals_exact(rows, bits=at_bits, return_intervals=True)
        if len(ivs) != n:
            raise ValueError(
                f"resonant_spectrum(exact=True): the exact eigensolver returned "
                f"{n} eigenvalues but the Sturm isolation returned {len(ivs)} "
                "isolating intervals on the same operand — an upstream "
                "inconsistency, not an input error")
        for i in range(n):
            lo, hi = ivs[i]
            if not _bracket_holds(values[i], lo, hi, scale):
                raise ValueError(
                    "resonant_spectrum(exact=True): the two shipped exact ops "
                    f"disagree on eigenvalue order — isolating interval {i} = "
                    f"[{lo!r}, {hi!r}] does not hold {values[i]!r}. Both are "
                    "ascending Sturm orders, so this is an upstream "
                    "inconsistency, not an input error")
        return ivs

    intervals = _isolate(bits)
    resonances = _resonances_from_exact_brackets(values, intervals, scale, max_den)
    # An uncertified anchor means the enclosure is wider than the gap between
    # two admissible rationals. Re-isolate at DOUBLED precision (bounded: three
    # further attempts) rather than picking an endpoint. Still uncertified after
    # that, the record SAYS so — it is never guessed away.
    attempts = 0
    while attempts < 3 and any(not r["certified"] for r in resonances):
        attempts += 1
        bits *= 2
        intervals = _isolate(bits)
        resonances = _resonances_from_exact_brackets(
            values, intervals, scale, max_den)

    return {
        "tensions": values,
        "modes": modes,
        "force_orders": force_orders,
        "resonances": resonances,
    }


def _resonant_spectrum_native(L, orders: int, max_den: int):
    """The §75 native path: route through the ``srmech_resonant_spectrum`` C
    peer when it is bound, returning the same dict the pure-Python op returns
    (value-parity — native authoritative when present). Returns ``None`` when no
    native lib / symbol, so the caller runs the pure-Python complete alternative.
    """
    import ctypes
    from .. import _native
    from ..math import primes as _primes
    from ..math.mat import Mat

    lib = _native.LIB
    if (not _native.HAS_NATIVE or lib is None
            or not hasattr(lib, "srmech_resonant_spectrum")):
        return None

    rows = L.tolist() if hasattr(L, "tolist") else [list(r) for r in L]
    n = len(rows)
    if n == 0 or any(len(r) != n for r in rows):
        return None  # let the pure-Python path raise the precise ValueError
    flat = [float(rows[i][j]) for i in range(n) for j in range(n)]
    L_c = (ctypes.c_double * (n * n))(*flat)
    tens = (ctypes.c_double * n)()
    modes = (ctypes.c_double * (n * n))()
    fo = (ctypes.c_double * (orders * n * n))()
    npairs = max(n - 1, 1)
    rp = (ctypes.c_int32 * (npairs * 2))()
    rr = (ctypes.c_uint64 * (npairs * 2))()
    rl = (ctypes.c_int32 * npairs)()
    rcount = ctypes.c_uint32(0)
    ws_doubles = lib.srmech_resonant_spectrum_arena_bytes(ctypes.c_uint32(n)) // 8 + 16
    ws = (ctypes.c_double * int(ws_doubles))()
    rc = lib.srmech_resonant_spectrum(
        ctypes.c_uint32(n), L_c, ctypes.c_uint32(orders), ctypes.c_uint64(max_den),
        tens, modes, fo, rp, rr, rl, ctypes.byref(rcount),
        ws, ctypes.c_size_t(int(ws_doubles) * 8))
    if rc != _native.SRMECH_OK:
        return None  # the pure-Python path re-runs + raises the matching error

    tensions = Vec.from_sequence([tens[i] for i in range(n)], is_complex=False)
    modes_mat = Mat.from_rows(
        [[modes[i * n + j] for j in range(n)] for i in range(n)], is_complex=False)
    force_orders: List["Mat"] = []
    for k in range(orders):
        force_orders.append(Mat.from_rows(
            [[fo[k * n * n + i * n + j] for j in range(n)] for i in range(n)],
            is_complex=False))
    resonances: List[Dict[str, object]] = []
    for idx in range(rcount.value):
        num, den = int(rr[idx * 2]), int(rr[idx * 2 + 1])
        den_coords = {p: e for p, e in _primes.factor(den)} if den > 1 else {}
        resonances.append({
            "pair": (int(rp[idx * 2]), int(rp[idx * 2 + 1])),
            "ratio": (num, den),
            "den_coords": den_coords,
            "locked": bool(rl[idx]),
        })
    return {
        "tensions": tensions,
        "modes": modes_mat,
        "force_orders": force_orders,
        "resonances": resonances,
    }


def resonant_spectrum(
    L,
    *,
    orders: int = 2,
    max_den: int = 64,
    exact: bool = False,
) -> Dict[str, object]:
    """Read a coupling Laplacian as a stored resonant object (§75 / F928).

    Args:
        L: an ``(n, n)`` real-symmetric coupling Laplacian — a
            :class:`~srmech.math.mat.Mat` (or list-of-rows / ndarray-like). The
            stored ("dark") object before any excitation. Under ``exact=True``
            it is instead an EXACT operand (``QMat`` / rows of ``int`` /
            :class:`fractions.Fraction` / ``Q``) — see *Accuracy* below.
        orders: how many force-orders to materialise — ``[L¹, …, Lᵒ]`` (default
            2: the force ``L`` and the biharmonic forces-of-forces ``L²``).
            Must be ``≥ 1``.
        max_den: the ``best_rational`` denominator ceiling for the resonance
            read (Class-N). Default 64 (the Laplace 4:2:1 ladder fits well
            inside it). The lock/libration cutoff scales as ``isqrt(max_den)``.
        exact: keyword-only opt-in to the EXACT route (rc467, ``#T1188``; the
            :func:`~srmech.math.laplacian.symmetric_eigendecompose` precedent).
            Default ``False`` — the float64 route below, unchanged byte for
            byte. See *Accuracy* for the contract, the carriers and the cost.

    Returns:
        A dict with four keys on BOTH routes; the CARRIERS differ, because the
        exact route returns the exact objects rather than a lift.

        Default route (``exact=False``):

        * ``"tensions"`` — a real :class:`~srmech.math.vec.Vec` of eigenvalues
          ASCENDING (the stored "dark" tension spectrum; no excitation).
        * ``"modes"`` — an ``n×n`` real :class:`~srmech.math.mat.Mat` whose
          COLUMNS are the eigenvectors (the excitation modes).
        * ``"force_orders"`` — a list of ``orders`` :class:`~srmech.math.mat.Mat`
          ``[L, L², …, Lᵒ]``; ``Lᵏ = V·diag(Λᵏ)·Vᵀ`` reconstructed from the ONE
          eigensolve (Λ raised to ``k`` in the eigenbasis), never repeated
          ``L``-matmuls **on this route** (the exact route cannot take that
          reconstruction — see *Accuracy*).
        * ``"resonances"`` — a list of dicts, one per adjacent nonzero-tension
          pair, each ``{"pair": (i, j), "ratio": (num, den), "den_coords":
          {prime: exp}, "locked": bool}``: the Class-N best-rational of the
          tension ratio + the Class-J prime-coordinate factorisation of its
          denominator + the lock (smooth/2-adic den) vs libration (large-prime
          den) verdict.

        Exact route (``exact=True``):

        * ``"tensions"`` — a ``list`` of ``n`` :class:`~srmech.math.qalg.Qalg`
          eigenvalues ASCENDING with multiplicity, each over its OWN number
          field. A rational one answers ``.as_rational()``; the exact zero mode
          satisfies ``value == 0``.
        * ``"modes"`` — an ``n×n`` nested ``list`` of ``Qalg`` (``V[i][j]``)
          whose COLUMNS are the exact eigenvectors, each over its eigenvalue's
          own field.
        * ``"force_orders"`` — a list of ``orders``
          :class:`~srmech.math.qmat.QMat` ``[L, L², …, Lᵒ]``, entries plain
          ``Q`` (no field at all).
        * ``"resonances"`` — the same four keys PLUS two: ``"certified"``
          (``bool`` — both endpoints of the exact ratio ENCLOSURE read to the
          same anchor) and ``"ratio_enclosure"`` (both anchors, so a
          ``certified=False`` record still shows what it was between).

    **Accuracy (rc467, ``#T1188``).**

    Default route (``exact=False``) — a SILENT CARRIER DEMOTION, now declared.
    ``L`` is coerced to the float64 :class:`~srmech.math.mat.Mat` carrier at the
    entry, so an exact entry wider than 53 significand bits loses its low bit
    before the first Jacobi rotation, and the native peer
    ``srmech_resonant_spectrum`` takes ``const double *L_rowmajor``, so it
    cannot carry an exact operand either. Measured on the 3-node path Laplacian
    with weights ``(2**53+1, 1)`` — ``[[P, -P, 0], [-P, P+1, -1], [0, -1, 1]]``
    with ``P = 2**53+1`` — the float route returns tensions
    ``[0.13144078898136016, 1.5756659922051879, 1.8014398509481988e+16]``
    where the exact answers are ``0``, a degree-2 algebraic near ``3/2``, and
    a degree-2 algebraic near ``1.8e16``: the two small tensions are wrong by
    ``O(0.1)``. Its resonance list comes back EMPTY, and for a structural
    reason worth naming — the free-mode floor is RELATIVE
    (:data:`_ZERO_TENSION_REL` ``= 1e-9`` of the largest tension), which on
    this operand is ``1.8e16 · 1e-9 = 1.8e7``, so a real tension of ``3/2`` is
    discarded as "free" and no adjacent pair survives to be read. The
    ``force_orders`` reconstruction is lossy at that scale too:
    ``L²[0][0]`` comes back ``1.6225927682921347e+32`` against the exact
    ``2·P² = 162259276829213399420375029252098`` (float
    ``1.622592768292134e+32``). Those digits were measured in BOTH cells and
    are byte-identical: the C peer is bound and IS the route taken natively, so
    this is not a pure-cell artefact.

    ``exact=True`` — the route composes FOUR shipped exact ops and introduces
    no new type and no new C symbol:

    * ``tensions`` and ``modes`` — the ONE exact eigensolve,
      :func:`srmech.math.laplacian.symmetric_eigendecompose`'s ``exact=True``
      engine (exact integer char-poly → irreducible factors → Sturm-isolated
      roots → the null space of ``A − λI`` over ``ℚ(λ)``), entered under THIS
      op's name so a refusal never surfaces another op's identity.
    * ``force_orders`` — :class:`~srmech.math.qmat.QMat` ``matmul`` powers of
      the OPERAND.
    * ``resonances`` — :func:`srmech.cascade.matrix_cascades.eigvals_exact`
      with ``return_intervals=True`` (the exact rational Sturm brackets) and
      :func:`srmech.math.rational.best_rational` on BOTH endpoints of the ratio
      enclosure.

    On the witness above it returns ``tensions[0] == 0`` EXACTLY,
    ``force_orders[1][0][0] == 2·P²`` exactly, and one CERTIFIED resonance
    record where the float route returned none.

    Four things this route does, stated so nobody reads them in:

    1. **The modes are UNNORMALISED eigenlines.** Each column is a null-space
       basis vector of ``A − λI``; ``‖col‖²`` is an integer or an irrational,
       never ``1`` (measured on the witness: ``3`` for the constant zero-mode
       column, and an element with no rational value for the others).
       Normalising needs ``sqrt(‖v‖²)`` — a further quadratic extension with no
       shipped carrier — and inside a degenerate eigenspace the columns
       are not orthogonal either. The float route's ``Mat`` columns ARE
       orthonormal; that difference is the price of exactness, not an oversight.
    2. **The exact zero mode is ``λ == 0``**, not the ``1e-9`` relative floor
       the float route uses. That floor is what empties the witness's resonance
       list. The positivity test is a Class-K sign pin read off the exact
       bracket (never ``abs()``, never a bare ``λ != 0``): ``best_rational``
       REFUSES a negative numerator and an INDEFINITE real-symmetric operand is
       reachable through this contract — ``[[1, 2], [2, 1]]`` has tensions
       ``-1`` and ``3`` — so a ``!= 0`` test would keep the negative one and
       then raise inside ``best_rational``. Both routes drop it.
    3. **``(0, 1)`` in a resonance ``"ratio"`` is the UNDERFLOW SENTINEL**, not
       an integer lock: ``best_rational`` returns it whenever the ratio is
       below ``1/max_den``. On the witness the surviving pair is
       ``λ₁/λ₂ ≈ 8.3e-17``, far under ``1/64``, so its ``ratio`` is ``(0, 1)``
       with an EMPTY ``den_coords``. This route reproduces the default route's
       verdict on that record byte for byte — including that
       :func:`_tension_is_locked` reads an empty ``den_coords`` as an integer
       lock, which for an UNDERFLOWED anchor is the wrong verdict. That is a
       PRE-EXISTING defect of the shipped op, not one this route introduces —
       measured, ``resonant_spectrum([[1.0, 0.0], [0.0, 100.0]])`` already
       reports ``{'ratio': (0, 1), 'den_coords': {}, 'locked': True}`` on the
       default route today, and the same wrong verdict is written in the C peer
       (``srmech_coupling.c``, ``den <= 1`` ⇒ locked). It is deliberately NOT
       special-cased here: fixing it on the exact route alone would make the
       two routes disagree on a verdict for the same operand, and fixing it at
       root means one change in BOTH languages under the Python↔C value-parity
       gate. Named here as an OPEN defect of both routes, with its own
       sequenced fix; ``certified`` is unaffected (the enclosure is genuinely
       ``(0, 1)`` at both endpoints).
    4. **``force_orders`` changes ALGORITHM, necessarily.** The float route
       reconstructs ``Lᵏ = V·diag(Λᵏ)·Vᵀ`` from the one eigensolve. That is
       exactly the cross-field PRODUCT the
       :func:`~srmech.cascade.matrix_cascades.singular_values_exact` precedent
       refuses — ``V``'s columns live in per-eigenvalue fields and ``Λᵏ`` in
       another, and assembling across them needs a compositum — so the exact
       route multiplies the OPERAND instead. Nothing ELSE here forms a
       cross-field object (``tensions`` is a LIST of per-field ``Qalg``,
       ``modes`` is per-COLUMN over its own field, ``force_orders`` is entirely
       in ``ℚ``, and the resonance read touches only the RATIONAL bracket
       endpoints), which is why the combined dict IS returned here where
       ``singular_values_exact`` refuses a combined ``U·Σ·Vᵀ``.

    Two ROUTE ASYMMETRIES, stated rather than discovered: ``exact=True``
    requires the operand to be SYMMETRIC and EXACT and refuses otherwise BY
    NAME, where the default route accepts a non-symmetric operand (and reads
    the float Jacobi's answer on it) and rounds a wide exact one. Both
    refusals name ``resonant_spectrum(exact=True)``.

    Cost, measured (pure cell, this tree): the exact route runs 141–251× the
    float route on integer path Laplacians — ``n=3`` 0.16 s vs 0.0011 s,
    ``n=6`` 1.31 s vs 0.0067 s, ``n=8`` 4.58 s vs 0.018 s — which is why it is
    opt-in and the float Jacobi stays the default. Roughly half of that is the
    SECOND isolation: the brackets are a separate ``eigvals_exact`` pass,
    because ``_symmetric_eig_exact`` discards ``eig_exact``'s
    ``denominator_scale`` and the private isolator is not reachable through the
    public wrapper. ``force_orders`` is NOT the expensive half and does not
    explode: exact ``Lᵏ`` entries grow LINEARLY in digits (measured on the
    witness — 33 digits at ``k=2``, 130 at ``k=8``, 520 at ``k=32``, each step
    ~0.4 ms), so ``orders`` carries the same unbounded contract on both routes
    and no ceiling is imposed on one of them.

    ADR-0009 §1.2 (a disclosed missing capability is still a missing
    capability): a bare-C host runs 0 of this route. ``srmech_resonant_spectrum``
    takes ``const double *L_rowmajor`` and can never carry it; the exact KERNELS
    it would dispatch to are C-backed already (``srmech_sturm_isolate``,
    ``srmech_eigvec_exact``, ``srmech_factor_integer_poly``, the
    ``srmech_qmat_*`` family), so the gap is orchestrator-level. Closing it
    later ADDS a symbol and is therefore ABI-additive.

    The op composes SHIPPED ops only — ``laplacian.symmetric_eigendecompose``
    (Class L), ``laplacian.mat_matmul`` / the carrier ``@`` (Class L),
    ``rational.best_rational`` (Class N), ``primes.factor`` /
    ``qprime.Qprime`` (Class J) — so the DEFAULT route is value-identical on
    the native and pure-Python paths (the C peer ``srmech_resonant_spectrum``
    orchestrates the same kernels). No ``abs()`` (tension signs are read by
    comparison, Class-K).

    Raises:
        ValueError: ``orders < 1`` or a non-square / empty ``L``; and under
            ``exact=True`` also a non-EXACT (float / complex) entry or a
            non-SYMMETRIC operand, each refused by name.
    """
    from ..math import laplacian as _L  # lazy: laplacian imports carriers (avoid cycle)
    from ..math.mat import Mat

    if not isinstance(orders, int) or orders < 1:
        raise ValueError(f"resonant_spectrum: orders must be an int >= 1; got {orders!r}")

    # The EXACT route (rc467, `#T1188`) branches BEFORE the Mat coercion below
    # AND before the native call: Mat is float64, so Mat.from_rows would round
    # 2**53+1 to 2**53 and _symmetric_eig_exact would then refuse its own
    # operand by name; and srmech_resonant_spectrum takes `const double *
    # L_rowmajor`, so the C peer can never carry this route (see the docstring's
    # ADR-0009 note). The raw rows go straight to the exact ops.
    if exact:
        return _resonant_spectrum_exact(L, orders, max_den)

    # Native path (value-parity, native authoritative when present): the C peer
    # orchestrates the same kernels. Returns None ⇒ run the pure-Python complete
    # alternative below (no native lib / symbol / a non-square that the pure path
    # turns into the precise ValueError).
    L_mat = L if isinstance(L, Mat) else (
        Mat.from_rows([list(r) for r in (L.tolist() if hasattr(L, "tolist") else L)],
                      is_complex=False))
    native = _resonant_spectrum_native(L_mat, orders, max_den)
    if native is not None:
        return native

    # ── (1) the ONE eigensolve — Class L. tensions ASCENDING + real modes V. ──
    tensions, modes = _L.symmetric_eigendecompose(L)
    n = tensions.shape[0]
    if n == 0:
        raise ValueError("resonant_spectrum: L must be a non-empty square matrix")
    if modes.shape != (n, n):
        raise ValueError(
            f"resonant_spectrum: L must be square; eigenvectors are {modes.shape}")

    lam = [float(tensions[i]) for i in range(n)]  # plain-float spectrum (ascending)

    # ── (2) force-orders Lᵏ = V·diag(Λᵏ)·Vᵀ from the ONE eigensolve. ──
    # Reuse the eigenbasis: scale V's columns by Λᵏ, contract with Vᵀ. This is
    # the Class-L cascade (mat_matmul), NOT repeated L-matmuls — one eigensolve
    # serves every order. The reconstruction is real (real-symmetric input).
    Vt = modes.transpose()  # Vᵀ (n×n real)
    force_orders: List["Mat"] = []
    for k in range(1, orders + 1):
        lam_k = [lam[i] ** k for i in range(n)]
        # (V · diag(Λᵏ)) — scale column i of V by Λᵏ[i]; row-major build.
        scaled_rows = [
            [modes[r, c] * lam_k[c] for c in range(n)] for r in range(n)
        ]
        v_scaled = Mat.from_rows(scaled_rows, is_complex=False)
        force_orders.append(_L.mat_matmul(v_scaled, Vt))  # (V·diag) · Vᵀ = Lᵏ

    # ── (3) resonances — Class N best_rational + Class J prime-coords. ──
    # Read every ADJACENT nonzero-tension pair (ascending) via the shared
    # _resonances_from_tensions helper (the SAME logic resonant_spectrum_sparse
    # reuses — one lock/libration source of truth).
    resonances = _resonances_from_tensions(lam, max_den)

    return {
        "tensions": tensions,
        "modes": modes,
        "force_orders": force_orders,
        "resonances": resonances,
    }


def from_bodies(
    masses: Sequence[float],
    positions: Sequence[float],
) -> Tuple[int, List[Tuple[int, int]], List[float]]:
    """Build the gravity coupling-graph ``(n, edges, weights)`` for a body set.

    A nice-to-have builder for :func:`resonant_spectrum`'s input: each unordered
    body pair ``(i, j)`` gets the Newtonian coupling weight
    ``w = mᵢ·mⱼ / rᵢⱼ²`` (``rᵢⱼ`` the separation of their 1-D positions). The
    central body convention (index 0 at position 0) and the moon-gap convention
    match the F928 Jupiter+Galilean prototype: a pair touching the central body
    uses the outer body's position as ``r``; a non-central pair uses the
    position gap. A zero / negative separation drops the edge.

    Returns ``(n, edges, weights)`` ready to feed
    ``laplacian.dense_laplacian(n, edges, weights)``. Pure
    arithmetic (the ``/r²`` is a coupling weight, not a libm call).
    """
    m = [float(x) for x in masses]
    pos = [float(x) for x in positions]
    n = len(m)
    if len(pos) != n:
        raise ValueError(
            f"from_bodies: masses ({n}) and positions ({len(pos)}) length mismatch")
    edges: List[Tuple[int, int]] = []
    weights: List[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            # central body (i==0) sits at the origin: r is the outer body's
            # position; otherwise r is the position gap.
            r = pos[j] if i == 0 else (pos[j] - pos[i])
            if r > 0.0:
                edges.append((i, j))
                weights.append(m[i] * m[j] / (r * r))
    return n, edges, weights


# =====================================================================
# §75-sparse — resonant_spectrum_sparse: the F172 storage signature at
# UNBOUNDED n (issue #698). resonant_spectrum reads the storage signature
# only through the DENSE Class-L eigensolve (native-capped at
# MAX_NATIVE_NODES=256; O(n²) RAM, O(n³) eig). This reads the SAME signature
# — the k EXTREME tensions (bottom-k + top-k of the COMBINATORIAL Laplacian
# L = D − W) + their Class-N/J resonance lock/libration verdicts — via
# streaming power iteration + deflation on the packed edge stream: RAM
# O(k·n), time O(k·|E|·iters), n UNBOUNDED. It COMPOSES the §51/§52 out-of-
# core machinery (write_packed_graph + the fiedler_sparse streaming matvec),
# extended from ONE mode to bottom-k + top-k, then runs the SAME
# _resonances_from_tensions lock/libration read on the k tensions. SAME-RC C
# peer srmech_laplacian_k_extreme_modes_file (streams the packed file via the
# PAL; caller-arena, no node cap) — c_dispatched. numpy-free; no abs().
# =====================================================================

# The Rayleigh-quotient convergence floor for one extreme mode (relative to
# 1+|λ|; a Class-N float read of when the tension has settled) + the required
# run of consecutive settled steps. Shared VERBATIM by the C peer so the
# native + pure paths run the identical iteration count (within-tol parity).
_KEXT_TOL: float = 1e-13
_KEXT_STABLE_RUN: int = 3


def _kext_scramble_init(n: int) -> List[float]:
    """The same deterministic Class-I multiplicative scramble init
    (Knuth 2654435761; uint32-wrap → [−1, 1)) fiedler_sparse uses — a generic
    Fiedler component regardless of node ordering, bit-identical to the C twin.
    NOT deflated here (the caller deflates against the found modes)."""
    return [(((k * 2654435761 + 1013904223) & 0xFFFFFFFF) / 4294967296.0) * 2.0 - 1.0
            for k in range(n)]


def _kext_degrees(n: int, edges, weights) -> List[float]:
    """Weighted degree of every node (both endpoints) — the diagonal of L."""
    deg = [0.0] * n
    for (a, b), w in zip(edges, weights):
        deg[a] += w
        deg[b] += w
    return deg


def _kext_wv(n: int, edges, weights, v: List[float]) -> List[float]:
    """One streamed adjacency matvec ``y = W·v`` (undirected: both endpoints)
    — the O(|E|) edge loop, the ONLY edge-touching step (n never squared)."""
    y = [0.0] * n
    for (a, b), w in zip(edges, weights):
        y[a] += w * v[b]
        y[b] += w * v[a]
    return y


def _kext_deflate(v: List[float], basis: List[List[float]]) -> None:
    """Gram-Schmidt-deflate ``v`` against the found unit modes (keeps a new
    iterate orthogonal to every already-converged extreme mode)."""
    n = len(v)
    for b in basis:
        dot = 0.0
        for i in range(n):
            dot += v[i] * b[i]
        for i in range(n):
            v[i] -= dot * b[i]


def _kext_normalize(v: List[float]) -> Optional[List[float]]:
    """Unit-normalise ``v`` (Class-N root of the Class-K magnitude-square sum);
    ``None`` if ``v`` is the zero vector (caller stops that mode)."""
    n2 = 0.0
    for x in v:
        n2 += x * x                 # Class-K magnitude-square (no abs())
    if n2 <= 0.0:
        return None
    nrm = float(_rsqrt(n2))         # Class-N∘K root (rational-isqrt cascade, no float_pow)
    return [x / nrm for x in v]


def _kext_rayleigh_l(n: int, edges, weights, deg: List[float], v: List[float]) -> float:
    """The L-Rayleigh-quotient ``vᵀ L v = Σ deg_i v_i² − vᵀ W v`` on a unit ``v``
    — the tension read (accurate even when the iterate converged on the SHIFTED
    operator σI − L for a bottom mode)."""
    y = _kext_wv(n, edges, weights, v)
    r = 0.0
    for i in range(n):
        r += deg[i] * v[i] * v[i] - v[i] * y[i]
    return r


def _kext_one_mode(n, edges, weights, deg, sigma, top, basis, max_iters):
    """Find ONE extreme eigenpair by deflated power iteration, then read its
    L-tension. ``top`` → iterate on ``L`` (largest tension); else on the shift
    ``σI − L`` (largest of the shift = smallest tension of ``L``). Deflates each
    step against ``basis`` (the found unit modes). Returns ``(tension, unit
    eigvec)`` or ``None`` (degenerate / exhausted subspace)."""
    v = _kext_scramble_init(n)
    _kext_deflate(v, basis)
    v = _kext_normalize(v)
    if v is None:
        return None
    lam_prev: Optional[float] = None
    stable = 0
    for it in range(max_iters):
        y = _kext_wv(n, edges, weights, v)
        if top:
            av = [deg[i] * v[i] - y[i] for i in range(n)]           # L·v
        else:
            av = [sigma * v[i] - (deg[i] * v[i] - y[i]) for i in range(n)]  # (σI−L)·v
        _kext_deflate(av, basis)
        lam = 0.0
        for i in range(n):
            lam += v[i] * av[i]     # Rayleigh of the iterated operator on unit v
        av = _kext_normalize(av)
        if av is None:
            break
        v = av
        if lam_prev is not None:
            d = lam - lam_prev
            mag = d if d >= 0.0 else -d          # Class-K sign branch (no abs())
            ref = 1.0 + (lam if lam >= 0.0 else -lam)
            if mag <= _KEXT_TOL * ref:
                stable += 1
                if stable >= _KEXT_STABLE_RUN and it >= 5:
                    break
            else:
                stable = 0
        lam_prev = lam
    return _kext_rayleigh_l(n, edges, weights, deg, v), v


def _kext_modes_py(n, edges, weights, k, max_iters):
    """Pure-Python COMPLETE streaming k-extreme read (the no-native alternative,
    and the value oracle). Bottom-k modes of L via the shift σI−L (σ = 2·max_deg
    + 1, a Gershgorin upper bound on λ_max), then top-k modes of L, each deflated
    against ALL modes found so far (so bottom/top never re-find each other and,
    when 2k ≥ n, the union is the full spectrum). Returns a list of distinct
    ``(tension, unit-eigvec)`` pairs in found order (unsorted)."""
    deg = _kext_degrees(n, edges, weights)
    max_deg = 0.0
    for d in deg:
        if d > max_deg:
            max_deg = d
    sigma = 2.0 * max_deg + 1.0
    basis: List[List[float]] = []
    pairs: List[Tuple[float, List[float]]] = []
    kb = k if k < n else n
    # Pin the EXACT trivial mode: the constant vector is always a 0-eigenvector
    # of the combinatorial Laplacian (L·1 = deg − Σw = 0), and 0 is always the
    # SMALLEST tension (L is PSD), so it is always in bottom-k. On a near-
    # degenerate low-frequency spectrum it converges SLOWLY by power iteration
    # (its M-gap is λ₁ ≈ 0), so pinning it exactly (tension 0.0) makes the zero
    # mode identical native-vs-pure — the analytic-deflation of the known trivial
    # mode, mirroring how fiedler_sparse deflates its √deg mode.
    if kb >= 1 and n >= 1:
        c = 1.0 / float(_rsqrt(float(n)))    # 1/√n — Class-N∘K root, no float_pow
        const = [c] * n
        pairs.append((0.0, const))
        basis.append(const)
    for _ in range(kb - 1):
        res = _kext_one_mode(n, edges, weights, deg, sigma, False, basis, max_iters)
        if res is None:
            break
        pairs.append(res)
        basis.append(res[1])
    kt = k if k < n else n
    for _ in range(kt):
        if len(basis) >= n:
            break
        res = _kext_one_mode(n, edges, weights, deg, sigma, True, basis, max_iters)
        if res is None:
            break
        pairs.append(res)
        basis.append(res[1])
    return pairs


def _kext_modes_file_native(n, path, k, max_iters):
    """numpy-free native dispatch for the streaming k-extreme read — calls the
    standalone-C ``srmech_laplacian_k_extreme_modes_file`` with a CALLER-arena
    (the bound is the caller's RAM, no compiled-in node cap; the matvec power
    iteration + deflation run in C reading the adjacency from ``path`` via the
    PAL streaming-read). Returns the same distinct ``(tension, eigvec)`` pair
    list the pure path returns, or ``None`` on any non-OK status."""
    import ctypes
    from .. import _native

    lib = _native.LIB
    kk = int(k)
    cap = 2 * kk
    arena = lib.srmech_laplacian_k_extreme_modes_arena_bytes(ctypes.c_uint32(n))
    ws_doubles = int(arena) // 8 + 8
    tens = (ctypes.c_double * (cap if cap > 0 else 1))()
    modes = (ctypes.c_double * ((cap if cap > 0 else 1) * (n if n > 0 else 1)))()
    count = ctypes.c_uint32(0)
    ws = (ctypes.c_double * ws_doubles)()
    rc = lib.srmech_laplacian_k_extreme_modes_file(
        ctypes.c_uint32(n), path.encode("utf-8"), ctypes.c_uint32(kk),
        ctypes.c_uint32(int(max_iters)), tens, modes, ctypes.byref(count),
        ws, ctypes.c_size_t(ws_doubles * 8))
    if rc != _native.SRMECH_OK:
        return None
    m = count.value
    return [(tens[r], [modes[r * n + c] for c in range(n)]) for r in range(m)]


def _kext_from_edges(n, edges, weights, k, max_iters):
    """k-extreme pairs from an in-RAM edge list — native (write a temp packed
    file, stream it in C) else the pure-Python streaming read."""
    from .. import _native

    if _native.has_native_k_extreme_modes() and n >= 1:
        import os
        import tempfile
        from ..math import laplacian as _L
        fd, tmp = tempfile.mkstemp(suffix=".bin", prefix="srmech_kext_")
        os.close(fd)
        try:
            _L.write_packed_graph(tmp, edges, weights)
            res = _kext_modes_file_native(n, tmp, k, max_iters)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
        if res is not None:
            return res
    return _kext_modes_py(n, edges, weights, k, max_iters)


def _kext_from_path(n, path, k, max_iters):
    """k-extreme pairs from a packed edge FILE — native streams it directly
    (edges never resident); the pure path reads it in (correct, not bounded —
    the fiedler_sparse_file precedent)."""
    from .. import _native
    from ..math import laplacian as _L

    if _native.has_native_k_extreme_modes():
        res = _kext_modes_file_native(n, path, k, max_iters)
        if res is not None:
            return res
    edges, weights = _L._read_packed_graph(path)
    return _kext_modes_py(n, edges, weights, k, max_iters)


def resonant_spectrum_sparse(
    edges_or_path,
    weights=None,
    *,
    k: int = 8,
    n: Optional[int] = None,
    max_iters: int = 1000,
    max_den: int = 64,
) -> Dict[str, object]:
    """Read the resonant storage signature at UNBOUNDED ``n`` — the streaming /
    out-of-core k-extreme-mode peer of :func:`resonant_spectrum` (issue #698).

    :func:`resonant_spectrum` reads the storage signature (eigen-tensions + the
    Class-N/J resonance lock/libration verdict) only through the DENSE Class-L
    eigensolve, which the native kernels cap at ``MAX_NATIVE_NODES = 256`` (dense
    ``O(n²)`` RAM, ``O(n³)`` eig). This reads the SAME signature — restricted to
    the ``k`` EXTREME modes (the ``k`` LOWEST-tension + ``k`` HIGHEST-tension
    eigenpairs of the COMBINATORIAL Laplacian ``L = D − W``) — via streaming
    power iteration + Gram-Schmidt deflation on the packed edge stream. Bottom-k
    ride the shift ``σI − L`` (σ a Gershgorin upper bound on ``λ_max``), top-k
    ride ``L`` directly; each new mode deflates against all found modes (so
    bottom/top never collide, and when ``2k ≥ n`` the union is the FULL
    spectrum). RAM ``O(k·n)``, time ``O(k·|E|·iters)``, ``n`` UNBOUNDED — it
    breaks the ``n ≤ 256`` dense wall the same way :func:`fiedler_sparse` breaks
    it for the 2-way cut.

    The ``k`` extreme tensions then feed the SAME
    :func:`_resonances_from_tensions` lock/libration read
    :func:`resonant_spectrum` uses (Class-N :func:`best_rational` + Class-J
    prime-coordinate factor + the smooth-den LOCK / large-prime-den libration
    verdict) — reused, not reinvented, so the verdicts are IDENTICAL to the dense
    read on the same tension values.

    Composes the §51/§52 out-of-core machinery: :func:`write_packed_graph` (the
    on-disk adjacency) + the ``fiedler_sparse`` streaming matvec, extended from
    ONE mode to bottom-k + top-k. Dispatches to the standalone-C
    ``srmech_laplacian_k_extreme_modes_file`` when ``HAS_NATIVE`` (the matvec /
    power iteration / deflation run in C, streaming the packed file via the PAL,
    caller-arena, no node cap); else the pure-Python streaming read is the
    complete alternative. No ``abs()`` (magnitudes are the Class-K
    square, signs read by comparison).

    Accuracy envelope (honest): deflated power iteration resolves an extreme mode
    accurately when it is SEPARATED from its neighbour — the well-separated
    regime a k-extreme read is FOR (the F172 storage-signature extremes). On such
    graphs the k extreme tensions match the dense :func:`resonant_spectrum`
    eigensolve to ``~1e-9`` and the lock/libration verdicts are IDENTICAL. When
    the spectrum is NEAR-DEGENERATE at the k-boundary (a dense low-frequency
    cluster, e.g. a large ring/lattice bulk), those clustered modes converge
    slowly — the genuine limitation of ANY iterative extreme-eigenvalue read
    versus a full dense eigensolve; the dense op is the exact all-modes reference
    at ``n ≤ 256``, and this op is the read past that wall for the SEPARATED
    extremes. The native and pure paths agree within float tolerance regardless
    (same iteration, same arithmetic order).

    Args:
        edges_or_path: an in-RAM undirected edge iterable ``[(u, v), …]`` OR a
            ``str`` path to a packed edge file (written by
            :func:`write_packed_graph`; streamed, edges never resident).
        weights: per-edge weights (default all ``1.0``); ignored when
            ``edges_or_path`` is a path (the weights live in the file).
        k: modes per extreme side (default 8) — the read returns up to ``2k``
            distinct extreme tensions (fewer when ``2k ≥ n``).
        n: node count. ``None`` → inferred (max endpoint + 1 for an edge list;
            read from the packed file for a path).
        max_iters: per-mode power-iteration cap (default 1000; the Rayleigh
            convergence floor usually stops earlier).
        max_den: the ``best_rational`` denominator ceiling for the resonance read
            (default 64, matching :func:`resonant_spectrum`).

    Returns:
        A dict of the SAME shape :func:`resonant_spectrum` returns, restricted to
        the ``k`` extreme modes:

        * ``"tensions"`` — a real :class:`~srmech.math.vec.Vec` of the extreme
          eigenvalues ASCENDING (the k lowest ++ k highest, sorted, distinct).
        * ``"modes"`` — an ``n × m`` real :class:`~srmech.math.mat.Mat` whose
          COLUMNS are the corresponding extreme eigenvectors (``m`` = number of
          tensions returned).
        * ``"resonances"`` — the adjacent-tension lock/libration list (the SAME
          ``{pair, ratio, den_coords, locked}`` dicts :func:`resonant_spectrum`
          returns), read on the extreme tension list.
        * ``"k"`` / ``"n"`` / ``"n_modes"`` — the request + the node count + the
          number of extreme modes actually returned.

        (No ``"force_orders"`` — a dense ``Lᵏ`` cannot be materialised at
        unbounded ``n``; the extreme tensions carry the storage signature.)

    Raises:
        ValueError: ``k < 1``, or ``n`` cannot be inferred from an empty edge
            list without an explicit ``n``.
    """
    if not isinstance(k, int) or k < 1:
        raise ValueError(f"resonant_spectrum_sparse: k must be an int >= 1; got {k!r}")

    from ..math import laplacian as _L
    from ..math.mat import Mat

    if isinstance(edges_or_path, str):
        path = edges_or_path
        if n is None:
            edges, _w = _L._read_packed_graph(path)
            n = (1 + max(max(a, b) for a, b in edges)) if edges else 0
        pairs = _kext_from_path(int(n), path, k, max_iters)
    else:
        edges = [(int(a), int(b)) for (a, b) in edges_or_path]
        if weights is None:
            w_list = [1.0] * len(edges)
        else:
            w_list = [float(x) for x in weights]
            if len(w_list) != len(edges):
                raise ValueError(
                    f"resonant_spectrum_sparse: weights ({len(w_list)}) and edges "
                    f"({len(edges)}) length mismatch")
        if n is None:
            n = (1 + max(max(a, b) for a, b in edges)) if edges else 0
        pairs = _kext_from_edges(int(n), edges, w_list, k, max_iters)

    n = int(n)
    # Sort the distinct extreme pairs by tension ASCENDING → tensions + columns.
    pairs = sorted(pairs, key=lambda p: p[0])
    lam = [p[0] for p in pairs]
    m = len(pairs)
    tensions = Vec.from_sequence(lam, is_complex=False)
    if m > 0 and n > 0:
        mode_rows = [[pairs[c][1][r] for c in range(m)] for r in range(n)]
        modes = Mat.from_rows(mode_rows, is_complex=False)
    else:
        # Degenerate (empty graph / no modes) — a 1×1 zero placeholder Mat.
        modes = Mat.from_rows([[0.0]], is_complex=False)
    resonances = _resonances_from_tensions(lam, max_den)
    return {
        "tensions": tensions,
        "modes": modes,
        "resonances": resonances,
        "k": int(k),
        "n": n,
        "n_modes": m,
    }


# =====================================================================
# §Ch-2 — the fractal-spectrum (self-similar / spectral-decimation) dual
# of resonant_spectrum. Pure orchestration over already-C-backed ops (no
# new numerical kernel) — ships non_compute (no dedicated C peer).
# =====================================================================

_FRACTAL_Q1 = Q(1, 1)
_FRACTAL_Q2 = Q(2, 1)


def _octaves(r: "Q") -> int:
    """F974 bit-exact ``|q|``-meter: ``ceil(log2(1/r))`` = the number of halvings
    of 1 until ``<= r``. Pure ``Q``-halving — no float, no ``abs()`` (the loop
    bound is a Class-K comparison, never an ALU magnitude)."""
    n = 0
    x = _FRACTAL_Q1
    while x > r:
        x = x / _FRACTAL_Q2
        n += 1
    return n


def fractal_spectrum(R, branches, *, log_terms: int = 25) -> Dict[str, object]:
    """Read a self-similar lattice's spectral-decimation structure — the Ch-2
    (quasi-periodic / fractal) DUAL of :func:`resonant_spectrum` (F686 / F974).

    Where :func:`resonant_spectrum` reads a symmetric Laplacian's FLAT
    eigenspectrum (one eigensolve), ``fractal_spectrum`` reads a self-similar
    lattice's **SPECTRAL-DECIMATION** structure: the spectrum is the ITERATED
    PREIMAGE of the renormalization map ``R`` (a decimation :class:`~srmech.math.poly.Poly`
    with a fixed point at the trivial eigenvalue, ``R(0)=0``), NOT a flat list.

    Grounded on the Sierpinski gasket: on the NORMALIZED Laplacian the decimation
    is exactly ``R(z)=z(5−4z)`` (measured — Rammal 1984; Fukushima & Shima,
    *Potential Analysis* 1 (1992) 1–35, OA-attested via the arXiv:1505.05855
    restatement; the paywalled DOIs are motivation-only).

    Args:
        R: the spectral-decimation map — a :class:`~srmech.math.poly.Poly` (or an
            ascending-degree coefficient sequence, coerced with
            :meth:`~srmech.math.poly.Poly.from_coeffs`). Must be degree ``≥ 2``
            with ``R(0) = 0`` and ``R'(0) > 1``.
        branches: the number of self-similar copies (an int ``≥ 2``).
        log_terms: INERT since rc320 (kept for back-compat; a follow-up rc
            removes it). It fed ``rational.log``'s ``terms`` knob, which the Q61
            cascade always ignored; rc320 removed that knob, so ``log_terms`` no
            longer threads anywhere and the log is the exact Q61 rational. Passing
            it changes nothing.

    Returns:
        A dict with:

        * ``"decimation_map"`` — the exact renormalization ``Poly`` ``R``
          (Class-L ↔ operand).
        * ``"scale"`` — ``R'(0)``, the exact-``Q`` per-level eigenvalue-shrink
          factor (the Laplacian scaling).
        * ``"branches"`` — the self-similar copy count.
        * ``"self_similarity_dim"`` — the fracton (spectral) dimension
          ``d_s = 2·log(branches)/log(scale)`` as a Class-N ``best_rational``
          ``(num, den)`` anchor (``2·log3/log5 ≈ 1.36521`` for the gasket).
        * ``"q_octaves_per_level"`` — the F974 bit-exact ``|q|``-meter reading
          ``ceil(log2(scale))`` (3 for the gasket).
        * ``"rung_class"`` — ``"constant"``: ONE decimation ``R`` iterated is
          memoryless-geometric (self-similar), a single ``|q|`` rung.
        * ``"log_period_over_2pi"`` — the discrete-scale-invariance / complex-
          dimension imaginary period ``2π/log(scale)`` divided by ``2π`` (i.e.
          ``1/log(scale)``) as a ``best_rational`` ``(num, den)``
          (``1/ln5 ≈ 0.6213`` for the gasket).
        * ``"spectrum_open"`` — the honest OPEN: the full spectrum is the JULIA
          SET of ``R`` (operand-IRREPRESENTABLE — no finite exact carrier decides
          ``λ ∈ spectrum``).

    Pure orchestration over SHIPPED, already-C-backed ops — ``Poly.derivative`` /
    ``Poly.eval`` (Class-L, ``has_native_poly``), Class-N ``log`` /
    ``best_rational`` (C-backed), and the F974 ``_octaves`` ``|q|``-meter — so it
    adds NO new numerical kernel and ships **non_compute** (no dedicated C peer;
    the ``from_bodies`` / ``cooccurrence_edges`` precedent — everything-mirrors is
    satisfied because every underlying op is already C-mirrored). Exact-``Q``; no ``abs()`` (the ``|q|``-meter is a Class-K comparison; ``log``
    is the Class-N float-projection surface reading the bit pattern exactly).

    Raises:
        ValueError: ``R`` not a Poly / coercible sequence, ``R.degree < 2``,
            ``R(0) ≠ 0``, ``R'(0) ≤ 1``, or ``branches < 2``.
    """
    from ..math import rational as _rational  # best_rational (N) + log (N; = calculus.log)
    from ..math.poly import Poly               # exact-ℚ decimation polynomial carrier (lazy)

    # R may be a Poly OR an ascending-degree coefficient sequence — coerce the
    # latter (the ToolEntry/MCP surface can hand a coeff list; the "Poly" coercer
    # passes a list through, so the op coerces it here).
    if not isinstance(R, Poly):
        try:
            R = Poly.from_coeffs(R)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "fractal_spectrum: R must be a Poly or an ascending-degree "
                f"coefficient sequence; got {R!r}") from exc
    if R.degree < 2:
        raise ValueError("fractal_spectrum: R must be a degree>=2 decimation Poly")
    if R.eval(0) != Q(0, 1):
        raise ValueError(
            "fractal_spectrum: R(0) must be 0 (fixed point at the trivial eigenvalue)")
    if branches < 2:
        raise ValueError("fractal_spectrum: branches must be >= 2")

    # SCALE = R'(0) = the exact per-level eigenvalue-shrink factor (the Laplacian
    # scaling) — the Class-L renormalization derivative at the trivial fixed point.
    scale = R.derivative().eval(0)              # exact Q
    if scale <= _FRACTAL_Q1:
        raise ValueError(
            "fractal_spectrum: R'(0) must be > 1 (contraction toward 0 under preimage)")
    si = int(scale) if scale.denominator == 1 else None

    # SELF-SIMILARITY (fracton / spectral) DIMENSION d_s = 2 log(branches)/log(scale).
    # rc320: `rational.log` dropped its always-ignored `terms` knob (the Q61
    # cascade never used it), so `log_terms` no longer threads anywhere — the log
    # is the exact Q61 rational, byte-identical to every prior rc. `log_terms` is
    # kept on the signature for back-compat but is now INERT (a follow-up rc
    # removes it); passing it changes nothing.
    lb = _rational.log(branches)
    ls = _rational.log(
        si if si is not None else float(scale.numerator) / scale.denominator)
    ds = (_FRACTAL_Q2 * lb) / ls                # Q ratio of the exact Q61 logs
    d_s = _rational.best_rational(ds.numerator, ds.denominator, 10 ** 9)

    # F974 |q|-METER: octaves per level = ceil(log2(scale)); a SINGLE R iterated is
    # memoryless-geometric -> a CONSTANT / one-|q| rung.
    q_oct = _octaves(_FRACTAL_Q1 / scale)

    # DISCRETE-SCALE-INVARIANCE / complex-dimension imaginary period = 2*pi / log(scale).
    inv_ls = _FRACTAL_Q1 / ls
    period_over_2pi = _rational.best_rational(
        inv_ls.numerator, inv_ls.denominator, 10 ** 9)

    return {
        "decimation_map": R,                    # the exact renormalization Poly (Class-L↔operand)
        "scale": scale,                         # R'(0), exact Q
        "branches": branches,
        "self_similarity_dim": d_s,             # (num, den) Class-N anchor of 2 log(b)/log(scale)
        "q_octaves_per_level": q_oct,           # F974 |q|-meter reading of the scale
        "rung_class": "constant",               # constant = self-similar (one |q| iterated)
        "log_period_over_2pi": period_over_2pi,  # complex-dimension period / 2pi
        "spectrum_open": (
            "the full spectrum = the JULIA SET of the decimation map R "
            "(operand-IRREPRESENTABLE: no finite exact carrier decides "
            "lambda-in-spectrum). candidate next-theory: complex dynamics of "
            "rational maps / spectral-decimation Julia-set theory"),
    }


# =====================================================================
# §Ch-2b — fold_encode / fold_spectrum: the BIDIRECTIONAL translation
# between a stored HDC fold and a self-similar lattice's SPECTRAL-
# DECIMATION structure (task #697; the "Q2 reader made LITERAL"). Where
# fractal_spectrum(R, branches) reads the decimation from an EXPLICIT
# Poly R, these two ops read/write the decimation through a STORED
# Klein-4 HDC FOLD — a translation layer that runs BOTH directions.
#
# The two directions are ASYMMETRIC by the nature of HDC, and THAT
# asymmetry is the design:
#   fold_encode  (params -> fold): EXACT / total / deterministic. The
#     decimation Poly R's coefficients + the branch count are role-filler
#     bound into a single lossy Klein-4 bundle (the cooccurrence_fold
#     store shape; F584/F758).
#   fold_spectrum(fold -> params): a SIMILARITY / CLEANUP-MEMORY readout,
#     NOT exact. The bundle is LOSSY BY DESIGN, so reading the decimation
#     back is a cleanup-memory recovery — it returns the fractal_spectrum
#     params PLUS an explicit similarity/confidence readout, and when the
#     crosstalk overwhelms the signal it returns an HONEST "unrecovered"
#     verdict, NEVER a silent wrong Poly.
#
# Pure orchestration over shipped, already-C-backed ops (klein4_role /
# klein4_bind / klein4_bundle / klein4_match_count / klein4_similarity +
# Poly.from_coeffs + fractal_spectrum's own helpers) — adds NO new
# numerical kernel, so BOTH ship non_compute (the cooccurrence_fold /
# from_bodies precedent; no dedicated C peer). numpy-free; no abs().
# =====================================================================

# The HDC bundle-capacity floor, as a multiple of the stored-pair count.
# A role-filler bundle of ``k`` bound pairs resolves cleanly only when the
# width ``D`` comfortably exceeds ``k`` — bundle capacity is LINEAR in the
# stored-item count (Kanerva 2009, *Hyperdimensional Computing*, Cognitive
# Computation 1, 139). Below ``D ~ 2k`` the fold is DEGENERATE: two
# different value assignments can bundle to the SAME vector, a genuine
# information-theoretic ambiguity no reader can resolve. ``4×`` is the
# measured comfortable floor (it eliminates the sub-capacity silent
# collisions across the degree-2..4 decimation Polys while passing every
# high-dim recovery). NOT a magic number — the linear-capacity structure
# constant with a measured safety multiple.
_FOLD_CAPACITY_MULT = 4

# The confident-cleanup separation floor: the winning value code must beat
# the runner-up by at least this Klein-4 similarity margin. Baseline random
# Klein-4 similarity is 1/4 (two independent {0,1} bits per coordinate), so
# a 1/10 margin is a clear separation above chance crosstalk.
_FOLD_MARGIN_FLOOR = Q(1, 10)

#: The slot name carrying the branch count in a fold store.
_FOLD_BRANCH_SLOT = "branches"


def _fold_val_token(q: "Q") -> str:
    """Canonical value-token string for an exact-``Q`` coefficient: ``'num/den'``
    (``Q`` keeps ``den > 0``). The token is the cleanup-memory key — a value's
    Klein-4 code is ``klein4_role`` keyed deterministically by this string, so
    the SAME coefficient always maps to the SAME code (the recovery key)."""
    return f"{q.numerator}/{q.denominator}"


def _fold_parse_token(tok: str) -> "Q":
    """Parse a ``'num/den'`` value-token back to an exact ``Q`` (the inverse of
    :func:`_fold_val_token`)."""
    num_s, den_s = tok.split("/")
    return Q(int(num_s), int(den_s))


def fold_encode(R, branches, *, dim, seed=0):
    """Encode a spectral-decimation structure INTO a stored HDC fold — the
    EXACT / total FORWARD direction of the #697 bidirectional translation.

    This is the WRITE half of the "Q2 reader made LITERAL": the decimation map
    ``R`` (a :class:`~srmech.math.poly.Poly`, ``R(0)=0``) and the branch count
    are folded into a single Klein-4 bundle — a **role-filler record** in the
    shape of :func:`srmech.math.hdc.cooccurrence_fold`'s holographic store. Each
    coefficient slot ``c{i}`` (and the ``branches`` slot) gets a deterministic
    **role** code (:func:`~srmech.math.hdc.klein4_role`, keyed by the slot
    name); each distinct coefficient VALUE gets a deterministic **filler** code
    (seeded by its ``'num/den'`` token). The fold is the
    :func:`~srmech.math.hdc.klein4_bundle` superposition of the role⊗value binds
    ``bind(role_slot, code_value)`` — one lossy Klein-4 hypervector holding the
    whole decimation.

    This direction is **EXACT and total**: given ``(R, branches, dim, seed)`` the
    fold + codebooks are fully determined (bit-for-bit reproducible). The
    LOSSINESS lives entirely in the READ (:func:`fold_spectrum`) — recovering
    which slot holds which value from the superposition is a cleanup-memory
    similarity read, NOT an exact inverse (the HDC asymmetry, F584).

    Args:
        R: the spectral-decimation map — a :class:`~srmech.math.poly.Poly` (or an
            ascending-degree coefficient sequence coerced with
            :meth:`~srmech.math.poly.Poly.from_coeffs`). Degree ``>= 2``.
        branches: the number of self-similar copies (an int ``>= 2``).
        dim: the Klein-4 width ``D`` of the fold (one uint8 per coordinate). For a
            confident round-trip pick ``dim`` comfortably above
            ``4·(degree + 2)`` (the HDC bundle-capacity floor); the gasket
            (``R=z(5−4z)``, 4 bound pairs) round-trips reliably at ``dim >= 512``.
        seed: base seed for the deterministic role / value codes (default 0).

    Returns:
        A fold store (JSON-native once its :class:`~srmech.math.hdc.HV` values are
        serialised, exactly like :func:`~srmech.math.hdc.cooccurrence_fold`):

        * ``"fold"`` — the single Klein-4 :class:`~srmech.math.hdc.HV` bundle
          (the lossy superposition of every role⊗value bind).
        * ``"roles"`` — ``{slot: HV}`` the deterministic per-slot role codes.
        * ``"codes"`` — ``{value_token: HV}`` the value codebook (the cleanup
          alphabet, mirroring cooccurrence_fold's ``codes``).
        * ``"coeff_slots"`` — ``["c0", …, "c{degree}"]`` the coefficient slot
          names in ascending degree.
        * ``"branch_slot"`` — ``"branches"``.
        * ``"slots"`` — the full ordered slot list (``coeff_slots + [branch_slot]``).
        * ``"dim"`` — ``D``; ``"seed"`` — the base seed; ``"n_pairs"`` — the
          number of bound pairs (``degree + 2``).

    Pure orchestration over shipped Klein-4 ops → adds NO new numerical kernel,
    ships **non_compute** (the cooccurrence_fold / from_bodies precedent). No ``abs()``.

    Raises:
        ValueError: ``R`` not a Poly / coercible sequence, ``R.degree < 2``,
            ``branches < 2``, or ``dim < 1``.
    """
    from ..math import hdc as _hdc                # klein4_role / bind / bundle (M)
    from ..math.poly import Poly                   # exact-ℚ decimation carrier (lazy)

    if not isinstance(R, Poly):
        try:
            R = Poly.from_coeffs(R)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "fold_encode: R must be a Poly or an ascending-degree coefficient "
                f"sequence; got {R!r}") from exc
    if R.degree < 2:
        raise ValueError("fold_encode: R must be a degree>=2 decimation Poly")
    if branches < 2:
        raise ValueError("fold_encode: branches must be >= 2")
    if dim < 1:
        raise ValueError("fold_encode: dim must be >= 1")

    coeffs = R.coeffs
    coeff_slots = [f"c{i}" for i in range(len(coeffs))]
    slots = coeff_slots + [_FOLD_BRANCH_SLOT]

    # Deterministic per-slot ROLE codes (the binding keys).
    roles = {
        s: _hdc.klein4_role(dim, "ROLE:" + s, seed)
        for s in slots
    }

    # Deterministic per-value FILLER codes (the cleanup alphabet). A repeated
    # coefficient value reuses its one code (so the codebook is value-keyed).
    codes: Dict[str, object] = {}

    def code_for(tok: str):
        c = codes.get(tok)
        if c is None:
            c = _hdc.klein4_role(dim, "VAL:" + tok, seed)
            codes[tok] = c
        return c

    # Fold = klein4_bundle of the role⊗value binds (Class-M superposition).
    pairs = []
    for i, c in enumerate(coeffs):
        tok = _fold_val_token(c)
        pairs.append(_hdc.klein4_bind(roles[coeff_slots[i]], code_for(tok)))
    branch_tok = f"{int(branches)}/1"
    pairs.append(_hdc.klein4_bind(roles[_FOLD_BRANCH_SLOT], code_for(branch_tok)))
    fold = _hdc.klein4_bundle(pairs)

    return {
        "fold": fold,
        "roles": roles,
        "codes": codes,
        "coeff_slots": coeff_slots,
        "branch_slot": _FOLD_BRANCH_SLOT,
        "slots": slots,
        "dim": dim,
        "seed": seed,
        "n_pairs": len(slots),
    }


def fold_spectrum(fold, *, log_terms: int = 25,
                  margin_floor=None, capacity_mult=None) -> Dict[str, object]:
    """Read a stored HDC fold BACK to its spectral-decimation params — the
    SIMILARITY / CLEANUP-MEMORY READ direction of the #697 bidirectional
    translation (the "Q2 reader made LITERAL").

    This is the READ half, and it is **NOT the exact inverse** of
    :func:`fold_encode` — it CANNOT be, because the fold is a LOSSY Klein-4
    superposition (F584). For each slot it binds the role back against the fold
    (:func:`~srmech.math.hdc.klein4_unbundle` = self-inverse XOR) and cleans the
    value-plus-crosstalk estimate up against the value codebook
    (``argmax_token similarity(unbundle, codes[token])`` — the cooccurrence_fold
    cleanup-memory pattern, ``klein4_similarity(bundles[a], codes[b])``). The
    recovered tokens rebuild the decimation ``Poly`` and the branch count, and —
    **where the recovery is confident** — feed the SAME orchestration as
    :func:`fractal_spectrum`, producing the IDENTICAL spectral-decimation dict.

    The honesty boundary is load-bearing — the read NEVER returns a wrong Poly
    silently. A recovery is accepted (``verdict == "recovered"``) ONLY when all
    three gates hold:

    1. **Capacity** — ``dim >= capacity_mult · n_pairs`` (default ``4·n_pairs``).
       Below the HDC bundle-capacity floor the fold is degenerate and two
       assignments can collide to the same vector; the read refuses to claim.
    2. **Separation** — every slot's winning value beats the runner-up by at
       least ``margin_floor`` similarity (default ``1/10``; baseline chance is
       ``1/4``). An ambiguous near-tie is not a recovery.
    3. **Self-consistency** — re-bundling the recovered role⊗value binds
       reproduces the stored fold **bit-for-bit** (``fold_consistency == 1``).
       Because :func:`fold_encode` is EXACT, a fully-correct recovery reconstructs
       the fold identically; any wrong slot perturbs the bundle. This is the
       op_provenance one-sided honesty (``"EQUAL"`` = provably reproduces the
       fold; ``"UNKNOWN"`` = cannot prove — NEVER a false claim).

    When any gate fails the op returns the honest **unrecovered** verdict — the
    similarity/confidence readout, the reason, and a ``spectrum_open``-style OPEN
    message — WITHOUT a ``decimation_map`` / spectral params (the #717
    honestly-inexact / carrier-ladder project-error discipline).

    Args:
        fold: a fold store from :func:`fold_encode` (or the JSON-serialised
            equivalent — the Klein-4 values may be :class:`~srmech.math.hdc.HV`
            OR plain uint8 lists; both ride the klein4 coercion).
        log_terms: the Class-N ``log`` series-truncation depth forwarded to
            :func:`fractal_spectrum` on a confident recovery (default 25).
        margin_floor: override the separation gate (an exact ``Q`` / ``(num,den)``
            / int; default ``_FOLD_MARGIN_FLOOR = 1/10``).
        capacity_mult: override the capacity-floor multiple (default ``4``).

    Returns:
        On a confident recovery — the full :func:`fractal_spectrum` dict
        (``decimation_map`` / ``scale`` / ``branches`` / ``self_similarity_dim`` /
        ``q_octaves_per_level`` / ``rung_class`` / ``log_period_over_2pi`` /
        ``spectrum_open``) PLUS: ``"verdict": "recovered"``, ``"op_provenance":
        "EQUAL"``, ``"similarity"`` (the weakest slot's cleanup similarity, ``Q``),
        ``"confidence"`` (the weakest slot's separation margin, ``Q``),
        ``"fold_consistency"`` (the bit-identical-reconstruction similarity, ``Q``,
        ``== 1``), and ``"per_slot"`` (``{slot: {value, similarity, margin}}``).

        On an unrecovered read — ``{"verdict": "unrecovered", "op_provenance":
        "UNKNOWN", "similarity", "confidence", "fold_consistency", "per_slot",
        "reason", "spectrum_open"}`` and NO decimation Poly / spectral params.

    Pure orchestration over shipped ops → **non_compute**. No
    ``abs()`` (the similarity/margin comparisons are exact-``Q`` Class-K reads).

    A :class:`RecoverableFold` (rc125) is ALSO accepted: when it carries an
    exact seed, this reads R EXACTLY from the carried complement (exact at ANY
    dim, including below the rc124 capacity floor); when it is a bare/"found"
    fold (no seed) this falls back to the rc124 similarity read on its bundle
    (the honest ``unrecovered`` path preserved).

    Raises:
        ValueError: ``fold`` is not a fold-store dict / is missing required keys.
    """
    # rc125: a RecoverableFold pair carrier reads through its own path — EXACT
    # recovery from the carried complement, or the rc124 bare fallback.
    if isinstance(fold, RecoverableFold):
        return fold._read_spectrum(
            log_terms=log_terms, margin_floor=margin_floor,
            capacity_mult=capacity_mult)

    from ..math import hdc as _hdc                # klein4 bind / bundle / similarity

    if not isinstance(fold, dict):
        raise ValueError(
            "fold_spectrum: fold must be a fold-store dict from fold_encode "
            "(or a RecoverableFold); "
            f"got {type(fold).__name__}")
    try:
        stored = fold["fold"]
        roles = fold["roles"]
        codes = fold["codes"]
        coeff_slots = list(fold["coeff_slots"])
        branch_slot = fold["branch_slot"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "fold_spectrum: fold-store missing a required key "
            "(fold / roles / codes / coeff_slots / branch_slot)") from exc
    if not codes:
        raise ValueError("fold_spectrum: fold-store has an empty value codebook")

    slots = coeff_slots + [branch_slot]
    n_pairs = len(slots)

    cap_mult = _FOLD_CAPACITY_MULT if capacity_mult is None else int(capacity_mult)
    if margin_floor is None:
        marg_floor = _FOLD_MARGIN_FLOOR
    elif isinstance(margin_floor, Q):
        marg_floor = margin_floor
    elif isinstance(margin_floor, tuple):
        marg_floor = Q(margin_floor[0], margin_floor[1])
    else:
        marg_floor = Q(int(margin_floor), 1)

    # The true width D = the stored fold's coordinate count (NOT the metadata,
    # so a hand-built store still reads honestly). Every code must share it —
    # klein4_match_count raises on a length mismatch, surfacing a corrupt store.
    d = len(_hdc._as_klein4_buf(stored, "fold_spectrum.fold"))

    # ── Per-slot cleanup-memory recovery ────────────────────────────────────
    per_slot: Dict[str, object] = {}
    recovered_tok: Dict[str, str] = {}
    min_top: Optional[Q] = None
    min_margin: Optional[Q] = None
    for s in slots:
        # Bind the role back against the fold = unbundle (self-inverse XOR) →
        # the value-plus-crosstalk estimate; clean it up against the codebook.
        probe = _hdc.klein4_bind(stored, roles[s])
        ranked = sorted(
            ((_hdc.klein4_match_count(probe, code), tok)
             for tok, code in codes.items()),
            key=lambda kv: kv[0], reverse=True)
        top_count, top_tok = ranked[0]
        second_count = ranked[1][0] if len(ranked) > 1 else 0
        top_sim = Q(top_count, d)
        margin = Q(top_count - second_count, d)
        recovered_tok[s] = top_tok
        per_slot[s] = {"value": top_tok, "similarity": top_sim, "margin": margin}
        if min_top is None or top_sim < min_top:
            min_top = top_sim
        if min_margin is None or margin < min_margin:
            min_margin = margin

    # ── Holistic self-consistency: re-bundle the recovered binds and compare
    # the reconstruction to the stored fold BIT-FOR-BIT. fold_encode is exact,
    # so a fully-correct recovery reconstructs identically (consistency == 1).
    recon = _hdc.klein4_bundle(
        [_hdc.klein4_bind(roles[s], codes[recovered_tok[s]]) for s in slots])
    consistency = _hdc.klein4_similarity(recon, stored)   # Q; == 1 iff identical

    # ── The three-gate honesty verdict ──────────────────────────────────────
    capacity_ok = d >= cap_mult * n_pairs
    margin_ok = min_margin >= marg_floor
    self_consistent = consistency == Q(1, 1)
    recovered = capacity_ok and margin_ok and self_consistent

    if not recovered:
        reasons = []
        if not capacity_ok:
            reasons.append(
                f"below HDC bundle-capacity floor (dim {d} < {cap_mult}*{n_pairs} "
                f"= {cap_mult * n_pairs})")
        if not margin_ok:
            reasons.append(
                f"cleanup separation below floor (min margin {float(min_margin):.4f}"
                f" < {float(marg_floor):.4f})")
        if not self_consistent:
            reasons.append(
                "recovered assignment does not reconstruct the fold bit-for-bit "
                f"(consistency {float(consistency):.4f} < 1)")
        return {
            "verdict": "unrecovered",
            "op_provenance": "UNKNOWN",
            "similarity": min_top,
            "confidence": min_margin,
            "fold_consistency": consistency,
            "per_slot": per_slot,
            "reason": "; ".join(reasons),
            "spectrum_open": (
                "the stored fold's decimation is NOT recoverable at this "
                "dim/seed — the Klein-4 superposition crosstalk overwhelmed the "
                "signal (F584 lossy-by-design). Honestly UNKNOWN, NOT a wrong "
                "Poly (#717 honestly-inexact). Re-encode at a higher dim (>= "
                f"{cap_mult * n_pairs}) for a confident read."),
        }

    # ── Confident recovery: rebuild R + branches, run the SAME fractal_spectrum
    # orchestration → the identical spectral-decimation dict. ────────────────
    from ..math.poly import Poly

    coeffs = [_fold_parse_token(recovered_tok[s]) for s in coeff_slots]
    R = Poly.from_coeffs(coeffs)
    branch_q = _fold_parse_token(recovered_tok[branch_slot])
    assert branch_q.denominator == 1, \
        "fold_spectrum: recovered branch token must be an integer"
    branches = int(branch_q.numerator)

    out = dict(fractal_spectrum(R, branches, log_terms=log_terms))
    out["verdict"] = "recovered"
    out["op_provenance"] = "EQUAL"
    out["similarity"] = min_top
    out["confidence"] = min_margin
    out["fold_consistency"] = consistency
    out["per_slot"] = per_slot
    return out


# =====================================================================
# §Ch-2c — RecoverableFold: the HarmonicMaass-shaped PAIR carrier that
# makes a generated fold recover EXACTLY at ANY dim (task #723; the direct
# follow-on to rc124). rc124's fold_spectrum reads a LOSSY bundle by a
# similarity/cleanup pass — exact WHEN the fold has capacity, honest-
# `unrecovered` below the dim>=4·n_pairs floor. rc125 makes recovery exact
# at ANY dim by ATTACHING the exact complement (the generating decimation R),
# following the field–excitation recoverability principle: a lossy projection
# is recoverable iff you attach the exact complement it dropped.
#
# The shape MIRRORS srmech.apokatastasis.harmonic_maass.HarmonicMaass(hol, shadow) —
# the (holomorphic-part, shadow) pair where "storing the shadow IS storing the
# completion" (the completion f⁻ is the Eichler integral of the stored shadow,
# recoverable not stored). Here the pair is (lossy_bundle, exact_seed_R) where
# "storing R IS storing the recovery":
#   lossy_bundle  ↔ hol     — the PRIMARY / lossy projected part (the fold).
#   exact_seed_R  ↔ shadow  — the EXACT COMPLEMENT whose presence makes the
#                             pair fully recoverable/decidable (the decimation).
# Pure orchestration + data over shipped ops (rc124 fold_encode/fold_spectrum
# + rc117 op_provenance + Poly + fractal_spectrum) → NO new numerical kernel,
# NO new C peer (the carrier is data). numpy-free; no abs().
# =====================================================================

class RecoverableFold:
    """A generated HDC fold PAIRED with the exact complement that recovers it —
    the RECOVERABILITY analogue of :class:`~srmech.apokatastasis.harmonic_maass.HarmonicMaass`
    ``(hol, shadow)`` (rc71; task #723). Immutable.

    A rc124 :func:`fold_encode` bundle is a LOSSY Klein-4 superposition —
    :func:`fold_spectrum` recovers it by a similarity/cleanup pass that is
    exact only WHEN the fold has capacity (``dim >= 4·n_pairs``) and honestly
    ``unrecovered`` below that floor. This pair makes recovery EXACT at ANY dim
    by carrying the exact generating decimation ``R`` alongside the bundle — the
    field–excitation recoverability principle: a lossy projection is recoverable
    iff you attach the exact complement it dropped.

    Mirrors ``HarmonicMaass(hol, shadow)``:

    - :attr:`lossy_bundle` ↔ ``hol`` — the PRIMARY / lossy projected part (the
      rc124 fold store dict).
    - :attr:`exact_seed_R` ↔ ``shadow`` — the EXACT COMPLEMENT (the decimation
      :class:`~srmech.math.poly.Poly`) whose presence makes the pair fully
      recoverable/decidable. ``None`` for a bare/"found" fold (a real-corpus
      ``cooccurrence_fold`` with no generator) — then recovery falls back to the
      rc124 similarity read (honest ``unrecovered`` below the floor preserved).
    - :meth:`complement` ↔ ``HarmonicMaass.xi()`` — returns the exact complement
      (``R``); storing it IS storing the recovery (the pair's defining property).

    Read it with :func:`fold_spectrum` (which dispatches on this type) or the
    :meth:`recover` shortcut. Compare identity with :func:`fold_identity`."""

    __slots__ = ("_lossy_bundle", "_exact_seed_R", "_branches", "_dim", "_seed")

    def __init__(self, lossy_bundle, exact_seed_R, *, branches=None) -> None:
        if not isinstance(lossy_bundle, dict):
            raise TypeError(
                "RecoverableFold(lossy_bundle, exact_seed_R): lossy_bundle must "
                "be a fold-store dict from fold_encode; got "
                f"{type(lossy_bundle).__name__}")
        from ..math.poly import Poly                # exact-ℚ decimation carrier (lazy)
        if exact_seed_R is not None:
            if not isinstance(exact_seed_R, Poly):
                try:
                    exact_seed_R = Poly.from_coeffs(exact_seed_R)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "RecoverableFold: exact_seed_R must be a Poly (or an "
                        "ascending-degree coefficient sequence), or None for a "
                        "bare fold") from exc
            if branches is None:
                raise ValueError(
                    "RecoverableFold: branches is required when an exact seed "
                    "is carried (it is part of the recovered identity)")
            branches = int(branches)
            if branches < 2:
                raise ValueError("RecoverableFold: branches must be >= 2")
        self._lossy_bundle = lossy_bundle
        self._exact_seed_R = exact_seed_R
        self._branches = branches
        self._dim = lossy_bundle.get("dim")
        self._seed = lossy_bundle.get("seed", 0)

    # ── accessors (the HarmonicMaass-shaped pair) ──────────────────────────────
    @property
    def lossy_bundle(self) -> Dict[str, object]:
        """The rc124 lossy Klein-4 fold store (the PRIMARY projected part;
        ↔ ``HarmonicMaass.hol``)."""
        return self._lossy_bundle

    @property
    def exact_seed_R(self):
        """The exact generating decimation :class:`~srmech.math.poly.Poly` ``R``
        (the EXACT COMPLEMENT; ↔ ``HarmonicMaass.shadow``), or ``None`` for a
        bare fold. Storing it IS storing the recovery."""
        return self._exact_seed_R

    @property
    def has_seed(self) -> bool:
        """True iff the exact complement is carried (recovery is EXACT at any
        dim); False for a bare fold (recovery is the rc124 similarity read)."""
        return self._exact_seed_R is not None

    @property
    def branches(self) -> Optional[int]:
        """The self-similar copy count carried with the seed (``None`` for a
        bare fold)."""
        return self._branches

    @property
    def dim(self) -> Optional[int]:
        """The Klein-4 width ``D`` of the stored lossy bundle."""
        return self._dim

    def complement(self):
        """The exact complement ``R`` that recovers this fold (↔
        ``HarmonicMaass.xi()`` returning the shadow). ``None`` for a bare fold."""
        return self._exact_seed_R

    # ── the reader (exact-from-seed, or the rc124 bare fallback) ───────────────
    def recover(self, *, log_terms: int = 25, margin_floor=None,
                capacity_mult=None) -> Dict[str, object]:
        """Recover the spectral-decimation params — EXACT from the carried seed
        (at ANY dim), or the rc124 similarity read for a bare fold. Equivalent
        to ``fold_spectrum(self)``."""
        return self._read_spectrum(
            log_terms=log_terms, margin_floor=margin_floor,
            capacity_mult=capacity_mult)

    def _read_spectrum(self, *, log_terms: int = 25, margin_floor=None,
                       capacity_mult=None) -> Dict[str, object]:
        if self._exact_seed_R is None:
            # Bare/"found" fold — fall back to the rc124 similarity/cleanup read
            # on the stored bundle (honest ``unrecovered`` below the floor).
            return fold_spectrum(
                self._lossy_bundle, log_terms=log_terms,
                margin_floor=margin_floor, capacity_mult=capacity_mult)
        # EXACT recovery from the CARRIED complement — R is carried, not decoded,
        # so this is exact at ANY dim (including dim < 4·n_pairs where the rc124
        # similarity read honestly fails). Feed the SAME fractal_spectrum
        # orchestration → the IDENTICAL spectral-decimation dict.
        out = dict(fractal_spectrum(
            self._exact_seed_R, self._branches, log_terms=log_terms))
        out["verdict"] = "recovered"
        out["op_provenance"] = "EQUAL"
        out["recovery"] = "exact-seed"        # from the carried complement, NOT cleanup
        out["fold_consistency"] = self._seed_consistency()  # Q; ==1 for a genuine pair
        out["similarity"] = _FRACTAL_Q1       # exact recovery: perfect fidelity
        out["confidence"] = _FRACTAL_Q1
        out["identity"] = self.identity()
        return out

    def _seed_consistency(self) -> "Q":
        """Re-encode the carried seed at the stored dim/seed and compare the
        fold BIT-FOR-BIT to the stored lossy bundle — the integrity check that
        the carried complement genuinely GENERATED this bundle (``Q``; ``==1``
        for a pair built by :func:`fold_encode_recoverable`). The op_provenance
        one-sided EQUAL self-check ONE level up: presence-of-complement makes it
        decidable."""
        from ..math import hdc as _hdc            # klein4_similarity (M)
        stored = self._lossy_bundle.get("fold")
        if stored is None or self._dim is None:
            return Q(0, 1)
        regen = fold_encode(
            self._exact_seed_R, self._branches, dim=self._dim, seed=self._seed)
        return _hdc.klein4_similarity(regen["fold"], stored)   # Q; ==1 iff identical

    # ── the DECIDABLE identity (present-complement only) ───────────────────────
    def identity(self) -> Optional[str]:
        """The op_provenance chain-hash of this fold's EXACT recoverable content
        (the decimation ``R`` coefficients + the branch count) via
        :func:`srmech.introspect.op_provenance.lossy_projection_record` — the fold's
        DECIDABLE identity when the complement is present, else ``None`` (you
        cannot decide identity from a lossy bundle alone). dim/seed are NOT part
        of the identity: two folds of the same ``(R, branches)`` at different
        dims recover the SAME object and share this address."""
        if self._exact_seed_R is None:
            return None
        from ..introspect import op_provenance as _op  # rc117 canonical machinery (lazy)
        rec = _op.lossy_projection_record(
            "srmech.biology.coupling.fold_encode",
            {"R": list(self._exact_seed_R.coeffs), "branches": int(self._branches)},
        )
        return rec["chain_sha256"]

    def __repr__(self) -> str:
        seed = "None" if self._exact_seed_R is None else \
            f"Poly(deg={self._exact_seed_R.degree})"
        return (f"RecoverableFold(dim={self._dim}, branches={self._branches}, "
                f"exact_seed_R={seed})")


def fold_encode_recoverable(R, branches, *, dim, seed=0) -> "RecoverableFold":
    """Encode a spectral-decimation structure into a RECOVERABLE PAIR — the
    HarmonicMaass-shaped follow-on to :func:`fold_encode` (task #723).

    Produces a :class:`RecoverableFold` PAIR: the rc124 lossy Klein-4 fold store
    (``.lossy_bundle`` ↔ ``HarmonicMaass.hol``) AND the exact generating
    decimation ``R`` (``.exact_seed_R`` ↔ ``HarmonicMaass.shadow``). Because R
    is CARRIED, :func:`fold_spectrum` on the pair recovers EXACTLY at ANY dim —
    including ``dim < 4·n_pairs``, where the rc124 bare read honestly fails
    (crosstalk overwhelms the lossy bundle). "Storing R IS storing the
    recovery."

    rc124's bare :func:`fold_encode` is UNCHANGED (it still returns the bare
    fold-store dict); this is the additive recoverable path.

    Args:
        R: the spectral-decimation map — a :class:`~srmech.math.poly.Poly` (or an
            ascending-degree coefficient sequence coerced with
            :meth:`~srmech.math.poly.Poly.from_coeffs`). Degree ``>= 2``.
        branches: the number of self-similar copies (an int ``>= 2``).
        dim: the Klein-4 width ``D`` of the lossy bundle (``>= 1``). Recovery is
            exact at ANY dim (the seed is carried); dim only affects the LOSSY
            bundle's rc124 similarity read.
        seed: base seed for the deterministic role / value codes (default 0).

    Returns:
        A :class:`RecoverableFold` pair ``(lossy_bundle, exact_seed_R=R)``.

    Pure orchestration + data over shipped ops → NO new numerical kernel, NO new
    C peer. No ``abs()``.

    Raises:
        ValueError: ``R`` not a Poly / coercible sequence, ``R.degree < 2``,
            ``branches < 2``, or ``dim < 1`` (surfaced by :func:`fold_encode`).
    """
    from ..math.poly import Poly                    # exact-ℚ decimation carrier (lazy)
    if not isinstance(R, Poly):
        try:
            R = Poly.from_coeffs(R)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "fold_encode_recoverable: R must be a Poly or an ascending-"
                f"degree coefficient sequence; got {R!r}") from exc
    bundle = fold_encode(R, branches, dim=dim, seed=seed)   # rc124 lossy store
    return RecoverableFold(bundle, R, branches=branches)


def fold_identity(a, b) -> str:
    """The RECOVERABLE-FOLD identity verdict — ``"EQUAL"`` / ``"NOT_EQUAL"`` /
    ``"UNKNOWN"`` (task #723; the hybrid's second half).

    Two :class:`RecoverableFold`\\ s are the SAME fold iff they recover the same
    ``(R, branches)`` — decided via each fold's :meth:`RecoverableFold.identity`
    (the op_provenance canonical-hash of the ``fold_encode`` op with ``R`` +
    branches as the pinned EXACT inputs; rc117 machinery reused for
    consistency):

    * **EQUAL / NOT_EQUAL when BOTH carry the exact complement** — the identity
      hashes are decidable because the inputs are EXACT: equal hash ⟹ EQUAL,
      different hash ⟹ NOT_EQUAL (a genuinely different recoverable object).
    * **UNKNOWN when EITHER fold lacks the complement** — you CANNOT decide
      identity from a lossy bundle alone (the recoverability principle: identity
      is decidable only when you hold the complement). NEVER a false
      EQUAL/NOT_EQUAL from lossy bundles.

    This IS :func:`srmech.introspect.op_provenance.op_verdict`'s EQUAL/UNKNOWN
    one-sidedness — but here the one-sidedness comes from PRESENCE-vs-ABSENCE of
    the complement, and the exactness of the carried complement is what upgrades
    the EQUAL/UNKNOWN pair to the DECIDABLE EQUAL/NOT_EQUAL when both are
    present (op_verdict cannot answer NOT_EQUAL because program-equality is
    undecidable; here the operand IS exact, so inequality is decidable).

    Raises:
        ValueError: either operand is not a :class:`RecoverableFold`.
    """
    if not isinstance(a, RecoverableFold) or not isinstance(b, RecoverableFold):
        raise ValueError(
            "fold_identity: both operands must be RecoverableFold; got "
            f"{type(a).__name__} and {type(b).__name__}")
    ha, hb = a.identity(), b.identity()
    if ha is None or hb is None:
        # A lossy bundle with no complement carries no decidable identity.
        return "UNKNOWN"
    return "EQUAL" if ha == hb else "NOT_EQUAL"


__all__ = ["signed_sum_squared", "resonant_spectrum", "resonant_spectrum_sparse",
           "from_bodies", "fractal_spectrum", "fold_encode", "fold_spectrum",
           "RecoverableFold", "fold_encode_recoverable", "fold_identity"]
