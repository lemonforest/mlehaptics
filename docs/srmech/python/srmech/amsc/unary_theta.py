"""srmech.amsc.unary_theta — ``UnaryTheta``, the first WEIGHT-GRADED carrier.

The operand ladder so far — :class:`~srmech.amsc.q.Q` (an exact scalar),
:class:`~srmech.amsc.poly.Poly` (an ordinary polynomial), the q-level
:class:`~srmech.amsc.qpoly.QPoly`, the elliptic
:class:`~srmech.amsc.ellbase.EllRatio` / :class:`~srmech.amsc.thetasum.ThetaSum`
— is entirely **weight-0**: every carrier holds a modular OBJECT of weight 0
(a rational function, a balanced theta-quotient). That is a real ceiling. The
harmonic-Maass / mock-theta program (research item #9) needs weight-graded
objects: Ramanujan's order-3 mock theta

    f(q) = Σ_{n≥0} q^{n²} / (−q; q)_n²

is a weight-1/2 mock modular form, and its **shadow** is the weight-3/2 unary
theta

    g₃(τ) = Σ_{n≥1} (−12 / n) · n · q^{n²/24}

(Zagier, *Ramanujan's mock theta functions and their applications [d'après Zwegers
and Bringmann–Ono]*, Séminaire Bourbaki, Astérisque 326 (2009), Exp. 986, p. 150;
the exact shadow of f(q)). A weight-0 carrier simply cannot hold g₃ — its weight
is 3/2, not 0 — so the shadow was IRREPRESENTABLE in the ladder. ``UnaryTheta``
augments the ladder with a **weight axis** and makes the shadow representable
in-carrier, the #9 payoff.

A UNARY THETA SERIES is

    g(τ) = Σ_{n ∈ support} χ(n) · n^j · q^{(a·n² + b·n) / D}

— a single (hence *unary*) sum of a character ``χ`` against a power ``n^j`` of the
summation index, over a quadratic exponent ``(a·n² + b·n)/D``. Its **WEIGHT** is

    weight = 1/2 + j

(half-integral, the classical weight of a unary theta with a degree-``j``
spherical/polynomial factor: ``j = 0`` is the weight-1/2 Jacobi theta θ₃, ``j = 1``
is a weight-3/2 form like the shadow g₃ above, ``j = 2`` is weight-5/2, …). This is
the weight axis: the operand grade equals ``1/2 + deg(n^j)``.

The two anchors this carrier must hold (the build gates):

  * **θ₃** — ``unary_theta(trivial χ, j=0, a=1, b=0, D=1, support='all')`` is
    ``θ₃ = Σ_{n∈ℤ} q^{n²}`` (Jacobi-triple-product theta): weight 1/2,
    ``q_series = 1 + 2q + 2q⁴ + 2q⁹ + …`` (coefficient ``[1, 2, 0, 0, 2, …]``).
  * **g₃** — ``unary_theta(χ = (−12/·), j=1, a=1, b=0, D=24, support='positive')``
    is the order-3 mock-theta SHADOW: weight 3/2, and (factoring out the leading
    ``q^{1/24}``) ``q_series = 1 − 5q − 7q² + 11q⁵ + 13q⁷ − 17q¹² − 19q¹⁵ +
    23q²² + 25q²⁶ + …`` — the coefficient ``±n`` of ``q^{(n²−1)/24}`` carries the
    Kronecker sign ``(−12/n)``. THIS is the weight-3/2 object the weight-0 ladder
    could not hold.

Everything is exact INTEGER arithmetic: the q-series coefficients of a unary
theta are integers (a sum of ``χ(n)·n^j`` terms, each an exact ``int``), so the
carrier is exact-integer all the way (no float, no ``math``, no numpy). The sign
of the character is the **Class-K** pin-slot via an explicit ``±1`` branch, never
an ALU ``abs()``. The one rational that appears is the WEIGHT itself (``Q(1, 2) +
j``), an exact :class:`~srmech.amsc.q.Q` — the weight axis is rational by nature
(half-integral), so it is the natural home for the carrier's grade.

The C peer ``srmech_unary_theta`` (rc70) mirrors the integer q-series + the
weight over caller-arena ``srmech_bigint`` (the same exact-integer substrate as
``srmech_poly``; malloc-free, JPL-clean). The pure-Python body here is the
COMPLETE alternative + the C peer's parity oracle — both emit byte-identical
exact integer coefficients at any magnitude (the coefficient ``n^j`` is full
bignum, no int64 ceiling).
"""

