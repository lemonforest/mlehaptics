# F892 (thread 2) — The amplitude-collapse (the null getting DARKER, F890) is precisely the 1/√N degeneracy law: signal ≈ 0.43·N^(−0.47) (asymptotically N^(−0.474)), floor = the ~0.25 Klein-4 chance level, and the Chandrasekhar collapse threshold N* (signal lost in the floor = the dark-star transition) extrapolates to ~3k–36k binds. F890 showed the real scale law is amplitude collapse (capacity, not gravity). Fitting recall amplitude vs load N (10-reference average, clean): the **signal (amp − floor) follows a power law signal ≈ 0.43·N^(−0.47)** — asymptotic (N≥16) **N^(−0.474)** — i.e. **the 1/√N capacity/degeneracy law** (F871) measured precisely. The **floor is steady at ~0.25** (the Klein-4 four-sector chance level), independent of load. Within the measured range (≤512 binds) the signal is still recoverable (0.023 at N=512, well above the ~0.003 floor scatter), so the **Chandrasekhar collapse threshold N*** — where the recall signal sinks irrecoverably into the chance floor (the dark-star / over-stuff transition, F870/F876) — **extrapolates to ~2,800 (signal<0.01) → ~36,000 (signal<0.003) binds**. The substrate's "degeneracy pressure" is therefore **∝ N^(−1/2)** — the framework-native HDC exponent, NOT the stellar polytrope (4/3) — and the dark-star collapse is **structurally Chandrasekhar** (a critical load beyond which the bound structure can no longer support itself against the noise floor).

**Date:** 2026-06-20 · **srmech:** 0.9.0rc11 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-892_chandrasekhar_amplitude_collapse_fit.py`, `simplewiki_v082`, load 1→512, 10-ref average, log-log fit · **Composes:** F890 (amplitude collapse = the real scale law — now fitted), F871 (capacity ~ 1/√N — confirmed precisely, p=0.47), F870 (over-stuff cliff = the collapse), F876 (the null = inverse of information = the floor), RESEARCH_QUEUE Q2b (Chandrasekhar = the fermionic/degeneracy form of the info-density limit — now given an exponent + threshold) · **User direction (2026-06-20):** "fit the amplitude-collapse-vs-load to the Chandrasekhar/degeneracy form (Q2b)."

## Measured (sparse, srmech-native; 10-ref avg)
| N (load / "mass") | recall amp | floor | signal = amp − floor |
|---|---|---|---|
| 1 | 1.0000 | 0.249 | 0.751 (degenerate: perfect self-recall) |
| 4 | 0.4720 | 0.252 | 0.220 |
| 16 | 0.3680 | 0.249 | 0.119 |
| 24 (≈ the F871 wall) | 0.3441 | 0.250 | 0.094 |
| 64 | 0.3137 | 0.250 | 0.064 |
| 128 | 0.2962 | 0.253 | 0.043 |
| 256 | 0.2840 | 0.256 | 0.028 |
| 512 | 0.2775 | 0.254 | 0.023 |
- **Fit:** signal ≈ **0.43·N^(−0.472)**; asymptotic (N≥16) **N^(−0.474)** → the **1/√N (p=0.5) degeneracy/capacity law** (F871), measured.
- **Floor:** steady ~0.25 (Klein-4 4-sector chance), load-independent — the "dark" level the signal collapses toward.
- **Chandrasekhar threshold N\*** (extrapolated, signal < floor-scatter): ~**2,830** (<0.01) · ~**12,200** (<0.005) · ~**35,800** (<0.003) binds.

## Reading
- **The dark-star collapse is the 1/√N degeneracy law.** Each binding adds orthogonal "pressure," but the recall SNR dilutes as **N^(−1/2)** — the framework's degeneracy-pressure exponent. The null gets *darker* (signal → floor) with load, exactly F890's "amplitude collapse, not gradient softening."
- **N\* = the substrate's Chandrasekhar mass.** The load where the signal can no longer be told from the chance floor = the dark-star / over-stuff transition (F870/F876). It is **structurally** the Chandrasekhar limit (a critical collapse load), with the **HDC 1/√N exponent**, not the stellar 4/3 polytrope — the analogy is the *critical-collapse shape*, not the equation of state.
- **Closes the AGN/scale arc (F890):** the scale law is this degeneracy collapse (the null darkens at 1/√N toward N\*), NOT the gravitational 1/M² tidal gradient. The boundary *gradient* is scale-invariant (F890); the *amplitude* collapses at 1/√N (here) — two distinct, both-measured scale behaviours.

## Honest scope
- **N\* is extrapolated** — at the largest measured load (512) the signal is still recoverable (0.023), so the collapse threshold is a power-law extrapolation (~3k–36k depending on the floor-noise cutoff), not a directly observed collapse. The **exponent p ≈ 0.47–0.474 is robust** (10-ref average, clean monotone).
- The N=1 point is the degenerate perfect-recall case (excluded from the fit). Floor scatter (~0.003) sets N\* loosely.
- Sparse held: `klein4_bundle`/`bind`/`unbind`/`similarity`; `Q` collapsed only at the analysis boundary; no dense, no numpy, no bag.

## Verdict / next
The amplitude-collapse is **precisely the 1/√N degeneracy law** (signal ≈ 0.43·N^(−0.47); asymptotic N^(−0.474) = F871's capacity exponent), the floor is the Klein-4 chance level (~0.25), and the **Chandrasekhar collapse threshold N\*** (dark-star transition) extrapolates to **~3k–36k binds**. The substrate's degeneracy pressure ∝ N^(−1/2) is framework-native (not stellar); the Chandrasekhar analogy is the critical-collapse *shape*. With F890 this closes the scale picture: **gradient scale-invariant, amplitude collapsing at 1/√N toward a Chandrasekhar N\*.** **Next:** (1) reach N\* directly (push load to ~10⁴ with native sims to *observe* the collapse, not extrapolate); (2) does chunking (F872) raise N\* — i.e. is the chunked-M's Chandrasekhar mass higher (more pages before collapse)?; (3) attest the Chandrasekhar constants (Q2b no-magic). Framework reading → srmech measurement; the degeneracy exponent measured; the collapse threshold framed honestly as extrapolated.
