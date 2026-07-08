"""Rosetta-completeness ratchet (rc7; issue #928).

The C-mirror goal: every public **compute** op in ``srmech`` should dispatch to
a bit-exact C twin OR be a pure composition of such twins, so ``libsrmech`` runs
standalone — on a full OS *or* a thread-less microcontroller — with no host
Python. This test is the down-only debt ledger for that goal (cf. the C-transpile
libm ratchet that went 23 -> 0): the ``python_only_debt`` and
``c_exists_unbound`` counts only ever DECREASE.

How it works:
  1. Enumerate the live public-op surface (every public callable defined in
     ``srmech.amsc`` / ``srmech.qm`` / ``srmech.signal_processing``), keyed by
     its canonical ``defined_at`` = ``<module>.<qualname>`` (re-export-stable).
  2. Load the committed classification (``rosetta_classification.ndjson``) — one
     of six buckets per op (see ROSETTA_LEDGER.md §"The classification").
  3. Assert the live set and the classified set agree EXACTLY (a new op with no
     bucket fails here -> forces every addition to be classified; a removed op
     left in the file fails too -> keeps the ledger current).
  4. Assert the two DEBT buckets are at or below their pinned ceilings. To close
     debt: give an op its C twin (or wire the unbound one up), move its line to
     ``c_dispatched`` / ``composition_of_c``, and LOWER the matching ceiling.

The ceilings move DOWN only. Raising one is the one edit this test exists to
forbid — a rising ceiling means a Python-only kernel was added without a C twin,
which is exactly the standalone-C regression the ledger guards against.

Buckets (see ROSETTA_LEDGER.md):
  c_dispatched           — routes to a srmech_* C symbol (standalone-ready)
  composition_of_c       — pure composition of c_dispatched ops (standalone-ready)
  c_exists_unbound       — DEBT (cheap): a C twin exists, Python doesn't dispatch
  python_only_debt       — DEBT: irreducible kernel, no C twin yet (renamed from
                           python_only_irreducible at rc138 — the honest name for
                           a monotone-decreasing OWED-C-mirror debt bucket)
  bignum_reference       — intentional exact-rational arbitrary-precision oracle;
                           MUST carry an explicit oracle_justification (or a
                           c_companion c_dispatched path) so it cannot HIDE compute
                           from the ratchet the way the_one did before rc138 gave
                           it the srmech_the_one C peer + moved it to c_dispatched
  non_compute            — IO / registry / schema / introspection (no kernel)
"""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
from pathlib import Path

import pytest

# rc170 — the SHARED Rosetta transitive call-graph walk (see conftest.py). The
# non_compute ``composes_c`` sub-bucket reuses the SAME standalone-C reachability
# machinery the transitive-standalone ratchet uses. `from conftest import` is the
# project's proven shared-helper path — but pytest's prepend import-mode does not
# add a package dir (tests/ has an __init__.py) to sys.path on isolated
# collection, so guard the tests dir onto the path first (the test_immolation.py /
# test_riemann_theta_rc80.py precedent).
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)
from conftest import (  # noqa: E402
    ROSETTA_NOT_READY,
    rosetta_live_objects,
    rosetta_reached_ledger_ops,
)

# #564 (numpy out the door): the qm / signal_processing surfaces are numpy-free
# now, and this audit walks them with stdlib importlib / inspect / pkgutil only
# (a submodule that still fails to import is simply skipped by ``_iter_submodules``
# — it contributes no live ops). So the completeness ratchet runs numpy-ABSENT
# (no ``importorskip``; the test must PASS, not skip, with numpy uninstalled).

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# Roots of the public COMPUTE surface (mirrors notes/_rosetta_inventory.py).
_ROOTS = ("srmech.amsc", "srmech.qm", "srmech.signal_processing")