from __future__ import annotations

from typing import Callable, Dict, List, Sequence, Tuple, Union

from .q import Q

__all__ = ["Character", "UnaryTheta", "theta_coefficients", "unary_theta"]

_Q_HALF = Q(1, 2)


# ── the character χ (a Kronecker / Dirichlet symbol over a modulus) ──────────


CharSpec = Union[str, int, Callable[[int], int], Sequence[int], Dict[int, int],
                 "Character"]


class Character:
    """A periodic character ``χ : ℤ → {−1, 0, +1}`` of modulus ``M``. The
    multiplier of the unary theta's summand. Three construction forms:

    - ``Character.trivial()`` — the trivial character ``χ ≡ 1`` (``M = 1``).
    - ``Character.from_table(M, table)`` — a residue table ``table[r] = χ(r)``
      for ``r = 0 … M−1`` (each entry in ``{−1, 0, 1}``).
    - ``Character.from_callable(M, fn)`` — any ``fn(n) ∈ {−1, 0, 1}`` that is
      ``M``-periodic (the modulus is recorded for divisibility bookkeeping; the
      callable is evaluated on ``n mod M``).

    The value is exact and integral; the sign is the **Class-K** pin-slot (a
    stored ``±1``, never an ALU ``abs()``)."""

    __slots__ = ("_M", "_table")

    def __init__(self, modulus: int, table: Sequence[int]) -> None:
        if not isinstance(modulus, int) or modulus < 1:
            raise ValueError(f"Character modulus must be a positive int; got {modulus!r}")
        tab = tuple(int(t) for t in table)
        if len(tab) != modulus:
            raise ValueError(
                f"Character table length {len(tab)} != modulus {modulus}")
        for t in tab:
            if t not in (-1, 0, 1):
                raise ValueError(f"Character value must be in {{-1, 0, 1}}; got {t}")
        self._M = modulus
        self._table = tab

    # ── construction ─────────────────────────────────────────────────────────
    @classmethod
    def trivial(cls) -> "Character":
        """The trivial character ``χ ≡ 1`` (modulus 1; every ``χ(n) = 1``)."""
        return cls(1, (1,))

    @classmethod
    def from_table(cls, modulus: int, table: Sequence[int]) -> "Character":
        """A character from an explicit residue table ``table[r] = χ(r)`` for
        ``r = 0 … modulus−1``."""
        return cls(modulus, table)

    @classmethod
    def from_callable(cls, modulus: int, fn: Callable[[int], int]) -> "Character":
        """A character from any ``M``-periodic ``fn(n) ∈ {−1, 0, 1}`` — sampled on
        the residues ``0 … modulus−1`` to build the exact table."""
        return cls(modulus, [int(fn(r)) for r in range(modulus)])

    # ── accessors ────────────────────────────────────────────────────────────
    @property
    def modulus(self) -> int:
        """The period ``M`` of the character."""
        return self._M

    @property
    def table(self) -> Tuple[int, ...]:
        """The residue table ``(χ(0), …, χ(M−1))``."""
        return self._table

    @property
    def is_trivial(self) -> bool:
        """True iff this is the trivial character ``χ ≡ 1``."""
        return self._M == 1 and self._table == (1,)

    def __call__(self, n: int) -> int:
        """``χ(n) ∈ {−1, 0, +1}`` (evaluated on ``n mod M``; exact integer)."""
        return self._table[n % self._M]

    def __eq__(self, other) -> bool:
        if isinstance(other, Character):
            return self._M == other._M and self._table == other._table
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._M, self._table))

    def __repr__(self) -> str:
        if self.is_trivial:
            return "Character(trivial)"
        return f"Character(modulus={self._M}, table={self._table})"


def _kronecker_minus12(n: int) -> int:
    """The Kronecker symbol ``(−12 / n) ∈ {−1, 0, +1}`` — period 12: ``+1`` for
    ``n ≡ 1, 11 (mod 12)``, ``−1`` for ``n ≡ 5, 7 (mod 12)``, ``0`` otherwise
    (when ``gcd(n, 12) > 1``). This is the character of the order-3 mock-theta
    shadow g₃ (Zagier, Astérisque 326, p. 150). The sign is the Class-K pin-slot
    (a returned ``±1``), no ALU ``abs()``."""
    r = n % 12
    if r in (1, 11):
        return 1
    if r in (5, 7):
        return -1
    return 0


