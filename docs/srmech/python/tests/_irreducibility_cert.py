"""rc475 (`#T1188`) — an INDEPENDENT irreducibility certificate for a ℤ[x] factor.

WHY THIS EXISTS. The factor-parity gates use the pure ``factor_integer_poly`` as
the oracle for the native one. That settles AGREEMENT, and agreement between two
implementations of the same algorithm is a consistency check — it is not a proof
that a returned factor is irreducible. Through rc474 the tree's own claim was
"irreducibility is PROVEN for factors of degree <= 3 by a rational-root test, and
for degree >= 4 the evidence is agreement between two implementations". That
second half is not evidence of irreducibility at all, and it was load-bearing in
a gate: the rc474 corruption's own wrong-value witness served a REDUCIBLE
degree-9 factor as irreducible while satisfying the composite's multiply-back
self-check, so "the product reconstructs the input" cannot see the defect either.

WHAT THIS MODULE IS. A decidable certificate search, in exact integers, over
hand-rolled 𝔽_p[x] and ℤ[x] arithmetic that shares NO CODE with
``srmech.cascade.matrix_cascades``. Sharing code would make the checker fail in
the same direction as the thing it checks, which is the defect class this whole
module is written against. Nothing here imports srmech.

THE TIERS, and which are COMPLETE rather than merely sufficient:

======  ==============================================================  ========
tier    certificate                                                     status
======  ==============================================================  ========
A       degree 1                                                        complete
A2      degree 2: ``b^2 - 4ac`` is not a perfect square                  complete
E       monic even quartic ``x^4 + b x^2 + c``: an elementary criterion  complete
D       ``g == Phi_n`` for the ``n`` with ``phi(n) = deg``               complete
B       a prime ``p`` with ``p`` not dividing lead, ``g`` square-free    sufficient
        and IRREDUCIBLE mod ``p`` (verified by distinct-degree
        factorisation through the Frobenius matrix); COMPLETE for
        PRIME degree, because a transitive group of prime degree ``n``
        has order divisible by ``n`` and so contains an ``n``-cycle,
        and Chebotarev then gives such primes density >= 1/n
C       a LIST of primes whose mod-``p`` factor-DEGREE patterns admit    sufficient
        no common proper subset-sum in ``[1, deg-1]``; catches groups
        with no ``n``-cycle at all, e.g. ``Gal = A_4``
F       the EVEN REDUCTION — see :func:`_even_reduction_certificate`      complete
                                                                         under a
                                                                         stated
                                                                         premise
======  ==============================================================  ========

A2, E and F are two-sided or complete-under-a-premise, so they can report
``reducible=True``/decline rather than merely shrug. The others are one-sided: a
factor they cannot certify is RESIDUAL, and the caller must name it rather than
pass it. There is still deliberately no universal cheap tier — a degree-8 factor
with ``Gal = C_2^3`` (the Swinnerton-Dyer family) has NO certifying prime and
survives the degree sieve at ``deg/2`` forever, and closing THAT needs a second
full factorisation, which is another implementation rather than a certificate.

MEASURED on three independent corpora from the proof lane (146 + 725 + 134
factors): every factor certified, **0 residual, 0 reducible served**, worst
0.022 s per factor and at most 17 primes examined. The tiers that mattered were
D and E: before they existed the residuals were exactly the cyclotomic rows
(``Phi_8``, ``Phi_12``, ``Phi_15``, ``Phi_21``, ``Phi_24``) and the
``x^4 + bx^2 + c`` rows of the SVD family — abelian and Klein-four Galois groups,
where no prime certifies.

⚠️ TIER F EXISTS BECAUSE THIS GATE'S OWN CORPUS FOUND WHAT THOSE THREE DID NOT.
On the rc475 parity corpus the sieve left exactly one uncertified factor,
``x^8 + 3x^6 - 6x^2 + 4``, and raising the prime budget was measured USELESS
rather than merely slow: over **2259 usable primes below 20000 only FIVE distinct
mod-p patterns occur** — ``(4,4)``, ``(2,2,2,2)``, ``(1,1,1,1,2,2)``,
``(1,1,2,4)``, ``(1,1,1,1,1,1,1,1)`` — and every one of them admits 4 as a
subset-sum, so the surviving set stays ``{4}`` forever. That is a
group-theoretic obstruction, not a budget problem, which is exactly why the
answer is a theorem (tier F) and not a bigger loop. The same measurement is the
argument against ever "fixing" a residual by widening ``PRIME_BUDGET``.

Stdlib only; numpy-free; no ``math`` import (the integer sqrt is Newton's, so
this module is also usable from a numpy-absent pure cell).
"""
from __future__ import annotations

import time

#: Primes examined per factor before declaring RESIDUAL.
PRIME_BUDGET = 120

