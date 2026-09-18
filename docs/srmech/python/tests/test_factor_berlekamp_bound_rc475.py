"""rc475 (`#T1188`) — the equal-degree split is DETERMINISTIC and its loops carry
a PROVEN STATIC bound.

WHAT REPLACED WHAT. Through rc474 ``_equal_degree_split`` (and its C peer
``fp_equal_degree``) was Cantor–Zassenhaus: draw a random polynomial, raise it to
``(q^d - 1)/2``, gcd, and RETRY on failure — a Las Vegas loop with an EXPECTED
bound and no static one, spelled ``do { ... } while (lr <= 1)`` in C and
``while True:`` in Python. rc475 replaces it with Berlekamp: compute the
subalgebra ``{v : v^p = v mod g}`` as ``nullspace((Q - I)^T)`` with
``Q[i] = x^(i*p) mod g``, and separate each block by ``gcd(v - s, part)`` over
every basis vector ``v`` and every shift ``s`` in 𝔽_p. Every loop is then a
``for`` whose trip count is fixed at entry.

THE BOUND THIS FILE ASSERTS IS THE TIGHT ONE, and that is the point of the file.
By CRT the subalgebra has dimension EXACTLY ``k = n/d``, and ANY basis of it
separates every pair. The loose statement — ``k*p`` passes and ``k*p*k`` gcds —
is true, and it is what the shipped docstrings quote. It is NOT the worst case:

  * the constant ``1`` is ALWAYS the first RREF basis vector (column 0 of
    ``(Q - I)^T`` is zero because ``Q[0] = x^0``), it separates nothing, and the
    code skips it — so passes are bounded by ``(k-1)*p``;
  * only parts of degree ``> d`` are gcd'd, and each holds at least 2
    irreducibles — so gcds per pass are bounded by ``floor(k/2)``.

Hence **passes <= (k-1)*p and gcds <= p*(k-1)*floor(k/2)**. Asserting the loose
form instead would leave a 4x slack for a regression to hide under: MEASURED, the
maximum observed fraction is **0.9545** of the tight bound (21 of 22 gcds at
``(p,d,k) = (11,2,3)``) against **0.26** of ``k*p*k``. A ceiling a real
regression cannot reach is not a ceiling.

⚠️ EVERY ASSERTION HERE IS ON A COUNT, NEVER ON A TIME. The static worst case is
reachable in principle: ``p < 100000`` and ``k <= deg <= 48``, so the absolute
bound is ``99991 * 47 * 24`` gcds, and large ``p`` IS reachable from a public op
(``factor_integer_poly`` takes arbitrary integers, and a lead divisible by every
small odd prime skips them all). So the trip count is bounded and the wall clock
is not bounded by any corpus. A timing assertion here would be a flake.

⚠️ THE COUNTING CLONE IS PINNED TO THE SHIPPED FUNCTION. A counter in a copy of
the algorithm measures the copy. Every block below asserts
``clone(block) == _equal_degree_split(block)``, so the counts cannot drift away
from the code that ships without this file going red.

Numpy-free; no native library needed (this is the PURE projection's bound, and
the C peer is the same loop structure by construction — the C side is covered
here only by the source-shape roster at the end).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from srmech.cascade.matrix_cascades import (
    _equal_degree_split, _fp_berlekamp_basis, _fp_divmod, _fp_gcd,
    _fp_make_monic, _fp_trim, _poly_sub_fp,
)

_HERE = Path(__file__).resolve().parent
_C_SRC = _HERE.parent.parent / "c" / "src" / "srmech_factor_poly.c"
_PY_SRC = (_HERE.parent / "srmech" / "cascade" / "matrix_cascades.py")


# ── the corpus: every equal-degree block we can enumerate exactly ─────────────

def _irreducibles(p: int, d: int):
    """Every monic irreducible of degree ``d`` over 𝔽_p, by trial division.

    Enumerated rather than sampled so the block corpus is exact. The COUNT is
    asserted against the closed form in :func:`test_the_enumerator_is_correct`,
    because an enumerator that silently returned a subset would shrink every
    bound test below into a weaker claim that still reads green.
    """
    lower = []
    for e in range(1, d):
        lower += _irreducibles(p, e)
    out = []
    for i in range(p ** d):
        co, t = [], i
        for _ in range(d):
            co.append(t % p)
            t //= p
        g = co + [1]
        if any(_fp_divmod(g, h, p)[1] == [0] for h in lower):
            continue
        out.append(g)
    return out


_IRR_CACHE: "dict[tuple[int, int], list]" = {}


def _irr(p, d):
    if (p, d) not in _IRR_CACHE:
        _IRR_CACHE[(p, d)] = _irreducibles(p, d)
    return _IRR_CACHE[(p, d)]


def _mul(a, b, p):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = (out[i + j] + x * y) % p
    return _fp_trim(out, p)


def _blocks():
    """``(p, d, k, block, factors)`` over a census of equal-degree blocks.

    ``k``-subsets are taken in lexicographic order with a cap per cell rather
    than exhaustively, because ``C(78, 5)`` is 24 million and materialising it
    is what made a previous lane's run look like a slow splitter when it was a
    slow harness.
    """
    out = []
    for p in (3, 5, 7, 11, 13):
        for d in (1, 2, 3):
            irr = _irr(p, d)
            if len(irr) < 2:
                continue
            for k in range(2, 7):
                if len(irr) < k:
                    continue
                made = 0
                idx = list(range(k))
                while made < 24:
                    facs = [irr[i] for i in idx]
                    if (len(facs[-1]) - 1) * k <= 48:
                        block = [1]
                        for f in facs:
                            block = _mul(block, f, p)
                        out.append((p, d, k, block, facs))
                        made += 1
                    # next lexicographic k-subset
                    j = k - 1
                    while j >= 0 and idx[j] == len(irr) - k + j:
                        j -= 1
                    if j < 0:
                        break
                    idx[j] += 1
                    for t in range(j + 1, k):
                        idx[t] = idx[t - 1] + 1
    return out


BLOCKS = _blocks()


def test_the_enumerator_is_correct():
    """The irreducible COUNTS must equal the closed forms.

    ``q`` for ``d = 1``, ``(q^2 - q)/2`` for ``d = 2``, ``(q^3 - q)/3`` for
    ``d = 3``. This is the control that makes the census exact rather than
    merely non-empty: a trial-division bug that dropped half the irreducibles
    would leave every bound assertion below passing on a smaller world.
    """
    for p in (3, 5, 7, 11, 13):
        assert len(_irr(p, 1)) == p, (p, 1)
        assert len(_irr(p, 2)) == (p * p - p) // 2, (p, 2)
        assert len(_irr(p, 3)) == (p ** 3 - p) // 3, (p, 3)


def test_the_block_census_is_not_vacuous():
    assert len(BLOCKS) >= 200, f"{len(BLOCKS)} blocks; >= 200 expected"
    ks = {b[2] for b in BLOCKS}
    assert ks >= {2, 3, 4, 5}, f"k coverage is only {sorted(ks)}"
    ds = {b[1] for b in BLOCKS}
    assert ds == {1, 2, 3}, f"d coverage is only {sorted(ds)}"


# ── the counting clone, pinned to the shipped function ────────────────────────

def _split_counted(f, d, q):
    """A COUNTING clone of ``_equal_degree_split``, statement for statement.

    Kept as a clone rather than as instrumentation on the shipped function
    because the shipped function must stay exactly what ships; the pin in
    :func:`test_the_bound_holds_on_every_block` is what keeps the clone honest.
    """
    g = _fp_make_monic(f, q)
    n = len(g) - 1
    if n == d:
        return [g], 0, 0, 1
    k = n // d
    basis = _fp_berlekamp_basis(g, n, q)
    passes = 0
    gcds = 0
    max_gcds_in_a_pass = 0
    parts = [g]
    for v in basis:
        if len(parts) == k:
            break
        if len(v) <= 1:
            continue
        for s in range(q):
            if len(parts) == k:
                break
            vs = _poly_sub_fp(v, [s % q], q)
            passes += 1
            in_this_pass = 0
            top0 = len(parts)
            for i in range(top0):
                h = parts[i]
                if len(h) - 1 <= d:
                    continue
                gcds += 1
                in_this_pass += 1
                gg = _fp_gcd(vs, h, q)
                if len(gg) < 2 or len(gg) >= len(h):
                    continue
                gg = _fp_make_monic(gg, q)
                other, _r = _fp_divmod(h, gg, q)
                parts[i] = gg
                parts.append(_fp_make_monic(other, q))
            if in_this_pass > max_gcds_in_a_pass:
                max_gcds_in_a_pass = in_this_pass
    return parts, passes, gcds, len(basis), max_gcds_in_a_pass


def test_the_bound_holds_on_every_block():
    """The TIGHT bound, per block, plus the two premises it rests on.

    Four claims per block: the Berlekamp dimension is exactly ``k``; the split
    returns exactly the ``k`` intended irreducibles; the pass count is within
    ``(k-1)*p``; the gcd count is within ``p*(k-1)*floor(k/2)``. And the clone
    is pinned to the shipped function, so none of the counts is measuring a copy
    that drifted.
    """
    worst = 0.0
    worst_at = None
    total_gcds = 0
    for p, d, k, block, facs in BLOCKS:
        parts, passes, gcds, nbasis, max_in_pass = _split_counted(block, d, p)
        assert nbasis == k, (
            f"Berlekamp dimension {nbasis} != k = {k} at (p,d) = ({p},{d}); "
            f"dim B = k is the premise the whole method rests on"
        )
        assert sorted(parts) == sorted(facs), (
            f"the split did not return the {k} intended irreducibles at "
            f"(p,d,k) = ({p},{d},{k})"
        )
        assert parts == _equal_degree_split(block, d, p), (
            f"the counting clone diverged from the SHIPPED "
            f"_equal_degree_split at (p,d,k) = ({p},{d},{k}) — the counts "
            f"below would then be measuring the clone, not the code"
        )
        pass_bound = (k - 1) * p
        gcd_bound = p * (k - 1) * (k // 2)
        assert passes <= pass_bound, (
            f"passes {passes} > (k-1)*p = {pass_bound} at "
            f"(p,d,k) = ({p},{d},{k})"
        )
        assert gcds <= gcd_bound, (
            f"gcds {gcds} > p*(k-1)*floor(k/2) = {gcd_bound} at "
            f"(p,d,k) = ({p},{d},{k})"
        )
        assert max_in_pass <= k // 2, (
            f"{max_in_pass} gcds in ONE pass > floor(k/2) = {k // 2} at "
            f"(p,d,k) = ({p},{d},{k}) — the per-pass half of the bound"
        )
        total_gcds += gcds
        if gcd_bound:
            frac = gcds / gcd_bound
            if frac > worst:
                worst, worst_at = frac, (p, d, k, gcds, gcd_bound)
    assert total_gcds > 0, (
        "zero gcds over the whole census: every block took the early return, "
        "so the bound was never exercised and this test is vacuous"
    )
    # The tight bound must actually be TIGHT on this census, or it is not the
    # bound worth asserting. Measured worst is ~0.95; anything below ~0.5 means
    # the census stopped reaching the hard cells.
    assert worst > 0.5, (
        f"worst gcd fraction of the tight bound is only {worst:.4f} at "
        f"{worst_at}; the census is no longer reaching the cells that make the "
        f"bound tight, so a regression could hide under the slack"
    )


def test_the_constant_is_always_the_first_basis_vector():
    """The premise behind ``(k-1)`` rather than ``k``.

    Column 0 of ``(Q - I)^T`` is zero because ``Q[0] = x^0 = e_0``, so column 0
    is free and its RREF basis vector is the constant ``1`` — which separates
    nothing and is skipped. MEASURED 17238/17238 in the proof lane; asserted on
    every block here.
    """
    for p, d, k, block, _facs in BLOCKS:
        g = _fp_make_monic(block, p)
        basis = _fp_berlekamp_basis(g, len(g) - 1, p)
        assert len(basis) == k, (p, d, k, len(basis))
        assert len(basis[0]) <= 1, (
            f"the first RREF basis vector is not the constant at "
            f"(p,d,k) = ({p},{d},{k}): {basis[0]}"
        )


def test_the_completeness_guard_FIRES_on_a_mutated_basis():
    """⚠️ A PLANTED MUTATION, because the guard cannot fire on valid input.

    ``_equal_degree_split`` raises ``ValueError`` when the Berlekamp dimension
    is not ``k`` and when the parts do not reach ``k``. Neither can happen on a
    well-formed block, so a green suite proves NOTHING about them — the same
    class as the width guards this rc added, which is exactly why they get a
    mutation and not a hope. Truncating the basis to one vector must raise.
    """
    import srmech.cascade.matrix_cascades as mc

    p, d, k, block, _facs = next(b for b in BLOCKS if b[2] >= 3)
    real = mc._fp_berlekamp_basis
    try:
        mc._fp_berlekamp_basis = lambda g, n, q: real(g, n, q)[:1]
        with pytest.raises(ValueError) as exc:
            mc._equal_degree_split(block, d, p)
    finally:
        mc._fp_berlekamp_basis = real
    assert "Berlekamp dimension" in str(exc.value), str(exc.value)
    # and the unmutated call still works, so the mutation was the cause
    assert len(mc._equal_degree_split(block, d, p)) == k


def test_the_completeness_guard_FIRES_on_a_non_multiple_degree():
    """The second guard: ``n % d != 0`` cannot arise from a distinct-degree
    bucket, so it too needs a planted input. A degree-3 block declared as
    degree-2 must not be answered."""
    import srmech.cascade.matrix_cascades as mc
    p = 5
    block = _mul(_irr(p, 3)[0], _irr(p, 3)[1], p)      # degree 6, d = 3, k = 2
    assert mc._equal_degree_split(block, 3, p)          # the honest call works
    with pytest.raises(ValueError):
        mc._equal_degree_split(block, 4, p)             # 6 % 4 != 0


# ── the retry-regression roster ───────────────────────────────────────────────

#: The five C names the Cantor–Zassenhaus retry needed. All five are REMOVED,
#: and the roster is here because "the randomness came back under a different
#: name" is the regression this cannot otherwise see. ⚠️ ``fp_equal`` is matched
#: with a call-shaped pattern on purpose: a plain substring search for it also
#: matches ``fp_equal_degree``, which is the function that STAYS.
_C_GONE = ("fac_rng_next", "FAC_RNG_SEED", "fp_polypow_big", "fp_ed_exp")


def test_the_removed_C_retry_machinery_stays_removed():
    src = _C_SRC.read_text(encoding="utf-8")
    present = [n for n in _C_GONE if n in src]
    assert not present, (
        f"the Cantor–Zassenhaus retry machinery is back in "
        f"{_C_SRC.name}: {present}"
    )
    fp_equal_calls = re.findall(r"\bfp_equal\s*\(", src)
    assert not fp_equal_calls, (
        f"fp_equal (the poly-equality helper the retry needed) is back: "
        f"{len(fp_equal_calls)} call site(s). Note this predicate is "
        f"call-shaped so that fp_equal_degree, which stays, does not match."
    )
    assert "fp_equal_degree(" in src, (
        "the vacuity control: fp_equal_degree must still be there, or the "
        "predicate above is passing because the file moved"
    )


def test_fp_equal_degree_has_no_unbounded_loop_and_no_randomness():
    """The C body must contain no ``while``, no ``do`` and no rng call.

    Scoped to its measured extent: this guards ONE function by name. It is not
    a Rule-2 detector for the tree — that is ``test_jpl_audit.py``'s
    ``RULE_2_SEEDED``.
    """
    src = _C_SRC.read_text(encoding="utf-8")
    start = src.index("static srmech_status_t fp_equal_degree(")
    depth, i, body_start = 0, start, None
    while i < len(src):
        if src[i] == "{":
            if body_start is None:
                body_start = i
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0 and body_start is not None:
                break
        i += 1
    body = src[body_start:i]
    assert body_start is not None and i < len(src), "could not span the body"
    for tok in ("while", " do ", "do {", "rng", "rand"):
        assert tok not in body, (
            f"fp_equal_degree's body contains {tok!r}; the rc475 replacement "
            f"is `for` loops with trip counts fixed at entry"
        )
    assert body.count("for (") >= 2, (
        "the body has fewer than two `for` loops, so the span walk probably "
        "captured the wrong text"
    )


def test_the_pure_peer_takes_no_rng_argument():
    """The Python side of the same claim, on the signature rather than the body.

    ``_equal_degree_split(f, d, q)`` — the fourth ``rng`` parameter is gone, and
    so is the ``_rng`` closure in ``factor_integer_poly`` that fed it. A
    signature check is the cheapest statement that the randomness cannot be
    reintroduced by a caller.
    """
    import inspect
    params = list(inspect.signature(_equal_degree_split).parameters)
    assert params == ["f", "d", "q"], params
    src = _PY_SRC.read_text(encoding="utf-8")
    assert "def _rng(" not in src, "the xorshift closure is back"
    assert "0x2545F4914F6CDD1D" not in src, "the xorshift seed constant is back"
    assert "_factor_mod_p(fp_monic, prime)" in src, (
        "the vacuity control: the rng-free call site must be present, or the "
        "two assertions above are passing on a file that moved"
    )