_MINUS12 = Character.from_callable(12, _kronecker_minus12)


def _coerce_character(spec: CharSpec) -> Character:
    """Coerce a character spec to a :class:`Character`.

    - a :class:`Character` passes through;
    - ``'trivial'`` / ``1`` → :meth:`Character.trivial`;
    - ``'minus12'`` / ``'-12'`` → the ``(−12/·)`` Kronecker character (g₃);
    - a callable ``fn`` is rejected here (no modulus known) — wrap it via
      :meth:`Character.from_callable` first;
    - a sequence ``table`` → :meth:`Character.from_table` of modulus ``len(table)``.
    """
    if isinstance(spec, Character):
        return spec
    if spec == "trivial" or spec == 1:
        return Character.trivial()
    if spec in ("minus12", "-12", "(-12/.)"):
        return _MINUS12
    if callable(spec):
        raise TypeError(
            "a bare callable character needs a modulus — pass "
            "Character.from_callable(modulus, fn), not the raw function")
    if isinstance(spec, (tuple, list)):
        return Character.from_table(len(spec), spec)
    raise TypeError(f"unrecognised character spec: {spec!r}")


# ── the support (which n the sum runs over) ──────────────────────────────────

# Support is one of:
#   'all'      — every integer n ∈ ℤ (the two-sided theta, e.g. θ₃)
#   'positive' — n ≥ 1 (the one-sided shadow sum, e.g. g₃)
#   'nonneg'   — n ≥ 0
_SUPPORTS = ("all", "positive", "nonneg")


def _isqrt(x: int) -> int:
    """Integer floor-sqrt (Class-J / Newton, no float ``math.isqrt`` import) for a
    non-negative ``x``. Used only to bound the n-window (JPL Rule 2)."""
    if x < 0:
        raise ValueError("_isqrt of a negative")
    if x < 2:
        return x
    lo, hi = 0, x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _n_window(a: int, b: int, max_exp_num: int) -> int:
    """An explicit ceiling ``nmax`` such that EVERY integer ``n`` with
    ``a·n² + b·n ≤ max_exp_num`` satisfies ``|n| ≤ nmax``. From ``a·n² + b·n ≤
    M`` ⇒ ``|n| ≤ (|b| + √(b² + 4a·M)) / (2a)``; we over-bound by an exact
    integer floor-sqrt + 2 (no float). The window is symmetric, so iterating
    ``[−nmax, nmax]`` is provably COMPLETE for any sign of ``b`` (no monotone-
    break heuristic). Bounded loop (JPL Rule 2)."""
    babs = b if b >= 0 else -b               # Class-K magnitude, no abs()
    disc = babs * babs + 4 * a * (max_exp_num if max_exp_num > 0 else 0)
    root = _isqrt(disc)
    return (babs + root) // (2 * a) + 2


def _support_iter_bound(support: str, a: int, b: int, D: int, max_exp_num: int):
    """Yield the integers ``n`` of ``support`` whose RAW exponent numerator
    ``a·n² + b·n`` is ``≤ max_exp_num`` (so the term lands at or below the
    requested series order after the leading-power factor-out). Enumerated over
    the EXPLICIT symmetric window ``[−nmax, nmax]`` (:func:`_n_window`), which is
    provably complete for any sign of ``b`` — a bounded loop (JPL Rule 2), no
    float, no monotone-break heuristic."""
    nmax = _n_window(a, b, max_exp_num)
    if support == "positive":
        lo, hi = 1, nmax
    elif support == "nonneg":
        lo, hi = 0, nmax
    else:                                    # "all"
        lo, hi = -nmax, nmax
    for n in range(lo, hi + 1):
        if a * n * n + b * n <= max_exp_num:
            yield n


def _coerce_support(support: str) -> str:
    if support not in _SUPPORTS:
        raise ValueError(
            f"support must be one of {_SUPPORTS}; got {support!r}")
    return support


# ── the native dispatch ──────────────────────────────────────────────────────


