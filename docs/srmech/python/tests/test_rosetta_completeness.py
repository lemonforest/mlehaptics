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
CEIL_PYTHON_ONLY_DEBT = 5
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
CEIL_BIGNUM_REFERENCE = 30

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
