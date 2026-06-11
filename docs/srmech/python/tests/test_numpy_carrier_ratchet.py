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
# rc89: stft flips numpy-free (workflow-scoped batch; windowed follower of cross_spectral,
# reusing the codified `_PI = float(pi_cascade_digits(30))` + `_ccos` -> rational.cos π
# source). The signal coerces to a list of complex; the default Hann window is the same
# `_PI`-formed `_ccos` cascade; per-frame `signal·window` + `_sc.fft` build a list-of-lists
# STFT matrix (no np.zeros stack). spectrogram (already top-level-numpy-free since rc70 —
# uncounted) consumes the list-of-lists and computes |z|²=real²+imag² (no abs()) elementwise.
# stft's baseline + rc33 window/op tests move `.ndim`/`.shape` -> isinstance/len; only stft
# carries a top-level import, so the count drops by one. 38 -> 37.
# rc90: spectral_subtraction flips numpy-free (Class-L FFT-PSD ∘ Class-N rational floor).
# The FIRST flip whose numpy-free output is NOT bit-exact-0.0: `np.angle` (libm atan2) routes
# through `rational.atan2` and the phasor/magnitude — previously the NUMPY-CARRIER helpers
# `elementwise_transcendental(phase, "exp_i")` + `elementwise_sqrt` (both use np.zeros/reshape
# INTERNALLY, the rc70 "runnable!=loadable" trap) — are inlined per-bin as `rational.{sqrt,cos,
# sin}` so the op runs numpy-ABSENT. `np.maximum` floor -> builtin `max`; `_sc.fft`/`_sc.ifft`
# return List[complex]. Value-faithful to machine eps (maxerr 6.7e-16, the rational cascades
# match libm to <=1 ULP), NOT bit-exact. Returns a list of float; smoke `.shape` -> len. 37 -> 36.
# rc91: multitaper flips numpy-free (Class-L DPSS eigenbasis ∘ Class-M tapered-periodogram
# bundle-average). scipy.signal.windows.dpss is an EXTERNAL accelerator (needs numpy) → kept
# LAZY inside the try; numpy-absent it raises ImportError and the op falls to the fully
# numpy-free cosine-taper fallback (`_PI`+`_csin`→rational.sin; ℓ²-norm inline
# `rational.sqrt(Σvᵢ²)` since the old `dense_norm` helper is numpy-carrier INTERNALLY). The
# per-taper |F|²=real²+imag² (no abs()) bundle-average is an explicit list comp; `_sc.fft`
# returns List[complex]. Differential dpss-path BIT-EXACT (maxerr 0.0); the rc60 `np.linalg.norm`
# absence ratchet + rc61 routed assert stay green (no np.linalg.norm, keeps `_sc`). Returns a
# list of float; the 3 op-smoke `.shape` asserts (rc33 ×2 + baseline) move to isinstance/len. 36 -> 35.
# rc92: multirate flips numpy-free (Class-N rational rate ∘ Class-C cyclic streaming). The
# windowed-sinc low-pass taps use a substrate-native `_sinc` (sin(πx)/(πx) over the Class-N
# `_PI`; the x=0 removable singularity is a Class-K branch returning 1.0, NO division, no abs())
# + a numpy-free `_ccos` Hamming window; `np.arange`->range, `np.zeros`->[0.0]*, `np.sum`->sum,
# strided upsample insert is a plain loop, `_dsp.convolve` already returns a list, downsample is
# a `[::down]` slice scaled by `up`. Value-faithful to machine eps (maxerr 7.1e-15, the rational
# sinc/cos cascades match libm to <=1 ULP), NOT bit-exact. op returns a list of float; the rc33
# `_ccos` Hamming test moves `.ndim`/broadcast -> list-comp + isinstance/len, and the baseline
# smoke `.ndim` -> isinstance(list). 35 -> 34.
# rc93: sinc_interp flips numpy-free (Class-L band-limit eigenbasis ∘ Class-K pin-slot;
# Whittaker-Shannon). The sinc kernel reuses the rc92 `_sinc` (sin(πx)/(πx) over `_PI`,
# x=0 Class-K branch → 1.0, no division, no abs()) + a pure-Python `_median` of the
# sample-spacing diffs. The complex matvec out[q]=Σ_s sinc((t_q−t_s)/T)·y[s] is an inline
# nested sum over plain lists — NOT `dense_matvec_complex` (numpy-carrier INTERNALLY, the
# rc70 trap; also a matmul-ledger site, but the math ratchet is `<=` so its removal stays
# green). Value-faithful to machine eps (maxerr 1.1e-16; identity/scalar paths bit-exact
# 0.0). op returns a list of complex (or a single complex for a scalar target); the
# baseline smoke `.shape` -> isinstance/len. 34 -> 33.
# rc94: path_b_ops/sign_quantise flips numpy-free (Class-K pin-slot ∘ Class-M
# dispatch tag; Spike #174 sign-quantise BER anchor). Pure carrier — np.asarray/
# np.zeros_like/np.where with NO helper deps; the np.where IS the Class-K sign-
# branch, now an explicit per-element if/else (no abs()). Returns a list of int
# {-1,0,+1} (was an int8 ndarray); bit-exact to the old decision. The Spike #174
# path_b_mvp BER test already wraps the dispatch result in np.asarray(dtype=int8)
# before .tobytes()/.astype(), so it's robust to the list return. 33 -> 32.
# rc98 (#564): FIRST CONSUMER flip riding the completed Mat foundation —
# closed_form_ops/esprit goes numpy-FREE by routing its three matrix steps
# through the native mat_hermitian_eigendecompose / mat_lstsq / mat_eigvals trio
# (drops `import numpy as np`; argsort -> pure-Python sorted; returns list of
# complex). The Mat foundation (rc74/95/96/97) is what made this runnable, not
# just loadable (the rc70 trap). 32 -> 31.
# rc99 (#564): SECOND CONSUMER flip — closed_form_ops/music (the ESPRIT sibling)
# goes numpy-FREE by routing its covariance eigendecomp + noise-subspace
# projection through native mat_hermitian_eigendecompose + mat_matmul (drops
# `import numpy as np`; argsort -> pure-Python sorted; returns list of float).
# 31 -> 30.
# rc100 (#564): THIRD CONSUMER flip — closed_form_ops/heat_kernel (graph
# heat-kernel exp(-tL)·signal) goes numpy-FREE: eigendecomp through native
# mat_hermitian_eigendecompose, the exp(-tλ) spectral filter through the Class-N
# rational.exp cascade (real eigenvalues), the project/reconstruct matvecs as
# pure-Python sums over the eigenvector Mat (drops `import numpy as np`; returns
# list of complex). 30 -> 29.
# rc101 (#564): FOURTH CONSUMER flip — closed_form_ops/lmmse (real-valued linear
# MMSE estimator, a DIFFERENT sub-shape: a real dense SOLVE, not an
# eigendecomposition) goes numpy-FREE: the Class-L gain solve routes off the
# numpy-carrier dense_solve onto native mat_solve over a real Mat (Ryyᵀ·Z=Rxyᵀ),
# and the K·(y-mean_y) estimate is a pure-Python matvec (drops `import numpy as
# np`; returns list of float). 29 -> 28.
# rc102: map_ml (the linear-Gaussian MAP/ML estimator) goes numpy-FREE — the
# covariance inverse (R_v^{-1}/R_x^{-1}) + normal-equation solve route off the
# numpy-carrier dense_solve onto native mat_solve over real Mats, A^T R_v^{-1}
# rides mat_matmul, and the matvecs are pure-Python sums (drops `import numpy as
# np`; returns list of float). 28 -> 27.
CEIL_NUMPY_CARRIER = 27


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
