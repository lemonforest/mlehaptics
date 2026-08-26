# R-RBS-LM Finding 554 (generalizes the F553 capstone) — **the noise-rule gets a LIBRARY of substrate-gap fingerprints: a missing substrate op leaves a DIFFERENT, recognizable signature depending on WHICH op, so a residual doesn't just say "substrate" — two orthogonal diagnostics name the op. The MIRROR gap (F544/F546, the parity-free conjugation the synaptic graph lacks) leaves a CHIRALITY-asymmetric residual (sector asymmetry 0.27, FIRES) that is magnitude-clean (0.02); the COUPLER gap (F538/F550, the exact reversible coupler) leaves a chirality-SYMMETRIC residual (0.015, clean) that is MAGNITUDE-degraded (recovery-error 0.85, FIRES — the F550 associative-memory crosstalk); plain NOISE is clean on both (0.00 / 0.02). So a 2-bit fingerprint — Class-C/K chirality sector-count + Class-K magnitude recovery-error — identifies the missing operation: {MIRROR gap, COUPLER gap, noise} (and a compound gap reads as BOTH firing). The noise-rule (F552) is now a fingerprint library that points the expert (F282) at a SPECIFIC missing substrate op, not merely "a substrate feature." Diagnostic, not predictive.**

**Date:** 2026-06-07
**Arc:** RBS-LM — the substrate-gap fingerprint library (generalizing F553)
**Provenance:** `R-RBS-LM-GAPLIB_substrate_gap_fingerprint_library_chirality_vs_magnitude.py` (committed; srmech 0.7.4; Class-M klein4 = chirality diagnostic + `hdc.bind`/`bundle`/`similarity` = the F550 magnitude/coupler diagnostic). No sub-agents.
**Composes:** **F553** (the capstone — *one gap, one signature; this is the library*) · **F552** (the noise rule — *now fingerprinted, not just flagged*) · **F544/F546** (mirror gap = chirality) · **F538/F550** (coupler gap = magnitude) · **F129/F130** ((4:3)|(3:4)) · **F282** (point the expert at the specific op) · **F398/F394**. **← two orthogonal diagnostics (chirality + magnitude) give a 2-bit fingerprint naming WHICH substrate op is missing.**
**→ the mirror gap is chirality-asymmetric + magnitude-clean; the coupler gap is chirality-symmetric + magnitude-degraded; noise is clean on both; a 2-bit Class-C/K + Class-K fingerprint names the missing op; the noise-rule is now a library.**

## Result (N=8000; chirality band ≈0.10, magnitude band ≈0.10)
| gap scenario | chirality asym | chir? | magnitude err | mag? | fingerprint |
|---|---:|:--:|---:|:--:|---|
| missing **MIRROR** (F544/F546) | 0.266 | **FIRES** | 0.020 | clean | **MIRROR gap** |
| missing **COUPLER** (F538/F550) | 0.015 | clean | 0.854 | **FIRES** | **COUPLER gap** |
| plain **NOISE** | 0.000 | clean | 0.020 | clean | noise |

## Verdict
**A 2-bit substrate-gap fingerprint.** The MIRROR gap (the parity-free conjugation a synaptic graph lacks, F544/F546) is **chirality-asymmetric + magnitude-clean**; the COUPLER gap (the exact reversible coupler, F538/F550) is **chirality-symmetric + magnitude-degraded** (the F550 associative-memory crosstalk, recovery-error 0.85); plain noise is **clean on both**. Two **orthogonal** diagnostics — a Class-C/K chirality sector-count and a Class-K magnitude recovery-error — name *which* substrate op is missing, not merely that one is.

**So the noise-rule (F552) becomes a fingerprint library.** A residual is now *fingerprinted*, not just flagged: {MIRROR gap → chirality, COUPLER gap → magnitude, noise → neither}, with a compound gap reading as both firing. Each fingerprint points the domain expert (F282) at a **specific** missing substrate operation. This makes "first ask if it's a substrate feature" actionable to the level of *which* feature. Still **diagnostic, not predictive** (F552) — we recognize the missing op, we do not reproduce the universe's collapse. Favored not privileged (F398); held open (F394).