def _native():
    """The native ``_native`` module IF the rc70 ``srmech_unary_theta`` peer is
    present, else ``None`` — so the carrier dispatches to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the parity
    oracle). Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_unary_theta", None)
    if probe is None or not probe():
        return None
    return nat


# ── the carrier ──────────────────────────────────────────────────────────────


class UnaryTheta:
    """A numpy-free EXACT unary theta series

        g(τ) = Σ_{n ∈ support} χ(n) · n^j · q^{(a·n² + b·n) / D}

    — the first WEIGHT-GRADED carrier. Immutable. Holds the character ``χ``, the
    polynomial degree ``j`` (the ``n^j`` factor), the quadratic exponent params
    ``(a, b, D)`` and the ``support``. Its grade is :attr:`weight` ``= 1/2 + j``.
    The q-series coefficients (:meth:`q_series`) are exact integers. See the
    module docstring for the θ₃ / g₃ anchors and the #9 mock-theta-shadow
    motivation."""

    __slots__ = ("_char", "_j", "_a", "_b", "_D", "_support")

    def __init__(self, char: CharSpec, j: int, a: int, b: int, D: int,
                 support: str = "positive") -> None:
        self._char = _coerce_character(char)
        if not isinstance(j, int) or j < 0:
            raise ValueError(f"the polynomial degree j must be a non-negative int; got {j!r}")
        if not isinstance(a, int) or not isinstance(b, int) or not isinstance(D, int):
            raise TypeError("the exponent params (a, b, D) must be ints")
        if a <= 0:
            raise ValueError(f"the quadratic coefficient a must be a positive int; got {a}")
        if D <= 0:
            raise ValueError(f"the exponent denominator D must be a positive int; got {D}")
        self._j = j
        self._a = a
        self._b = b
        self._D = D
        self._support = _coerce_support(support)

    # ── accessors ────────────────────────────────────────────────────────────
    @property
    def char(self) -> Character:
        """The character ``χ``."""
        return self._char

    @property
    def degree(self) -> int:
        """The polynomial degree ``j`` (the ``n^j`` factor)."""
        return self._j

    @property
    def exponent_params(self) -> Tuple[int, int, int]:
        """The quadratic exponent params ``(a, b, D)`` — exponent ``(a·n²+b·n)/D``."""
        return (self._a, self._b, self._D)

    @property
    def support(self) -> str:
        """The summation support (``'all'`` / ``'positive'`` / ``'nonneg'``)."""
        return self._support

    @property
    def weight(self) -> Q:
        """The half-integral WEIGHT ``= 1/2 + j`` (exact :class:`~srmech.amsc.q.Q`)
        — THE WEIGHT AXIS. ``j = 0`` ⇒ weight 1/2 (a Jacobi theta like θ₃); ``j =
        1`` ⇒ weight 3/2 (a shadow like g₃); ``j = 2`` ⇒ weight 5/2; …"""
        return _Q_HALF + self._j

    # ── the q-series (exact integer coefficients) ────────────────────────────
    def leading_power(self) -> Q:
        """The minimal raw exponent ``(a·n² + b·n)/D`` over the support — the
        fractional ``q``-power factored out so :meth:`q_series` returns an INTEGER
        series. Exact :class:`~srmech.amsc.q.Q` (e.g. ``Q(1, 24)`` for g₃, ``Q(0,
        1)`` for θ₃). Computed over the contributing ``n`` (``χ(n) ≠ 0``) only."""
        return Q(self._min_raw_num(), self._D)

    def _min_raw_num(self) -> int:
        """The minimum raw exponent NUMERATOR ``a·n² + b·n`` over the support's
        CONTRIBUTING ``n`` (``χ(n) ≠ 0``). The quadratic vertex is at ``n* =
        −b/(2a)``; the minimum over the lattice is attained at a small ``n`` near
        the vertex, so a bounded probe of the contributing ``n`` in a window
        around the vertex finds it exactly (no float — the vertex window is
        ``⌊−b/(2a)⌋ ± (M + 1)`` to clear the character period ``M``). Bounded loop
        (JPL Rule 2)."""
        a, b, M = self._a, self._b, self._char.modulus
        # integer floor of the vertex −b/(2a) without float (Class-K sign): the
        # exact two-int division, floored toward −inf.
        vtop, vbot = -b, 2 * a
        vfloor = vtop // vbot  # Python // is floor division (toward −inf)
        best = None
        # probe a window wide enough to cover the character period either side of
        # the vertex, so the minimum CONTRIBUTING n is captured exactly.
        lo = vfloor - (M + 1)
        hi = vfloor + (M + 1)
        for n in range(lo, hi + 1):
            if not self._n_in_support(n):
                continue
            if self._char(n) == 0:
                continue
            val = a * n * n + b * n
            if best is None or val < best:
                best = val
        if best is None:
            # no contributing term anywhere near the vertex: scan a wider net.
            for n in range(vfloor - 6 * (M + 1), vfloor + 6 * (M + 1) + 1):
                if not self._n_in_support(n):
                    continue
                if self._char(n) == 0:
                    continue
                val = a * n * n + b * n
                if best is None or val < best:
                    best = val
        if best is None:
            raise ValueError(
                "UnaryTheta: the character is identically zero on the support — "
                "the series is empty (no leading power)")
        return best

    def _n_in_support(self, n: int) -> bool:
        s = self._support
        if s == "all":
            return True
        if s == "positive":
            return n >= 1
        return n >= 0  # nonneg

    def q_series(self, N: int) -> List[int]:
        """The exact INTEGER coefficient list ``[c_0, c_1, …, c_N]`` of the series
        AFTER factoring out the leading ``q``-power (:meth:`leading_power`):

            g(τ) = q^{leading} · Σ_{e=0}^{∞} c_e · q^e ,   c_e = Σ_{n : E(n)=e} χ(n)·n^j

        where ``E(n) = (a·n² + b·n)/D − leading`` is the (non-negative integer)
        reduced exponent of term ``n``. Returns the integer coefficients to order
        ``N`` inclusive. Exact integers, no float, no ``abs()`` (the character
        sign is the Class-K pin-slot), no numpy / ``math``.

        For θ₃ this is ``[1, 2, 0, 0, 2, …]`` (= Σ q^{n²}); for the shadow g₃ it is
        ``[1, −5, −7, 0, 0, 11, 0, 13, …]`` (the Zagier coefficients, the #9
        payoff). DISPATCHES to the native ``srmech_unary_theta`` C peer when it is
        loaded (a 1:1 exact-integer mirror — the C coefficients EQUAL the Python
        coefficients, so it is trusted only when ``has_native_unary_theta``);
        otherwise the pure-Python :meth:`_q_series_py` body computes it (the
        COMPLETE alternative + the C peer's parity oracle)."""
        if not isinstance(N, int) or N < 0:
            raise ValueError(f"q_series order N must be a non-negative int; got {N!r}")
        nat = _native()
        if nat is not None:
            try:
                got = nat.unary_theta_q_series_c(
                    self._char.modulus, self._char.table,
                    self._j, self._a, self._b, self._D, self._support, N)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass  # fall to the pure path
        return self._q_series_py(N)

    def _q_series_py(self, N: int) -> List[int]:
        """The COMPLETE pure-Python ``q_series`` (the parity oracle for the C
        peer): exact integer coefficients to order ``N`` after the leading-power
        factor-out."""
        a, b, D = self._a, self._b, self._D
        lead_num = self._min_raw_num()
        coeffs = [0] * (N + 1)
        # the reduced exponent of term n is (a·n²+b·n − lead_num)/D; it must be a
        # non-negative integer for the term to land on the lattice. We enumerate
        # n whose raw exponent numerator is ≤ lead_num + N·D (so reduced ≤ N).
        max_num = lead_num + N * D
        for n in self._support_iter(max_num):
            chi = self._char(n)
            if chi == 0:
                continue
            raw = a * n * n + b * n
            shifted = raw - lead_num
            # shifted must be a non-negative multiple of D to land on an integer
            # power (the contributing characters are chosen so it always is; a
            # non-multiple is a term off the integer lattice and is skipped).
            if shifted < 0 or shifted % D != 0:
                continue
            e = shifted // D
            if e > N:
                continue
            # coefficient χ(n)·n^j; the χ sign is the Class-K pin-slot (chi ∈
            # {−1, +1}); n^j is exact bigint. n may be negative — n^j keeps its
            # sign for odd j, which is the correct (two-sided) theta coefficient.
            coeffs[e] += chi * (n ** self._j)
        return coeffs

    def _support_iter(self, max_num: int):
        """Yield the support's ``n`` with raw exponent numerator ``a·n²+b·n ≤
        max_num`` (a bounded enumeration; see :func:`_support_iter_bound`)."""
        return _support_iter_bound(self._support, self._a, self._b, self._D, max_num)

    # ── equality / repr ──────────────────────────────────────────────────────
    def __eq__(self, other) -> bool:
        if isinstance(other, UnaryTheta):
            return (self._char == other._char and self._j == other._j
                    and self._a == other._a and self._b == other._b
                    and self._D == other._D and self._support == other._support)
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._char, self._j, self._a, self._b, self._D, self._support))

    def __repr__(self) -> str:
        return (f"UnaryTheta(weight={self.weight}, j={self._j}, "
                f"exp=({self._a}n²+{self._b}n)/{self._D}, support={self._support!r})")


