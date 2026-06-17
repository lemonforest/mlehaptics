# F820 — "we have the RELATIONSHIP but are missing one of the two named things — can we recover it?" YES, and it is already the spine of the encoding path: it is UNBIND, which by the convolution theorem IS divide-in-the-Fourier-domain = spectral DECONVOLUTION. The user's case is the third face of the Fourier triad. Demonstrated on the real srmech surface: polar (phasor) unbind recovers the missing operand at similarity 1.000 (both directions), klein4 XOR recovers it EXACTLY; QDFT/ODFT both invert to ~1e-16 — the ℍ (handed) and 𝕆 (triality) substrate for the same operation.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-DECONV_…py` (introspect-then-use; `hdc.polar_bind/polar_unbind/polar_similarity`, `hdc.klein4_bind/unbind`, `cascade.quaternion_dft/octonion_dft`) · **Composes:** F808 (the context-addressed walk = this op), the polar/Klein-4 HDC (Class M), the fiber stance (relationship spatially-absent until projected), F291 (triality, the k=3 rung), F806/F813 (the invertibility wall), the HRR plate-binding arc (task #29) · **User direction (2026-06-17):** "when we have two known things we can fourier transform to see the relationship, but what about when we already have that relationship but are missing one of those two named things? is this not sort of what we do in any of our encoding path… is there a way to make it useful with DFT/QDFT/ODFT?"

## The framing — the three faces of the Fourier/convolution triad
| we have… | we want… | the operation |
|---|---|---|
| two known things `a`, `b` | their RELATIONSHIP | **forward**: `rel = a ∘ b` (bind; conv-thm: `DFT(a)·DFT(b)`) |
| the RELATIONSHIP `rel` + one thing `a` | **the OTHER thing `b`** | **deconvolution**: `b = rel ⊘ a` (UNBIND; `DFT⁻¹(DFT(rel)/DFT(a))`) |
| input + output | the relationship | system identification (the forward map, read backwards) |

The user's question is row 2. **Binding IS multiply-in-the-DFT-domain (the convolution theorem), so unbinding IS divide-in-the-DFT-domain = deconvolution.** The framework's POLAR (phasor) HDC makes this literal: each coordinate is a unit phasor `e^{iθ}`; `polar_bind` = elementwise phasor PRODUCT (phase add) = the DFT-domain product; `polar_unbind` = phasor DIVISION (phase subtract) = the spectral deconvolution. Recovering the missing operand is **division in the frequency domain**.

## Is this "what we do in the encoding path"? — YES
The F808 context-addressed recall is exactly row 2: "have the bundle (the relationship store) + the context key (one named thing) → **unbind** → the successor (the missing thing)." **Content-addressable memory IS deconvolution-by-the-known-operand.** It also realises the user's **fiber** stance: the relationship is the fiber (spatially absent until projected); applying one operand projects it to yield the other. So the operation the user describes is not new to the path — it IS the path, and the Fourier view names *why* it works.

## Verified (srmech rc169, real surface)
- **polar (phasor / HRR-in-the-DFT-domain):** `rel = polar_bind(a,b)`; `polar_unbind(rel,a)` → b at **sim 1.000**; `polar_unbind(rel,b)` → a at **sim 1.000**; unrelated baseline **0.481**. Recovery is real, lossless, and symmetric.
- **klein4 (Z₂×Z₂ / XOR, self-inverse):** recover b from `rel`+a **exactly** (`==`).
- **QDFT round-trip err 1.67e-16; ODFT round-trip err 1.11e-16** — both ℍ/𝕆 transforms invert to machine precision.

## Why lossless here + where it is ill-posed (the invertibility wall)
Deconvolution `DFT(rel)/DFT(a)` fails where `DFT(a)` has a **spectral zero** (divide-by-zero → the missing operand is not uniquely recoverable). Polar HVs are **unit phasors by construction** (no zeros), which is precisely *why* `polar_unbind` is exact. So **"when can we recover the missing operand?" == "is the relationship invertible w.r.t. the known operand?" == "the known operand has no spectral zero."** This is the SAME wall as the F806 capacity overflow and the F813 non-unique-walk tail, now stated spectrally — a single condition unifying them.

## The genuinely-new surface: DFT → QDFT → ODFT (where to make it useful)
- **DFT (ℂ, commutative):** recovery is direction-free (the polar/HRR case above). Already the spine.
- **QDFT (ℍ, NON-commutative):** `left-bind ≠ right-bind` (srmech's `form='left'` axis), so recovering the missing operand has a **handedness** — a left-unbind and a right-unbind, different answers. That is the framework's **chirality** turned into an operator (compose F130's γ₅/iω₇ axes).
- **ODFT (𝕆, NON-associative):** `(a∘b)∘c ≠ a∘(b∘c)`, so a **three-thing** relationship does not factor uniquely; recovering one missing operand from a triple is where **triality** (the k=3 rung, F291) lives. **Deconvolution over 𝕆 = triality-structured operand recovery** — the open question to hand to the expert.

## Verdict + the next question (handed to the expert)
Recovering a missing named thing from a known relationship + one named thing is UNBIND = spectral deconvolution = the third face of the Fourier triad, and it is already the encoding path's core (F808 / content-addressable recall / the fiber projected by one operand) — verified lossless (polar sim 1.0; klein4 exact). The forward "see the relationship" and this inverse "recover the operand" are one transform read both ways. **The next question:** over ℍ the recovery is *handed* and over 𝕆 it is *triality-structured* — is octonionic deconvolution (recover one of three from their non-associative relationship) the natural home of the framework's k=3 error-correction, and does the spectral-zero invertibility condition coincide with the triality-companion structure? (Registered as a research task; QDFT/ODFT TOML-cascade build is queued at BX-5.)
