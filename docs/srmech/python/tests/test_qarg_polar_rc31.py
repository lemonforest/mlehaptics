"""rc31 — the **Qarg** graduation: exact POLAR accessors on the ``Qi`` exact-
complex carrier (F924 / UPSTREAM §74).

``Qi`` gains ``modulus()`` [Class K magnitude], ``arg()`` [Class C orientation],
``as_polar``, ``from_polar`` and ``from_complex`` — composing the exact-``Q``
``cos``/``sin``/``atan2``/``sqrt`` already shipped in
``srmech.amsc.rational`` (re-exported by ``srmech.asymptotic_calculus``). This
closes the harmonic-ladder **Class C + Class K** open rungs: Class C recovers
WHICH-WAY (the directed-edge phase sign), Class K recovers HOW-MUCH (the
direction-blind modulus), both EXACTLY.

Numpy-free + ``math``-free + ``abs()``-free: srmech + stdlib ``fractions`` only.
Magnitudes/residuals are projected to ``float`` ONLY for a comparison, computed
via the Class-N ``hypot`` cascade — never an ALU ``abs()``.
"""
from fractions import Fraction

import srmech.amsc.rational as ac
import srmech.amsc.laplacian as lap
from srmech.amsc.q import Q
from srmech.amsc.qi import Qi


# ── helpers (float projection for COMPARISON only; never an algebraic abs) ──
def _fmag(q):
    """The float magnitude of a single exact ``Q`` — via the Class-N ``hypot``
    cascade (``|q| = hypot(q, 0)``), never an ALU ``abs()``. Projected to float
    only so a residual/sign can be compared."""
    return float(ac.hypot(q, Q(0)))


def _resid(reconstructed: "Qi", original: "Qi") -> float:
    """Reconstruction residual magnitude = ``|Δre + i·Δim|`` via the Class-M/N
    ``hypot`` (the complex-modulus cascade), float-projected for the threshold
    comparison only — no ``abs()``."""
    dre = reconstructed.real - original.real
    dim = reconstructed.imag - original.imag
    return float(ac.hypot(dre, dim))


# ── 1. modulus is EXACT for a perfect-square radicand (the Class-K headline) ─
def test_modulus_3_4_is_exactly_5():
    z = Qi(Q(3), Q(4))                  # |z|² = 9 + 16 = 25, √25 = 5 EXACT
    r = z.modulus()
    assert isinstance(r, Q)
    assert r == Q(5)                    # exact-rational equality, not a float
    assert r == 5
    # composes the carrier's own exact norm_sq()
    assert z.norm_sq() == Q(25)


def test_modulus_equals_abs_alias():
    """``modulus()`` is the named polar alias of the numbers.Complex ``__abs__``."""
    z = Qi(Q(1, 3), Q(2, 7))
    assert z.modulus() == abs(z)        # both ride rational.sqrt(norm_sq)
    assert isinstance(z.modulus(), Q)


# ── 2. arg quadrant SIGNS across the 4 quadrants + the 4 axes ────────────────
def test_arg_quadrant_signs():
    half_pi = float(ac.atan2(Q(1), Q(0)))      # +π/2 reference (exact Q→float)
    pi = float(ac.atan2(Q(0), Q(-1)))          # +π reference

    # Q1: re>0, im>0 → θ ∈ (0, π/2)
    t = float(Qi(Q(2), Q(3)).arg())
    assert 0.0 < t < half_pi
    # Q2: re<0, im>0 → θ ∈ (π/2, π)
    t = float(Qi(Q(-2), Q(3)).arg())
    assert half_pi < t < pi
    # Q3: re<0, im<0 → θ ∈ (−π, −π/2)
    t = float(Qi(Q(-2), Q(-3)).arg())
    assert -pi < t < -half_pi
    # Q4: re>0, im<0 → θ ∈ (−π/2, 0)
    t = float(Qi(Q(2), Q(-3)).arg())
    assert -half_pi < t < 0.0

    # +x axis: θ ≈ 0
    assert Qi(Q(5), Q(0)).arg() == Q(0)
    # +y axis: θ ≈ +π/2
    assert float(Qi(Q(0), Q(5)).arg()) == half_pi
    # −x axis: θ ≈ ±π (atan2 convention: +π for im≥0)
    t = float(Qi(Q(-5), Q(0)).arg())
    assert abs_free_close(t, pi) or abs_free_close(t, -pi)
    # −y axis: θ ≈ −π/2
    assert float(Qi(Q(0), Q(-5)).arg()) == -half_pi


