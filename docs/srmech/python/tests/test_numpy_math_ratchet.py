"""numpy-math ratchet — the down-only guard that keeps numpy a *carrier*, not a
*math engine* (#928; user direction 2026-06-08).

The discipline: **all math runs through srmech cascades; numpy is only ever for
vector packing** (array creation / dtype / shape / slicing / the ctypes bridge).
numpy bundles a full math engine alongside its carrier — ``np.linalg.*``,
``np.fft.*``, the ``@`` matmul, the transcendental ufuncs. Every one of those is
libm-at-the-array-level and has (or will have) a srmech cascade equivalent that
rides the libm-free C core. A stray ``np.linalg.solve`` is therefore a *defect*,
not a convenience — the same class of defect the C-transpile arc drove out of
``libsrmech`` (libm 23 → 0).

This test is the down-only debt ledger for that goal — a sibling of the libm
C-transpile ratchet and the Rosetta-completeness ratchet. It greps the srmech
**source** (carriers + math, but NOT the tests) for numpy-math callsites in three
categories and pins each at a ceiling that only ever moves **down**:

  * ``linalg_fft`` — ``np.linalg.*`` / ``np.fft.*`` (solve / svd / qr / eig /
    lstsq / inv / fft / …): the heavy-engine surface.
  * ``matmul``     — the ``@`` / ``@=`` operator, ``.dot(``, and
    ``np.{matmul,einsum,kron,convolve,correlate,outer,tensordot,vdot,inner,
    cross}``: the contraction surface.
  * ``ufunc``      — ``np.{sin,cos,tan,exp,log,sqrt,sign,abs,arctan,power,…}``:
    the transcendental / sign surface (the Python-tier residue of the C-transpile
    arc — ``libsrmech`` is already libm-free, the scientific tier is not yet).

To close debt: route a callsite through the srmech cascade that already backs it
(``laplacian.dense_solve`` / ``dense_matvec_complex``, the ``cascade.fft`` /
``dft`` family, ``rational.{sin,cos,exp,sqrt}`` / the trig cascade, …), then
**lower the matching ceiling to the new exact count**. The ceilings are TIGHT
(``== ceiling``, not ``<=``) for the same reason the Rosetta ratchet is: a count
*below* the ceiling means a callsite was removed without updating the ledger;
a count *above* means numpy math was added where a cascade belongs — which is
exactly the regression this guard exists to forbid.

Carrier ops (``np.zeros`` / ``np.asarray`` / ``np.ascontiguousarray`` /
``reshape`` / ``.T`` / elementwise ``+ - *`` on arrays / indexing) are NOT
counted — those are legitimate vector packing.

Reductions (``np.sum`` / ``np.mean`` / ``np.prod`` / ``np.cumsum`` …) sit on the
carrier⇄math boundary and are a DEFERRED category — not yet pinned here; revisit
when the three engine surfaces above approach zero.

The regex is run over the source TEXT (not via ``tokenize``), so the counts are
identical across CPython 3.10–3.14 — ``tokenize``'s f-string handling changed in
3.12 and would make the ledger version-dependent.
"""
from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# The srmech source tree (carriers + math). Tests live in a sibling dir and are
# intentionally NOT scanned.
# ---------------------------------------------------------------------------
SRMECH_PKG = Path(__file__).resolve().parent.parent / "srmech"

_LINALG_FFT = re.compile(r"\b(?:np|numpy)\.(?:linalg|fft)\.")
_MATMUL_PATTERNS = (
    re.compile(r" @[ =]"),  # binary ``a @ b`` / ``a @= b`` (decorators are ``@name`` — no space)
    re.compile(
        r"\b(?:np|numpy)\.(?:matmul|einsum|kron|convolve|correlate|outer"
        r"|tensordot|vdot|inner|cross)\b"
    ),
    re.compile(r"\.dot\("),  # ``np.dot(`` and ``x.dot(``
)
_UFUNC = re.compile(
    r"\b(?:np|numpy)\.(?:sin|cos|tan|exp|expm1|log|log1p|log2|log10|sqrt|cbrt"
    r"|sign|abs|absolute|arcsin|arccos|arctan|arctan2|power|float_power|hypot"
    r"|square|reciprocal)\("
)

