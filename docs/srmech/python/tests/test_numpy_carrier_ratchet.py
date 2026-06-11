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
# rc82: iir flips numpy-free (same pattern as allpass rc77). The optional scipy
# accelerator stays lazy (scipy needs numpy → numpy-absent falls through), passing
# list inputs straight to lfilter/sosfilt and wrapping the result in list(); the
# no-scipy path is the pure-Python direct-form-II difference equation (Class-C
# recursive cascade of the Class-N b/a rational) over lists. Returns list; the
# smoke test moves .shape -> len. 45 -> 44.
# rc83: viterbi flips numpy-free (workflow-scoped batch). The trellis DP tables
# (delta/psi) become list-of-lists, the branch metrics are explicit Class-M
# multiply-adds over the column A[:,s] (list comp), and the two np.argmax merges
# are the Class-K pin-slot as Python max(range, key=) (first-maximal tie-break,
# matching np.argmax). Self-contained — no scipy/helper delegation. Returns list;
# the smoke test moves .shape -> len. 44 -> 43.
# rc84: ofdm flips numpy-free (workflow-scoped batch). The modulate path returns a
# 1-D list ([complex(0)]*N buffer; prefix + time_block concat via +; slice-assign);
# the demodulate path returns a list-of-lists (one row per OFDM symbol). The Class-L
# one-tap equaliser inlines the numpy-bound elementwise_hypot via the numpy-free
# Class-N rational.hypot in a per-subcarrier comprehension, and the np.where |H_k|
# guard becomes an explicit Class-K pin-slot sign-branch (> 1e-12 → H_k else 1.0; no
# abs()). _sc.fft/_sc.ifft already return List[complex]. Returns list / list-of-list;
# the baseline + rc61-routing smoke tests move .shape/.reshape -> len/flatten. 43 -> 42.
# rc85: polyphase flips numpy-free (workflow-scoped batch; clean leaf like fir/
# matched_filter). Its only delegate is the numpy-free `_dsp.convolve` (List return);
# the np.asarray wrap drops. The strided polyphase split/interleave `[::L]` are native
# list slices, and the per-component accumulate (`out[:n] += filtered`) + the strided
# interleave write (`out[k::L][:m] = c`) become explicit Class-M elementwise index
# loops. `decompose` returns list-of-lists, `op` returns a list. 42 -> 41.
# rc86: beamforming_fixed flips numpy-free (workflow-scoped batch; clean leaf). The
# array_signals coerce to a list-of-lists of complex; np.full/np.zeros -> plain lists;
# np.complex/np.int -> complex()/int(); the `max_delay` is the builtin `max` over the
# integer delays (Class-L reduce, no abs()); the per-mic delay-and-sum is an explicit
# scale-and-accumulate (Class-M) index loop `out[i] += w[m]*sig[m][delay+i]`. Returns a
# list of complex; the smoke test moves `y.ndim==1`/`y.shape[0]` -> isinstance/len. 41 -> 40.
# rc87: wiener flips numpy-free (workflow-scoped batch; clean leaf). FFT -> per-bin
# |X|²=X.real²+X.imag² -> Class-N rational MMSE gain S/(S+N) -> IFFT -> real part, all
# explicit elementwise list comprehensions; the np.maximum(..., 1e-30) eps floors
# become the builtin `max(x, 1e-30)` per bin. `_sc.fft`/`_sc.ifft` already return
# List[complex]; np.asarray/np.real wraps drop. Returns a list of float; the baseline +
# rc61 smoke tests move `.shape` -> len (the rc61 finite/real checks pass on the list). 40 -> 39.
# rc88: cross_spectral flips numpy-free (workflow-scoped batch; MODERATE — the FIRST
# sigproc carrier-flip to need π). The Hann window uses a module-level
# `_PI = float(pi_cascade_digits(30))` (Class-N Archimedes hexagon-doubling cascade,
# already the numpy-free π source in exact_dft/spectral_cascades) fed to `rational.cos`;
# the cross-product X·conj(Y), per-bin |z|²=real²+imag² (no abs()) and the
# np.maximum(...,1e-30) coherence floor (builtin max) are explicit list comprehensions.
# `_sc.fft` returns List[complex], `_fc.fftfreq` returns a plain list numpy-absent.
# Returns (list, list); the baseline smoke moves `.shape` -> len (rc61 wraps coh in
# np.asarray, resilient). 39 -> 38.
CEIL_NUMPY_CARRIER = 38


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