def abs_free_close(a: float, b: float, tol: float = 1e-9) -> bool:
    """Closeness check WITHOUT a Python ALU ``abs()`` — the magnitude of the
    float difference via the Class-N ``hypot`` cascade (``|a−b| = hypot(a−b, 0)``)."""
    return float(ac.hypot(a - b, 0.0)) < tol


# ── 3. round-trip across the 4 quadrants + axes + a fraction point ───────────
def test_from_polar_round_trip():
    pts = [
        Qi(Q(2), Q(3)),      # Q1
        Qi(Q(-2), Q(3)),     # Q2
        Qi(Q(-2), Q(-3)),    # Q3
        Qi(Q(2), Q(-3)),     # Q4
        Qi(Q(5), Q(0)),      # +x
        Qi(Q(0), Q(5)),      # +y
        Qi(Q(-5), Q(0)),     # −x
        Qi(Q(0), Q(-5)),     # −y
        Qi(Q(1, 3), Q(2, 7)),  # fraction point
    ]
    for z in pts:
        recon = Qi.from_polar(*z.as_polar())
        assert _resid(recon, z) < 1e-9, f"round-trip residual too large for {z!r}"


# ── 4. from_complex lift ─────────────────────────────────────────────────────
def test_from_complex_lift():
    z = Qi.from_complex(3 + 4j)
    # within float-lift precision the components are exactly 3 and 4
    assert z.real == Q(3)
    assert z.imag == Q(4)
    assert _fmag(z.modulus() - Q(5)) < 1e-12   # modulus ≈ 5


# ── 5. THE HEADLINE C + K CLOSURE on the magnetic Laplacian ──────────────────
def test_magnetic_laplacian_chirality_closure():
    """Reversing every directed edge flips the magnetic-Laplacian phase sign
    (Class C: arg_fwd + arg_rev == 0 EXACT) while the magnitude is
    direction-blind (Class K: modulus_fwd == modulus_rev). The C + K closure."""
    fwd = [(0, 1), (1, 2), (2, 0)]
    rev = [(1, 0), (2, 1), (0, 2)]
    Lf = lap.magnetic_laplacian(3, fwd, q=0.25)
    Lr = lap.magnetic_laplacian(3, rev, q=0.25)

    # a corresponding off-diagonal complex entry of each
    zf = Qi.from_complex(Lf[0, 1])
    zr = Qi.from_complex(Lr[0, 1])

    arg_fwd = zf.arg()
    arg_rev = zr.arg()
    # Class C — the chirality flip: reversing the edge flips the phase sign.
    assert arg_fwd + arg_rev == Q(0)            # EXACT zero
    assert isinstance(arg_fwd + arg_rev, Q)

    # Class K — direction-blind magnitude.
    assert zf.modulus() == zr.modulus()
    assert isinstance(zf.modulus(), Q)


# ── 6. the no-new-code claim: the ops accept + return Q ──────────────────────
def test_ops_accept_and_return_q():
    z = Qi(Q(3), Q(4))
    assert isinstance(ac.sqrt(z.norm_sq()), Q)
    assert isinstance(ac.atan2(z.imag, z.real), Q)
    assert isinstance(ac.cos(z.arg()), Q)
    assert isinstance(ac.sin(z.arg()), Q)
    # as_polar returns the (Q, Q) pair; from_polar consumes the Q theta directly
    r, th = z.as_polar()
    assert isinstance(r, Q) and isinstance(th, Q)
    assert isinstance(Qi.from_polar(r, th), Qi)


# ── 7. the carrier stays numpy-free / fractions-interop sanity ──────────────
def test_polar_is_numpy_free_fractions_interop():
    # a Q theta is Fraction-coercible (carrier numeric-protocol conformance)
    z = Qi(Q(1, 2), Q(1, 2))
    th = z.arg()
    assert Fraction(th) == Fraction(th.numerator, th.denominator)
    # round-trip still lands
    recon = Qi.from_polar(*z.as_polar())
    assert _resid(recon, z) < 1e-9