def unary_theta(char: CharSpec, j: int, a: int, b: int, D: int,
                support: str = "positive") -> UnaryTheta:
    """Construct a :class:`UnaryTheta` series

        g(τ) = Σ_{n ∈ support} χ(n) · n^j · q^{(a·n² + b·n) / D}

    — the public construction helper for the first WEIGHT-GRADED carrier
    (weight ``= 1/2 + j``). The two anchors:

    - ``unary_theta('trivial', j=0, a=1, b=0, D=1, support='all')`` → θ₃, weight
      1/2, ``q_series = [1, 2, 0, 0, 2, …]`` (Σ_{n∈ℤ} q^{n²}).
    - ``unary_theta('minus12', j=1, a=1, b=0, D=24, support='positive')`` → the
      order-3 mock-theta SHADOW g₃, weight 3/2, ``q_series = [1, −5, −7, 0, 0, 11,
      …]`` (the Zagier coefficients) after factoring the leading ``q^{1/24}`` — the
      #9 payoff (the shadow made representable in-carrier at weight 3/2).

    ``char`` is a :class:`Character`, ``'trivial'``, ``'minus12'``, or a residue
    table; ``j ≥ 0`` is the ``n^j`` degree; ``(a, b, D)`` (``a > 0``, ``D > 0``)
    is the quadratic exponent; ``support`` is ``'all'`` / ``'positive'`` /
    ``'nonneg'``. Exact integer q-series, exact-``Q`` weight; no float, no
    ``abs()``, no numpy / ``math``."""
    return UnaryTheta(char, j, a, b, D, support)