#: How many primes the tier-C degree sieve may accumulate.
SIEVE_PRIMES = 40


def _small_odd_primes(limit: int) -> "list[int]":
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    i = 2
    while i * i <= limit:
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
        i += 1
    return [i for i in range(3, limit + 1) if sieve[i]]


PRIMES = _small_odd_primes(5000)


# ── exact 𝔽_p[x], hand-rolled (shares nothing with srmech.cascade) ─────────────

def _ptrim(a: "list[int]") -> "list[int]":
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def _pmod(a, p):
    return _ptrim([x % p for x in a])


def _pmul(a, b, p):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j] = (out[i + j] + x * y) % p
    return _ptrim(out)


def _pdivmod(a, b, p):
    a = list(a)
    inv = pow(b[-1], p - 2, p)
    db = len(b) - 1
    if len(a) - 1 < db:
        return [0], _ptrim(a)
    q = [0] * (len(a) - db)
    for i in range(len(a) - 1, db - 1, -1):
        c = a[i] * inv % p
        if c:
            q[i - db] = c
            for j in range(db + 1):
                a[i - db + j] = (a[i - db + j] - c * b[j]) % p
    return _ptrim(q), _ptrim(a[:db] if db else [0])


def _pgcd(a, b, p):
    a, b = _ptrim(list(a)), _ptrim(list(b))
    while b != [0]:
        _q, r = _pdivmod(a, b, p)
        a, b = b, r
    inv = pow(a[-1], p - 2, p)
    return [x * inv % p for x in a]


def _pderiv(a, p):
    return _ptrim([(i * a[i]) % p for i in range(1, len(a))]) if len(a) > 1 else [0]


def _psub(a, b, p):
    out = [0] * max(len(a), len(b))
    for i, x in enumerate(a):
        out[i] = x
    for i, x in enumerate(b):
        out[i] = (out[i] - x) % p
    return _ptrim(out)


def _frobenius_rows(g, p):
    """``rows[i]`` = the coefficient vector of ``x^(i*p) mod g``.

    Built once per (g, p) so each later ``x^(p^i)`` costs one matrix apply
    instead of a fresh power: the DDF loop below is then O(n^3 + n^2 log p),
    which is what keeps the worst factor under 0.03 s.
    """
    n = len(g) - 1
    r, base, e = [1], [0, 1], p
    while e:
        if e & 1:
            r = _pdivmod(_pmul(r, base, p), g, p)[1]
        e >>= 1
        if e:
            base = _pdivmod(_pmul(base, base, p), g, p)[1]
    xp = r
    rows, cur = [], [1]
    for i in range(n):
        if i:
            cur = _pdivmod(_pmul(cur, xp, p), g, p)[1]
        rows.append([cur[j] if j < len(cur) else 0 for j in range(n)])
    return rows


def _frobenius_apply(rows, v, p):
    n = len(rows)
    out = [0] * n
    for i, vi in enumerate(v):
        if vi:
            ri = rows[i]
            for j in range(n):
                out[j] = (out[j] + vi * ri[j]) % p
    return out