# ----- the down-only debt ceilings (rc7 baseline; issue #928) -----------
# LOWER these as ops gain C twins. NEVER raise them.
# rc67: symmetric_eigendecompose stopped being Python-only-irreducible — it now
# delegates to the c_dispatched hermitian_eigendecompose + phase-canon, so it
# moved to composition_of_c. python_only_debt 108 -> 107.
# rc6 (0.9.0, §60 / F864): klein4_random earns its standalone-C MT19937 twin
# srmech_klein4_random (byte-identical to random.Random(seed).randrange(4)) and
# dispatches to it -> c_dispatched. python_only_debt 107 -> 106.
# rc16 (0.9.0): hypercomplex_couple rewritten onto the exact-Q61 octonion couple
# `_couple_q61` (cd_basis_product + Q61 fxmul) which dispatches to the new
# standalone-C srmech_hypercomplex_couple_q61 -> c_dispatched. This also empties
# the transitive-standalone ratchet allowlist (the two sed_*_working edges).
# python_only_debt 106 -> 105.
# rc110 (#1234 Item 1b / #863): cascade.quaternion_dft GRADUATED onto the rc109
# qm.quaternion foundation and dispatches the whole transform to the new
# standalone-C srmech_quaternion_dft (byte-exact composed fallback)
# -> c_dispatched. python_only_debt 105 -> 104.
# rc111 (#1234 Item 1c / #863): cascade.octonion_dft GRADUATED onto the
# qm.octonion foundation (the rc111 octonion_twiddle + the 8x8 loop operators)
# and dispatches the whole transform — ALL THREE forms, with the DECLARED
# bracketing as an explicit attested field — to the new standalone-C
# srmech_octonion_dft (byte-exact composed fallback)
# -> c_dispatched. python_only_debt 104 -> 103.
# rc139 (#743/#747 Foundation F1): the NUMERIC complex128 FFT foundation
# srmech_fft_c128 (radix-2 + Bluestein chirp-z for prime/arbitrary N; libm-free)
# lands, and the fft-family dispatches to it. spectral_cascades.dft + .fft route
# their float path to srmech_fft_c128 -> c_dispatched (×2); .idft/.ifft compose
# them, and the closed_form_ops + path_b_ops fft/ifft/rfft (×6) funnel through
# the spectral_cascades cascade -> composition_of_c (×8). (kron is NOT an FFT —
# it stays python_only_debt.) python_only_debt 103 -> 93.
# rc140 (Foundation F2): the numeric-LA foundations srmech_qr_f64 (direct
# Householder) + srmech_svd_f64 (one-sided-Jacobi, bounded-sweep convergence
# contract) land, and the subspace / MIMO / LA family dispatches its REAL path
# to them (complex stays on the already-C-backed Gram-eigen / list-Householder
# pure route). matrix_cascades.{qr,lstsq} route real input to srmech_qr_f64 ->
# c_dispatched (×2); matrix_cascades.{svd,eigvals} + closed_form_ops
# {esprit,map_ml,mimo_svd} compose the (now-C-backed) mat_svd / mat_eigvals /
# mat_hermitian_eigendecompose / mat_solve foundations -> composition_of_c (×5).
# (einsum is a tensor contraction, not LA; beamforming_fixed is delay-and-sum;
# ica_jade's dominant JADE Givens joint-diagonalisation is a pure-Python kernel
# with no C twin — all three honestly stay python_only_debt.)
# python_only_debt 93 -> 86.
# rc142 (BATCH B1 — hdc_klein4_exact, the FIRST compute batch): the 9 EXACT
# klein4/hdc ops earn same-rc C twins over the srmech_hdc / srmech_klein4
# foundation — hdc.bundle_with_ties -> srmech_hdc_bundle_with_ties;
# klein4_chirality_flip_gamma5 / _omega7 / cpt_mirror -> srmech_klein4_sector_flip;
# klein4_sector_count -> srmech_klein4_sector_count; klein4_holographic_encode /
# _decode -> srmech_klein4_holographic_{encode,decode}; klein4_triality_encode /
# _correct -> srmech_klein4_triality_{encode,correct} (both COMPOSING
# srmech_klein4_triality_cycle in C). All byte-identical (integer/sector, no
# float) -> c_dispatched. python_only_debt 86 -> 77.
# rc143 (BATCH B6a — sp_coder_dp part 1): the 5 EXACT signal-processing coder /
# quantizer ops earn same-rc C twins (4 symbols; the two sign_quantise paths
# share srmech_sign_quantise) — closed_form_ops.sign_quantise.op + path_b_ops.
# sign_quantise.op -> srmech_sign_quantise; vector_quantisation.op ->
# srmech_vector_quantise_encode; rle.op -> srmech_rle_encode; huffman.op ->
# srmech_huffman_build_codes. All integer/exact coders, byte-identical (no float
# tolerance, no libm, no abs) -> c_dispatched. python_only_debt 77 -> 72.
# rc144 (BATCH B6b — sp_coder_dp part 2): arithmetic_coding / lz77 / viterbi /
# mlse earn same-rc C twins -> c_dispatched (jpeg deferred as a float-DCT numeric
# op). python_only_debt 72 -> 68.
# rc145 (BATCH B8a — qm_exact_assembly part 1): the 6 EXACT relativistic/spin
# Dirac-gamma / Clifford ops move to composition_of_c. Each is a pure composition
# of the already-C-backed matrix algebra — the c_dispatched laplacian.mat_matmul
# + the rc141 C carrier ops srmech_mat_scale/add/sub that back the Mat *,+,-
# operators + the composition_of_c laplacian.mat_norm — over the
# already-composition_of_c gamma/Pauli constant builders. gamma_5 = i·γ⁰γ¹γ²γ³;
# weyl_left/right = (I∓γ₅)/2; charge_conjugation = i·γ²γ⁰; clifford_residuals /
# pauli_clifford_residuals = anticommutator/commutator residual norms (exact-zero
# when the algebra holds). Entries are Gaussian integers {0,±1,±i} so the native
# path is BYTE-IDENTICAL to forced-pure (verified). NO new C symbol: the base
# γ/Pauli constants are already composition_of_c (standalone-ready constant data),
# and re-emitting them in C would only have to reproduce the Python literals' -0.0
# slots (from -1j / -1.0·0) — a byte-identity hazard with no standalone gain — so
# the honest classification is composition_of_c (the fewest new C symbols: zero).
# python_only_debt 68 -> 62.
# rc146 (BATCH B8b — qm_exact_assembly part 2): the 9 so(8)/octonion/triality ops
# move to composition_of_c. Two honest sub-classes, BOTH standalone-C-reproducible
# with NO new C symbol (ABI stays 3):
#   • 6 BYTE-EXACT: so8_adjoint_basis / g2_subalgebra route their EXACT-INTEGER
#     derivation matmuls through the c_dispatched laplacian.mat_matmul
#     (srmech_dense_matmul_complex) — integer sums are order-independent in float64
#     so native == forced-pure BYTE-FOR-BYTE. triality_swap / triality_automorphism
#     / triality_companions / lean_isa_seventh_primitive compose mat_matmul +
#     mat_norm over the exact-DYADIC-ℚ companion maps; the companion maps' exact-ℚ
#     solve is standalone-reproducible via the c_dispatched srmech_qmat_rref
#     (VERIFIED byte-identical to the fast pure-Fraction sparse solve — the Python
#     keeps the sparse solve only for speed) — all byte-identical native==pure.
#   • 3 FLOAT-COMPOSITION: so7_subalgebra / an_embedding /
#     quaternion_subalgebra_stabilizer compose the C-backed mat_svd
#     (srmech_svd_f64) ∘ mat_hermitian_eigendecompose ∘ mat_matmul ∘ kron — the
#     SAME established composition_of_c pattern as the rc140 esprit / map_ml /
#     mimo_svd float-SVD ops (the "matmul ∘ eig ∘ kron" ledger example); native
#     agrees with forced-pure within the accepted ~1e-9 SVD/eig carrier shift
#     (per [[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]) and
#     every span / dimension / closure invariant is preserved exactly.
# python_only_debt 62 -> 53.
# rc147 (BATCH B8c — qm_exact_assembly part 3, CLOSES B8): the 9 gauge/bell/sm/misc
# ops move to composition_of_c with NO new C symbol (ABI stays 3). Every op is a
# pure composition of the already-C-backed matrix algebra — the c_dispatched
# laplacian.mat_matmul (srmech_dense_matmul_complex) + mat_hermitian_eigendecompose
# + the rc141 C carrier ops srmech_mat_{add,sub,scale} (the Mat +,-,* operators) +
# the composition_of_c laplacian.mat_norm + the byte-exact Class-N rational.{sqrt,
# cos,sin,cexp} integer-cascade C ports. Two honest sub-classes (EMPIRICAL):
#   • 7 BYTE-IDENTICAL: chsh_pauli_combination / chsh_operator / casimir_operator /
#     lie_algebra_residual / harmonic_oscillator_hamiltonian /
#     single_particle.commutator / ckm_unitarity_residual. The C matmul accumulates
#     real/imag SEPARATELY over p=0..k-1 — bit-for-bit CPython's complex s+=a*b —
#     and rational.{sqrt,cos,sin} are byte-exact cascade ports, so native==pure is
#     BYTE-IDENTICAL even for the irrational-VALUED entries (σ_z⊗σ_z's 1/√2, λ⁸'s
#     1/√3, the ladder √n, the CKM cos/sin). (Honest: ckm's residual VALUE is a
#     small ~1e-16 float — unitarity to float precision, NOT exact-0 — but the
#     native-vs-pure PARITY is byte-identical; lie_algebra_residual is exact-0.0
#     when the algebra holds.) The two bell ops route their tensor-sum through the
#     Mat +,-,* carrier ops + a LOCAL private kron (index-addressing, like
#     so8.an_embedding's _kron) — NOT the public python_only_debt spectral_cascades
#     .kron.
#   • 2 FLOAT-COMPOSITION: gauge_path_segment / wilson_loop_from_segments build the
#     Wilson holonomy exp(iM) = V·diag(e^{iλ})·Vᴴ through the C-backed
#     mat_hermitian_eigendecompose ∘ rational.cexp ∘ mat_matmul — the SAME
#     composition_of_c float-eigenbasis pattern as the rc146 so7 / an_embedding.
#     The Jacobi basis is non-unique, so native agrees with forced-pure on the
#     unitarity invariant + (exp(iM) being basis-independent) the reconstructed
#     holonomy within the accepted ~1e-9 carrier shift, NOT element-wise.
# python_only_debt 53 -> 44. B8 (qm_exact_assembly, 24 ops over B8a/B8b/B8c) COMPLETE.
# rc148 (BATCH B4a — sp_transform part 1, the FFT-spectral family): the 5 NUMERIC
# DSP transform ops move to composition_of_c with NO new C symbol (ABI stays 3).
# Each COMPOSES the rc139 c_dispatched numeric FFT foundation srmech_fft_c128 (via
# spectral_cascades.fft/_sc.fft) and/or the c_dispatched laplacian.mat_matmul
# (srmech_dense_matmul_complex, via mat_matvec) plus the byte-exact Class-N
# rational.{cos,sin,sqrt} integer-cascade C ports for the window/taper bases:
#   • stft / spectrogram / cross_spectral / multitaper — each windowed/tapered
#     frame's transform funnels through _sc.fft -> srmech_fft_c128 (the SAME
#     composition_of_c pattern as the rc139 fft/ifft/rfft wrappers, one layer up
#     with a Hann/cosine window + |z|²/cross-product/bundle-average elementwise
#     glue — numpy-free list-comps, no abs()); spectrogram composes stft.
#   • dct — the cosine-basis matvec M·x now rides mat_matvec ∘ mat_matmul ->
#     srmech_dense_matmul_complex (the cosine basis is the C-backed rational.cos
#     cascade); the 2·/DCT-III-first-term scaling is trivial glue.
# NUMERIC (float DSP): the parity contract is WITHIN-TOL native==pure (reldiff
# ≤ 1e-9, differential — NOT byte-identical), the SAME classification as the F1
# FFT / F2 SVD numeric foundations. The FFT-then-window / matmul accumulations
# can FMA-fuse ~1 ULP on some platforms (macOS clang), so byte-identity is NOT
# claimed; cross-platform CI is the arbiter. python_only_debt 44 -> 39.
# rc149 (BATCH B4b — sp_transform part 2, the filter family): the 5 NUMERIC DSP
# filter ops move debt -> c_dispatched / composition_of_c. One genuinely-new C
# symbol lands — srmech_iir_lfilter_f64 (the direct-form-I recursive IIR
# difference equation; the feedback term reads the output still being produced,
# so it is inherently SEQUENTIAL and does NOT decompose into a matmul/FFT):
#   • iir / allpass -> c_dispatched: dispatch the recursion to
#     srmech_iir_lfilter_f64 (allpass builds the mirrored (b,a) pair first; a
#     biquad cascade dispatches per second-order section) -> c_dispatched (×2).
#   • fir / closed_form_ops.matched_filter / path_b_ops.matched_filter ->
#     composition_of_c: a (feed-forward-only) linear convolution / correlation
#     re-expressed as a Toeplitz matvec through the c_dispatched
#     srmech_dense_matmul_complex (via _dsp.convolve_matmul / correlate_matmul ->
#     mat_matvec ∘ mat_matmul) -> composition_of_c (×3).
# NUMERIC (float DSP): the parity contract is WITHIN-TOL native == pure (reldiff
# ≤ 1e-9, differential — NOT byte-identical), the SAME classification as the F1
# FFT / F2 SVD / B4a numeric batches. python_only_debt 39 -> 34.
# rc150 (BATCH B4c — sp_transform part 3, wiener / rate-conversion / polyphase):
# the 5 NUMERIC DSP ops move debt -> composition_of_c (×4) / non_compute (×1)
# with NO new C symbol (ABI stays 3). Each composes an EXISTING C foundation:
#   • closed_form_ops.wiener / path_b_ops.wiener -> composition_of_c: the forward
#     + inverse transform funnel through _sc.fft / _sc.ifft -> the c_dispatched
#     numeric FFT foundation srmech_fft_c128 (rc139); the |X|² power, the Class-L
#     eps-floor and the Class-N rational MMSE gain S_xx/(S_xx+S_nn) are numpy-free
#     elementwise glue (the SAME composition_of_c pattern as the B4a stft /
#     cross_spectral windowed-transform ops) (×2).
#   • multirate.op -> composition_of_c: up-sample (zero-insertion) -> low-pass
#     convolution -> decimate; the convolution rides a Toeplitz matvec through
#     the c_dispatched srmech_dense_matmul_complex (via _dsp.convolve_matmul),
#     the windowed-sinc taps are the byte-exact Class-N rational.sin/cos cascades.
#   • polyphase.op -> composition_of_c: each polyphase component's convolution
#     rides the same Toeplitz matvec (_dsp.convolve_matmul); the strided split /
#     accumulate / interleave are exact integer glue.
#   • polyphase.decompose -> non_compute: splitting a tap table into L phase
#     branches E_k[n]=h[k+n·L] is a pure integer REINDEX (taps[k::L] + zero-pad),
#     no float kernel to mirror in C — it honestly carries no owed-C debt.
# NUMERIC (float DSP): the parity contract is WITHIN-TOL native == pure (reldiff
# ≤ 1e-9, differential — NOT byte-identical), the SAME classification as the F1
# FFT / F2 SVD / B4a / B4b numeric batches. python_only_debt 34 -> 29.
# rc151 (BATCH B4d — sp_transform part 4, CLOSES B4: interpolators / wavelet /
# spectral-subtraction): the last 4 NUMERIC sp_transform ops move debt ->
# composition_of_c with NO new C symbol (ABI stays 3). Each composes an EXISTING
# C foundation:
#   • farrow.op -> composition_of_c: the poly-in-mu mixer collapses to one
#     length-4 effective FIR h_eff[j]=Σ_k mu^k·C[k][j], and the Farrow output is
#     the "valid" cross-correlation of the zero-padded signal with h_eff — a
#     Toeplitz matvec through the c_dispatched srmech_dense_matmul_complex (via
#     _dsp.correlate_matmul); mu=0 -> exact integer-delay passthrough.
#   • sinc_interp.op -> composition_of_c: the Whittaker-Shannon reconstruction is
#     the matvec out = S·y with the real band-limit kernel S[q][s]=sinc((t_q-t_s)/T)
#     routed through mat_matvec -> srmech_dense_matmul_complex; target==sample ->
#     S=I so out==y exactly.
#   • wavelet.op -> composition_of_c: each Haar analysis level is one banded matvec
#     [approx; detail]=H·current (low-pass +c,+c band over high-pass +c,-c band,
#     c=1/√2, decimation baked into the row stride) through the same C matmul; the
#     orthonormal transpose is the exact perfect-reconstruction inverse.
#   • spectral_subtraction.op -> composition_of_c: the forward + inverse transform
#     funnel through _sc.fft / _sc.ifft -> the c_dispatched numeric FFT foundation
#     srmech_fft_c128 (rc139); the observed bin magnitude |X|²=re²+im² is the
#     genuine Class-K pin-slot magnitude (NO abs() on a complex bin), the max(·)
#     floor is Class-N, phase preserved via rational.atan2/cos/sin.
# NUMERIC (float DSP): WITHIN-TOL native == pure (reldiff ≤ 1e-9, differential —
# NOT byte-identical). BATCH B4 is COMPLETE (19 sp_transform ops rc148-151).
# python_only_debt 29 -> 25.
# rc152 (BATCH B9 — qm-numeric): the 9 NUMERIC qm ops (norms / eigenvalue-
# invariants / time-evolution that produce floats) move python_only_debt ->
# composition_of_c with NO new C symbol (ABI stays 3). Each is a pure composition
# of the already-C-backed matrix algebra — the c_dispatched laplacian.mat_matmul
# (srmech_dense_matmul_complex) + mat_hermitian_eigendecompose
# (srmech_hermitian_eigendecompose_ws) + mat_solve (srmech_dense_solve_f64_ws) +
# the composition_of_c mat_norm / mat_eigvals + the byte-exact Class-N rational.
# {sqrt,cos,sin,cexp} integer-cascade C ports. Two honest parity sub-classes:
#   • 1 BYTE-EXACT: bell.chsh_pauli_combination_norm — the primary CHSH identity
#     ‖σ_x⊗σ_x + σ_z⊗σ_z‖ = 2 rides the EXACT-INTEGER eigenvalue cascade
#     matrix_cascades.eigvals_exact (char-poly Faddeev-LeVerrier → Sturm →
#     rational bisection, all Fraction/int — the bignum_reference oracle, itself
#     standalone-ready) over the byte-exact integer Mat add, so the value is
#     exactly 2.0 and native==pure is byte-identical AND platform-invariant.
#   • 8 FLOAT / eig-INVARIANT (WITHIN-TOL native == pure, reldiff ≤ 1e-9): bell.
#     chsh_operator_norm (‖B_CHSH‖ = 2√2 via the Jacobi max|λ|) / bell.verify_chsh
#     (bool verdict + residuals) / gauge.casimir_eigenvalue (trace(T^aT^a)/dim =
#     (N²−1)/(2N); the byte-exact casimir_operator matmul + a pure trace/divide) /
#     pseudo_hermitian.construct_eta_from_eigendecomposition (the eigenvector null-
#     space now routes through the C-backed Gram Hermitian-eigendecomposition —
#     mat_matmul ∘ mat_hermitian_eigendecompose — the SAME SVD/Gram-eig null-space
#     pattern as the rc146 so8 subalgebra builders, REPLACING the former hand-
#     rolled float Gaussian-elimination RREF Python-only kernel) / is_pseudo_
#     hermitian + pseudo_hermitian_eigenvalues_real (bool verdict + residual) /
#     single_particle.heisenberg_evolve + liouville_evolve (A(t)=U†AU / ρ(t)=UρU†
#     via mat_hermitian_eigendecompose ∘ rational.cexp ∘ mat_matmul). These bottom
#     out in the non-unique Jacobi eigenBASIS and/or a multi-term complex matmul
#     accumulation that can FMA-fuse ~1 ULP cross-platform (the rc147 ckm lesson),
#     so byte-identity is NOT claimed; the physics INVARIANT (η Hermitian +
#     pseudo-Hermiticity; A(0)=A + Hermiticity; ρ(0)=ρ + trace) + the scalar/bool
#     VALUE are asserted native==pure within-tol. NO new public op (tools.total
#     stays 403); NO new C symbol (ABI stays 3). python_only_debt 25 -> 16.
# rc153 (BATCH B7 — modulation): the 3 NUMERIC signal-processing modulation ops
# move python_only_debt -> composition_of_c with NO new C symbol (ABI stays 3).
# Each COMPOSES an EXISTING C foundation (the SAME numeric-DSP contract as B4):
#   • closed_form_ops.fsk -> composition_of_c: modulate is the C-backed Class-N
#     rational.cos/sin tone cascade (via _exp_i); demodulate's correlator-bank
#     inner product corr_k = Σ_j tones[k][j]·conj(window[j]) IS the matvec
#     corr = Tones·conj(window), routed through the c_dispatched laplacian.
#     mat_matvec ∘ mat_matmul (srmech_dense_matmul_complex) — the SAME Toeplitz-
#     matvec-through-the-C-matmul pattern as the B4b matched_filter correlator.
#     The argmax|corr_k|² is a Class-K decision (no abs()).
#   • closed_form_ops.ofdm -> composition_of_c: modulate's IFFT + demodulate's
#     FFT funnel through spectral_cascades.ifft/.fft -> the c_dispatched numeric
#     FFT foundation srmech_fft_c128 (rc139); the per-subcarrier |H_k| equaliser
#     rides the composition_of_c rational.hypot; the cyclic-prefix / one-tap
#     divide are numpy-free elementwise / integer glue (the SAME pattern as the
#     B4a stft / B4c wiener transform ops).
#   • closed_form_ops.psk_qam -> composition_of_c: the constellation build IS the
#     genuine float math — the PSK phases e^{i·2π·k/M} ride the c_dispatched
#     rational.cos/sin and the QAM grid rides the c_dispatched rational.sqrt (√M);
#     modulate is an integer index lookup, demodulate is a nearest-neighbour
#     Class-K decision-region search over the numpy-free |received−const|² glue.
# NUMERIC (float DSP): the parity contract is WITHIN-TOL native == pure (reldiff
# ≤ 1e-9, differential — NOT byte-identical), the SAME classification as the F1
# FFT / F2 SVD / B4 / B9 numeric batches. NO new public op (tools.total stays
# 403); NO new C symbol (ABI stays 3). python_only_debt 16 -> 13.
# rc154 (BATCH B10 — misc, the near-final compute batch): the 8 misc ops move
# python_only_debt -> composition_of_c (×7) / c_dispatched (×1). Honest per-op
# classification (EACH was a MIS-BUCKETED composition, not an irreducible kernel):
#   • coupling.signed_sum_squared / harmonics.classify_chirality_harmonic /
#     hdc.polar_similarity / compose.greedy_bipartite_alignment -> composition_of_c:
#     pure Class-K/L/N/E primitive compositions (bipolar+square / inner-products+
#     magnitude+ratio / skip+match-count / greedy-argmax) reaching NO non-standalone
#     leaf, libm-free, no abs() — the SAME status as the mat_dot pure-reduction /
#     cascade.compose.signed_sum_squared / top_k_by_score. Value-oracle verified.
#   • hdc.polar_from_real -> composition_of_c: the whole encode IS the c_dispatched
#     sign_quantise.op cascade (srmech_sign_quantise, rc143) — byte-identical.
#   • hdc.polar_unbind -> composition_of_c: unbind == bind on the ±1 sub-alphabet,
#     so it COMPOSES the c_dispatched polar_bind (srmech_polar_bind) — byte-identical.
#   • laplacian.three_fold_eigvec_groups -> composition_of_c: composes the
#     composition_of_c symmetric_eigendecompose (C Hermitian-eig) + c_dispatched
#     srmech_three_fold_bands; eig-INVARIANT native==pure (non-unique basis — band
#     SIZES + spans, not element-wise; the rc146/rc152 invariant precedent).
#   • hdc.polar_random -> c_dispatched: a RANDOM op reaching Python-only
#     random.Random has NO standalone-C path — it earns its OWN deterministic C RNG
#     srmech_polar_random (MT19937 + _randbelow(3) via getrandbits(2) rejection,
#     byte-identical to random.Random(seed).randrange(-1, 2); the polar sibling of
#     §60 srmech_klein4_random) rather than a FALSE composition-of-c. ONE new C
#     symbol; ABI stays 3 (additive). NO new public op (tools.total stays 403).
# Remaining compute python_only_debt = 5 (the honestly-hard residue: einsum / kron
# tensor contractions, ica_jade JADE Givens, jpeg float-DCT, beamforming_fixed
# delay-and-sum). python_only_debt 13 -> 5.
# rc155 (BATCH B-residue — the COMPUTE python-free milestone): the FINAL 5 compute
# ops close python_only_debt to 0. Honest per-op classification:
#   • spectral_cascades.kron -> composition_of_c: A⊗B = the OUTER PRODUCT
#     vec(A)·vec(B)ᵀ (a rank-1 matmul through the c_dispatched laplacian.mat_matmul
#     / srmech_dense_matmul_complex) followed by a pure integer block RE-INDEX;
#     an integer / Gaussian-integer input is BYTE-IDENTICAL to the pure element
#     loop (single-term multiply per entry). Value-oracle verified.
#   • matrix_cascades.einsum -> composition_of_c: a clean 2-operand contraction
#     (matmul / matvec / dot / outer / rank-n) routes its Class-M sum-of-products
#     bundle through the c_dispatched mat_matmul (_einsum_pair_via_matmul); the
#     gather + output re-index are exact glue. Single-operand specs (trace /
#     transpose) fall back to the general index-iteration, whose multiply-
#     accumulate is primitive glue (the mat_dot reduction precedent) reaching no
#     non-standalone leaf. WITHIN-TOL vs the explicit-sum oracle.
#   • beamforming_fixed.op -> composition_of_c: the delay-and-sum output
#     out[i]=Σ_m w[m]·sig[m][delay[m]+i] IS the matvec out = D·w over the
#     delay-aligned window matrix D[i][m]=sig[m][delay[m]+i] (the time-shift is
#     exact integer indexing), routed through the c_dispatched laplacian.mat_matvec
#     ∘ mat_matmul. WITHIN-TOL vs the manual delay-sum oracle.
#   • jpeg.op -> composition_of_c: the only float KERNEL is the block DCT-II /
#     inverse DCT-III, which runs entirely through the already-composition_of_c
#     dct.op (rc148: the cosine-basis matvec rides mat_matmul); the Wallace
#     scaling, Class-K round-quantise, zigzag/block indexing and dequantise
#     multiply are exact integer/float glue (the rc144 deferral was only because
#     the DCT was not yet C-backed; rc148 closed that). Encode→decode round-trip
#     ≈ input within quantisation error.
#   • ica_jade.op -> c_dispatched: THE last real compute gap. Whitening (PCA eig)
#     already composes the C mat_hermitian_eigendecompose and the cumulant assembly
#     is a plain Class-M accumulate, but the JADE Givens JOINT-DIAGONALISATION is a
#     genuinely-iterative data-dependent kernel — so it earns its OWN standalone-C
#     symbol srmech_jade_jointdiag (the Givens sweep in C, composing the libm-free
#     Class-N srmech_atan2 / srmech_cos / srmech_sin; caller-arena, JPL-clean,
#     bounded max_iter, no abs/libm) rather than a false composition tag. JADE's
#     basis is permutation/sign/scale-ambiguous, so native == pure WITHIN-TOL on
#     the recovered separation (~5e-11 element-wise), NOT byte-for-byte. ONE new C
#     symbol; ABI stays 3 (additive); NO new public op (tools.total stays 403).
# THE MILESTONE: python_only_debt 5 -> 0 — the ENTIRE compute surface now runs on
# a bare C host (dispatches to a srmech_* C twin OR is a pure composition of such).
CEIL_PYTHON_ONLY_DEBT = 0
# rc8: SHA-256 mint cluster (6 ops) routed off raw hashlib onto sha256_raw -> 17.
# rc9: octonion left_mult/right_mult/conjugate (3) delegate to the C-backed
# hdc.loop_* family -> moved c_exists_unbound -> composition_of_c -> 14.
# rc10: cascade.cd_basis_product dispatches to srmech_cd_basis_product
# (-> c_dispatched) and octonion_mult_table composes it (-> composition_of_c) -> 12.
# rc11: cascade.hamming_encode/syndrome dispatch to srmech_hamming_* (-> c_dispatched)
# and hamming_decode_correct composes hamming_syndrome (-> composition_of_c) -> 9.
# rc12: hdc.polar_{bind,bundle,density} dispatch to srmech_polar_* (-> c_dispatched);
# all int8, bit-exact -> 6.
# rc13: lmmse.op routes its solve through the dense_solve cascade + its matvec
# through dense_matvec_complex (numpy is carriers-only there now) -> composes two
# c_dispatched ops -> composition_of_c -> 5. The remaining 5 were the Klein-4
# family (see also test_numpy_math_ratchet.py — the source-level guard that keeps
# numpy a carrier, not a math engine).
# rc170 (§53 / F818): klein4_bind/_bundle/_similarity dispatch to srmech_klein4_*
# (the C twins always shipped + were ctypes-bound; hdc.py just never called them)
# -> c_dispatched; klein4_unbind == klein4_bind(c, a) so it composes the now-
# dispatched bind -> composition_of_c. 5 -> 1 (only klein4_triality_cycle).
# rc171 (§53 / F818): klein4_triality_cycle dispatches to srmech_klein4_triality_cycle
# (same forward/inverse 3-cycle tables -> bit-identical) -> c_dispatched. 1 -> 0:
# the c_exists_unbound DEBT IS NOW EMPTY — every public op with a C twin dispatches
# to it. Keep this at 0; a regression means a Python-only op shipped with an
# unbound C twin — wire it, don't raise the ceiling.
CEIL_C_EXISTS_UNBOUND = 0