# ---------------------------------------------------------------------------
# DOWN-ONLY ceilings. Lower (never raise) the matching one when a callsite is
# routed through a srmech cascade. Baseline pinned at v0.7.5rc13 after the lmmse
# solve+matvec migration (decrement #1: -1 linalg, -1 matmul); rc16 routed the 5
# dense complex 2-D matmuls in matrix_cascades.py (qr/svd/lstsq/eigvals internals)
# through dense_matmul_complex (matmul 185 -> 180); rc17 routed qm.single_particle's
# 12 contractions (commutator + TDSE/Heisenberg/Liouville U·…·Uᴴ) onto the
# dense_matmul/matvec cascades (matmul 180 -> 168); rc18 routed qm.spin (15 Pauli
# products) + qm.gauge (6 — Lie-algebra commutator/Casimir/Wilson) through
# dense_matmul_complex (matmul 168 -> 147); rc19 routed qm.relativistic's 9
# gamma-matrix products + qm.pseudo_hermitian's 3 (Oᴴη/ηO + V·Vᴴ) onto the
# matmul cascade (matmul 147 -> 135); rc20 added the dense_dot_complex bilinear
# helper (Σ aᵢbᵢ via elementwise-multiply + reduction) and routed the complex
# matvec/dot/sandwich sites onto the matvec + dot cascades — qm.pseudo_hermitian's
# 3 η-sandwiches (⟨a|η|b⟩, ⟨ψ|ηO|ψ⟩, ⟨ψ|η|ψ⟩ = 7 `@` tokens), heat_kernel's 2
# eigenbasis matvecs, spectral's 2 decompose/recompose matvecs, and music's
# Enᴴ·A noise-subspace matmul (matmul 135 -> 123). The remaining real-typed
# (so8 / triality / octonion-DFT / Minkowski / DSP) sites await a real-matmul +
# real-matvec cascade; the matrix_cascades QR-internal vdot/back-solves await a
# shape-polymorphic pass; rc21 introduced the real-matmul cascade trio
# (dense_matmul_real / dense_matvec_real / dense_dot_real = the complex kernel on
# imag-free input, .real → float64) and routed hypercomplex_dft's 8 octonion-rep
# (8×8 real) matvecs onto dense_matvec_real (matmul 123 -> 115). The remaining
# real so8/triality/DSP/Minkowski sites land in subsequent batches; rc22 routed
# qm.triality's 7 real products (octonion-rep matvecs + the 28×28 tau=S_B·S_C /
# tau² / tau³ matmuls) onto dense_matmul_real/dense_matvec_real and reworded the
# 3 docstring `@` to `·` (matmul 115 -> 105); rc23 routed qm.so8's 17 sites —
# 15 real (commutators, su(3)/g₂ Gram products, basis-projection matvecs,
# Gram-Schmidt dot) onto dense_matmul_real/matvec_real/dot_real, and 2 COMPLEX
# (the su(3)-weight Rayleigh quotients vᴴv / vᴴ·ad·v on the complex eigenvectors
# of the real ad(H)) onto dense_dot_complex/dense_matvec_complex (matmul
# 105 -> 86). The 2 np.kron stay (different op). Minkowski / DSP real sites next.
# rc24 routed the real "Minkowski + real-dot" sweep — qm.relativistic's eta@k
# matvec + np.dot(k_spatial,k_spatial) + the kᵀηk bilinear, qm.propagators' eta@k
# matvec, and the amsc real Class-L inner products (harmonics _spectral_scores'
# 3 ⟨x,·⟩ symmetry probes + hdc loop_inv / loop_inv_hd / g2_three_form ⟨·,·⟩
# norms) onto dense_matvec_real / dense_dot_real (matmul 86 -> 75). The amsc
# helpers import dense_dot_real function-locally to keep harmonics/hdc
# numpy-absent-safe (§22). Remaining real sites: the DSP closed_form_ops +
# matrix_cascades QR-internal vdot/back-solves; then np.outer/kron/einsum
# (distinct ops, own cascades).
# rc25 routed the real DSP closed_form_ops cluster — dct (M·arr / arr·Mᵀ DCT
# matrix products), map_ml (the AᵀR⁻¹A normal-equation matmuls + matvecs; the
# np.linalg.inv/solve stay), ica_jade (the Xᵀ·X covariance + whitening/Givens
# rotation matmuls; the 2 np.einsum + np.linalg.eigh stay) — onto
# dense_matmul_real / dense_matvec_real, plus fsk's complex tones·conj(window)
# correlator-bank matvec onto dense_matvec_complex (matmul 75 -> 60). These DSP
# modules import numpy at module top, so the helper import is top-level here
# (unlike the lazy-numpy amsc modules). Remaining: sinc_interp / vector_quant /
# farrow / esprit (dtype-verify each), the matrix_cascades QR-internals, then
# np.outer / kron / einsum / convolve / correlate (distinct ops, own cascades).
# rc26 routed the genuine-code tail of the dense-matmul migration — vector_quant's
# real vec·cbᵀ codebook product, sinc_interp's COMPLEX K·y (y is complex128 IQ →
# dense_matvec_complex, NOT real), farrow's real Lagrange C[k]·x fractional-delay
# dot, and qm.potentials' a†·a number-operator + qm.sm's V·Vᴴ CKM-unitarity (both
# complex) (matmul 60 -> 55). The remaining ~55 are NOT genuine dense-matmul code:
# ~16 are docstring/comment/summary-string `@` mentions (spectral / mimo_svd /
# heat_kernel / tool_schema / lmmse / esprit / profile_loader — a cosmetic `·`
# reword sweep), and ~25 are distinct ops needing their OWN cascades (np.convolve
# in fir/polyphase/multirate, np.correlate in matched_filter, np.kron in so8,
# np.outer in propagators, np.einsum in ica_jade). The dense-matmul-migration
# floor is essentially reached; further matmul reduction is reword-sweep +
# distinct-op cascades (separate work items). The laplacian Schur `L_pi·X` is
# deferred (in-helper, shape-polymorphic — its own careful pass).
# rc27 OPENS the linalg_fft decrement (pinned at 126 since rc13): the dense-matmul
# floor reached, the arc pivots to np.linalg/np.fft → cascade. Per user direction
# (cascade + TOML for ALL maths; numpy is a carrier only, with the carrier itself
# removed as the FINAL step AFTER the maths sweep), the cascades REPLACE numpy math
# even where not bit-exact — fft (radix-2) / svd (Gram-route) / qr (Householder) /
# eig (Jacobi) are round-off-faithful to numpy (~1e-14), not bit-identical, and
# that within-tolerance shift is accepted; any bit-equality-vs-numpy test relaxes
# to a tolerance. rc27 routes the linear-solve family: map_ml's 2 np.linalg.solve →
# dense_solve (bit-exact for the 1-D RHS both sites have) + triality/esprit's
# np.linalg.lstsq → matrix_cascades.lstsq (round-off-faithful, complex-safe; the
# bare-ndarray return replaces numpy's 4-tuple, so the callsite unpack changed)
# (linalg_fft 126 -> 122). NOT migrated: the cascade ops' OWN internal numpy
# kernels (laplacian eigh/solve — designated Class-L impls with pure-Python
# fallbacks; a deeper separate pass) and the docstring/ToolEntry-summary
# `numpy.linalg.*` cross-reference MENTIONS (precise docs — left intact, not gamed).
# Next: np.fft (n/axis handling) + np.linalg.svd/qr/eigvals + inv/pinv.
#
# rc28 EXACTIFIES the dft/fft cascade (no ratchet movement — counts unchanged).
# Per the sharpened user direction ("don't use floats for bit-exact math, that's
# what ints and complex are for; floats are for FPU lift"), the dft/fft cascade
# now routes an all-integer / Gaussian-integer power-of-two signal through an
# exact cyclotomic-integer engine (ℤ[ζ_N], ζ^{N/2}=-1 Class-K sign-flip → pure
# integer add/subtract) with ONE FPU lift at the end — exact-until-rotation, MORE
# faithful than a float FFT (which rounds every butterfly). This is the FIRST
# exact cascade and a correction to rc27's "round-off-faithful is fine" framing
# for the integer case. It adds NO numpy, NO public surface (private engine
# srmech.amsc.cascade.exact_dft), so all three ceilings (linalg_fft/matmul/ufunc)
# AND the rosetta python_only_irreducible debt bucket are untouched. Exposing the
# exact ℤ[ζ_N] spectrum as a public op belongs with its C twin (a follow-up).
#
# rc34 resumes the matmul decrement by ROUTING distinct-op callsites onto the
# already-shipped kron / einsum cascades (no new public op — pure routing):
# qm.so8's `np.kron(ad.T,I) - np.kron(I,ad)` superoperator (×2) and qm.bell's
# `_kron` (×1) → `spectral_cascades.kron` (`np.asarray` is carrier-only); and
# qm.triality's octonion-couple `np.einsum("i,j,ijk->k")` (×1) →
# `matrix_cascades.einsum`. All four are value-faithful (so8/triality bit-exact
# err 0.0; bell bit-exact on its Pauli/measurement operators) (matmul 55 -> 51).
# DEFERRED: ica_jade's 2 einsum sit in the hot Jacobi sweep loop (a perf-careful
# pass), the np.outer family awaits a dense_outer cascade (a new public op), and
# the matrix_cascades QR-internal vdot/outer/@ await the shape-polymorphic pass.
#
# rc51 ships the dense_outer cascade (the deferred new public op): laplacian
# gains `dense_outer_complex` / `dense_outer_real` (an outer product IS the k=1
# case of dense_matmul_complex, so it rides the native kernel bit-identically),
# and routes the 3 genuine np.outer sites — qm.propagators' two real k^μk^ν
# momentum tensors (→ dense_outer_real) and qm.single_particle's complex |ψ⟩⟨ψ|
# density matrix (→ dense_outer_complex) (matmul 51 -> 48). The 2 remaining
# np.outer are the matrix_cascades QR-internal Householder updates, still on the
# shape-polymorphic pass with the QR-internal vdot/@.
# rc52 OPENS the ufunc decrement: the new `laplacian.elementwise_hypot`
# (per-element rational.hypot — the Class-N |z| cascade, native
# srmech_rational_sqrt-dispatched, numpy carries the array only) routes the
# 5 DSP `np.hypot(z.real, z.imag)` magnitude sites (fsk/mlse/psk_qam/ofdm/
# spectral) off numpy's ufunc engine (ufunc 48 -> 43). Round-off-faithful
# (rational sqrt floor-projected vs IEEE round-to-nearest; the magnitude
# shift never flips a nearest-symbol / argmax decision). Next ufunc batches:
# the np.exp complex-phase sites onto elementwise_transcendental, then
# np.sqrt / np.sin / np.cos / np.log / np.sign.
# rc53 continues the ufunc decrement: routes the 14 genuine `np.exp` callsites
# onto cascades — the array e^{iθ} phases (qm.gauge time-evolution diag,
# qm.single_particle TDSE/Heisenberg/Liouville per-mode phases, fsk tone bank,
# psk_qam constellation, spectral_subtraction phase re-attach, spectral phase
# extrapolate, laplacian magnetic directed-phase) onto `elementwise_transcendental
# (·, 'exp_i')` (its real cos/sin run the native libm-free C cascade), the real
# array exps (heat_kernel decay, rbs_lm softmax) onto `(·, 'exp')`, and the 2
# scalar CKM phases (qm.sm) onto `rational.cexp` (Euler). Plus 2 doc/summary
# `np.exp(` mentions de-parened (ratchet-visible). ufunc 43 -> 27. The 2
# remaining np.exp are elementwise_transcendental's OWN complex-input fallback +
# real no-native fallback (the documented internal kernel; deferred). Next: the
# np.sqrt cluster (12), then np.sin/np.cos/np.log/np.sign.
# rc54 continues the ufunc decrement: the new `laplacian.elementwise_sqrt`
# (per-element rational.sqrt — the Class-N√ cascade, native
# srmech_rational_sqrt-dispatched, numpy carries the array only) routes the 2
# array `np.sqrt` sites (spectral_subtraction PSD magnitude, ica_jade
# whitening eigenvalues), and the 10 SCALAR np.sqrt sites (gauge Gell-Mann
# 1/√3 ×3, potentials √n ladder, relativistic on-shell energy, so8 ×2,
# triality, psk_qam √M, wavelet 1/√2) route onto `rational.sqrt`. ufunc
# 27 -> 15. Round-off-faithful (rational sqrt floor-projected vs IEEE
# round-to-nearest, ≤1-ULP; bit-exact on perfect squares). Next: np.sin (3)
# + np.cos (3) onto elementwise_transcendental, np.log (5), np.sign (2); then
# the 2 internal exp fallbacks (the deferred cascade kernel).
# rc55 clears the EXTERNAL ufunc residue: the 2 scalar `np.log` (mlse
# uniform-prior A_log / pi_log) route onto `rational.log`, and the 1 array
# `np.sign` (hdc.polar_bundle's Pyodide fallback for srmech_polar_bundle)
# routes onto a Class-K comparison sign `(x>0)-(x<0)` (carrier comparisons,
# no np.sign ufunc; bit-identical to np.sign for the real int sum; no abs()).
# Plus 2 ratchet-visible comment mentions de-parened. ufunc 15 -> 10. The
# remaining 10 are ALL `elementwise_transcendental`'s OWN internal numpy
# fallback (2 exp + 3 sin + 3 cos + 2 log — the complex-input path + the
# no-native real path); driving those to zero is the deferred cascade-kernel
# work (needs complex-input trig/exp/log cascades), tracked separately.
# rc56 CLOSES the ufunc bucket to ZERO (rc52 hypot 48->43, rc53 exp ->27,
# rc54 sqrt ->15, rc55 log/sign ->10, rc56 ->0). The last 10 were
# `elementwise_transcendental`'s OWN internal numpy fallback (its complex-
# input path + its no-native real path). rc56 makes both numpy-free: the
# real fallback loops `rational.exp/cos/sin/log` (Class-N scalar cascades,
# bit-exact vs numpy over the tested range), the complex path runs
# `rational.complex_exp` (exp) / cosh-sinh-from-rational.exp (cos/sin) /
# `rational.log(hypot)+i*atan2` (log) per element. numpy is now PURELY a
# carrier across the entire transcendental + magnitude surface. Next numpy-
# math front: the `linalg_fft` ledger (122 — np.linalg.* / np.fft.*).
# rc57 — the matmul-ledger REWORD SWEEP (the ledger's documented next step:
# 'reword sweep + distinct-op cascades = separate work items'). The ufunc
# bucket is 0 (rc52-rc56); turning to matmul, ~30 of its 48 matches were
# TEXTUAL ` @ ` / np.{vdot,einsum,convolve,correlate,kron} mentions in
# docstrings / comments / ToolEntry summaries (+ one profile_loader f-string
# ` @ ` false positive), not compute. rc57 strips them all (write the NumPy
# op name / `·` without the dotted-paren form, per the rc34 convention) — ZERO
# behaviour change. matmul 48 -> 18. The remaining 18 ARE genuine deferred
# compute: matrix_cascades QR-internals (vdot/outer/@/back-solve, shape-
# polymorphic), ica_jade einsum hot loop, fir/multirate/polyphase np.convolve
# + matched_filter np.correlate (distinct-op cascades — own future work),
# laplacian Schur L_pi·X + the dense_matvec kernel-internal @. Next: the
# convolve/correlate cascades, then the QR shape-polymorphic pass, then linalg_fft.
# rc58 — the convolve/correlate cascade (the documented next step). The 6
# DSP callsites (fir / multirate / polyphase ×2 np.convolve + closed_form /
# path_b matched_filter np.correlate) route onto a new signal_processing-
# internal helper `_dsp_cascades.{convolve,correlate}`: direct linear
# convolution as Class-I shift ∘ Class-M scaled-accumulate (`full[i:i+nb] =
# full[i:i+nb] + a[i]*b`, numpy a carrier only — no convolve/matmul/ufunc),
# with full/same/valid edge modes; correlate = convolve(a, conj(v)[::-1])
# with NumPy's exact same-mode crop (floor for na>=nv, ceil for na<nv).
# Value-faithful to NumPy across 15 length-combos × 3 dtypes × 3 modes.
# NOT a public srmech.amsc op (it composes carrier arithmetic, no own C
# symbol → would only add python_only_irreducible debt; a future rc can
# promote it WITH a C twin). matmul 18 -> 12. The remaining 12 are the
# matrix_cascades QR-internals (8) + ica_jade einsum hot loop (2) + laplacian
# Schur/dense_matvec (2). Next: the QR shape-polymorphic pass, then linalg_fft.
# rc59 — the QR shape-polymorphic pass (the documented next step). The 8
# matrix_cascades QR-internal sites route onto the EXISTING value-faithful
# dense_* kernels (no new kernel): the 2 `np.vdot(v,v)` (the _norm2 / vhv
# Hermitian self-bind) -> `dense_dot_complex(conj(v), v)` (plain bilinear, so
# conj passed explicitly); the 2 `np.outer` (the Householder reflector v vᴴ) ->
# `dense_outer_complex`; the `conj(v) @ R` / `Q @ v` reflector matvecs ->
# `dense_matvec_complex`; and the lstsq back-solve `Qᴴ·b` + `R[i,i+1:]·x[i+1:]`
# -> dense_matvec/matmul (branch on rhs ndim) / dense_dot (1-D) / dense_matvec
# (k-col) — the shape-polymorphic case. The kernels are value-faithful, so the
# QR/SVD/lstsq/eig INVARIANTS (reconstruction, orthonormal Q, upper-tri R,
# singular values, eigenvalue multiset) are preserved — verified vs numpy
# across real+complex, 1-D + multi-column rhs. matmul 12 -> 4. The final 4 are
# genuinely deferred: ica_jade np.einsum (the hot JADE cumulant loop) + the
# laplacian Schur `L_pi·X` + the `dense_matvec_complex` kernel-INTERNAL `@`
# fallback (a kernel can't route onto itself). Next numpy-math front: the
# `linalg_fft` ledger (122 — np.linalg.* / np.fft.*).
# ---------------------------------------------------------------------------
# rc61: the np.fft.* family, first batch. The 15 one-dimensional
# `np.fft.fft(x)` / `np.fft.ifft(x)` callsites in signal_processing
# (cross_spectral ×4, ofdm ×2, spectral_subtraction ×2, multitaper ×1,
# stft ×2, wiener ×2, path_b/wiener ×2) route onto the value-faithful
# `srmech.amsc.cascade.spectral_cascades.fft` / `.ifft` cascade (radix-2
# Cooley-Tukey + dft fallback for non-power-of-2 N; exact-until-rotation,
# verified == numpy across real+complex N=2..100), wrapped `np.asarray(...)`
# so the result stays an ndarray carrier. The DSP-op INVARIANTS (coherence,
# Wiener gain, OFDM round-trip, STFT frames, multitaper PSD) are preserved —
# 447 signal_processing tests pass post-route. linalg_fft 102 -> 87. The
# remaining np.fft. sites are the n=/axis= Path-A reference ops
# (fft.py/ifft.py/rfft.py + fftfreq), which need an array-aware (n-pad +
# axis) wrapper over the 1-D cascade — deferred to the next batch. The
# np.linalg.{svd,qr,eig,solve,inv,...} decomposition cluster (~36 genuine
# sites, mostly qm/so8.py) is the front after that.
# rc62: DRAIN the np.fft.* family. New signal_processing/_fft_carrier.py lifts
# the 1-D spectral_cascades fft/ifft to NumPy's ndarray + n= (zero-pad /
# truncate) + axis= contract (NumPy a carrier only: moveaxis / reshape / pad /
# slice), plus a real-input rfft (full-transform-then-slice, with a complex-
# input TypeError raise mirroring NumPy) and an fftfreq carrier (integer bin
# indices / (n*d); no transcendentals). All 8 remaining genuine np.fft.* calls
# route onto it — the 6 Path-A/Path-B fft/ifft/rfft ops (closed_form_ops +
# path_b_ops) + the 2 cross_spectral fftfreq sites — and the ~18 textual
# `numpy.fft.X` doc/summary mentions are reworded to "NumPy fft". The carriers
# are bit-faithful to NumPy across real+complex, 1-D + n-D, every axis, and n
# pad/truncate (~1e-9). rfft is value-faithful (~1 ULP) NOT bit-identical to
# NumPy's pocketfft real-FFT (even np.fft.fft(real)[:n//2+1] != np.fft.rfft
# bit-for-bit) — matching pocketfft's exact rounding was a NumPy-backend
# artifact, not a substrate property, so the rfft-vs-NumPy tests are now
# allclose (the Path-A-vs-Path-B cascade identity stays exact). np.fft. -> 0.
# linalg_fft 87 -> 61. Next: the np.linalg.{svd,qr,eig,solve,inv,...} cluster.
# rc63a (first np.linalg.* sub-rc): route the genuine sign/order-invariant
# decompositions onto the already-shipped value-faithful matrix_cascades
# cascades. The 5 `q, _ = np.linalg.qr(X)` callsites (qm/so8.py) consume Q only
# through `q @ q.T` projectors / its column span / a sum-of-squares leak test —
# all invariant to QR's per-column sign — so `matrix_cascades.qr` (faithful up
# to column sign) is exact for the usage (verified: q@q.T == numpy to ~1e-9).
# The 2 `np.linalg.eigvals(X)` callsites (pseudo_hermitian `max|imag|`, esprit
# rotation set) consume the eigenvalue MULTISET (order-free) -> `.eigvals`
# (set-faithful ~1e-12). 83 so8/esprit/pseudo_hermitian/triality op-tests pass
# post-route. Plus the ~22 textual `numpy.linalg.X` faithfulness/summary
# mentions in matrix_cascades / tool_schema / triality (no genuine calls there)
# reworded to "NumPy X". np.linalg. 61 -> 32. The genuine svd / matrix_rank /
# inv / eig / eigh / solve / lstsq / pinv (sign/order-delicate, mostly qm/so8.py
# + amsc/laplacian.py) are the rc63b/c sub-batches.
# rc63b (v0.7.5rc64): the 2 real `np.linalg.inv` covariance-inverse sites in
# signal_processing/closed_form_ops/map_ml.py route onto the already-exported
# `laplacian.dense_solve(M, np.eye(n))` (a unique, well-conditioned solve — the
# inverse IS A·X=I; verified == numpy ~1e-9). The so8 `np.linalg.matrix_rank`
# sites were investigated and KEPT ON NUMPY: the cascade SVD is value-faithful
# for large singular values but its nullspace (small-singular-value) accuracy is
# too low for an absolute-tol rank count on a RANK-DEFICIENT matrix (it over-
# counted so8 `rank_with_so4` 6 -> 9) — a legitimate numpy-as-ACCURACY site, not
# numpy-as-carrier (deferred with the dense_solve fallback + matmul-4 tail).
# linalg_fft 32 -> 30. rc63c/d: pinv (svd-reconstruct, sign-invariant), complex
# inv (needs a complex solve), eigh (hermitian_eigendecompose), eig/svd-direct.
CEIL_LINALG_FFT = 30
CEIL_MATMUL = 4
CEIL_UFUNC = 0


