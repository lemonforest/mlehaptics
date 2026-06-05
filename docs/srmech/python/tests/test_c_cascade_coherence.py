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
violations only go DOWN, never up). rc42 recorded the count (23); rc43–rc45
ported ``srmech_{sin,cos,atan,atan2}`` + ``srmech_rational_sqrt`` into JPL-clean
C and repointed kepler/kuramoto/laplacian (23 -> 16 -> 13 -> 3); **rc46 closes
it out** — ``srmech_exp``/``srmech_log`` (the Q61 integer exp/atanh cascades)
repoint the laplacian elementwise transcendental, and the last ``fabs`` becomes
a Class-K sign-branch, so the baseline is **ZERO**: the shipped libsrmech holds
no libm transcendental. The guard now also covers the C99 **complex** libm
(``csin``/``ccos``/``cexp``/``csqrt``/... and any ``<complex.h>`` include) so a
future complex op can't silently reintroduce libm. The executable, the
C+Python source, and the research notebook all agree (C-transpile triality).
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

# libm scalar transcendentals that each have an exact Class-N srmech cascade
# peer. NOT ratcheted: integer helpers, ``M_E`` etc. The C99 complex variants
# (csin/cexp/...) are included so a future complex op can't silently bring libm
# back in — they have no cascade peer yet, so their ceiling is 0.
_LIBM_FUNCS = (
    "sin", "cos", "tan", "asin", "acos", "atan2", "atan",
    "exp", "log2", "log10", "log", "sqrt", "hypot", "pow", "fabs", "cbrt",
    "csin", "ccos", "ctan", "cexp", "clog", "csqrt", "cpow", "cabs",
)
_CALL_RE = re.compile(r"\b(" + "|".join(_LIBM_FUNCS) + r")\s*\(")
_MPI_RE = re.compile(r"\bM_PI(?:_2|_4)?\b")

# BASELINE — ZERO at rc46 (the shipped library c/src + c/include only; c/test/*
# explorer/demo code is excluded — not compiled into libsrmech). rc42 recorded
# 23; rc43/44/45/46 transpiled the trig / sqrt / exp / log Class-N cascades into
# C and routed kepler/kuramoto/laplacian off libm. There is no libm
# transcendental left in the shipped library; this dict stays EMPTY (any file
# that reintroduces one fails — the ratchet only ever goes DOWN).
_BASELINE = {}                # rc46: ZERO — executable fully on the cascade
_BASELINE_TOTAL = 0           # rc46: closeout (23 -> 16 -> 13 -> 3 -> 0)


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


@pytest.mark.skipif(not _C_SRC.is_dir(), reason="C source absent (installed wheel)")
def test_no_complex_h_include_in_shipped_library():
    """GUARD (rc46): the shipped libsrmech does not pull in C99 ``<complex.h>``.
    The complex-libm transcendentals (csin/ccos/cexp/csqrt/...) have no Class-N
    cascade peer yet — so the door stays shut until one exists. Phase factors
    are done as pure algebra (gamma/|gamma|), never via complex libm."""
    offenders = []
    for p in _c_files():
        src = _strip_c_comments(p.read_text(encoding="utf-8", errors="replace"))
        if re.search(r"#\s*include\s*<complex\.h>", src):
            offenders.append(p.name)
    assert not offenders, (
        "shipped libsrmech must not include <complex.h> (no cascade peer for "
        f"the complex libm transcendentals yet): {offenders}"
    )


@pytest.mark.skipif(not _C_SRC.is_dir(), reason="C source absent (installed wheel)")
def test_c_explog_cascade_peers_exist_and_repointed():
    """Coherence anchor (rc46 closeout): the double-wrapper exp/log cascades
    ``srmech_exp`` / ``srmech_log`` ship in ``srmech_explog.c``, and the
    laplacian elementwise transcendental routes through them — no bare libm
    ``exp(``/``log(`` remains in ``srmech_laplacian.c``. Executable == source."""
    explog_c = _C_SRC / "srmech_explog.c"
    assert explog_c.is_file(), "srmech_explog.c (the C exp/log cascade) is missing"
    explog_src = explog_c.read_text(encoding="utf-8")
    assert "srmech_status_t srmech_exp(" in explog_src
    assert "srmech_status_t srmech_log(" in explog_src

    lap_src = _strip_c_comments(
        (_C_SRC / "srmech_laplacian.c").read_text(encoding="utf-8")
    )
    assert "srmech_exp(" in lap_src and "srmech_log(" in lap_src
    assert not re.search(r"(?<![A-Za-z0-9_])exp\s*\(", lap_src), "bare libm exp( in laplacian.c"
    assert not re.search(r"(?<![A-Za-z0-9_])log\s*\(", lap_src), "bare libm log( in laplacian.c"