def ddf_pattern(g, p):
    """The sorted mod-``p`` factor-degree pattern of ``g``, or ``None`` when
    ``p`` divides the lead or ``g`` is not square-free mod ``p`` (both make the
    pattern uninformative rather than wrong)."""
    if g[-1] % p == 0:
        return None
    gm = _pmod(g, p)
    inv = pow(gm[-1], p - 2, p)
    gm = [x * inv % p for x in gm]
    n = len(gm) - 1
    if n == 0:
        return []
    if _pgcd(gm, _pderiv(gm, p), p) != [1]:
        return None
    if n == 1:
        return [1]
    rows = _frobenius_rows(gm, p)
    pattern, rem = [], gm
    v = [0] * n
    v[1] = 1                                    # x
    i = 0
    while len(rem) - 1 >= 2 * (i + 1):
        i += 1
        v = _frobenius_apply(rows, v, p)        # x^(p^i) mod gm
        h = _pgcd(_psub(list(v), [0, 1], p), rem, p)
        if h != [1]:
            pattern += [i] * ((len(h) - 1) // i)
            rem = _pdivmod(rem, h, p)[0]
    if len(rem) - 1 >= 1:
        pattern.append(len(rem) - 1)
    return sorted(pattern)


# ── exact integer helpers ─────────────────────────────────────────────────────

def _isqrt(x: int) -> int:
    if x < 0:
        return -1
    if x < 2:
        return x
    r = 1 << ((x.bit_length() + 1) // 2)
    while True:
        y = (r + x // r) // 2
        if y >= r:
            return r
        r = y


def _is_square(x: int) -> bool:
    if x < 0:
        return False
    r = _isqrt(x)
    return r * r == x


def _subset_sums(pattern, n):
    s = {0}
    for d in pattern:
        s |= {a + d for a in s}
    return {a for a in s if 0 < a < n}


def _zmul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j] += x * y
    return out


def _zexact_div(a, b):
    """``a / b`` over ℤ with ``b`` monic-or-unit-lead; ASSERTS exactness, so a
    wrong Möbius product below cannot pass as a cyclotomic."""
    a = list(a)
    q = [0] * (len(a) - len(b) + 1)
    for i in range(len(a) - 1, len(b) - 2, -1):
        c = a[i] // b[-1]
        assert c * b[-1] == a[i], "cyclotomic division is not exact"
        q[i - len(b) + 1] = c
        for j in range(len(b)):
            a[i - len(b) + 1 + j] -= c * b[j]
    assert all(x == 0 for x in a), "cyclotomic division left a remainder"
    return q


def _mobius(n: int) -> int:
    m, r, d = 1, n, 2
    while d * d <= r:
        if r % d == 0:
            r //= d
            if r % d == 0:
                return 0
            m = -m
        d += 1
    if r > 1:
        m = -m
    return m


_PHI_CACHE: "dict[int, list[int]]" = {}


def cyclotomic(n: int) -> "list[int]":
    """``Phi_n`` by exact Möbius division of ``prod (x^(n/d) - 1)^mu(d)``."""
    if n in _PHI_CACHE:
        return _PHI_CACHE[n]
    num, den = [1], [1]
    for d in range(1, n + 1):
        if n % d:
            continue
        mu = _mobius(d)
        if mu == 0:
            continue
        f = [-1] + [0] * (n // d - 1) + [1]
        if mu == 1:
            num = _zmul(num, f)
        else:
            den = _zmul(den, f)
    out = _zexact_div(num, den)
    _PHI_CACHE[n] = out
    return out


def _euler_phi(n: int) -> int:
    r, m, d = n, n, 2
    while d * d <= m:
        if m % d == 0:
            while m % d == 0:
                m //= d
            r -= r // d
        d += 1
    if m > 1:
        r -= r // m
    return r


def cyclotomic_index(g):
    """The ``n`` with ``g == Phi_n``, else ``None``.

    ``phi(n) = deg`` forces ``n <= 2*deg^2``, which bounds the search.
    """
    deg = len(g) - 1
    for n in range(1, 2 * deg * deg + 2):
        if _euler_phi(n) == deg and cyclotomic(n) == g:
            return n
    return None


def _even_quartic_reducible(g) -> bool:
    """Monic ``x^4 + b x^2 + c``: reducible over ℚ iff ``b^2 - 4c`` is a square,
    or ``c = e^2`` with ``2e - b`` or ``-2e - b`` a square.

    COMPLETE, by unique factorisation: if ``g`` is even and factors into two
    irreducible quadratics ``A*B``, then ``A(-x)`` is an associate of ``A``
    (so ``A`` is even, giving the first case via ``y = x^2``) or
    ``A(-x) = B`` (giving the second).
    """
    b, c = g[2], g[0]
    if _is_square(b * b - 4 * c):
        return True
    if _is_square(c):
        e = _isqrt(c)
        return _is_square(2 * e - b) or _is_square(-2 * e - b)
    return False


def _is_even_poly(g) -> bool:
    """Only even-degree terms are nonzero, i.e. ``g(x) = m(x^2)``."""
    return all(c == 0 for c in g[1::2])


def _even_reduction_certificate(g, patterns, surviving):
    """Tier F — COMPLETE under the premise ``surviving == {deg/2}``.

    THE THEOREM. Let ``g`` be monic and EVEN of degree ``2n``, so ``g = m(x^2)``
    with ``deg m = n``, and suppose the tier-C sieve has narrowed the possible
    proper factor degrees to exactly ``{n}``. Then any proper factorisation is
    ``g = A*B`` with ``A``, ``B`` monic IRREDUCIBLE of degree ``n`` (a factor of
    any other degree is already excluded). Because ``g(-x) = g(x)``, the
    involution ``x -> -x`` permutes ``g``'s irreducible factors up to sign, so
    it either FIXES ``A`` or SWAPS it with ``B``:

      (i) ``A(-x) = ±A``. The ``-A`` branch makes ``A`` odd, hence ``A(0) = 0``,
          hence ``x | A`` — a degree-1 factor, which the premise excludes. So
          ``A`` is EVEN, ``A = a(x^2)`` with ``deg a = n/2``, and ``a`` is a
          proper divisor of ``m``: **``m`` is REDUCIBLE**. (If ``n`` is odd this
          branch is impossible outright.)
      (ii) ``A(-x) = ±B``, i.e. ``g(x) = ±A(x)*A(-x)``.

    Both branches are REFUTABLE by cheap, independent evidence:

      * branch (i) dies if ``m`` is certified IRREDUCIBLE — a recursive call,
        one degree down.
      * branch (ii) dies on ONE prime. If ``g = ±A(x)A(-x)`` then for any ``p``
        not dividing the lead with ``g`` square-free mod ``p``, factoring ``A``
        mod ``p`` as ``prod a_i`` gives ``A(-x) = prod a_i(-x)``, and each
        ``a_i(-x)`` is irreducible of the SAME degree. So ``g``'s mod-``p``
        degree pattern is a multiset ``P`` union ``P`` — **every multiplicity is
        EVEN**. A single prime whose pattern has a degree of ODD multiplicity
        therefore refutes branch (ii) outright.

    With both branches refuted, ``g`` has no proper factorisation: it is
    irreducible. Returns the certificate dict, or ``None`` if either refutation
    is unavailable (in which case the caller reports RESIDUAL, as it must).
    """
    deg = len(g) - 1
    if deg % 2 or g[-1] != 1 or not _is_even_poly(g):
        return None
    n = deg // 2
    if surviving != {n}:
        return None
    odd_mult_prime = None
    for p, pat in patterns:
        counts: "dict[int, int]" = {}
        for d in pat:
            counts[d] = counts.get(d, 0) + 1
        if any(c % 2 for c in counts.values()):
            odd_mult_prime = (p, tuple(pat))
            break
    if odd_mult_prime is None:
        return None                       # branch (ii) not refuted
    if n % 2 == 0:
        m = g[0::2]                       # m with g(x) = m(x^2)
        mc = certify(m)
        if mc["tier"] == "RESIDUAL" or mc.get("reducible"):
            return None                   # branch (i) not refuted
        return {"m_tier": mc["tier"], "m_cert": mc["cert"],
                "odd_multiplicity_prime": odd_mult_prime}
    # n odd: branch (i) is impossible, so the single prime suffices.
    return {"m_tier": "n-odd-so-branch-i-impossible", "m_cert": None,
            "odd_multiplicity_prime": odd_mult_prime}


def certify(g: "list[int]") -> dict:
    """Search a certificate for ``g`` (coefficients low->high).

    Returns ``{"tier", "cert", "primes", "secs"}``, plus ``"reducible"`` on the
    two-sided tiers and ``"surviving_degrees"`` on a RESIDUAL. A RESIDUAL is not
    a failure of ``g`` — it is the checker declining to make a claim, and the
    caller must report it as such.
    """
    t0 = time.time()
    deg = len(g) - 1
    if deg == 1:
        return {"tier": "A", "cert": None, "primes": 0, "secs": 0.0}
    if deg == 2:
        a, b, c = g[2], g[1], g[0]
        d = b * b - 4 * a * c
        return {"tier": "A2", "cert": ("disc", d), "primes": 0,
                "secs": round(time.time() - t0, 4), "reducible": _is_square(d)}
    if deg == 4 and g[4] == 1 and g[3] == 0 and g[1] == 0:
        return {"tier": "E", "cert": ("even-quartic", g[2], g[0]), "primes": 0,
                "secs": round(time.time() - t0, 4),
                "reducible": _even_quartic_reducible(g)}
    if g[-1] in (1, -1):
        n = cyclotomic_index(g if g[-1] == 1 else [-c for c in g])
        if n is not None:
            return {"tier": "D", "cert": ("Phi", n), "primes": 0,
                    "secs": round(time.time() - t0, 4)}
    allowed = None
    examined = 0
    sieve: "list[int]" = []
    patterns: "list[tuple[int, list[int]]]" = []
    for p in PRIMES:
        if examined >= PRIME_BUDGET:
            break
        pat = ddf_pattern(g, p)
        if pat is None:
            continue
        examined += 1
        patterns.append((p, pat))
        if pat == [deg]:
            return {"tier": "B", "cert": ("p", p), "primes": examined,
                    "secs": round(time.time() - t0, 4)}
        if len(sieve) < SIEVE_PRIMES:
            sieve.append(p)
            ss = _subset_sums(pat, deg)
            allowed = ss if allowed is None else (allowed & ss)
            if allowed is not None and not allowed:
                return {"tier": "C", "cert": ("primes", tuple(sieve)),
                        "primes": examined, "secs": round(time.time() - t0, 4)}
    fcert = _even_reduction_certificate(g, patterns,
                                        set(allowed) if allowed else set())
    if fcert is not None:
        return {"tier": "F", "cert": fcert, "primes": examined,
                "secs": round(time.time() - t0, 4)}
    return {"tier": "RESIDUAL", "cert": None, "primes": examined,
            "secs": round(time.time() - t0, 4),
            "surviving_degrees": sorted(allowed) if allowed else None}
