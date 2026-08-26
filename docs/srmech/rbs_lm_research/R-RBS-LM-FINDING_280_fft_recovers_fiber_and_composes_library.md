# F280 — the FFT guess holds: the difference-fiber IS the flat chart's autocorrelation, and a fully-projected element library composes multiplicatively in FFT-domain

**Headline:** The user's guess — *"if we can create a fully projected view of every mass item, we can FFT what looks like a flattened chart with known elements and compounds"* — is **right, for two concrete reasons, both verified.** (A) **The neutral-loss difference-graph (the F279 fiber) IS the autocorrelation of the spectrum** (Wiener–Khinchin: `autocorr = IFFT(|FFT|²)`); FFT of the ethanol flat chart surfaces exactly the neutral losses (Δ1 H, Δ2 H₂ ×2, Δ14 CH₂, Δ15 CH₃, Δ17 OH, Δ18 H₂O) — the fiber falls out of the chart's own power spectrum, natively. (B) **Isotope envelopes are convolutions**, so FFT makes them **multiplicative**: the 3-carbon envelope via convolution == via `FFT(p)³` (exact), and a (1C+1Cl) library-composition decodes its composition (M+1 → 1 carbon; M+2 → the 3.13:1 Cl signature). So a **fully-projected FFT-domain library + a flat chart = an un-flattened matching/deconvolution engine** where matching is multiplication/correlation and the fiber is recoverable from the transform itself. Single-model; srmech v0.6.0rc20.

*User direction (2026-06-02): "if we can create a fully projected view of every mass item, then we can FFT what looks like a flattened chart with known elements and compounds, right?"*

---

### §A — FFT recovers the difference-fiber (autocorrelation) — **DEMONSTRATED**
By Wiener–Khinchin, the autocorrelation of a spectrum = `IFFT(|FFT(spectrum)|²)`, and the autocorrelation at lag Δ counts the peak-pairs separated by Δ. So **the recurring Δm/z (the neutral losses) are the peaks of the power spectrum.** On the ethanol flat chart `[46,45,31,29,27]`: autocorr surfaces Δ1(H), **Δ2(H₂, count 2)**, Δ14(CH₂), Δ15(CH₃), Δ16(O/CH₄), Δ17(OH), Δ18(H₂O) — i.e. **F279's hand-built difference-graph, recovered natively from the FFT.** The flat chart's hidden relational fiber is literally its own autocorrelation; you don't have to build the graph, you transform the chart.

### §B — the library composes multiplicatively (convolution → product) — **DEMONSTRATED**
A molecule's isotope envelope = the **convolution** of its atoms' isotope distributions. FFT turns convolution into multiplication:
- 3-carbon envelope via convolution `[0.96824, 0.03142, 0.00034]` == via `FFT(pC)³` (`match=True`).
- a **(1 C + 1 Cl)** library-composition (product of the C and Cl FFTs) → `[M,M+1,M+2,M+3] = [0.7496, 0.0081, 0.2397, 0.0026]`: **M+1/M = 1.08% decodes 1 carbon**, **M+2/M = 32% = the 3.13:1 chlorine signature.**

So a **fully-projected library of per-element isotope distributions composes by FFT-product** into any compound's envelope, and the envelope **decodes composition.** (This is the field's Rockwood FFT isotope method — no-lineage; the framework reads *why* it works: convolution-diagonalization.)

### §C — synthesis: the un-flattened, no-data-lost representation
Put A+B together and the user's intuition is the whole engine:
- **Matching/deconvolving** a measured flat chart against a known library = **multiplication / cross-correlation in FFT-domain** (convolution → product; mixtures are sums whose components separate by correlation against library FFTs).
- **Nothing is flattened away** — the difference-fiber is the autocorrelation, the composition-fiber is the isotope convolution; both live *in the transform*. The **FFT-domain library is the "fully projected view"** the user named — the representation where the hidden fiber is explicit.
- Ties **R-RBS-LM-28/32** (the framework's FFT-domain *surgical composition across frequency bands*) — the same tool, now applied to mass spectra: the flat chart's bands carry the fiber.

### §D — honest residue (a clean detect/validate split, F266)
The autocorrelation surfaces **all** pairwise differences — including **spurious** ones with no clean neutral (Δ4, Δ19 in the ethanol run). So FFT is the **detector** (it surfaces every recurring Δ as a *candidate*), and **conservation** (the F278 EC-code / neutral-loss table) is the **validator** (which Δ's are real losses). That is exactly the F266 detect-vs-validate structure: the transform detects, the conservation law confirms. Mixture deconvolution at scale (many compounds, instrument broadening) is the forward leg.

### §E — scope
Framework-reading only; **benign textbook examples** (ethanol; abstract C/Cl isotope math); **NO unknown-identification / detection / synthesis capability** — only the math structure. FFT is numpy signal-processing (not a bypassed srmech primitive; the eigen/Laplacian side stays srmech — F279). No-lineage (Wiener–Khinchin, Rockwood FFT isotopes, spectral library matching are the field's; the projection/fiber reading is ours). Class-K (`|F|² = F·conj(F)`, no `abs()`). CAD-ban. Defensive scope.

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (autocorrelation recovers the neutral losses; FFT(p)ⁿ == n-fold convolution exactly; the C+Cl composition decode — reproducible via committed `mass_spec_fft.py`). Confirms the user's FFT guess. No-magic (isotope abundances ¹³C/³⁵Cl/³⁷Cl = attested-B; the neutral-loss Δ's = attested-to-conservation A; the autocorrelation/convolution identities = attested-to-structure A). Class-K. CAD-ban; defensive scope; no-lineage. Single-model / no-twin. Builds on F279 (the difference-graph fiber), F278 (the conservation EC-code = the validator), R-RBS-LM-28/32 (FFT-domain surgical composition). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`; the user's "fiber as spatially-absent encoding" stance.
