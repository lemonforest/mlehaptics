"""Exact discrete Fourier transform — integer arithmetic, one FPU lift.

The substrate-native answer to "don't use floats for bit-exact math": a DFT's
twiddle factors ``e^{-2πi·j/N}`` are *roots of unity* — algebraic integers in the
cyclotomic ring ``ℤ[ζ_N]``. So the DFT of an integer (or Gaussian-integer)
substrate signal is **exact integer arithmetic**: every spectral coefficient is
an exact ``ℤ[ζ_N]`` element (an integer vector in the cyclotomic power basis),
computed with **no floating-point at all**. Floats appear exactly **once**, at
the very end, in the FPU *lift* (:func:`lift`) that rotates ``ℤ[ζ_N] → ℂ`` by
evaluating ``ζ_N = e^{-2πi/N}`` — the projection from the discrete substrate to
the continuous observable (per ``[[user_stance_epicycle_via_gear_plus_pin]]``:
floats are for the FPU lift, not the math).

For a power-of-two ``N`` the cyclotomic polynomial is ``Φ_N(x) = x^{N/2} + 1``,
so ``ζ^{N/2} = -1`` and the ring collapses to the **negacyclic** integers
``ℤ[x]/(x^{N/2}+1)`` — a length-``N/2`` integer vector with the single reduction
rule ``ζ^j = -ζ^{j-N/2}`` for ``j ≥ N/2`` (a **Class K** pin-slot sign-flip, NOT
``abs``). The transform is then pure integer add/subtract: bit-for-bit
deterministic, platform-independent, and *more* faithful than a float FFT (which
accumulates rounding at every butterfly) because it rounds exactly once.

Public surface (v0.7.5rc29):

- :func:`exact_dft` / :func:`exact_idft` — return the **exact** ``ℤ[ζ_N]``
  integer spectrum (an :data:`ExactSpectrum`: one ``(real_vec, imag_vec)``
  integer pair per output bin) of an integer / Gaussian-integer signal at
  **any** length ``N ≥ 2``. No floats. The native-C twin
  ``srmech_exact_dft_i64`` runs the int64 fast path for power-of-two ``N``;
  arbitrary-precision magnitudes fall back to the Python bignum path.
- :func:`lift` — the single FPU lift ``ℤ[ζ_N] → ℂ`` (the *only* float producer).

The public ops are also the **internal engine** behind
:mod:`srmech.cascade.spectral_cascades` ``dft`` / ``fft``, which route an
all-integer / Gaussian-integer signal of **any** length ``N ≥ 2`` through
:func:`_exact_transform` (exact-until-rotation), and keep the float ``cexp``
path only for genuinely floating-point signals and for ``N < 2``. A power-of-two
``N`` takes the negacyclic radix-2 split :func:`_exact_dft_radix2`; every other
``N`` takes the general ``Φ_N`` reduction :func:`_exact_dft_core_general` over
the length-``φ(N)`` power basis.

⚠️ This header said *"General-``N`` cyclotomic reduction is a follow-up; until
then :func:`exact_dft` raises on non-power-of-two"* until `#T1188`. That was a
SHIPPED FALSEHOOD: the general-``N`` path landed in v0.7.5rc30,
:func:`_exact_dft_core` has routed non-power-of-two lengths to it ever since,
and :func:`exact_dft`'s own docstring two hundred lines below already said
"**any** ``N``". Nothing raises on non-power-of-two. The two statements
contradicted each other inside one module and no gate reads prose, so the false
one survived every release between.

**Complexity — Θ(N²) here is the OUTPUT SIZE, not a deficiency.** An
:data:`ExactSpectrum` at power-of-two ``N`` is ``N`` ring elements of dimension
``N/2``, each an integer ``(real, imag)`` pair: exactly ``N²`` integers. No
algorithm can emit ``N²`` integers in fewer than ``N²`` writes, so **no
Cooley–Tukey split can make the exact transform ``O(N log N)``**, however the
twiddles are arranged — that ceiling is information-theoretic, not algorithmic.
What the radix-2 split DOES buy is the constant: :func:`_exact_dft_radix2`
performs exactly ``N²`` integer additions — one per output coefficient, the
floor — where the doubly-nested ``Σ_n x_n ζ^{nk}`` loop it replaced paid ``2N²``.
:func:`_radix2_ring_op_count` states that count in closed form and
``tests/test_exact_radix2_rc463.py`` measures it against the running recursion.
(The ``O(N log N)`` in :func:`~srmech.cascade.spectral_cascades.fft`'s docstring
is the FLOAT radix-2, whose output is ``N`` complex scalars, not ``N²``
integers — a different carrier with a different floor.)

Class chain: **Class I** (cyclic index ``nk mod N``) ∘ **Class K** (the
``ζ^{N/2}=-1`` pin-slot sign-flip = cyclotomic reduction) ∘ **Class M** (the
integer bundle/accumulate) ∘ a final **Class C** rotation (the FPU lift).
"""
from __future__ import annotations

