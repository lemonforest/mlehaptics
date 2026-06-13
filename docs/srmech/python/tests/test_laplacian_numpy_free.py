"""v0.7.0rc40 — the real-symmetric Class-L core is numpy-absent-safe, the
eigenvalue math is srmech's OWN Jacobi cascade (never numpy LAPACK), and the
whole package is free of ALU ``abs()`` (UPSTREAM §22 + the user directives
"abs() is never fine" and "never use numpy math when srmech can do it with a
cascade").
"""
import ast
import importlib
import pathlib

import pytest

import srmech.amsc.laplacian as L


# --- the srmech Jacobi cascade == the numpy/native eigenvalue path -----------

def _ref_path_graph_laplacian(n):
    edges = [(i, i + 1) for i in range(n - 1)]
    return edges


def test_jacobi_cascade_matches_numpy_path():
    """jacobi_eigvals's no-native fallback is srmech's pure-Python Jacobi
    cascade; it matches the native/numpy spectrum to Jacobi round-off."""
    edges = _ref_path_graph_laplacian(6)
    Lm = L.dense_laplacian(6, edges)        # native or numpy build
    eig_main = [float(x) for x in L.jacobi_eigvals(Lm)]
    eig_py = L._jacobi_eigvals_py(L._dense_laplacian_py(6, edges, None))
    assert len(eig_py) == 6
    for a, b in zip(eig_py, eig_main):
        assert abs(a - b) < 1e-9  # noqa: abs() is allowed in TESTS (tolerance), not in shipped cascades


def test_jacobi_cascade_known_spectrum():
    # Path graph P4 Laplacian has the closed-form spectrum
    # {0, 2-√2, 2, 2+√2} = {0, 0.5857864, 2, 3.4142136}.
    eig = L._jacobi_eigvals_py(L._dense_laplacian_py(4, [(0, 1), (1, 2), (2, 3)], None))
    expected = [0.0, 2.0 - 2.0 ** 0.5, 2.0, 2.0 + 2.0 ** 0.5]
    for a, b in zip(eig, expected):
        assert abs(a - b) < 1e-9


def test_jacobi_cascade_diagonal_and_tiny():
    assert L._jacobi_eigvals_py([]) == []
    assert L._jacobi_eigvals_py([[5.0]]) == [5.0]
    # already-diagonal matrix: eigenvalues are the sorted diagonal
    eig = L._jacobi_eigvals_py([[3.0, 0.0], [0.0, 1.0]])
    assert eig == [1.0, 3.0]


# --- the real-symmetric core runs with numpy ABSENT --------------------------

def test_real_core_numpy_absent():
    """Post-#564 numpy is GONE from srmech entirely (there is no
    ``laplacian.np`` attribute to monkeypatch). The build → eigvals chain runs
    in pure Python (``list[list[float]]`` → ``list[float]``) by default, and
    the Jacobi cascade reproduces the closed-form path-graph spectrum.

    P5 (path on 5 nodes) Laplacian has the closed-form eigenvalues
    ``2 − 2·cos(kπ/5)``, ``k = 0..4`` → ``{0, 2−φ, 1, 2, 2+1/φ}`` numerically
    ``{0, 0.690983, 1.909830, 3.0, 3.690983}`` (Spielman, Spectral Graph
    Theory, path-graph eigenpairs)."""
    # numpy is absent: there is NO laplacian.np attribute.
    from srmech.amsc.mat import Mat
    from srmech.amsc.vec import Vec
    assert not hasattr(L, "np")

    edges = _ref_path_graph_laplacian(5)
    Lp = L.dense_laplacian(5, edges)         # rc129: -> real Mat (.shape + m[i,j])
    assert isinstance(Lp, Mat) and Lp.shape == (5, 5)
    eig = L.jacobi_eigvals(Lp)               # rc129: -> Vec via the cascade
    assert isinstance(eig, Vec)

    # Closed-form path-graph P5 spectrum (hand-computed, no numpy oracle).
    import math
    expected = sorted(2.0 - 2.0 * math.cos(k * math.pi / 5) for k in range(5))
    assert len(eig) == 5
    for a, b in zip(sorted(eig), expected):    # Vec → sorted(list of scalars)
        assert abs(a - b) < 1e-9
    # adjacency + normalized also build numpy-free (Mat carriers).
    assert isinstance(L.dense_adjacency(5, edges), Mat)
    assert isinstance(L.normalized_laplacian(5, edges), Mat)


