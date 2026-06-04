"""v0.7.0rc33 — the real-symmetric Class-L core is numpy-absent-safe, the
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

def test_real_core_numpy_absent(monkeypatch):
    """Force ``laplacian.np = None`` → the build → eigvals chain runs in pure
    Python (list[list[float]] → list[float]) and matches the numpy spectrum."""
    edges = _ref_path_graph_laplacian(5)
    ref_eig = [float(x) for x in L.jacobi_eigvals(L.dense_laplacian(5, edges))]

    monkeypatch.setattr(L, "np", None)
    Lp = L.dense_laplacian(5, edges)         # -> list[list[float]]
    assert isinstance(Lp, list) and isinstance(Lp[0], list)
    eig = L.jacobi_eigvals(Lp)               # -> list[float] via the Jacobi cascade
    assert isinstance(eig, list)
    for a, b in zip(eig, ref_eig):
        assert abs(a - b) < 1e-9
    # adjacency + normalized also build numpy-free
    assert isinstance(L.dense_adjacency(5, edges), list)
    assert isinstance(L.normalized_laplacian(5, edges), list)


def test_scientific_tier_raises_clean_without_numpy(monkeypatch):
    """The complex / signed / magnetic scientific-tier ops raise a clear
    ImportError (via _require_np) when numpy is absent — not an opaque
    AttributeError."""
    monkeypatch.setattr(L, "np", None)
    with pytest.raises(ImportError):
        L.hermitian_eigendecompose([[1.0, 0.0], [0.0, 1.0]])
    with pytest.raises(ImportError):
        L.signed_laplacian(2, [(0, 1)], [-1.0])


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