import functools
from typing import List, Optional, Sequence, Tuple

__all__ = ["exact_dft", "exact_idft", "lift", "ExactSpectrum"]

# A spectrum lives in the cyclotomic ring as (real-part, imag-part) integer
# coefficient vectors of length h = N/2 in the basis {1, ζ, …, ζ^{h-1}}.
ExactSpectrum = List[Tuple[List[int], List[int]]]

# Headroom under int64 (2^63): the largest exact coefficient is bounded by
# N·max|signal|, so we dispatch to the C int64 twin only when that bound is
# comfortably inside int64; larger magnitudes take the Python bignum path.
_INT64_SAFE = 1 << 62


def _try_int_pairs(signal: Sequence) -> Optional[Tuple[List[int], List[int]]]:
    """Split ``signal`` into integer ``(real, imag)`` component lists, or ``None``.

    Returns ``None`` if any element is non-integral. Accepts Python ``int`` /
    ``float`` / ``complex`` and numpy scalars uniformly via their ``.real`` /
    ``.imag`` attributes (an ``int`` has ``.real == self`` and ``.imag == 0``).
    """
    re: List[int] = []
    im: List[int] = []
    for v in signal:
        vr = v.real if hasattr(v, "real") else v
        vi = v.imag if hasattr(v, "imag") else 0
        try:
            ir = int(vr)
            ii = int(vi)
        except (TypeError, ValueError):
            return None
        if ir != vr or ii != vi:          # non-integral component → not exact-eligible
            return None
        re.append(ir)
        im.append(ii)
    return re, im


def _is_pow2(n: int) -> bool:
    """True iff ``n`` is a positive power of two (the Class-J radix test)."""
    return n >= 1 and (n & (n - 1)) == 0


def _poly_mul(a: List[int], b: List[int]) -> List[int]:
    """Integer polynomial product (coefficients low→high)."""
    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                out[i + j] += ai * bj
    return out


def _poly_exact_div(num: List[int], den: List[int]) -> List[int]:
    """Exact integer polynomial division ``num / den`` (den a monic factor)."""
    num = num[:]
    q = [0] * (len(num) - len(den) + 1)
    for i in range(len(q) - 1, -1, -1):
        c = num[i + len(den) - 1] // den[-1]
        q[i] = c
        if c:
            for j, dj in enumerate(den):
                num[i + j] -= c * dj
    return q