def theta_coefficients(theta: UnaryTheta, n_max: int) -> List[int]:
    """READ a :class:`UnaryTheta`'s exact integer q-expansion — the first
    registered CONSUMER of the ``UnaryTheta`` carrier (rc113; issue #1239 /
    F1027 / UPSTREAM §85: before this, a conversationally-built shadow was a
    dead end after display). Returns the coefficient list ``[c_0, …, c_n_max]``
    of the series AFTER factoring out the leading ``q``-power (exactly
    :meth:`UnaryTheta.q_series`):

    - θ₃ (``unary_theta('trivial', 0, 1, 0, 1, support='all')``) →
      ``[1, 2, 0, 0, 2, …]``;
    - the g₃ mock-theta shadow (``unary_theta('minus12', 1, 1, 0, 24)``) →
      the Zagier coefficients ``[1, −5, −7, 0, 0, 11, 0, 13, …]``
      (Astérisque 326 (2009), Exp. 986, p. 150).

    COMPUTE, C-dispatched THROUGH THE EXISTING rc70 1:1 peer: the expansion is
    :meth:`UnaryTheta.q_series`, which routes to the native
    ``srmech_unary_theta`` C symbol when present (byte-identical exact-integer
    mirror; a bare C host calls ``srmech_unary_theta`` directly) — no new C
    symbol is needed because the mirror already ships 1:1. Exact ints (each a
    ``Σ χ(n)·n^j`` bignum), the χ sign the Class-K pin-slot; no float, no
    ``abs()``, no numpy / ``math``."""
    if not isinstance(theta, UnaryTheta):
        raise TypeError(
            "theta_coefficients: theta must be a UnaryTheta (construct one "
            f"with unary_theta(...) / the 'g3' named shadow); got "
            f"{type(theta).__name__}")
    if isinstance(n_max, bool) or not isinstance(n_max, int) or n_max < 0:
        raise ValueError(
            f"theta_coefficients: n_max must be a non-negative int; got {n_max!r}")
    return theta.q_series(n_max)
