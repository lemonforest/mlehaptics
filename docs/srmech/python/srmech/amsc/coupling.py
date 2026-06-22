"""Class K ∘ L — signed-sum coupling score + the resonant-spectrum closure.

Two coupling-cascade ops live here:

``signed_sum_squared(sources)``: per-element ``(Σ_sources (2·bit − 1))²`` — the
Class-K bipolar sign-projection ∘ Class-L signed-magnitude-square (a *stack* of
bit-arrays → a coupling-strength score).

``resonant_spectrum(L, *, orders, max_den)``: the **spectral row of the
closure-dispatch** (UPSTREAM §75 / F928). It reads a real-symmetric coupling
Laplacian ``L`` as a *stored* (excitation-free) object:

* its **eigenvalues** (ascending) are the stored **"dark" tension spectrum** —
  the MFO **field** (the composition that exists with *no* pluck/excitation,
  F907). A single driven eigenmode is the **excitation** (matter).
* its **eigenvectors** (columns) are the **excitation modes**.
* the **force-orders** ``[L, L², …, Lᵒ]`` are forces-of-forces — ``L²`` is the
  **biharmonic / tidal** concentration (4th-order dispersive curvature, NOT the
  2nd-order matter curvature). Each ``Lᵏ = V·diag(Λᵏ)·Vᵀ`` is reconstructed in
  the eigenbasis from **one** eigensolve (Λ raised to ``k``), never by repeated
  ``L``-matmuls.
* the **resonances** are integer/prime ratios of the tensions: each adjacent
  nonzero-tension ratio is read with Class-N :func:`best_rational`, and the
  resulting denominator is prime-coordinate-factorised (Class-J
  :func:`srmech.amsc.primes.factor` / :class:`srmech.amsc.qprime.Qprime`) —
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

from typing import Dict, List, Optional, Sequence, Tuple

from .vec import Vec  # rc129: the numpy-free 1-D carrier (restores .shape)


def signed_sum_squared(sources: Sequence) -> "Vec":
    """Squared signed-sum coupling score across a stack of bit-arrays.

    Args:
        sources: A non-empty sequence of equal-length 1-D sequences, each
            holding bits in ``{0, 1}``.

    Returns:
        A real :class:`~srmech.amsc.vec.Vec` (same length as each source;
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


def _resonant_spectrum_native(L, orders: int, max_den: int):
    """The §75 native path: route through the ``srmech_resonant_spectrum`` C
    peer when it is bound, returning the same dict the pure-Python op returns
    (value-parity — native authoritative when present). Returns ``None`` when no
    native lib / symbol, so the caller runs the pure-Python complete alternative.
    """
    import ctypes
    from . import _native
    from . import primes as _primes
    from .mat import Mat

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
) -> Dict[str, object]:
    """Read a coupling Laplacian as a stored resonant object (§75 / F928).

    Args:
        L: an ``(n, n)`` real-symmetric coupling Laplacian — a
            :class:`~srmech.amsc.mat.Mat` (or list-of-rows / ndarray-like). The
            stored ("dark") object before any excitation.
        orders: how many force-orders to materialise — ``[L¹, …, Lᵒ]`` (default
            2: the force ``L`` and the biharmonic forces-of-forces ``L²``).
            Must be ``≥ 1``.
        max_den: the ``best_rational`` denominator ceiling for the resonance
            read (Class-N). Default 64 (the Laplace 4:2:1 ladder fits well
            inside it). The lock/libration cutoff scales as ``isqrt(max_den)``.

    Returns:
        A dict with:

        * ``"tensions"`` — a real :class:`~srmech.amsc.vec.Vec` of eigenvalues
          ASCENDING (the stored "dark" tension spectrum; no excitation).
        * ``"modes"`` — an ``n×n`` real :class:`~srmech.amsc.mat.Mat` whose
          COLUMNS are the eigenvectors (the excitation modes).
        * ``"force_orders"`` — a list of ``orders`` :class:`~srmech.amsc.mat.Mat`
          ``[L, L², …, Lᵒ]``; ``Lᵏ = V·diag(Λᵏ)·Vᵀ`` reconstructed from the ONE
          eigensolve (Λ raised to ``k`` in the eigenbasis), never repeated
          ``L``-matmuls.
        * ``"resonances"`` — a list of dicts, one per adjacent nonzero-tension
          pair, each ``{"pair": (i, j), "ratio": (num, den), "den_coords":
          {prime: exp}, "locked": bool}``: the Class-N best-rational of the
          tension ratio + the Class-J prime-coordinate factorisation of its
          denominator + the lock (smooth/2-adic den) vs libration (large-prime
          den) verdict.

    The op composes SHIPPED ops only — ``laplacian.symmetric_eigendecompose``
    (Class L), ``laplacian.mat_matmul`` / the carrier ``@`` (Class L),
    ``rational.best_rational`` (Class N), ``primes.factor`` /
    ``qprime.Qprime`` (Class J) — so it is value-identical on the native and
    pure-Python paths (the C peer ``srmech_resonant_spectrum`` orchestrates the
    same kernels). Numpy-free; no ``abs()`` (tension signs are read by
    comparison, Class-K).

    Raises:
        ValueError: ``orders < 1`` or a non-square / empty ``L``.
    """
    from . import laplacian as _L  # lazy: laplacian imports carriers (avoid cycle)
    from . import primes as _primes
    from . import rational as _rational
    from .mat import Mat

    if not isinstance(orders, int) or orders < 1:
        raise ValueError(f"resonant_spectrum: orders must be an int >= 1; got {orders!r}")

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
    # Read every ADJACENT nonzero-tension pair (ascending). The smaller-over-
    # larger ratio sits in (0, 1]; best_rational reads it; factor the denom.
    nz = [i for i in range(n) if lam[i] > lam[-1] * _ZERO_TENSION_REL]
    resonances: List[Dict[str, object]] = []
    for a, b in zip(nz, nz[1:]):
        lo, hi = lam[a], lam[b]  # ascending ⇒ lo ≤ hi, both > 0
        # ratio = lo/hi ∈ (0, 1]; scale to an integer pair for the exact read.
        num_in = int(round((lo / hi) * _RATIO_SCALE))
        num, den = _rational.best_rational(num_in, _RATIO_SCALE, max_den)
        den_coords = {p: e for p, e in _primes.factor(den)} if den > 1 else {}
        resonances.append({
            "pair": (a, b),
            "ratio": (num, den),
            "den_coords": den_coords,
            "locked": _tension_is_locked(den_coords, max_den=max_den),
        })

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
    ``laplacian.dense_laplacian(n, edges, weights)``. Numpy-free; pure
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


__all__ = ["signed_sum_squared", "resonant_spectrum", "from_bodies"]