@functools.lru_cache(maxsize=64)
def _cyclotomic_reduction(n: int) -> Tuple[Tuple[Tuple[int, ...], ...], int]:
    """The reduction table + degree for the cyclotomic ring ``ℤ[ζ_N]``.

    Computes ``Φ_N`` from ``x^N - 1 = Π_{d|N} Φ_d`` (recursive exact integer
    polynomial division — cyclotomic coefficients are integers) and builds the
    table ``T`` where ``T[j]`` is ``ζ^j`` reduced to the power basis
    ``{1, ζ, …, ζ^{d-1}}`` (``d = φ(N)``, the Euler totient = ``deg Φ_N``). Pure
    integer arithmetic; cached per ``N`` (this is the general-``N`` substrate the
    power-of-two negacyclic path specialises). For a power-of-two ``N`` this
    yields exactly the negacyclic ``ζ^{N/2} = -1`` basis (``d = N/2``).
    """
    divisors = [d for d in range(1, n + 1) if n % d == 0]
    phis: dict = {}
    for d in divisors:
        if d == 1:
            phis[1] = [-1, 1]                 # Φ_1 = x - 1
            continue
        xnm1 = [0] * (d + 1)                  # x^d - 1
        xnm1[0] = -1
        xnm1[d] = 1
        prod = [1]
        for e in divisors:
            if e < d and d % e == 0:
                prod = _poly_mul(prod, phis[e])
        phis[d] = _poly_exact_div(xnm1, prod)
    phi = phis[n]
    deg = len(phi) - 1                        # φ(N)
    red_top = [-phi[i] for i in range(deg)]   # ζ^d = -(φ_0 + φ_1 ζ + … + φ_{d-1} ζ^{d-1})
    table: List[Tuple[int, ...]] = []
    cur = [0] * deg
    cur[0] = 1                                # ζ^0 = 1
    for _ in range(n):
        table.append(tuple(cur))
        carry = cur[deg - 1]
        nxt = [0] * deg
        for i in range(deg - 1, 0, -1):       # multiply by ζ (shift up)
            nxt[i] = cur[i - 1]
        if carry:
            for i in range(deg):              # reduce ζ^d via Φ_N
                nxt[i] += carry * red_top[i]
        cur = nxt
    return tuple(table), deg


def _exact_dft_core_general(re: List[int], im: List[int], n: int,
                            *, inverse: bool = False) -> ExactSpectrum:
    """General-``N`` exact DFT over ``ℤ[ζ_N]`` (any length ≥ 2; pure integer).

    For non-power-of-two ``N`` the cyclotomic ring does not collapse to the
    simple negacyclic ``ζ^{N/2}=-1`` rule, so each ``ζ^{nk mod N}`` is reduced via
    the :func:`_cyclotomic_reduction` table to the length-``φ(N)`` power basis and
    accumulated. ``X[k] = Σ_n signal[n] · ζ^{±nk mod N}``. Pure-Python
    arbitrary-precision (no fixed-width C twin) — the ``bignum_reference`` shape.
    """
    table, deg = _cyclotomic_reduction(n)
    spectrum: ExactSpectrum = []
    for k in range(n):
        ar = [0] * deg
        ai = [0] * deg
        for idx in range(n):
            j = ((idx * k) % n) if not inverse else ((-idx * k) % n)
            t = table[j]
            rv = re[idx]
            iv = im[idx]
            for i in range(deg):
                ti = t[i]
                if ti:
                    ar[i] += rv * ti
                    ai[i] += iv * ti
        spectrum.append((ar, ai))
    return spectrum