# rc153 (user-directed 2026-07-06: "prevent import of python bignum like we
# prevent numpy import — it's why we do big int without depends"): the
# ``bignum_reference`` bucket (the Python-bignum exact-rational ORACLES without a
# srmech_bigint-backed C twin) is now a DOWN-ONLY tracked debt, mirroring the
# CEIL_NUMPY_CARRIER / CEIL_PYTHON_ONLY_DEBT ratchets. srmech ships its OWN
# srmech_bigint in C (no Python-bignum dependency), so every exact-rational
# oracle should eventually earn a srmech_bigint-backed C path (the Qalg-C
# exact-algebra tail) and this count should walk to 0. The new ceiling LOCKS the
# current 30 down-only (it may only SHRINK, NEVER grow). NOT touched this rc
# (B7 is a NUMERIC batch — the 3 modulation ops move to composition_of_c, none
# were bignum_reference); the ceiling just pins the 30 so no NEW Python-bignum
# oracle can be added without a C twin.
# rc156 (Qalg TAIL Batch 1a): the 5 exact-Q Taylor oracles
# rational.{exp,sin,cos,log1p,atan}_series_truncate now DISPATCH to the exact
# caller-arena srmech_bigint C peers srmech_{exp,sin,cos,log1p,atan}_series_
# truncate_big (byte-identical (num, den) at ANY magnitude; already shipped as
# the srmech_the_one foundation, now wired to the Python ops), and
# bell.tsirelson_bound (2*sqrt(2)) reaches C because rational.sqrt's precision
# integer-sqrt path (_integer_sqrt for n >= 2^128) now dispatches to
# srmech_bigint_isqrt. All 6 move bignum_reference -> c_dispatched (NO new C
# kernel — the kernels already existed; the batch is the Python wiring + the
# srmech_bigint_isqrt ctypes binding). CEIL_BIGNUM_REFERENCE 30 -> 24.
# rc157 (Qalg TAIL Batch 1b): the π family earns a C path. The NEW C kernel
# srmech_pi_archimedes runs the WHOLE Pfaff-Archimedes two-mean chiral-pair loop
# (per-step harmonic-mean divmod + geometric-mean isqrt) on the caller-arena
# srmech_bigint, so rational.pi_cascade_digits DISPATCHES to it (byte-identical
# "3.<digits>" to the pure-Python oracle; cross-checked pi_chudnovsky == pi_cascade).
# pi_cascade_digits moves bignum_reference -> c_dispatched, and its 2 signal_
# processing wrappers (closed_form_ops / path_b_ops pi_cascade.op) -> composition_of_c.
# CEIL_BIGNUM_REFERENCE 24 -> 21.
# rc158 (Qalg TAIL Batch 2): the 4 Cayley-Dickson INTEGER-cocycle NAVIGATION ops
# (cayley_dickson.{closure, left_orbit, min_generating_set,
# sedenion_zero_divisor_witness}) earn a C path. They are INTEGER (signed basis
# units +-e_i; NO bignum, NO new carrier) and COMPOSE the existing
# srmech_cd_basis_product cocycle: new C kernels srmech_cd_{closure, left_orbit,
# min_generating_set, zero_divisor_witness} (byte-identical native == pure incl.
# set/list ordering). They were only PARKED in bignum_reference alongside the
# arbitrary-precision cd_* QQ arithmetic; the integer navigation never needed
# bignum. All 4 move bignum_reference -> c_dispatched. CEIL_BIGNUM_REFERENCE
# 21 -> 17. (The 4 trivial cd_basis/conjugate/add/norm_sq QQ ops + the Qvec
# carrier are the next batch B3, 17 -> 13.)
# rc159 (Qalg TAIL Batch 3): the 4 TRIVIAL Cayley-Dickson EXACT-QQ arithmetic ops
# (cayley_dickson.{cd_basis, cd_conjugate, cd_add, cd_norm_sq}) earn a C path via
# a NEW srmech_cd_qvec exact-QQ VECTOR carrier (the 1-D sibling of srmech_qmat: a
# CD element of dim 2^k is a QQ-vector of num/den srmech_bigint pairs). The four
# C kernels srmech_cd_q{basis, conjugate, add, norm_sq} REUSE the qmat exact-QQ
# scalar machinery (qmat_q_add/mul/reduce over srmech_bigint) in-TU (no duplicated
# QQ arithmetic) — byte-identical reduced (num, den) to the pure Fraction oracle
# at ANY magnitude. All 4 move bignum_reference -> c_dispatched. CEIL_BIGNUM_
# REFERENCE 17 -> 13. (Next batch B4 = srmech_cd_mult + left_mult_matrix/kernel;
# 13 -> 8.)
# rc160 (Qalg TAIL Batch 4): the Cayley-Dickson MULTIPLICATION core earns a C
# path. The NEW C kernel srmech_cd_mult computes the arbitrary-rational CD product
# ((x·y)_{i⊕j} += x_i·y_j·sign) by composing the srmech_cd_basis_product cocycle
# with the SAME qmat exact-ℚ arithmetic the rc159 Qvec kernels use (in-TU, no
# duplicated ℚ algebra) — so cd_mult moves bignum_reference -> c_dispatched. Its
# two dependents ride the same C: left_mult_matrix (each column x·e_c is a cd_mult)
# and left_mult_kernel (srmech_qmat_nullspace over left_mult_matrix) move
# bignum_reference -> composition_of_c. And the two hypercomplex-exp Taylor oracles
# octonion/quaternion.exp_series_truncate were only PARKED in bignum_reference: each
# just packs the already-c_dispatched rational.{cos,sin}_series_truncate into the
# Euler-formula 4-/8-tuple, so both move bignum_reference -> composition_of_c (no
# new kernel). All 5 leave bignum_reference. CEIL_BIGNUM_REFERENCE 13 -> 8. (The
# remaining 8 are the exact-symbolic LA + integer-poly-factor tail: char_poly /
# eigvals / eigvec (×2) / eig / factor_integer_poly / jordan (×2).)
# rc161 (Qalg TAIL Batch 5): char_poly — the FOUNDATION of the exact-LA tail
# (eigvals_exact / eig_exact / jordan all reduce to the roots of the char-poly) —
# earns a C path. The NEW C kernel srmech_faddeev_leverrier runs the exact-INTEGER
# Faddeev–LeVerrier recursion (A·M matmul + trace + the exact /k divmod) over
# srmech_bigint, byte-identical to the pure _char_poly_int; char_poly moves
# bignum_reference -> c_dispatched. CEIL_BIGNUM_REFERENCE 8 -> 7. (The remaining 7
# are eigvals_exact / eigvec (×2) / eig_exact / factor_integer_poly / jordan (×2);
# next batch B6 = eigvals_exact via srmech_sturm_isolate, 7 -> 6.)
# rc162 (Qalg TAIL Batch 6): eigvals_exact — the exact ROOTS of the char-poly —
# earns a C path, BOTH the real and the complex spectrum. Two NEW C kernels:
# srmech_sturm_isolate (real: char_poly -> Yun square-free -> Sturm sign-sequence
# isolation -> rational bisection -> exact isolating (lo,hi) intervals) and
# srmech_complex_isolate (complex: pure rational-box subdivision over the upper
# half-plane, each box certified by srmech_poly_root_box_certify — the exact
# argument-principle winding in Fraction arithmetic — refined to 2^-bits). Both
# compose the exact-Q srmech_poly_* kernels + scalar srmech_bigint arithmetic,
# byte/structurally-identical to the pure _square_free_factors + _isolate_real_roots
# + _isolate_complex_roots_upper. eigvals_exact moves bignum_reference ->
# c_dispatched. CEIL_BIGNUM_REFERENCE 7 -> 6. (The remaining 6 are eigvec (×2) /
# eig_exact / factor_integer_poly / jordan (×2); next batch B7 = the Qalg-field
# jordan LA.)
# rc163 (Qalg TAIL Batch 7a): eigvec_exact + eigvec_exact_float — the exact
# EIGENVECTORS over the number field Q(lam)=Q[x]/(m) — earn a C path. The NEW C
# kernel srmech_eigvec_exact builds M = A - lam*I with Qalg entries and runs exact
# Gaussian elimination over the Q(lam) FIELD (the SECOND hard Qalg foundation: the
# eigenvectors carry ALGEBRAIC-NUMBER, not plain-Q, coordinates). It COMPOSES the
# exact-Q srmech_poly_* kernels — Qalg add/sub coefficientwise, mul = convolution
# then REDUCE mod m (srmech_poly_divmod), inverse = the extended Euclidean
# algorithm on Q[x] (b^-1 = u/g mod m) — reading the null-space basis off the
# canonical RREF, byte/structurally-identical to the pure _eigvec_exact_qalg.
# eigvec_exact_float is the terminal float read-out over the same exact body. Both
# move bignum_reference -> c_dispatched. CEIL_BIGNUM_REFERENCE 6 -> 4. (The
# remaining 4 are eig_exact / factor_integer_poly / jordan_chains_exact /
# jordan_form_exact; next batches B7b jordan_chains_exact via the Qalg carrier, B8
# factor_integer_poly, B9 eig_exact + jordan_form_exact capstones.)
# rc164 (Qalg TAIL Batch 7b): jordan_chains_exact — the exact JORDAN CHAINS
# (generalized eigenvectors) for a defective eigenvalue — earns a C path. The NEW
# C kernel srmech_jordan_chains composes the rc163 Qalg number-field carrier: it
# builds N = A − λI over ℚ(λ), computes the ranks of the matrix POWERS Nᵏ (a new
# Qalg matrix MATMUL + RANK), reads the Jordan structure off the rank drops, and
# builds the chains TOP-DOWN by nested NULLSPACE + column-rank independence — all
# exact Qalg, byte/structurally-identical to the pure _jordan_chains_build_pure
# (the RREF is canonical + the top-down selection deterministic). jordan_chains_exact
# moves bignum_reference -> c_dispatched. CEIL_BIGNUM_REFERENCE 4 -> 3. (The
# remaining 3 are eig_exact / factor_integer_poly / jordan_form_exact; next batches
# B8 factor_integer_poly (Zassenhaus), B9 eig_exact + jordan_form_exact capstones.)
# rc165 (Qalg TAIL Batch 8): factor_integer_poly — the exact IRREDUCIBLE factors of
# an integer polynomial over ℚ (Zassenhaus) — earns a C path. The NEW C kernel
# srmech_factor_squarefree_primitive factors a square-free primitive integer poly
# into its irreducibles: 𝔽_p[x] Cantor–Zassenhaus (distinct-degree + equal-degree
# split over a DETERMINISTIC xorshift64 rng that reproduces the Python rng stream
# byte-for-byte) + quadratic Hensel lift to mod p^k >= 2·B+1 (B the Mignotte bound)
# + subset recombination (exact ℤ trial-division), all over srmech_bigint. The
# Zassenhaus core — the arbitrary-precision oracle that had no fixed-width C kernel —
# now dispatches to C; the Yun square-free / content / sort orchestration stays in
# the shared Python wrapper (its gcds are the already-C-backed srmech_poly_gcd /
# srmech_bigint_gcd), so BOTH native and pure paths yield byte-identical factors +
# multiplicities + order (the factorization is unique). factor_integer_poly moves
# bignum_reference -> c_dispatched. CEIL_BIGNUM_REFERENCE 3 -> 2. (The remaining 2
# are eig_exact / jordan_form_exact; next batch B9 = the eig_exact + jordan_form_exact
# capstones -> CEIL_BIGNUM_REFERENCE 0.)
# rc166 (Qalg TAIL Batch 9 — THE CAPSTONE, CLOSES the exact-algebra tail): the last
# 2 oracles eig_exact + jordan_form_exact move bignum_reference -> composition_of_c.
# With rc165 every COMPUTE dependency became C — char_poly (srmech_faddeev_leverrier),
# factor_integer_poly (srmech_factor_integer_poly, Zassenhaus), eigvals_exact
# (srmech_sturm_isolate / srmech_complex_isolate / srmech_poly_root_box_certify),
# eigvec_exact (srmech_eigvec_exact over the ℚ(λ) field), jordan_chains_exact
# (srmech_jordan_chains) — so the two CAPSTONES are now THIN Python orchestrations
# that ONLY compose already-c_dispatched ops with trivial glue: char_poly -> factor
# -> _roots_of_irreducible (eigvals_exact on the companion) -> per-root Qalg λ ->
# eigvec_exact / jordan_chains_exact -> assemble the eigenpairs / build P (chain
# columns) + J (block-diagonal Jordan) -> the ONE terminal Qalg->float/complex
# rotation-last projection -> self-validate. There is NO irreducible compute kernel
# left in the orchestration (the mat_dot / factor-Yun / esprit precedent — a bare-C
# host orchestrates the C leaves the same way), so composition_of_c is the HONEST
# classification (NO new C symbol; ABI stays 3). THE MILESTONE:
# CEIL_BIGNUM_REFERENCE 2 -> 0 — the ENTIRE exact-algebra tail is now python-free
# (every leaf a srmech_* C twin; the bignum_reference bucket is EMPTY).
CEIL_BIGNUM_REFERENCE = 0

