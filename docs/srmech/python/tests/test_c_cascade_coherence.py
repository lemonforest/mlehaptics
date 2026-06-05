"""v0.7.0rc42 — C-transpile triality coherence ratchet (the native/executable tier).

The rc32/40/41 sweeps (``abs()`` / ``math.sqrt`` / ``math.{sin,cos,atan2,pi}``)
routed the **Python** scalar math onto the Class-N cascade, with AST ratchets
that walk ``*.py`` only. But on a native install (``HAS_NATIVE=True`` — the
default), ``kepler.{pin_slot,kepler_solve,equation_of_centre}`` /
``cascade.kuramoto_step`` / the signed-Laplacian ops dispatch to **C** peers
that still call libm ``sin``/``cos``/``atan2``/``sqrt``/``pow``/``fabs``. So the
*executable-machine* layer is not yet a faithful transpile of the Class-N
cascade the *Python source* + *research notebook* claim — the three coherence
layers (notebook / C+Python source / executable) do not agree (see
``docs/srmech/notes/continuous_math_as_14_class_cascade.md`` §"C-transpile
triality coherence"). Grounded in the RBS-LM ``native-algebra compute surface``
findings (F305/F306, PR #687, read-only): the native compute surface should be
substrate-native too.

This is a **DOWN-only baseline ratchet** (same shape as ``test_jpl_audit.py``:
violations only go DOWN, never up). rc42 records the current count; rc43–rc46
port ``srmech_{sin,cos,atan,atan2}_series_truncate`` + a C ``pi_cascade`` +
``srmech_rational_sqrt`` into JPL-clean C, repoint kepler/kuramoto/laplacian off
libm, and lower the baseline to zero. ``srmech_exp_series_truncate`` already
exists (the only §22 op with a C cascade peer today).
"""
import pathlib
import re

import pytest

import srmech.amsc.laplacian as _L

# --- locate the shipped C library source (repo checkout only) ----------------

#: ``.../docs/srmech/python/srmech/amsc/laplacian.py`` -> ``.../docs/srmech``
_SRMECH_ROOT = pathlib.Path(_L.__file__).resolve().parents[3]
_C_SRC = _SRMECH_ROOT / "c" / "src"
_C_INCLUDE = _SRMECH_ROOT / "c" / "include"

# libm scalar transcendentals that each have (or will have) an exact Class-N
# srmech cascade peer. NOT ratcheted: integer helpers, ``M_E`` etc.
_LIBM_FUNCS = (
    "sin", "cos", "tan", "asin", "acos", "atan2", "atan",
    "exp", "log2", "log10", "log", "sqrt", "hypot", "pow", "fabs", "cbrt",
)
_CALL_RE = re.compile(r"\b(" + "|".join(_LIBM_FUNCS) + r")\s*\(")
_MPI_RE = re.compile(r"\bM_PI(?:_2|_4)?\b")

# BASELINE captured at rc42 (the shipped library c/src + c/include only;
# c/test/* explorer/demo code is excluded — not compiled into libsrmech).
# These ONLY go DOWN as rc43+ transpiles the Class-N cascades into C. The
# per-file ceilings make a regression point at the exact file.
_BASELINE = {
    "srmech_kepler.c": 1,      # fabs x1 (rc46); trig routed -> srmech_sin/cos/atan2 (rc43)
    "srmech_kuramoto.c": 3,    # sin x3                              (rc44)
    "srmech_laplacian.c": 12,  # sqrt x8, exp x1, cos x1, sin x1, log x1 (rc45)
}
_BASELINE_TOTAL = 16          # rc43: kepler trig (7) routed onto the C cascade (23 -> 16)


def _strip_c_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def _count_libm(path: pathlib.Path) -> int:
    src = _strip_c_comments(path.read_text(encoding="utf-8", errors="replace"))
    return len(_CALL_RE.findall(src)) + len(_MPI_RE.findall(src))


def _c_files():
    files = []
    for root in (_C_SRC, _C_INCLUDE):
        if root.is_dir():
            files += sorted(root.glob("*.c")) + sorted(root.glob("*.h"))
    return files


@pytest.mark.skipif(not _C_SRC.is_dir(), reason="C source absent (installed wheel)")
def test_c_libm_baseline_only_goes_down():
    """RATCHET (rc42): libm scalar-math CALLS in shipped libsrmech only go DOWN
    toward zero. Each file's count must be <= its recorded ceiling, and no
    NEW file may introduce libm transcendentals. Route C scalar math through
    the (rc43+) ``srmech_*_series_truncate`` / ``srmech_rational_sqrt`` Class-N
    cascade peers, not libm — so the executable coheres with the Python source
    and the notebook (the C-transpile triality)."""
    counts = {p.name: _count_libm(p) for p in _c_files()}
    counts = {name: n for name, n in counts.items() if n}

    regressions = []
    for name, n in counts.items():
        ceiling = _BASELINE.get(name, 0)
        if n > ceiling:
            regressions.append(
                f"{name}: {n} libm/M_PI sites > baseline {ceiling} "
                f"(route through srmech_*_series_truncate / srmech_rational_sqrt)"
            )
    assert not regressions, "C libm ratchet REGRESSED (only goes down):\n  " + "\n  ".join(regressions)

    total = sum(counts.values())
    assert total <= _BASELINE_TOTAL, (
        f"C libm total {total} > baseline {_BASELINE_TOTAL}. The C-transpile "
        f"triality ratchet only goes DOWN. Per file: {counts}"
    )


@pytest.mark.skipif(not _C_SRC.is_dir(), reason="C source absent (installed wheel)")
def test_c_exp_cascade_peer_exists():
    """Coherence anchor: ``srmech_exp_series_truncate`` (the Class-N exp cascade)
    IS already in the C library — the one §22 op whose executable layer already
    coheres with Python ``rational.exp``. rc43+ brings the trig/sqrt peers up to
    the same standard."""
    rational_c = _C_SRC / "srmech_rational.c"
    assert rational_c.is_file()
    assert "srmech_exp_series_truncate" in rational_c.read_text(encoding="utf-8")