def test_scientific_tier_ops_run_without_numpy():
    """Post-#564 numpy is GONE, so the complex / signed / magnetic
    "scientific-tier" ops no longer raise an ImportError when numpy is absent —
    they just run as pure-Python cascades returning plain Python lists.

    (The old ``test_scientific_tier_raises_clean_without_numpy`` asserted a
    ``_require_np`` ImportError guard; that guard was deleted with numpy, so
    this now pins the inverse contract: the ops succeed numpy-free.)"""
    from srmech.amsc.mat import Mat
    from srmech.amsc.vec import Vec
    w, V = L.hermitian_eigendecompose([[1.0, 0.0], [0.0, 1.0]])
    assert isinstance(w, Vec) and list(w) == [1.0, 1.0]   # rc129: Vec eigenvalues
    assert isinstance(V, Mat) and V.shape == (2, 2)        # rc129: Mat eigenvectors

    Ls = L.signed_laplacian(2, [(0, 1)], [-1.0])
    assert isinstance(Ls, Mat) and Ls.shape == (2, 2)      # rc129: Mat carrier
    # |−1|-degree on each node is 1 → L = [[1, 1], [1, 1]] (sign on off-diagonal).
    assert Ls[0, 0] == pytest.approx(1.0)
    assert Ls[1, 1] == pytest.approx(1.0)


def test_hermitian_eigendecompose_degenerate_numpy_free():
    """REGRESSION (carrier-consolidation rc135): the pure-Python complex-Hermitian
    eigendecompose used to ``ZeroDivisionError`` on a DEGENERATE eigenvalue — the
    2n real-embedding doubles each complex eigenvector via the J-rotation ``i·z``,
    so the "every other column" pick collapses to a zero vector after Gram–Schmidt
    (the identity matrix is the minimal trigger). The fallback now scans the
    embedding columns at the same eigenvalue for an independent reconstruction.
    Pin: a unitary basis + exact reconstruction ``V·diag(λ)·Vᴴ = H`` on three
    degenerate complex-Hermitian matrices, numpy-free."""
    from srmech.amsc.mat import Mat

    cases = [
        [[1.0, 0.0], [0.0, 1.0]],                       # identity: λ = {1, 1}
        [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 5.0]],   # λ = {2, 2, 5}
        [[2.0, 0.0, 0.0], [0.0, 3.0, 1j], [0.0, -1j, 3.0]],    # complex, λ = {2, 2, 4}
    ]
    for rows in cases:
        H = Mat.from_rows(rows)
        n = H.n_rows
        w, V = L.hermitian_eigendecompose(H)
        lam = list(w)
        for a in range(n):                              # Vᴴ V = I (unitary basis)
            for b in range(n):
                s = sum(V[i, a].conjugate() * V[i, b] for i in range(n))
                tgt = 1.0 if a == b else 0.0
                # abs() allowed in TESTS (tolerance), not in shipped cascades.
                assert abs(s - tgt) < 1e-9              # noqa
        for i in range(n):                              # V·diag(λ)·Vᴴ = H
            for j in range(n):
                s = sum(V[i, a] * lam[a] * V[j, a].conjugate() for a in range(n))
                assert abs(s - complex(rows[i][j])) < 1e-9  # noqa


# --- the "abs() is never fine" codebase ratchet ------------------------------

_PKG_ROOT = pathlib.Path(L.__file__).resolve().parents[1]  # .../srmech/


def _py_files():
    return sorted(_PKG_ROOT.rglob("*.py"))


