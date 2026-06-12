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
import re

import srmech

# A column-0 (module-level) numpy IMPORT STATEMENT — not arbitrary prose that
# merely begins with the words "import numpy". The naive ``startswith("import
# numpy")`` over-counted a docstring line in ``amsc/cascade/one.py`` ("import
# numpy lazily (the [scientific] tier…") even though the_one is numpy-FREE at
# import (its only numpy is a LAZY ``require_numpy`` inside ``to_numpy`` /
# ``to_matrix``). This regex matches only a real statement: ``import numpy`` /
# ``import numpy as np`` / ``import numpy.sub`` / ``from numpy[.sub] import …``
# (optionally trailed by a comment), and crucially NOT ``import numpy <word>…``.
_NUMPY_IMPORT_RE = re.compile(
    r"^(?:import numpy(?:\.\w+)*(?:\s+as\s+\w+)?\s*(?:#.*)?$"
    r"|from numpy(?:\.\w+)*\s+import\s)"
)


def _is_numpy_import(line: str) -> bool:
    """True iff ``line`` is a real column-0 numpy import statement."""
    return _NUMPY_IMPORT_RE.match(line) is not None

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
# rc103: fsk (the FSK modulator/demodulator) goes numpy-FREE — the per-symbol
# tone phases e^{i·2π·f·t} route off the numpy-carrier elementwise_transcendental
# onto the Class-N rational.cos/sin cascade over `_PI` (the `_exp_i` helper), and
# the demod correlator bank is a pure-Python complex matvec deciding on
# argmax|corr|² (no sqrt / no abs); modulate returns list[complex], demod returns
# list[int] (drops `import numpy as np`). 27 -> 26.
# rc104: dct (DCT-II / DCT-III) goes numpy-FREE — the cosine basis is built as a
# list-of-lists through the Class-N rational.cos cascade over `_PI`, the transform
# is a pure-Python matvec (1-D) / per-axis row|column transform (2-D), DCT-III
# weights the j=0 term by 1 (exact scipy parity, the inverse of DCT-II), and the
# old scipy.fft.dct fast-path is dropped (it needed numpy as a carrier). The jpeg
# CONSUMER stays numpy (flips in its own later rc) and coerces dct's list return
# back to ndarray at the `_dct` boundary wrapper. dct drops `import numpy as np`;
# returns list / list-of-lists. 26 -> 25.
# rc105: vector_quantisation (nearest-codebook lookup) goes numpy-FREE — the
# nearest-neighbour query becomes a pure-Python argmin over the squared Euclidean
# distance Σ_j (x_j − c_j)² (the matmul cross-term trick is unnecessary for an
# argmin); inputs coerce via tolist(); encode returns list[int], decode returns a
# list-of-rows (drops `import numpy as np` + dense_matmul_real). 25 -> 24.
# rc106: psk_qam (PSK/QAM constellation map) goes numpy-FREE — the PSK points
# route through _exp_i (rational.cos/sin over the substrate-native _PI), the QAM
# grid is pure-Python Gray levels (√M via rational.sqrt), and the demod decision
# is argmin over the squared Euclidean distance |received − const|² (monotone in
# |·|, so no hypot/sqrt/abs); inputs coerce via tolist(); op returns python lists
# (drops `import numpy as np`). 24 -> 23.
# rc107: mlse (Viterbi-trellis channel equaliser) goes numpy-FREE — the trellis
# tables (transition/emission/initial log-prob) become pure-Python list-of-lists
# built with the Class-N rational.log cascade, the per-branch metric is an
# explicit |obs − expected|² multiply-add (no hypot/sqrt/abs), the no-ISI path is
# a squared-distance argmin, and the search delegates to the already-numpy-free
# viterbi.op (returns a list); drops `import numpy as np` + elementwise_hypot. 23 -> 22.
# rc109: mimo_svd (MIMO channel SVD) goes numpy-FREE — routes through the rc108
# `mat_svd` Mat-carrier foundation (Gram AᴴA → mat_hermitian_eigendecompose → √λ +
# A·v/σ + orthonormal null completion), inputs coerce via tolist(), op returns
# python lists (drops `import numpy as np` + `np.linalg.svd`). The np.linalg.svd
# removal ALSO decrements the math ratchet (linalg_fft 23 → 22). 22 -> 21.
# rc110: the two Path B DSP duals of already-flipped Path A ops go numpy-FREE —
# `path_b_ops/matched_filter` (delegates to the rc79 numpy-free `_dsp.correlate`,
# drops its `np.asarray` coerce + return-wrap) and `path_b_ops/wiener` (the rc87
# closed-form Wiener list-comprehension form: `_sc.fft` List[complex] → per-bin
# |X|²=real²+imag² → Class-N rational MMSE gain S/(S+N) with the builtin `max`
# eps-floor → `_sc.ifft` → real part). Both drop `import numpy as np` and return
# python lists (were ndarrays); the math ledger is untouched (the math was already
# cascade-routed; only the carrier `np.asarray`/`np.maximum`/`np.real` go). 21 -> 19.
# rc111: jpeg (block-DCT image compression) goes numpy-FREE — the LAST clean DSP
# carrier flip. The block transform already ran numpy-free via the rc104 `dct.op`
# (list-of-lists); jpeg now carries the 2-D image as nested Python lists end-to-
# end: list-of-lists quant table, per-element Wallace quality scaling (`int(...)`
# = exact floor for the non-negative `(luma·scale+50)/100`), Class-K quantise via
# `round` (round-half-to-even, == np.round), and nested-list encode/decode block
# loops. Drops `import numpy as np` + the `_dct` np.asarray wrapper; encode returns
# list-of-list-of-lists, decode returns a 2-D list (were ndarrays). Math ledger
# untouched (the DCT was already cascade-routed). 19 -> 18.
# rc112: ratchet-ACCURACY fix — `amsc/cascade/one.py` (the_one) was a FALSE
# POSITIVE: the_one is numpy-FREE at import (its only numpy is a LAZY
# `require_numpy` inside `to_numpy`/`to_matrix`), but a docstring line wrapping to
# "import numpy lazily (the…" at column 0 tripped the naive `startswith` scan. The
# scanner is hardened to a real-import regex (`_is_numpy_import`) that ignores
# such prose; the_one drops out of the count. Honest decrement (correcting a
# measurement, not removing a carrier — there was none). 18 -> 17.
# rc113 (#564): the RBS-LM subpackage flips numpy-free — `rbs_lm/substrate.py`
# + `rbs_lm/inference.py` both drop `import numpy as np`. numpy was only ever an
# INCIDENTAL deterministic source here (not a correctness oracle): the per-token
# Klein-4 vector seed (`np.random.default_rng(token_seed)` -> stdlib
# `klein4_random(D, seed=…)`), the learn-memory subsample (`rng.choice(...,
# replace=False)` -> `random.Random(seed).sample`), and the infer sampler
# (`gr.choice(..., p=p)` -> `random.Random(seed).choices(weights=p)`). The encode
# path now returns the framework-native HV carrier end-to-end and `_softmax`
# routes its per-element exp through the Class-N `rational.exp` cascade (NOT the
# numpy-carrier `elementwise_transcendental`). Per `[[feedback_carrier_ratchet_
# misses_require_numpy_subpackage_gates]]` the eager `_require_numpy("srmech.
# rbs_lm")` gate in `__init__.py` is also REMOVED (the whole subpackage is
# numpy-free, so `import srmech.rbs_lm` succeeds numpy-absent). Authorized one-
# time RNG re-base (values change, structural tests are RNG-independent). 17 -> 15.
# rc115 (#564): the first two qm submodules flip numpy-free — `qm/spin.py`
# (Pauli matrices + Clifford Cl(0,3)) and `qm/bell.py` (Bell-CHSH + Tsirelson
# 2√2). Both drop `import numpy as np`: spin's `pauli_matrices`/`pauli_identity`/
# `pauli_spin_operator` now return exact 2×2 complex `Mat` (entries in {0,±1,±i};
# the Clifford residuals combine via `mat_matmul` + the rc114 `mat_norm`); bell's
# `chsh_pauli_combination`/`chsh_operator` return `Mat` built via the numpy-free
# `kron` cascade, `chsh_pauli_combination_norm` uses the EXACT integer
# `eigvals_exact` (residual exactly 0), and `operator_norm`/`chsh_operator_norm`
# go through the unconditionally-numpy-free `mat_hermitian_eigendecompose`. The
# eager `_require_numpy("srmech.qm")` subpackage gate in `qm/__init__.py` is
# relaxed to LAZY per-submodule `__getattr__` (the rc71 signal_processing
# precedent) so spin/bell import numpy-absent while the not-yet-flipped qm
# modules still surface the actionable [scientific] hint. test_qm_spin.py +
# test_bell_chsh.py were rewritten numpy-FREE (no np oracle, no `.to_numpy()` —
# eigenvalues via `mat_hermitian_eigendecompose`, equality via direct `Mat`
# entry comparison) so the numpy-absent install runs its own tests. 15 -> 13.
# rc116 (#564): `qm/sm.py` (Standard Model — electroweak / Higgs / Yukawa / CKM)
# flips numpy-free. Every scalar op already routed through the Class-N `rational`
# cascade (Higgs VEV / W,Z masses / Weinberg residual / Yukawa); the only numpy
# was the CKM 3×3 matrix + its unitarity check. `ckm_matrix` now returns an
# exact-cascade `Mat` (cos/sin via `rational`, CP phase via `rational.cexp`),
# and `ckm_unitarity_residual` does `V·Vᴴ` via the native `mat_matmul` + the
# Class-N `mat_norm` of the entrywise `− I` (no numpy). `sm` is a leaf (no
# consumers — no producer-flip boundary needed). test_qm_sm.py rewritten
# numpy-FREE (no np oracle: unitarity via `mat_matmul` + direct `Mat`-entry
# comparison). The roadmap-paired `single_particle` is SPLIT to its own later
# rc (design-heavy: matrix-exponential `V·diag(e^{−iEₜ})·V†` via the complex
# diagonal from `rational` trig — "don't rush, split on wobble"). 13 -> 12.
#
# rc117 (#564): `qm/single_particle.py` (TDSE/TISE/Heisenberg/commutator/density-
# matrix/Liouville-vN) flips numpy-free — the design-heavy one split out of rc116.
# Working matrices are held in `Mat`; every linear-algebra step routes through the
# Class-L `mat_*` family (`mat_matmul` for matmul / matvec-via-column / outer-via-
# column·row, `mat_hermitian_eigendecompose` for the eigenbasis), and the per-mode
# time-evolution phase `e^{-iλt}` is the Class-N Euler cascade `rational.cexp`
# (NOT `np.exp`). State vectors are plain `complex` lists (`Mat` is 2-D only).
# The only srmech-side consumer is `tool_schema` registration metadata (strings,
# no call — no boundary coercion). Three test files rewritten numpy-FREE:
# test_qm_single_particle.py (physical-identity assertions — norm / energy / trace
# / hermiticity / unitarity preservation, deterministic PRNG, `rational` oracle);
# the two single_particle tests in test_qm_cascade_routing_rc33.py; and the
# cross-module test_qm_potentials.py harmonic-oscillator TDSE test (potentials'
# numpy H bridged to `Mat` at the flipped-op boundary, assertion numpy-free).
# 12 -> 11.
#
# rc118 (#564): `qm/relativistic.py` (Dirac γ-matrix algebra / Klein-Gordon / Weyl
# / charge-conjugation) flips numpy-free. The γ-matrices are assembled from the
# numpy-free Pauli 2×2 `Mat` blocks (a `_block4` numpy-free `np.block` replacement
# — no `.to_numpy()` boundary coercion needed now), products route through the
# native `mat_matmul`, residual norms through `mat_norm`, and the Klein-Gordon
# dispersion through the Class-N `rational.sqrt`; 4-momenta are plain float
# sequences. PRODUCER-FLIP: `propagators` (still a numpy carrier) consumes
# `dirac_operator_momentum_space` + `minkowski_metric`, so those 3 callsites coerce
# `.to_numpy()` at the boundary (the legit bridge inside a still-numpy carrier).
# test_qm_relativistic.py rewritten numpy-FREE (Clifford-algebra / chirality /
# charge-conjugation identities via `mat_matmul`/`mat_solve`/`mat_norm`, no np
# oracle); the two relativistic-producer calls in test_qm_propagators.py bridge
# `.to_numpy()`. CI-GUARD: rc117 named `relativistic` as the pure-wheel must-raise
# example — moved it to `propagators` (still numpy) and added relativistic to the
# flipped-and-exercised list. 11 -> 10.
#
# rc119 (#564): `qm/gauge.py` (Yang-Mills SU(2)/SU(3) generators + Gell-Mann
# matrices + structure constants + Casimirs + Wilson loops) flips numpy-free. The
# SU(2) generators consume the numpy-free Pauli 2×2 `Mat` blocks directly (the
# rc115 `.to_numpy()` boundary coercion this module CARRIED is REMOVED — gauge was
# the last consumer of spin's Pauli producer), the eight Gell-Mann matrices are
# exact small-integer `Mat` (λ⁸ via the Class-N rational.sqrt 1/√3), every product
# routes through `mat_matmul`, residual norms through `mat_norm`, and the
# path-segment holonomy `exp(i g A^a T^a)` through `mat_hermitian_eigendecompose`
# (V·diag(e^{iλ})·Vᴴ, the e^{+iλ} phase the Class-N `rational.cexp` Euler cascade).
# The structure constants f^{abc} become plain nested Python lists (rank-3; `Mat`
# is 2-D only), so `lie_algebra_residual` reads `f[a][b][c]` and shape-checks by
# nested `len`. No srmech-side CALL consumer (sm/so8 only mention gauge in
# comments). test_qm_gauge.py rewritten numpy-FREE (Hermiticity/trace/unitarity by
# direct Mat-entry arithmetic, deterministic LCG for the multi-segment Wilson loop,
# an analytic diagonal-λ³ exp oracle — no np); the gauge cell in
# test_qm_cascade_routing_rc33.py is numpy-free too (independent analytic oracle +
# native mat_matmul unitarity). CI-GUARD: the must-raise example stays `propagators`
# (still a numpy carrier — gauge ≠ propagators); gauge ADDED to the pure-wheel
# flipped-and-exercised list (su2_generators[0] is Mat + casimir_eigenvalue ≈ 0.75).
# 10 -> 9.
#
# rc121 (#564): `qm/potentials.py` (hydrogen radial + harmonic oscillator) flips
# numpy-free, enabled by the rc120 native-bound raise (Hermitian-eig now native to
# n ≤ 2048, so the grid sizes potentials needs use the FAST native C Jacobi).
# `hydrogen_radial` builds its real-symmetric tridiagonal Hamiltonian as a nested
# list → complex `Mat` and eigensolves through `mat_hermitian_eigendecompose`; the
# radial grid `r` and the eigen-energies are plain Python lists, and the
# eigenvectors are returned as a REAL `Mat` (the value-preserving real part of the
# complex unitary — H is real-symmetric). The ladder operator `a[n-1,n] = √n` uses
# the Class-N libm-free `rational.sqrt` and is a complex `Mat` (a† = a.conj().T);
# the oscillator Hamiltonian H = ω(a†a + ½I) is assembled through `mat_matmul` +
# numpy-free Mat add/scale. potentials is a leaf consumer (no srmech-side CALL
# consumer — chess-spectral / ephemerides-spectral are downstream packages).
# test_qm_potentials.py rewritten numpy-FREE (commutator/spectrum via mat_matmul /
# mat_hermitian_eigendecompose, hydrogen orthonormality via mat_matmul, the TDSE
# cross-check now passes the `Mat` Hamiltonian DIRECTLY to single_particle.tdse_evolve
# — no numpy→Mat bridge; the test grids reduced to n_grid=250/r_max=45 for a fast
# native eig still inside the unchanged accuracy bands). The potentials cell in
# test_qm_cascade_routing_rc33.py is numpy-free too (real-Mat Vᵀ V = I via the
# native mat_matmul + direct `energies` list indexing); numpy stays in that file
# only for the still-unflipped GENERIC hermitian_eigen routing cells (so8 / eigvalsh
# differential oracle). CI-GUARD: the must-raise example stays `propagators` (still a
# numpy carrier — potentials ≠ propagators); potentials ADDED to the pure-wheel
# flipped-and-exercised list (hydrogen_radial returns (list, list, real Mat)).
# 9 -> 8.
# rc122 (#564): qm/octonion.py flipped numpy-free (the int8 table is a nested
# tuple; L/R-mult return Mat) WITHOUT decrementing the ceiling — the count was
# already 7 when this rc opened (octonion dropped out, ceiling stale at 8).
# rc123/124/125 (#564): the octonion CONNECTED COMPONENT flips together —
# qm/so8.py + qm/triality.py (the two remaining column-0 carriers of the
# cluster) go numpy-free in one change (the EXACT-RREF / float Gram-Schmidt rank
# + mat_svd nullspace DUAL fix in so8; mat_solve/mat_matmul companions in
# triality), while amsc/hdc.py (a LAZY-proxy, not a column-0 carrier — the proxy
# is killed) and amsc/cascade/hypercomplex_dft.py (function-local numpy) also go
# fully numpy-free. Removing so8 + triality from the column-0 list takes the
# count 7 -> 5. The remaining 5 carriers are EXACTLY: mcp/_coercion.py,
# qm/propagators.py, qm/pseudo_hermitian.py,
# signal_processing/closed_form_ops/ica_jade.py, spectral/__init__.py. 8 -> 5.
# rc123 (#564): qm/propagators.py (Feynman scalar/fermion/photon/massive-vector
# propagators) flips numpy-free. A LEAF (only tool_schema metadata strings +
# qm/__init__ re-export consume it). The scalar propagator i/(k²−m²+iε) is a
# plain complex; the 4×4 numerators are held in `Mat` (consumed straight from
# the numpy-free relativistic producers minkowski_metric / dirac_operator_
# momentum_space — the rc118 `.to_numpy()` bridges DELETED); the kᵘkᵛ outer
# product rides the column·row Class-L mat_matmul cascade (dropping the numpy-
# carrier dense_matvec_real / dense_outer_real). test_qm_propagators.py rewritten
# numpy-FREE (pole structure / the (p̸+m)(p̸−m)=(k²−m²)I Clifford identity /
# photon transversality via Mat-entry + mat_matmul + complex arithmetic; the two
# relativistic-producer calls consume `Mat` directly). CI-GUARD: the pure-wheel
# must-raise example moved propagators -> pseudo_hermitian (still a numpy
# carrier); propagators ADDED to the flipped-and-exercised list. The remaining 4
# carriers are EXACTLY: mcp/_coercion.py, qm/pseudo_hermitian.py,
# signal_processing/closed_form_ops/ica_jade.py, spectral/__init__.py. 5 -> 4.
# rc124 (#564): qm/pseudo_hermitian.py (η-pseudo-Hermitian / PT-symmetric
# framework) flips numpy-free — the LAST qm carrier, so `srmech.qm` is now fully
# numpy-free. Matrices ride the Mat carrier, vectors are plain complex lists; the
# η = (V V†)⁻¹ construction needs the general non-Hermitian eigenVECTORS, each
# computed as the null vector of `O − λI` (deterministic Gaussian elimination,
# squared-modulus pivots, no abs()) over the eigenvalues from `mat_eigvals`, with
# the HPD Gram inverse via `mat_solve` (well-conditioned, no singular-solve). It
# is a LEAF (only tool_schema metadata + qm/__init__ re-export consume it).
# test_qm_pseudo_hermitian.py rewritten numpy-FREE. CI-GUARD: the pure-wheel
# must-raise [scientific]-hint example moved pseudo_hermitian -> ica_jade
# (`from srmech.signal_processing.closed_form_ops import ica_jade`, which still
# emits the hint via the closed_form_ops lazy package gate — a real remaining
# carrier); pseudo_hermitian ADDED to the flipped-and-exercised list. The
# remaining 3 carriers are EXACTLY: mcp/_coercion.py,
# signal_processing/closed_form_ops/ica_jade.py, spectral/__init__.py. 4 -> 3.
# rc125 (#564): spectral/__init__.py (Spike #115 runtime spectral decompose /
# delta / recompose / similarity / predict / prediction_error / truncate_sparse)
# flips numpy-free. A LEAF for its public ops — the only srmech-side importer is
# mcp/_coercion.py which imports the SpectralHandle TYPE (not a function); nothing
# in srmech calls the ops. The math routes onto the Mat carrier:
# hermitian_eigendecompose(L) -> mat_hermitian_eigendecompose(Mat) (the prior
# dense_matvec_complex / hermitian_eigendecompose are numpy CARRIERS that raise
# numpy-absent), projection Vᴴ·state / V·coeffs as explicit numpy-free matvecs.
# The complex128 coefficient bytes (np.frombuffer / .tobytes) -> struct
# pack/unpack of interleaved native-endian (re,im) float64 pairs (BYTE-IDENTICAL
# to the old layout, so descriptor / content hashes are stable); np.argsort ->
# `sorted(reverse=True)` (stable, same tie order); the per-mode predict phase
# e^{-iλt} -> rational.cexp; truncate magnitudes -> squared-modulus (no abs/sqrt).
# recompose now returns List[complex] (was np.ndarray); the MCP path serialises
# via the JSON wire so the return-type change is transparent. test_spectral.py +
# test_spectral_rcn_plus_2.py rewritten numpy-FREE (struct unpack, max(abs()),
# random.Random fixtures). ica_jade STAYS the pure-wheel must-raise example
# (spectral != ica_jade) -> NO CI-guard move. 3 -> 2.
# rc126: ica_jade flipped numpy-FREE — the LAST signal_processing carrier, so
# the whole subpackage now imports + runs numpy-absent. JADE whitening routes
# the covariance eig through mat_hermitian_eigendecompose (NOT the carrier
# hermitian_eigendecompose / dense_matmul_real / elementwise_sqrt); the 4-D
# cumulant tensor + Givens rotations are explicit numpy-free loops; op returns
# (S, W) as Mats. 2 -> 1.
# rc127 CAPSTONE (#564): numpy is GONE. mcp/_coercion (the last top-level carrier)
# is flipped numpy-free (nested-list wire form + a Mat branch in serialise_native);
# the export boundary to_numpy() methods are DELETED; _scientific.py is deleted;
# the [scientific] extra is removed. The WHOLE package — including the qm.* /
# signal_processing.* scientific tier — imports + RUNS with numpy not installed.
# This ceiling is now ZERO and is the permanent "no numpy carrier anywhere in
# srmech/" guard. 1 -> 0.
CEIL_NUMPY_CARRIER = 0


def _srmech_root() -> pathlib.Path:
    return pathlib.Path(srmech.__file__).parent


def _hard_numpy_import_files():
    """Files under srmech/ with a module-level (column-0) ``import numpy``."""
    hits = []
    for p in sorted(_srmech_root().rglob("*.py")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if _is_numpy_import(line):
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
        assert not _is_numpy_import(line), (
            "srmech.amsc.mat must stay numpy-free at import (lazy bridge only)"
        )