def _exact_dft_core_native(re: List[int], im: List[int], n: int,
                           inverse: bool) -> Optional[ExactSpectrum]:
    """Native-C int64 fast path for :func:`_exact_dft_core`, or ``None``.

    Returns ``None`` (caller runs the Python bignum path) when the native lib is
    absent / lacks the symbol, or when the exact coefficients could exceed the
    int64-safe bound ``N·max|signal|`` (arbitrary precision is then load-bearing).
    Magnitude is a Class-K sign-branch read, never ``abs``.
    """
    try:
        from srmech import _native
    except Exception:
        return None
    if not getattr(_native, "HAS_NATIVE", False):
        return None
    lib = getattr(_native, "LIB", None)
    if lib is None or not hasattr(lib, "srmech_exact_dft_i64"):
        return None
    maxabs = 0
    for v in re:
        a = v if v >= 0 else -v
        if a > maxabs:
            maxabs = a
    for v in im:
        a = v if v >= 0 else -v
        if a > maxabs:
            maxabs = a
    if maxabs * n >= _INT64_SAFE:         # coefficient magnitude could overflow int64
        return None
    import ctypes

    h = n // 2
    total = n * h
    c_re = (ctypes.c_int64 * n)(*re)
    c_im = (ctypes.c_int64 * n)(*im)
    out_re = (ctypes.c_int64 * total)()
    out_im = (ctypes.c_int64 * total)()
    rc = lib.srmech_exact_dft_i64(
        ctypes.c_uint32(n),
        ctypes.c_int(1 if inverse else 0),
        c_re, c_im, out_re, out_im,
    )
    if rc != 0:
        return None
    spectrum: ExactSpectrum = []
    for k in range(n):
        base = k * h
        spectrum.append(([int(out_re[base + j]) for j in range(h)],
                         [int(out_im[base + j]) for j in range(h)]))
    return spectrum


def _radix2_ring_op_count(n: int) -> Tuple[int, int, int]:
    """Structural op-count of :func:`_exact_dft_radix2` — closed form, no clock.

    Returns ``(scalar_adds, output_coefficients, recursion_depth)`` for a
    power-of-two ``n ≥ 2``. srmech ships no timing or benchmark surface, so
    "faster" is not a claim this tree can measure and none is made here. What it
    CAN state exactly is how many integer additions the split performs, and that
    number is closed-form, signal-independent and countable:

    - ``scalar_adds = n²`` — from the two-point base ``A(2) = 4`` and the level
      recurrence ``A(n) = 2·A(n/2) + 4·(n/2)·(n/4)`` (four adds per
      ``(output bin, sub-basis slot)`` pair: ``+`` and ``−`` on each of the real
      and imaginary coefficient vectors).
    - ``output_coefficients = n²`` — an :data:`ExactSpectrum` is ``n`` ring
      elements of dimension ``n/2``, each an integer ``(real, imag)`` pair.
    - ``recursion_depth = log2(n)`` — the top call counts as depth 1.

    **The two counts being EQUAL is the result.** The split performs exactly one
    integer addition per output coefficient, which is the information-theoretic
    floor for this representation — ``n²`` integers cannot be written in fewer
    than ``n²`` writes. So Θ(n²) is the output size, and the ``O(n log n)`` a
    Cooley–Tukey split buys on the FLOAT carrier (``n`` complex scalars out) is
    unreachable on this one however the twiddles are arranged. The doubly-nested
    ``Σ_n x_n ζ^{nk}`` loop this replaced paid ``2n²`` adds for the same output;
    the win is a factor of two, and it is a constant, not an exponent.

    ``tests/test_exact_radix2_rc463.py`` instruments the REAL recursion with a
    counting ``int`` subclass and asserts it hits these numbers exactly, so the
    closed form is measured against the running code rather than asserted beside
    it, and the growth ratio ``count(2n)/count(n) == 4`` is gated at five ``n``.

    Raises:
        ValueError: ``n`` is not a power of two ``≥ 2``. The general-``N``
            :func:`_exact_dft_core_general` path has no butterfly to count —
            its twiddles are dense ``Φ_N`` ring elements, not sign-flips.
    """
    if n < 2 or not _is_pow2(n):
        raise ValueError(
            f"_radix2_ring_op_count: power-of-two n >= 2 required; got n={n}. "
            f"Non-power-of-two N runs _exact_dft_core_general, which is not a "
            f"radix-2 split and has no butterfly op-count."
        )
    return n * n, n * n, n.bit_length() - 1