def test_no_abs_calls_anywhere_in_srmech():
    """RATCHET: no ALU ``abs()`` / ``np.abs()`` / ``math.fabs()`` CALL exists in
    any srmech source file (the user rule: "abs() is never fine" — magnitude is
    an explicit Class-K sign-branch / real-imag composition). This walks the AST
    so docstring/comment mentions of "abs()" don't trip it — only real calls do.
    """
    offenders = []
    for path in _py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            # builtin abs(...)
            if isinstance(fn, ast.Name) and fn.id == "abs":
                offenders.append(f"{path.name}:{node.lineno} abs(")
            # np.abs(...) / numpy.absolute(...) / math.fabs(...)
            elif isinstance(fn, ast.Attribute) and fn.attr in {"abs", "absolute", "fabs"}:
                offenders.append(f"{path.name}:{node.lineno} .{fn.attr}(")
    assert not offenders, (
        "ALU abs() calls found in srmech (abs() is never fine — use an explicit "
        "Class-K sign-branch / real-imag composition):\n  " + "\n  ".join(offenders)
    )


def test_no_math_sqrt_hypot_anywhere_in_srmech():
    """RATCHET (v0.7.0rc40): no ``math.sqrt`` / ``math.hypot`` CALL exists in any
    srmech source file. The ``math`` module's scalar roots have an exact Class-N
    srmech peer (``srmech.amsc.rational.sqrt`` / ``.hypot``) — route scalar roots
    through the cascade, not libm (the §22 "never use numpy/libm math when srmech
    can cascade" discipline; cf. the rc32 abs-sweep / rc33 numpy-math-sweep).
    ``cmath.sqrt`` (genuine complex root, no rational peer) and ``np.sqrt`` on a
    bulk array (no scalar-cascade peer for the vectorised op) are NOT flagged.
    AST-walked so docstring/comment mentions don't trip it — only real calls do.
    """
    offenders = []
    for path in _py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"sqrt", "hypot"}
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "math"
            ):
                offenders.append(f"{path.name}:{node.lineno} math.{node.func.attr}(")
    assert not offenders, (
        "math.sqrt / math.hypot calls found in srmech — route scalar roots through "
        "srmech.amsc.rational.{sqrt,hypot} (the Class-N cascade), not libm:\n  "
        + "\n  ".join(offenders)
    )


# the libm trig / π family each has an exact Class-N srmech peer:
# rational.{sin,cos,tan,atan,atan2} (rc33) + rational.exp (rc34) + the
# pi_cascade (Archimedes hexagon-doubling). `math.gcd` / `math.isqrt` /
# `math.fsum` are exact integer / numerical helpers (NOT continuous-libm
# transcendentals — isqrt even powers rational.py's own sqrt cascade) and are
# deliberately NOT in this family.
_MATH_TRIG_PI_FAMILY = frozenset(
    {"sin", "cos", "tan", "asin", "acos", "atan", "atan2", "exp", "pi", "tau"}
)


def test_no_math_trig_pi_anywhere_in_srmech():
    """RATCHET (v0.7.0rc41): no ``math.{sin,cos,tan,atan,atan2,exp,pi,tau}``
    reference (call OR bare constant) exists in any srmech source file. The
    libm trig / π family each has an exact Class-N srmech peer
    (``srmech.amsc.rational.{sin,cos,tan,atan,atan2,exp}`` + the
    ``pi_cascade``) — route continuous trig / π through the cascade, not libm
    (the §22 "never use numpy/libm math when srmech can cascade" discipline;
    cf. the rc40 ``math.sqrt`` sweep). The "continuous" number line is a
    projection (``[[feedback_continuous_number_line_pedagogical_obstacle]]``);
    a trig value is an exact rational cascade projected to float as the last
    step. Walks the AST (an ``ast.Attribute`` with ``value`` ``math``) so it
    catches both ``math.sin(x)`` calls and bare ``math.pi`` constants, while
    docstring / comment mentions don't trip it. ``math.{gcd,isqrt,fsum}`` are
    exact integer / numerical helpers and are NOT flagged.
    """
    offenders = []
    for path in _py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and node.attr in _MATH_TRIG_PI_FAMILY
                and isinstance(node.value, ast.Name)
                and node.value.id == "math"
            ):
                offenders.append(f"{path.name}:{node.lineno} math.{node.attr}")
    assert not offenders, (
        "math trig / π references found in srmech — route continuous trig / π "
        "through srmech.amsc.rational.{sin,cos,tan,atan,atan2,exp} + the "
        "pi_cascade (the Class-N cascade), not libm:\n  " + "\n  ".join(offenders)
    )
