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
the ITERATED PREIMAGE of the renormalization :class:`~srmech.amsc.poly.Poly`
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

from .q import Q  # rc100: the exact-ℚ scalar carrier (fractal_spectrum scale / |q|-meter)
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
    PREIMAGE of the renormalization map ``R`` (a decimation :class:`~srmech.amsc.poly.Poly`
    with a fixed point at the trivial eigenvalue, ``R(0)=0``), NOT a flat list.

    Grounded on the Sierpinski gasket: on the NORMALIZED Laplacian the decimation
    is exactly ``R(z)=z(5−4z)`` (measured — Rammal 1984; Fukushima & Shima,
    *Potential Analysis* 1 (1992) 1–35, OA-attested via the arXiv:1505.05855
    restatement; the paywalled DOIs are motivation-only).

    Args:
        R: the spectral-decimation map — a :class:`~srmech.amsc.poly.Poly` (or an
            ascending-degree coefficient sequence, coerced with
            :meth:`~srmech.amsc.poly.Poly.from_coeffs`). Must be degree ``≥ 2``
            with ``R(0) = 0`` and ``R'(0) > 1``.
        branches: the number of self-similar copies (an int ``≥ 2``).
        log_terms: the Class-N ``log`` series-truncation depth (default 25).

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
    satisfied because every underlying op is already C-mirrored). Exact-``Q``;
    numpy-free; no ``abs()`` (the ``|q|``-meter is a Class-K comparison; ``log``
    is the Class-N float-projection surface reading the bit pattern exactly).

    Raises:
        ValueError: ``R`` not a Poly / coercible sequence, ``R.degree < 2``,
            ``R(0) ≠ 0``, ``R'(0) ≤ 1``, or ``branches < 2``.
    """
    from . import rational as _rational  # best_rational (N) + log (N; = calculus.log)
    from .poly import Poly               # exact-ℚ decimation polynomial carrier (lazy)

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
    lb = _rational.log(branches, terms=log_terms)
    ls = _rational.log(
        si if si is not None else float(scale.numerator) / scale.denominator,
        terms=log_terms)
    ds = (_FRACTAL_Q2 * lb) / ls                # Q ratio of the series-truncated logs
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
# Pure orchestration over shipped, already-C-backed ops (klein4_random /
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
    Klein-4 code is ``klein4_random`` keyed deterministically by this string, so
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
    ``R`` (a :class:`~srmech.amsc.poly.Poly`, ``R(0)=0``) and the branch count
    are folded into a single Klein-4 bundle — a **role-filler record** in the
    shape of :func:`srmech.amsc.hdc.cooccurrence_fold`'s holographic store. Each
    coefficient slot ``c{i}`` (and the ``branches`` slot) gets a deterministic
    **role** code (:func:`~srmech.amsc.hdc.klein4_random`, seeded by the slot
    name); each distinct coefficient VALUE gets a deterministic **filler** code
    (seeded by its ``'num/den'`` token). The fold is the
    :func:`~srmech.amsc.hdc.klein4_bundle` superposition of the role⊗value binds
    ``bind(role_slot, code_value)`` — one lossy Klein-4 hypervector holding the
    whole decimation.

    This direction is **EXACT and total**: given ``(R, branches, dim, seed)`` the
    fold + codebooks are fully determined (bit-for-bit reproducible). The
    LOSSINESS lives entirely in the READ (:func:`fold_spectrum`) — recovering
    which slot holds which value from the superposition is a cleanup-memory
    similarity read, NOT an exact inverse (the HDC asymmetry, F584).

    Args:
        R: the spectral-decimation map — a :class:`~srmech.amsc.poly.Poly` (or an
            ascending-degree coefficient sequence coerced with
            :meth:`~srmech.amsc.poly.Poly.from_coeffs`). Degree ``>= 2``.
        branches: the number of self-similar copies (an int ``>= 2``).
        dim: the Klein-4 width ``D`` of the fold (one uint8 per coordinate). For a
            confident round-trip pick ``dim`` comfortably above
            ``4·(degree + 2)`` (the HDC bundle-capacity floor); the gasket
            (``R=z(5−4z)``, 4 bound pairs) round-trips reliably at ``dim >= 512``.
        seed: base seed for the deterministic role / value codes (default 0).

    Returns:
        A fold store (JSON-native once its :class:`~srmech.amsc.hdc.HV` values are
        serialised, exactly like :func:`~srmech.amsc.hdc.cooccurrence_fold`):

        * ``"fold"`` — the single Klein-4 :class:`~srmech.amsc.hdc.HV` bundle
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
    ships **non_compute** (the cooccurrence_fold / from_bodies precedent).
    numpy-free; no ``abs()``.

    Raises:
        ValueError: ``R`` not a Poly / coercible sequence, ``R.degree < 2``,
            ``branches < 2``, or ``dim < 1``.
    """
    from . import hdc as _hdc                # klein4_random / bind / bundle (M)
    from .poly import Poly                   # exact-ℚ decimation carrier (lazy)

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
        s: _hdc.klein4_random(dim, seed=_hdc._cooc_token_seed("ROLE:" + s, seed))
        for s in slots
    }

    # Deterministic per-value FILLER codes (the cleanup alphabet). A repeated
    # coefficient value reuses its one code (so the codebook is value-keyed).
    codes: Dict[str, object] = {}

    def code_for(tok: str):
        c = codes.get(tok)
        if c is None:
            c = _hdc.klein4_random(dim, seed=_hdc._cooc_token_seed("VAL:" + tok, seed))
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
    (:func:`~srmech.amsc.hdc.klein4_unbundle` = self-inverse XOR) and cleans the
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
            equivalent — the Klein-4 values may be :class:`~srmech.amsc.hdc.HV`
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

    Pure orchestration over shipped ops → **non_compute**. numpy-free; no
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

    from . import hdc as _hdc                # klein4 bind / bundle / similarity

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
    from .poly import Poly

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
# The shape MIRRORS srmech.amsc.harmonic_maass.HarmonicMaass(hol, shadow) —
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
    the RECOVERABILITY analogue of :class:`~srmech.amsc.harmonic_maass.HarmonicMaass`
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
      :class:`~srmech.amsc.poly.Poly`) whose presence makes the pair fully
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
        from .poly import Poly                # exact-ℚ decimation carrier (lazy)
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
        """The exact generating decimation :class:`~srmech.amsc.poly.Poly` ``R``
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
        from . import hdc as _hdc            # klein4_similarity (M)
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
        :func:`srmech.amsc.op_provenance.lossy_projection_record` — the fold's
        DECIDABLE identity when the complement is present, else ``None`` (you
        cannot decide identity from a lossy bundle alone). dim/seed are NOT part
        of the identity: two folds of the same ``(R, branches)`` at different
        dims recover the SAME object and share this address."""
        if self._exact_seed_R is None:
            return None
        from . import op_provenance as _op    # rc117 canonical machinery (lazy)
        rec = _op.lossy_projection_record(
            "srmech.amsc.coupling.fold_encode",
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
        R: the spectral-decimation map — a :class:`~srmech.amsc.poly.Poly` (or an
            ascending-degree coefficient sequence coerced with
            :meth:`~srmech.amsc.poly.Poly.from_coeffs`). Degree ``>= 2``.
        branches: the number of self-similar copies (an int ``>= 2``).
        dim: the Klein-4 width ``D`` of the lossy bundle (``>= 1``). Recovery is
            exact at ANY dim (the seed is carried); dim only affects the LOSSY
            bundle's rc124 similarity read.
        seed: base seed for the deterministic role / value codes (default 0).

    Returns:
        A :class:`RecoverableFold` pair ``(lossy_bundle, exact_seed_R=R)``.

    Pure orchestration + data over shipped ops → NO new numerical kernel, NO new
    C peer. numpy-free; no ``abs()``.

    Raises:
        ValueError: ``R`` not a Poly / coercible sequence, ``R.degree < 2``,
            ``branches < 2``, or ``dim < 1`` (surfaced by :func:`fold_encode`).
    """
    from .poly import Poly                    # exact-ℚ decimation carrier (lazy)
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

    This IS :func:`srmech.amsc.op_provenance.op_verdict`'s EQUAL/UNKNOWN
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


__all__ = ["signed_sum_squared", "resonant_spectrum", "from_bodies",
           "fractal_spectrum", "fold_encode", "fold_spectrum",
           "RecoverableFold", "fold_encode_recoverable", "fold_identity"]