def _exact_dft_radix2(re: List[int], im: List[int], n: int,
                      *, inverse: bool = False) -> ExactSpectrum:
    """Exact radix-2 Cooley–Tukey split on the negacyclic ring ``ℤ[x]/(x^{n/2}+1)``.

    Decimation-in-time. ``X[k] = E[k] + ζ^{k}·O[k]`` and
    ``X[k+h] = E[k] − ζ^{k}·O[k]`` for ``k < h = n/2``, the second line being
    ``ζ^{k+h} = −ζ^{k}`` — the **Class K** pin-slot again, at the bin index this
    time rather than the basis index. Everything here is integer:

    - the sub-transforms ``E`` / ``O`` live in ``ℤ[ζ_{n/2}]``, and ``ζ_{n/2} =
      ζ_n²``, so a sub-basis slot ``p`` **embeds** into slot ``2p`` of the parent
      basis (**Class I** — the cyclic re-index, a pure store, no arithmetic);
    - the twiddle ``ζ_n^{±k}`` is multiplication by ``x^{±k}`` in
      ``ℤ[x]/(x^h+1)``, i.e. a **rotation of the coefficient vector** with a
      sign flip at the wrap (**Class K** pin-slot ``x^h = −1``, then **Class C**
      re-applying the orientation to the carried coefficient — never ``abs``);
    - the butterfly itself is **Class M** bundle ``+`` / Class-K signed ``−``.

    So there is no "trig" anywhere: the entire twiddle is an index rotation plus
    a sign. That is what makes the split exact rather than exact-to-round-off.

    Bit-identical to the doubly-nested ``Σ_n x_n ζ^{nk mod n}`` loop it replaced
    (`#T1188`) — that loop now lives in ``tests/test_exact_radix2_rc463.py`` as
    the reference oracle, so the identity is gated rather than asserted, over
    real and Gaussian integers, forward and inverse, including 54-bit-significand
    entries that no float carrier could hold.

    ``n`` must be a power of two ``≥ 2`` — the callers
    (:func:`_exact_dft_core`, via :func:`exact_dft` / :func:`_exact_transform`)
    both establish that. ``n = 1`` has no cyclotomic basis at ``h = n/2 = 0`` and
    raises ``IndexError`` off the two-point base, exactly as the replaced loop
    did off its zero-length coefficient vector.

    See :func:`_radix2_ring_op_count` for the measured ``n²``-addition count and
    why Θ(n²) is the output size rather than an algorithmic deficiency.
    """
    if n < 4:
        # Base: n = 2. The ring is ℤ[x]/(x+1) — ζ = −1, dimension 1 — so the
        # whole two-point transform is one Class-M bundle and one Class-K flip.
        return [([re[0] + re[1]], [im[0] + im[1]]),
                ([re[0] - re[1]], [im[0] - im[1]])]
    h = n // 2                                # parent basis dimension
    hh = h // 2                               # sub-transform basis dimension
    ev = _exact_dft_radix2(re[0::2], im[0::2], h, inverse=inverse)
    od = _exact_dft_radix2(re[1::2], im[1::2], h, inverse=inverse)
    spectrum: ExactSpectrum = []
    for k in range(h):
        er, ei = ev[k]
        orr, oi = od[k]
        pr = [0] * h
        pi = [0] * h
        mr = [0] * h
        mi = [0] * h
        for p in range(hh):                   # Class I: embed ζ_{n/2}^p = ζ_n^{2p}
            q = 2 * p
            pr[q] = mr[q] = er[p]
            pi[q] = mi[q] = ei[p]
        for p in range(hh):                   # t = ζ_n^{±k}·O[k], then butterfly
            q = (2 * p - k) if inverse else (2 * p + k)
            wrapped = False
            if q >= h:                        # Class K: x^h = −1 (forward wrap)
                q -= h
                wrapped = True
            elif q < 0:                       # Class K: the same pin, other end
                q += h
                wrapped = True
            cr = orr[p]
            ci = oi[p]
            if wrapped:                       # Class C: re-apply the orientation
                cr = -cr
                ci = -ci
            pr[q] += cr                       # Class M: X[k]   = E[k] + t
            pi[q] += ci
            mr[q] -= cr                       # Class K: X[k+h] = E[k] − t
            mi[q] -= ci
        spectrum.append((pr, pi))
        spectrum.append((mr, mi))
    # Bins were produced in (k, k+h) pairs; the contract is bin order 0..n-1.
    return spectrum[0::2] + spectrum[1::2]