# ── the ORCHESTRATION→C phase driver (rc170; §"non_compute sub-buckets") ──────
# With the compute (CEIL_PYTHON_ONLY_DEBT=0), exact-algebra (CEIL_BIGNUM_
# REFERENCE=0) and self-hosting (CEIL_C_EXISTS_UNBOUND=0) arcs all CLOSED, the
# ``non_compute`` bucket (114 rows) is the last one with NO ceiling — the honest
# next frontier. The phase goal: make a bare-C host (no Python) run the WHOLE
# apparatus — dispatch, catalogs, IPC, the genome, the chain-runner — in C. This
# ceiling drives it, exactly as CEIL_BIGNUM_REFERENCE drove the Qalg-C tail.
#
# The 114 non_compute rows carry a ``non_compute_kind`` sub-classification (see
# rosetta_classification.ndjson + test_non_compute_ratchet_rc170.py), splitting
# them into FOUR honest sub-buckets that sum to 114:
#   owed_orchestration  (9) — genuine control/dispatch LOGIC a bare-C host needs
#                             (the amsc.compose chain-runner + its 2 catalog
#                             dependents list_catalog_chains / run_catalog_chain,
#                             the F929 infer router, the MCP op-schema lookup). THIS
#                             ceiling. Owed-C: only SHRINKS as each earns a C
#                             path (→ c_dispatched / composition_of_c / composes_c).
#                             NEVER grows. rc171: the 5 op-provenance verdict/carry
#                             ops earned C peers → composes_c (20 → 15). rc172: the
#                             6 catalog registry/kernel/audit ops earned C → composes_c
#                             (15 → 9).
#   composes_c (76)         — thin: already composes existing C (json/toml/genome/
#                             klein4/the_one/carriers/op_provenance) OR a pure
#                             accessor / constructor / validator (hides no
#                             compute). Gets a TRANSITIVE-REACHABILITY assert,
#                             not a ceiling.
#   host_glue (2)           — filesystem / host I/O (descriptor FS discovery,
#                             catalog-root FS registration). Tracked, no ceiling
#                             this rc (annex decision pending).
#   dev_tooling (27)        — a bare-C host does NOT need it (tool_schema register/
#                             extension/warmup, gap_suggester, the sp mutable
#                             plugin-registry / dispatch-lock / lazy-loader /
#                             profiling, the carrier-ladder descriptor). PINNED
#                             exempt allowlist — justified, never owed-C.
#
# LOWER this ceiling as each owed-orchestration op earns a C path (c_dispatched /
# composition_of_c). NEVER raise it — a rising owed count means new control logic
# was added Python-only, which is exactly the bare-C-host regression this drives.
# rc171: op_provenance verdict/carry earned C (the 5 op_provenance ops moved
# owed_orchestration → composes_c via srmech_op_verdict/_family_verdict/_op_carry/
# _lossy_projection_record/_op_reproject); 20 → 15.
# rc172 (2026-07-07): the catalog registry/kernel/audit batch earned C — 6
# catalog ops moved owed_orchestration → composes_c. Four earned dedicated C
# peers (list_registered_roots → srmech_catalog_registered_roots;
# get_local_kernel_state → srmech_catalog_local_kernel_state; use_local_kernel
# + clear_local_kernel → srmech_catalog_use_local_kernel;
# attestation_audit → srmech_catalog_attestation_audit) and list_attested_sources
# is classified composes_c directly (thin compose over the descriptor parse +
# a pure filter/sort/project, consistent with the already-composes_c
# get_attested_dataset / get_attested_descriptor). The 2 chain-runner-dependent
# catalog ops (list_catalog_chains / run_catalog_chain) stay owed — the
# amsc.compose chain-runner is not in C yet (rc173+). 15 → 9.
# rc173 (2026-07-07): the amsc.compose chain-runner PARSE half earned C — the
# 2 parse ops moved owed_orchestration → composes_c (parse_chain_spec →
# srmech_chain_spec_parse; parse_catalog_chains → srmech_chain_catalog_parse;
# JSON-in / normalized-canonical-JSON-out, args re-attached from the original
# dict). HONEST SPLIT: resolve_chain / run_chain STAY owed — they dispatch
# ARBITRARY srmech ops (heterogeneous kwargs) over the LIVE Python object
# graph (importlib + getattr + reference resolution against runtime step
# outputs), a bounded-op FFI + uniform value carrier scoped rc174 (NOT the
# bounded cascade atoms; confirmed run_chain invokes any of the 14 class
# modules by name). The 2 catalog dependents (list_catalog_chains /
# run_catalog_chain) also stay owed until the run loop lands. 9 → 7.
# rc174 (2026-07-07): the amsc.compose chain-runner RUN LOOP earned C — the
# 2 run ops moved owed_orchestration → composes_c. srmech_chain_run RUNS a
# validated chain end-to-end in C to byte-identical OUTPUT: it resolves each
# step's @row/@input/@step[N] arg references + dispatches the BOUNDED Class-N
# shipped-op set (pi_cascade_digits / {exp,sin,cos,log1p,atan}_series_truncate /
# rational_{add,mul,div,pow_uint}) to the EXISTING C kernels (srmech_pi_
# archimedes / srmech_*_series_truncate_big / srmech_rational_pow_uint_big + a
# bignum-ℚ add/mul/div composed from srmech_bigint) + marshals the final value
# back as a canonical descriptor. The WHOLE shipped apparatus (pi digits /
# asymptotic-calculus series / Friedmann dark-fraction) genuinely runs in C;
# rc103 inform-don't-limit routes any out-of-table op / @catalog ref / non-raise
# policy / non-i64 input to the COMPLETE pure path (never a wrong answer). The 2
# catalog dependents (list_catalog_chains / run_catalog_chain) become buildable
# next (rc175: run_catalog_chain / list_catalog_chains / dispatch.infer). 7 → 5.
# rc175 (2026-07-07): the 2 catalog CHAIN-ORCHESTRATION dependents earned C —
# list_catalog_chains → srmech_catalog_list_chains (parse+project the chain
# summaries); run_catalog_chain → srmech_catalog_run_chain (find the named chain
# in operator_chain + run it), each COMPOSING the rc173 parse + rc174 chain-
# runner. HONEST SPLIT: dispatch.infer (the F929 router) STAYS owed → rc176. It
# is not thin: its relationship payloads carry LIVE non-JSON carrier objects
# (BiPoly / TriPoly / QPoly / QBiPoly / EllRatio / Mat / the One), and moving its
# try-and-verify LOGIC to C needs a full multi-carrier FFI marshalling layer for
# the 7 reducer families + closed_form return marshalling — a multi-rc arc, not
# one clean rc. So owed 5 → 3 (the 3 remaining = dispatch.infer [→ rc176] + the
# deferred tool_schema pair [get_tool_schema / tool_schema_view → host-glue MCP
# server]). composes_c 80 → 82.
CEIL_NON_COMPUTE_OWED = 3

