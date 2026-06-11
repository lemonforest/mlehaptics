"""Carrier-removal ratchet (task #564) — down-only count of modules that hard
``import numpy`` at load time.

The numpy-MATH sweep (#928, rc53–rc68) drove the `np.linalg` / `np.fft` / matmul
/ ufunc call ledgers to their floor — numpy is gone as a *math engine*. What
remains is numpy as a **carrier**: a module-level (column-0) ``import numpy``
means that submodule cannot be loaded on a numpy-free install. The package
already imports numpy-free (these are lazy submodule imports — you only pay them
when you ``from srmech.qm import so8`` etc.); the carrier arc drives each such
module onto the framework-native carriers (:class:`srmech.amsc.hv.HV` 1-D /
:class:`srmech.amsc.mat.Mat` 2-D + the native ctypes dense kernels) so the math
runs with **no numpy present at all**.

This ratchet counts files under ``srmech/`` carrying a top-level ``import
numpy`` and asserts the count is **exactly** the ceiling. The number only goes
DOWN (each module flipped onto the numpy-free carriers decrements it); a new
hard ``import numpy`` raises the count and fails. rc69 (Phase 0, infra) ships
the ``Mat`` carrier + this ratchet and flips **no** modules, so the ceiling is
the pre-arc count.
"""

from __future__ import annotations

import pathlib

import srmech

# rc69: maths-engine sweep floored; carrier arc Phase 0 (infra only — Mat carrier
# + this ratchet, no module flips). Mat itself is numpy-free (its to_numpy bridge
# is a lazy import inside the method), so it does not bump the count.
# rc70: carrier-flip #1 — the FFT op-family goes numpy-free (1-D cascade path +
# lazy n-D fallback). 8 modules drop their top-level `import numpy`:
# _fft_carrier + closed_form_ops.{fft,ifft,rfft,spectrogram} +
# path_b_ops.{fft,ifft,rfft}. 61 -> 53.
# rc75: qm/hurwitz.py flips numpy-free (hurwitz_matrix dissolved into the Hurwitz
# [class] over the exact the_one). 53 -> 52.
# rc77: signal_processing carrier-flip batch #1 — allpass + sign_quantise drop
# their top-level `import numpy` (pure-Python list carriers; the math is the
# existing Class-K sign-branch / Class-N direct-form-I reference). 52 -> 50.
# rc78: signal_processing carrier-flip batch #2 — farrow drops its top-level
# `import numpy`. The cubic-Lagrange sub-filter is a plain-tuple constant table
# and each C[k]·x is an explicit length-4 Class-M micro-reduction (no longer a
# numpy-bound dense_dot_real, which fed numpy carriers into the native kernel
# only to contract four reals). The op runs numpy-absent on a list carrier. 50 -> 49.
# rc79: the DSP convolution foundation — `_dsp_cascades` drops its last numpy
# carrier (np.ascontiguousarray/np.zeros/np.conj). convolve/correlate now run on
# a plain-list buffer ([0]*N promotes int->float->complex exactly), the shift is
# a list slice, the conjugate is the element's own .conjugate(). The 5 consumer
# callsites (fir/matched_filter/multirate/polyphase/path_b matched_filter) wrap
# the list result in np.asarray, preserving their ndarray contracts. 49 -> 48.
# rc80: fir + matched_filter flip (now trivial — _dsp_cascades is numpy-free).
# Both drop their top-level `import numpy` and delegate straight to the numpy-free
# _dsp.convolve / _dsp.correlate (which coerce + 1-D-check + return a list); their
# only prior numpy was the np.asarray return-wrap, now removed. They return lists;
# the 2 smoke tests move .shape -> len. 48 -> 46.
# rc81: wavelet (Haar DWT) flips numpy-free. Its only numpy was np.asarray/np.zeros
# carriers (the 1/sqrt(2) normaliser was already the libm-free Class-N rational.sqrt);
# now a plain-list carrier with explicit elementwise Class-L 2-point sum/difference
# over the dyadic Class-N decimation, one-zero pad for odd lengths. Returns
# (approx_list, [detail_lists]); the smoke test already checks isinstance(details,
# list)+len, so zero test ripple. 46 -> 45.
CEIL_NUMPY_CARRIER = 45


def _srmech_root() -> pathlib.Path:
    return pathlib.Path(srmech.__file__).parent


def _hard_numpy_import_files():
    """Files under srmech/ with a module-level (column-0) ``import numpy``."""
    hits = []
    for p in sorted(_srmech_root().rglob("*.py")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("import numpy") or line.startswith("from numpy"):
                hits.append(p)
                break
    return hits


def test_numpy_carrier_count_is_at_ceiling():
    hits = _hard_numpy_import_files()
    rel = sorted(str(p.relative_to(_srmech_root())) for p in hits)
    assert len(hits) == CEIL_NUMPY_CARRIER, (
        f"numpy-carrier count {len(hits)} != ceiling {CEIL_NUMPY_CARRIER}.\n"
        f"This ratchet is DOWN-ONLY: a new top-level `import numpy` is a "
        f"regression; flipping a module onto the Mat/HV carriers should LOWER "
        f"the ceiling.\nFiles:\n  " + "\n  ".join(rel)
    )


def test_mat_carrier_is_itself_numpy_free():
    """The new 2-D carrier must NOT carry a top-level numpy import (else it would
    bump the very ratchet it exists to drive down)."""
    src = (_srmech_root() / "amsc" / "mat.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        assert not (line.startswith("import numpy") or line.startswith("from numpy")), (
            "srmech.amsc.mat must stay numpy-free at import (lazy bridge only)"
        )