def _exact_dft_core(re: List[int], im: List[int], *, inverse: bool = False) -> ExactSpectrum:
    """The exact integer DFT: ``X[k] = Σ_n signal[n] · ζ^{±nk mod N}``.

    Pure integer add/subtract — no floats. ``ζ = e^{-2πi/N}``. For a power-of-two
    ``N`` the ring is negacyclic (``ζ^{N/2} = -1``, the only "trig" is a Class-K
    sign flip) and this dispatches to the native-C int64 twin when int64-safe,
    else to the pure-Python radix-2 split :func:`_exact_dft_radix2`. For any
    other ``N`` it falls to the general cyclotomic path
    :func:`_exact_dft_core_general` (Φ_N reduction over the length-``φ(N)`` power
    basis). Returns ``N`` cyclotomic-integer coefficients, each a
    ``(real_vec, imag_vec)`` pair. Bit-for-bit deterministic.

    The two power-of-two projections are co-equal in VALUE and differ in SHAPE:
    the C twin ``srmech_exact_dft_i64`` is still the doubly-nested ``2N²``-add
    loop, while the Python projection is the ``N²``-add radix-2 split (`#T1188`).
    Both emit the same ``N²`` integers, so the parity tests hold; only the
    addition count differs, and only the Python one is instrumented.
    """
    n = len(re)
    if not _is_pow2(n):
        return _exact_dft_core_general(re, im, n, inverse=inverse)
    native = _exact_dft_core_native(re, im, n, inverse)
    if native is not None:
        return native
    return _exact_dft_radix2(re, im, n, inverse=inverse)


def _lift_spectrum(spectrum: ExactSpectrum, n: int, *, scale: int = 1) -> List[complex]:
    """The single FPU lift: rotate ``ℤ[ζ_N] → ℂ`` at ``ζ_N = e^{-2πi/N}``.

    The *only* place a float is produced — the projection from the exact discrete
    substrate to the continuous observable. ``scale`` divides the result (use
    ``scale=N`` for a normalised inverse). The root-of-unity table reuses the
    Class-N substrate-native ``cexp`` (same twiddle the float ``dft`` uses), so
    the lift is consistent with the legacy path. Imported lazily so the exact
    core above carries no float dependency (numpy-absent-safe; ``cexp`` /
    ``atan`` are pure-Python Class-N — and ``atan`` is C-dispatched — no numpy).
    """
    from srmech.math.rational import cexp, atan as _atan

    if not spectrum:
        return []
    # Basis degree d: N/2 for the power-of-two negacyclic ring, φ(N) in general.
    # Inferred from the coefficient-vector length so the lift handles both.
    deg = len(spectrum[0][0])
    two_pi = 8.0 * float(_atan(1.0))               # 8·atan(1) = 2π (c_dispatched)
    roots = [cexp(-two_pi * j / n) for j in range(deg)]  # e^{-2πi·j/N}
    out: List[complex] = []
    for (xr, xi) in spectrum:
        acc = 0j
        for j in range(deg):
            acc += complex(xr[j], xi[j]) * roots[j]
        out.append(acc / scale if scale != 1 else acc)
    return out