# The PINNED dev-tooling allowlist — the exact ``non_compute_kind == "dev_tooling"``
# set. A row here is JUSTIFIED as a genuine dev / LLM-affordance a bare-C host
# never needs (the tool_schema *introspection registry*, the gap_suggester, the
# signal_processing mutable plugin table / dispatch-lock / lazy-loader / profiling
# surface, the carrier-ladder self-descriptor) — analogous to the bignum_reference
# rows' oracle_justification. A NEW dev_tooling row must be added here DELIBERATELY
# (with the same justification burden); a control-logic op does NOT belong here —
# it is owed_orchestration and counts against CEIL_NON_COMPUTE_OWED instead.
NON_COMPUTE_DEV_TOOLING_EXEMPT = frozenset({
    "srmech.amsc.carrier_ladder.carrier_ladder_descriptor",
    "srmech.amsc.gap_suggester.register_classifier",
    "srmech.amsc.gap_suggester.register_probes",
    "srmech.amsc.gap_suggester.suggest_gap_collections",
    "srmech.amsc.tool_schema.load_extension_file",
    "srmech.amsc.tool_schema.register_profile_tools",
    "srmech.amsc.tool_schema.register_tool",
    "srmech.amsc.tool_schema.unregister_profile_tools",
    "srmech.amsc.tool_schema.warmup_all",
    "srmech.signal_processing.cascade_dispatcher.begin_cascade",
    "srmech.signal_processing.cascade_dispatcher.current_cascade",
    "srmech.signal_processing.cascade_dispatcher.dispatch",
    "srmech.signal_processing.cascade_dispatcher.end_cascade",
    "srmech.signal_processing.cascade_dispatcher.is_dispatch_table_locked",
    "srmech.signal_processing.cascade_dispatcher.lock_dispatch_table",
    "srmech.signal_processing.cascade_dispatcher.resolve_path",
    "srmech.signal_processing.cascade_dispatcher.unlock_dispatch_table",
    "srmech.signal_processing.path_registry.clear_registry",
    "srmech.signal_processing.path_registry.has_path",
    "srmech.signal_processing.path_registry.lookup",
    "srmech.signal_processing.path_registry.register",
    "srmech.signal_processing.path_registry.register_lazy_loader",
    "srmech.signal_processing.path_registry.registered_ops",
    "srmech.signal_processing.profiling.cell_grid",
    "srmech.signal_processing.profiling.clear_records",
    "srmech.signal_processing.profiling.iter_records",
    "srmech.signal_processing.profiling.record_profile",
})

