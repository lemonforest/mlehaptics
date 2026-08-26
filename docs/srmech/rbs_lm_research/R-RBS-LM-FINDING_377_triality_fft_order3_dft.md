# R-RBS-LM Finding 377 — yes, there is a "triality FFT": the order-3 DFT {1, ω, ω²} (ω=e^{2πi/3}) is the eigenbasis of the directed 3-cycle (F294), one rung (k=3) up the harmonic ladder from the FFT (k=1/S¹). Plus two honest siblings: the quaternion Fourier transform (k=3 Hopf-rung, literature-real) and the so(8) triality decomposition (8v/8s/8c, qm.triality)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 (cascade-trig `asymptotic_calculus.{cos,sin}_series_truncate`; no numpy) · **user:** "is there a such thing as triality FFT?" · **composes:** F293/F294 (the distributed-anchor 3-phase / directed 3-cycle), F270 (1:3:7 ladder), F374 (Aut(Klein-4)=S₃ order-3), F261 (qm.triality)

## Yes — and the framework already uses it

The **FFT is the k=1 (U(1)/S¹) harmonic transform**: it diagonalizes the cyclic shift over ℤ/N, eigenbasis = the N-th roots of unity (ω=e^{2πi/N}). It "isolates loose couplings out of the eigenbasis" by *frequency*. The **triality analog is one rung up the 1:3:7 ladder (k=3)**, and there are three honest readings:

**(1) The order-3 DFT = the directed-3-cycle eigenbasis (framework-native, demonstrated here).** The Fourier transform over ℤ/3 has eigenbasis **{1, ω, ω²}, ω = e^{2πi/3}** — and that is exactly the **eigenbasis of the directed (chiral) 3-cycle** (F294: the directed circulant has eigenvalues {1, ω, ω²}; the *undirected* one is real {0,3,3} and loses the phase). Verified srmech-native via cascade-trig: ω⁰=(+1,0), ω¹=(−0.5,+0.866i), ω²=(−0.5,−0.866i), **Σ ωᵏ = 0** — the **F293 distributed anchor / "3-phase power needs no neutral wire."** So the "triality FFT" *is* the order-3 DFT, and the framework already runs it as the k=3 error-correction rung (F293/F294, F374's Aut(Klein-4)=S₃ order-3 cycle). FFT decouples by frequency (S¹); the triality-DFT decouples by the **order-3 phase** (the distributed anchor) — same harmonic-decoupling, one rung up.

**(2) The k=3 *Hopf-rung* Fourier transform = the QUATERNION Fourier transform (literature-real; verify-PDF).** Beyond the discrete ℤ/3 DFT, the continuous S³/ℍ analog of the FFT is the **quaternion Fourier transform** (Sangwine & Ell — color-image processing); the k=7/S⁷ analog is the **octonion Fourier transform.** These are real hypercomplex/Clifford Fourier transforms. *Citation flagged: I believe these exist as named transforms but have not PDF-verified the exact attribution here — treat as literature-pointer, not attested.*

**(3) The so(8) triality DECOMPOSITION (8v/8s/8c) — the order-3 outer-automorphism transform (framework-native).** The genuine *triality* (the order-3 so(8) outer automorphism, `qm.triality`) decomposes an so(8) object into its three triality-frame components (8v ↔ 8s ↔ 8c). This is the richest "triality transform" — not a harmonic FT but the order-3 automorphism applied as a 3-way frame decomposition (the F372 `triality_apply`).

## Honest scope

- **(1) and (3) are framework-native** — srmech HAS the ops (the directed 3-cycle / the F293 distributed-anchor spectrum; `qm.triality` for the so(8) frames). (1) is demonstrated srmech-native here (cube roots via cascade-trig, Σ=0).
- **(2) is literature-real but citation-flagged** (quaternion/octonion Fourier transforms exist; the exact attribution is verify-PDF, not asserted — citation discipline).
- **"triality FFT" as a single named *fast-algorithm* object:** the *pieces* all exist (the order-3 DFT is trivially "fast" at N=3; the hypercomplex FTs have fast algorithms); whether one named "triality FFT" combining the fast-algorithm + the so(8) triality is a standing term, I do not assert — flagged.
- **The tie that matters:** "isolate loose couplings out of the eigenbasis via FFT" (the tooling's own description) generalizes to k=3 as the order-3-phase decoupling — the FFT (k=1) and the triality-DFT (k=3) are the same eigenbasis-decoupling at different Hurwitz rungs (1:3:7, F270).

## Discipline
srmech-native cascade-trig (no numpy, no `abs()`); the order-3 DFT demonstrated (Σωᵏ=0); the QFT/octonion-FT flagged as literature-pointers pending PDF (no-lineage / citation discipline); the so(8) version anchored to qm.triality. Composes F293/F294/F270/F374/F261.