def _count_category() -> dict[str, int]:
    counts = {"linalg_fft": 0, "matmul": 0, "ufunc": 0}
    for path in sorted(SRMECH_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        counts["linalg_fft"] += len(_LINALG_FFT.findall(text))
        counts["matmul"] += sum(len(p.findall(text)) for p in _MATMUL_PATTERNS)
        counts["ufunc"] += len(_UFUNC.findall(text))
    return counts


def _per_file_breakdown() -> str:
    rows = []
    for path in sorted(SRMECH_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        lf = len(_LINALG_FFT.findall(text))
        mm = sum(len(p.findall(text)) for p in _MATMUL_PATTERNS)
        uf = len(_UFUNC.findall(text))
        if lf or mm or uf:
            rows.append((lf + mm + uf, lf, mm, uf, str(path.relative_to(SRMECH_PKG))))
    rows.sort(reverse=True)
    return "\n".join(
        f"    {lf:3d} linalg/fft  {mm:3d} matmul  {uf:3d} ufunc   {name}"
        for _tot, lf, mm, uf, name in rows
    )


def test_numpy_math_ledger_is_tight():
    """Each engine-category count equals its down-only ceiling.

    A count ABOVE ceiling → numpy math was added where a srmech cascade belongs
    (the regression this guard forbids). A count BELOW ceiling → a callsite was
    migrated but the ceiling wasn't lowered — lower it to the new exact count.
    """
    counts = _count_category()
    ceilings = {
        "linalg_fft": CEIL_LINALG_FFT,
        "matmul": CEIL_MATMUL,
        "ufunc": CEIL_UFUNC,
    }
    mismatches = {k: (counts[k], ceilings[k]) for k in ceilings if counts[k] != ceilings[k]}
    assert not mismatches, (
        "numpy-math ledger drift "
        + ", ".join(
            f"{k}: live={live} ceiling={ceil}" for k, (live, ceil) in mismatches.items()
        )
        + ".\n  ABOVE ceiling → route the new callsite through a srmech cascade "
        "(numpy is carriers-only, never the math engine).\n  BELOW ceiling → you "
        "migrated a callsite; lower the matching CEIL_* to the new exact count.\n"
        "  Current per-file breakdown:\n" + _per_file_breakdown()
    )


def test_numpy_math_total_is_down_only():
    """The grand total is at or below the pinned sum (a coarse safety net)."""
    counts = _count_category()
    total = sum(counts.values())
    ceil_total = CEIL_LINALG_FFT + CEIL_MATMUL + CEIL_UFUNC
    assert total <= ceil_total, (
        f"numpy-math total {total} exceeds pinned {ceil_total}; a cascade op "
        "regressed to numpy math. Per-file breakdown:\n" + _per_file_breakdown()
    )