# The four honest sub-buckets of the non_compute bucket. Every non_compute row
# carries exactly one ``non_compute_kind`` in this set (see the rc170 ratchet).
_NON_COMPUTE_KINDS = (
    "owed_orchestration", "composes_c", "host_glue", "dev_tooling",
)

_DEBT_BUCKETS = ("python_only_debt", "c_exists_unbound")
_ALL_BUCKETS = (
    "c_dispatched", "c_exists_unbound", "composition_of_c",
    "python_only_debt", "bignum_reference", "non_compute",
)


def _iter_submodules(root_name):
    root = importlib.import_module(root_name)
    yield root
    if not hasattr(root, "__path__"):
        return
    for info in pkgutil.walk_packages(root.__path__, root_name + "."):
        name = info.name
        tail = name.rsplit(".", 1)[-1]
        if tail.startswith("_") and tail != "__init__":
            continue
        if any(p in name for p in ("._research", ".adapters", ".attested", "._native")):
            continue
        try:
            yield importlib.import_module(name)
        except Exception:  # noqa: BLE001 — a module that won't import has no live ops
            continue


def _live_ops():
    """Map canonical ``defined_at`` -> ``exposed_as`` for every public op.

    Same walk as notes/_rosetta_inventory.py: public, callable, NON-class,
    DEFINED in the srmech package (skips numpy/stdlib re-exports), deduped by
    ``<module>.<qualname>`` so re-exports collapse to one canonical identity.
    """
    seen = {}
    for root_name in _ROOTS:
        try:
            importlib.import_module(root_name)
        except Exception:  # noqa: BLE001
            continue
        for mod in _iter_submodules(root_name):
            names = getattr(mod, "__all__", None)
            if names is None:
                names = [n for n in dir(mod) if not n.startswith("_")]
            for n in names:
                obj = getattr(mod, n, None)
                if not callable(obj) or inspect.isclass(obj):
                    continue
                objmod = getattr(obj, "__module__", "") or ""
                if not objmod.startswith("srmech"):
                    continue
                qual = getattr(obj, "__qualname__", n)
                key = f"{objmod}.{qual}"
                seen.setdefault(key, f"{mod.__name__}.{n}")
    return seen