def exact_dft(signal: Sequence, *, inverse: bool = False) -> ExactSpectrum:
    """Exact ``ℤ[ζ_N]`` integer spectrum of an integer / Gaussian-integer signal.

    ``signal`` must be an all-integer (or Gaussian-integer) sequence of length
    ``N ≥ 2`` (**any** ``N`` — power-of-two or not). Returns the spectrum as ``N``
    cyclotomic-integer coefficients (an :data:`ExactSpectrum`), each a
    ``(real_vec, imag_vec)`` integer pair of length ``φ(N)`` (``= N/2`` when ``N``
    is a power of two) — **no floats**. ``inverse=True`` uses ``ζ^{-nk}`` (apply
    the ``1/N`` scale at :func:`lift` time). Bit-for-bit deterministic; the
    power-of-two case rides the native-C int64 twin, the general case uses the
    arbitrary-precision Python cyclotomic path.

    Raises ``ValueError`` for non-integral input (use
    :func:`~srmech.cascade.spectral_cascades.dft` for float signals) or
    ``N < 2``.
    """
    pairs = _try_int_pairs(signal)
    if pairs is None:
        raise ValueError(
            "exact_dft: integer / Gaussian-integer signal required (bit-exact "
            "math takes ints, not floats); use dft() for floating-point signals."
        )
    re, im = pairs
    n = len(re)
    if n < 2:
        raise ValueError(
            f"exact_dft: length >= 2 required; got N={n}. Use dft() for the "
            f"trivial N<2 case."
        )
    return _exact_dft_core(re, im, inverse=inverse)


def exact_idft(signal: Sequence) -> ExactSpectrum:
    """Inverse exact DFT — :func:`exact_dft` with the conjugate twiddle ``ζ^{-nk}``.

    Unnormalised: the ``1/N`` scale is a Class-N rational applied at :func:`lift`
    time (``lift(exact_idft(x), scale=N)``), keeping this core integer.

    Raises:
        ValueError: forwarded from :func:`exact_dft` — non-integral input (use
            :func:`~srmech.cascade.spectral_cascades.dft` for float signals),
            or ``N < 2``. Declared here rather than left to the delegate
            because this is a public entry point in its own right (added
            0.9.0rc434, `#T1130`: the registry named the exception, the
            docstring did not).
    """
    return exact_dft(signal, inverse=True)


def lift(spectrum: ExactSpectrum, *, scale: int = 1) -> List[complex]:
    """The single FPU lift: rotate an exact ``ℤ[ζ_N]`` spectrum to ``ℂ``.

    This is the **only** place a float is produced — the projection from the
    exact discrete substrate (:func:`exact_dft`) to the continuous observable, at
    ``ζ_N = e^{-2πi/N}``. ``scale`` divides the result (use ``scale=N`` for a
    normalised inverse). Pure-Python / numpy-absent-safe.
    """
    return _lift_spectrum(spectrum, len(spectrum), scale=scale)


def _exact_transform(signal: Sequence, *, inverse: bool = False) -> Optional[List[complex]]:
    """Exact-until-rotation DFT/iDFT of ``signal``, or ``None`` if ineligible.

    The routing helper behind ``dft`` / ``fft``: returns the lifted
    ``List[complex]`` (exact integer spectrum + one FPU lift) when ``signal`` is
    an all-integer / Gaussian-integer sequence of length ``N ≥ 2`` (**any** ``N``
    — the power-of-two case rides the negacyclic / native-C path, the general
    case the cyclotomic ``ℤ[ζ_N]`` path); otherwise ``None`` (caller runs the
    float ``cexp`` path). ``inverse=True`` applies the ``1/N`` normalisation at
    lift time.
    """
    pairs = _try_int_pairs(signal)
    if pairs is None:
        return None
    re, im = pairs
    n = len(re)
    if n < 2:                             # N < 2 is trivial — let the float path handle it
        return None
    spectrum = _exact_dft_core(re, im, inverse=inverse)
    return _lift_spectrum(spectrum, n, scale=(n if inverse else 1))