def _load_classification():
    rows = [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r["bucket"] for r in rows}


def _load_non_compute_kinds():
    """Map ``defined_at`` -> ``non_compute_kind`` for every ``non_compute`` row
    (the rc170 four-way sub-classification). Only non_compute rows carry the
    field."""
    rows = [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r.get("non_compute_kind")
            for r in rows if r.get("bucket") == "non_compute"}


def test_every_bucket_value_is_known():
    cls = _load_classification()
    bad = {da: b for da, b in cls.items() if b not in _ALL_BUCKETS}
    assert not bad, f"classification has unknown bucket values: {bad}"


def test_live_surface_is_fully_classified():
    """Every live public op has a committed bucket (new ops must be classified)."""
    live = _live_ops()
    cls = _load_classification()
    unclassified = sorted(set(live) - set(cls))
    assert not unclassified, (
        f"{len(unclassified)} live op(s) have no Rosetta classification — add a "
        f"bucket line to rosetta_classification.ndjson for each:\n"
        + "\n".join(f"  - {d}  (exposed: {live[d]})" for d in unclassified)
    )


def test_no_stale_classification():
    """Every classified op still exists (removed ops must leave the ledger)."""
    live = _live_ops()
    cls = _load_classification()
    stale = sorted(set(cls) - set(live))
    assert not stale, (
        f"{len(stale)} classified op(s) no longer exist — remove their lines "
        f"from rosetta_classification.ndjson:\n" + "\n".join(f"  - {d}" for d in stale)
    )


@pytest.mark.parametrize("bucket,ceiling", [
    ("python_only_debt", CEIL_PYTHON_ONLY_DEBT),
    ("c_exists_unbound", CEIL_C_EXISTS_UNBOUND),
])
def test_debt_bucket_is_monotone_decreasing(bucket, ceiling):
    """The two DEBT buckets stay at or below their down-only ceilings.

    If this fails because the count went UP, a Python-only op was added without a
    C twin (or an unbound one slipped in) — give it a twin / wire it up instead
    of raising the ceiling. If the count went DOWN, lower the ceiling to match.
    """
    cls = _load_classification()
    live = set(_live_ops())
    count = sum(1 for da, b in cls.items() if b == bucket and da in live)
    assert count <= ceiling, (
        f"{bucket} = {count} exceeds the down-only ceiling {ceiling}. "
        f"A standalone-C regression: close the debt, don't raise the ceiling."
    )
    # Tightness guard: if the real count dropped below the ceiling, the ceiling
    # must be lowered to lock the win in (keeps the ratchet honest).
    assert count == ceiling, (
        f"{bucket} = {count} is BELOW its ceiling {ceiling} — debt was closed; "
        f"lower CEIL_{bucket.upper()} to {count} to lock the ratchet."
    )


def test_bignum_reference_is_monotone_decreasing():
    """``bignum_reference`` (Python-bignum exact-rational oracle without a C twin)
    is a DOWN-ONLY debt — it may only SHRINK as each oracle earns a
    srmech_bigint-backed C path (the Qalg-C exact-algebra tail); it may NEVER
    grow. srmech ships its own srmech_bigint in C (no dep) — this drives the
    Python-bignum-ORACLE count to 0.

    Mirrors ``test_debt_bucket_is_monotone_decreasing`` /
    ``CEIL_NUMPY_CARRIER``: an OP-LEVEL ledger ratchet on the
    ``bignum_reference`` bucket (user-directed 2026-07-06 — "prevent import of
    python bignum like we prevent numpy import"). It is NOT a
    ``from fractions import Fraction`` import ban: the exact-ℚ CARRIERS
    (Poly / QMat / QPoly / Qalg / Qprime / TriPoly / EllBase) legitimately use
    ``Fraction`` as their Python-side rep and already have srmech_bigint C peers —
    this guards only the count of exact-rational ORACLE ops that have no C twin.
    """
    cls = _load_classification()
    live = set(_live_ops())
    count = sum(1 for da, b in cls.items()
                if b == "bignum_reference" and da in live)
    assert count <= CEIL_BIGNUM_REFERENCE, (
        f"bignum_reference = {count} exceeds the down-only ceiling "
        f"{CEIL_BIGNUM_REFERENCE}. A Python-bignum exact-rational oracle was "
        f"added without a srmech_bigint-backed C twin: give it a C path, don't "
        f"raise the ceiling."
    )
    # Tightness guard (as with the debt buckets): if the count dropped below the
    # ceiling, the ceiling must be lowered to lock the win in.
    assert count == CEIL_BIGNUM_REFERENCE, (
        f"bignum_reference = {count} is BELOW its ceiling {CEIL_BIGNUM_REFERENCE} "
        f"— an oracle earned a C path; lower CEIL_BIGNUM_REFERENCE to {count} to "
        f"lock the ratchet."
    )


def test_bignum_reference_rows_are_justified():
    """Every ``bignum_reference`` row must EITHER carry an explicit
    ``oracle_justification`` (why it is a genuine exact-rational / exact-integer
    arbitrary-precision oracle, not hidden compute) OR name a companion
    ``c_companion`` c_dispatched path that does the real work.

    This closes the hiding-spot ``the_one`` used before rc138: an op that is
    really a cascade of C-backed primitives can park in the non-debt
    ``bignum_reference`` bucket and dodge the everything-mirrors ratchet. Now a
    ``bignum_reference`` row must SAY why it belongs there (or point at its C
    companion) — a compute op with a C peer belongs in ``c_dispatched`` instead
    (as ``the_one`` / ``one_matrix`` / ``to_scalar`` now are, on srmech_the_one).
    """
    rows = [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    unjustified = []
    for r in rows:
        if r.get("bucket") != "bignum_reference":
            continue
        just = r.get("oracle_justification")
        companion = r.get("c_companion")
        ok = (isinstance(just, str) and just.strip()) or \
             (isinstance(companion, str) and companion.strip())
        if not ok:
            unjustified.append(r["defined_at"])
    assert not unjustified, (
        f"{len(unjustified)} bignum_reference row(s) HIDE compute from the ratchet "
        f"— give each an oracle_justification (why it is a genuine exact oracle) or "
        f"a c_companion c_dispatched path, or move it to c_dispatched if it has a C "
        f"peer:\n  " + "\n  ".join(sorted(unjustified))
    )


# ── rc170: the orchestration→C ratchet over the non_compute sub-buckets ───────

def test_every_non_compute_row_has_a_valid_kind():
    """Every ``non_compute`` row carries exactly one of the four honest
    ``non_compute_kind`` values — a new non_compute op MUST be sub-classified
    (this forces the owed-C-vs-dev-tooling decision, the way the top-level
    bucket forces the C-mirror decision)."""
    kinds = _load_non_compute_kinds()
    bad = {da: k for da, k in kinds.items() if k not in _NON_COMPUTE_KINDS}
    assert not bad, (
        f"{len(bad)} non_compute row(s) have no / an unknown non_compute_kind "
        f"(must be one of {_NON_COMPUTE_KINDS}):\n  "
        + "\n  ".join(f"{da}: {k!r}" for da, k in sorted(bad.items()))
    )


def test_non_compute_owed_is_monotone_decreasing():
    """``owed_orchestration`` (genuine control/dispatch logic a bare-C host needs)
    is a DOWN-ONLY owed-C debt — the orchestration→C phase driver. It may only
    SHRINK as each orchestration op earns a C path (c_dispatched /
    composition_of_c); it may NEVER grow. A bare-C host (no Python) must run the
    WHOLE apparatus — dispatch, catalogs, IPC, the genome, the chain-runner — in
    C, and this ceiling drives that, exactly as CEIL_BIGNUM_REFERENCE drove the
    Qalg-C exact-algebra tail. Each rc that moves an owed op to a C path lowers
    the ceiling to lock the win in.
    """
    kinds = _load_non_compute_kinds()
    live = set(rosetta_live_objects())
    count = sum(1 for da, k in kinds.items()
                if k == "owed_orchestration" and da in live)
    assert count <= CEIL_NON_COMPUTE_OWED, (
        f"owed_orchestration = {count} exceeds the down-only ceiling "
        f"{CEIL_NON_COMPUTE_OWED}. New Python-only control logic a bare-C host "
        f"needs was added: give it a C path (→ c_dispatched / composition_of_c), "
        f"don't raise the ceiling."
    )
    # Tightness guard (as with the debt buckets): a drop must lower the ceiling.
    assert count == CEIL_NON_COMPUTE_OWED, (
        f"owed_orchestration = {count} is BELOW its ceiling "
        f"{CEIL_NON_COMPUTE_OWED} — an orchestration op earned a C path; lower "
        f"CEIL_NON_COMPUTE_OWED to {count} to lock the ratchet."
    )


def test_non_compute_composes_c_is_transitively_reachable():
    """Every ``composes_c`` row hides NO Python compute kernel: walking its
    TRANSITIVE callee graph reaches NO non-standalone-ready leaf (python_only_debt
    / bignum_reference / c_exists_unbound). Reuses the SAME standalone-C
    reachability walk as the transitive-standalone ratchet (conftest.py).

    ``composes_c`` claims "thin": the op is either a pure composition of already-C
    ops (json/toml/genome/klein4/the_one/carriers) OR a pure accessor / constructor
    / validator. Both are only honest if the op cannot secretly reach a
    Python-only kernel. (Today all three debt buckets are 0, so this is a
    FORWARD-GUARD: it LOCKS the property so a future refactor cannot re-route a
    composes_c op through a newly-added Python kernel without tripping here —
    mirroring test_no_composition_reaches_nonstandalone_leaf, applied to the
    non_compute composes_c sub-bucket.)
    """
    kinds = _load_non_compute_kinds()
    cls = _load_classification()
    objs = rosetta_live_objects()
    violations = []
    for da, k in kinds.items():
        if k != "composes_c":
            continue
        fn = objs.get(da)
        if fn is None:
            continue
        for leaf in rosetta_reached_ledger_ops(fn, cls):
            if cls.get(leaf) in ROSETTA_NOT_READY:
                violations.append(f"{da}  ->  {leaf}  ({cls[leaf]})")
    assert not violations, (
        "composes_c non_compute op(s) transitively reach a non-standalone-ready "
        "leaf (a hidden Python kernel) — give the leaf a C path or reclassify the "
        "row (owed_orchestration if it is genuine control logic):\n  "
        + "\n  ".join(sorted(violations))
    )


def test_non_compute_dev_tooling_is_pinned():
    """The live ``dev_tooling`` set is EXACTLY the pinned allowlist
    ``NON_COMPUTE_DEV_TOOLING_EXEMPT``. A dev_tooling row is a justified dev /
    LLM-affordance a bare-C host never needs (the introspection registry, the
    gap_suggester, the sp mutable plugin table / dispatch-lock / lazy-loader /
    profiling, the carrier-ladder self-descriptor). Adding a new dev_tooling row
    requires DELIBERATELY extending the allowlist (the same justification burden
    as a bignum_reference oracle_justification) — so control logic cannot quietly
    escape the owed-C ceiling by being mislabeled dev_tooling.
    """
    kinds = _load_non_compute_kinds()
    live = set(rosetta_live_objects())
    live_dev = {da for da, k in kinds.items()
                if k == "dev_tooling" and da in live}
    missing = NON_COMPUTE_DEV_TOOLING_EXEMPT - live_dev
    extra = live_dev - NON_COMPUTE_DEV_TOOLING_EXEMPT
    assert not missing and not extra, (
        "the live dev_tooling set does not match the pinned allowlist.\n"
        f"  UNEXPECTED (in ledger, not allowlisted — JUSTIFY as dev-affordance "
        f"or reclassify as owed_orchestration): {sorted(extra)}\n"
        f"  STALE (allowlisted, no longer a live dev_tooling row — remove from "
        f"the allowlist): {sorted(missing)}"
    )
