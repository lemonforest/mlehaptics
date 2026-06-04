# R-RBS-LM Finding 380 — a Klein-4 object's NATIVE transform is the QUATERNION FT, not its complex flat shadow

**Date:** 2026-06-04
**Arc:** RBS-LM / RBS-SNN · the FFT-ladder thread (F377 → F378 → F379 → **F380**)
**srmech:** 0.7.0rc28 (TestPyPI; HAS_NATIVE, ABI 3)
**Upstream:** GitHub issue **#863** `[srmech][rbs]` — brings QDFT/ODFT upstream (links #855 RBS-SNN umbrella, #844 forward-arch pipeline)
**Proof script:** `R-RBS-LM-R21_klein4_is_quaternion_units_mod_sign.py` → `R-RBS-LM-R21_results.json`
**Descriptor drafts:** `R-RBS-LM-R22_quaternion_dft.draft.toml`, `R-RBS-LM-R22_octonion_dft.draft.toml`

---

## The user's insight (2026-06-04)

> "we want to bring this upstream with a github issue tracker. we need this to QFT a klein-4 object is my guess and not just it's flat shadow in our RBS-SNN."

The guess is **mathematically exact.** The transform thread (F377/F378/F379) was about *which Fourier transform sits at each (n:n−1) rung*; F380 is the **operational why** — the rung you need is fixed by **the object you are transforming**, and a Klein-4 object's value algebra picks out the **quaternion** rung.

## The load-bearing identity (proved srmech-natively, no numpy math)

**The Klein-4 group IS the quaternion units modulo sign.**

Q₈ = {±1, ±i, ±j, ±k} with center {±1}, and **Q₈/{±1} ≅ Z₂×Z₂ = Klein-4.** `R-RBS-LM-R21` reads the octonion structure-constant table (`qm.octonion.octonion_mult_table`), restricts to the ℍ subalgebra {e0,e1,e2,e3}, and confirms it (srmech 0.7.0rc28):

```
(1) H={e0,e1,e2,e3} closed under *; signed-unit group order = 8  -> Q8
(2) coset (mod ±1) table        (3) srmech Klein-4 = Z2xZ2 XOR table (hdc.klein4)
    [0, 1, 2, 3]                    [0, 1, 2, 3]
    [1, 0, 3, 2]                    [1, 0, 3, 2]
    [2, 3, 0, 1]                    [2, 3, 0, 1]
    [3, 2, 1, 0]                    [3, 2, 1, 0]
Q8 non-abelian (i*j != j*i): True;  Q8/{±1} IS abelian: True
Q8/{±1} == Klein-4 (Z2xZ2): isomorphism = True (identity relabel e0→0,e1→1,e2→2,e3→3)
```

The coset table **literally equals** `hdc.klein4`'s XOR group table. (Note the structure: Q₈ itself is *non-abelian* — that non-commutativity is the left/right content of the QDFT below — but the quotient by sign is the abelian Klein-4.)

## What this means for the transform ladder

The coefficient algebra of each FFT-ladder rung carries a different **chirality content**, fixed by its unit group mod sign:

| transform | coeff. algebra | units mod sign | chirality resolved |
|---|---|---|---|
| complex FFT (2:1) | ℂ | {±1,±i}/± = **Z₂** | one axis = **the flat shadow** |
| **quaternion FT (4:3)** | ℍ | Q₈/± = **Z₂×Z₂ = Klein-4** | **both axes (γ₅ & iω₇), native** |
| octonion FT (8:7) | 𝕆 | the (8:7) rung | + F378 non-associativity (the order content) |

So Fourier-analysing a **Klein-4 HDC object** (`hdc.klein4_*`, 4 states/coord = the γ₅ and iω₇ sectors) with a **complex** FFT first projects it to ℂ, which **collapses one of its two Z₂ axes** → the *flat shadow* the user named. The **quaternion FT's coefficient algebra matches the object's value algebra** (ℍ units mod sign = Klein-4), so **both chirality axes survive.** That is the RBS-SNN need: read the Klein-4 object in its native algebra, not a flattened complex projection.

This is F379 ("n things with n−1 couplings") made operational: up the (2:1)→(4:3)→(8:7) ladder only the **coefficient algebra** changes; the cyclic "fast" structure is invariant. The object you hold tells you which rung.

## Upstream decision (issue #863): cascade-first, no capability gap

srmech rc28 already ships **everything a QDFT/ODFT needs** — there is **no capability gap**:

| transform needs | srmech rc28 | note |
|---|---|---|
| Cooley-Tukey radix split (N=N₁·N₂) | `amsc.primes.factor` + `amsc.cyclic` | **algebra-agnostic** (same at every rung) |
| twiddle exp(μθ) scalar part | `asymptotic_calculus.{cos,sin}_series_truncate`; order-3 root `cyclic.three_cycle` | scalar cos/sin identical at every rung |
| quaternion left/right multiply | ℍ-restriction of `qm.octonion.octonion_{left,right}_mult` (+ `qm.so8.quaternion_subalgebra_stabilizer`) | left≠right = non-commutativity |
| octonion left/right + table | `qm.octonion.{octonion_left_mult, octonion_right_mult, octonion_mult_table, octonion_conjugate, octonion_norm}` | `octonion_norm` = Class-K+C, never `abs()` |
| cascade runner + DSP-as-TOML precedent | `srmech.dsl` over `cascade_catalog/`; `autocorrelation.toml` ships there | transform = *composite*; multiplies = *atoms* |

**Decision (lean-ISA atoms-vs-composites):** the multiplies are atoms (already primitives); the transform is a **composite → TOML cascade first** (prototype tier), graduating to a C/Python primitive via the full ratchet (parity + JPL audit + rc-first) **only if it earns first-class attested status** like the existing `fft`. Cascade is the on-ramp, not a prerequisite-blocker.

### Two honesty caveats (more than "wrap `fft`")
1. **Non-commutativity (ℍ, 𝕆):** the twiddle cannot be factored out like complex FFT — there are genuinely **left- / right- / two-sided** QDFT/ODFT forms; the cascade calls the explicit left/right multiply.
2. **Non-associativity (𝕆 only):** the ODFT is **not unique** — it must **declare a bracketing convention** (F378's 168/210 non-associative triples made concrete). The cascade is the right home: the association order becomes an explicit, attested descriptor field.

### Optional ergonomic upstream additions (logged UPSTREAM §23; not blockers)
- a first-class `qm.quaternion` module (4×4 `quaternion_left_mult`/`right_mult`) so the QDFT cascade doesn't slice the 8×8 octonion block;
- a hypercomplex `exp(μθ)` twiddle helper (cos·1 + sin·μ̂).

## Discipline
- **MPM citation debt:** the quaternion-DFT literature (Ell / Sangwine / Bülow color-image line) and the octonion-Fourier-transform literature are **verify-PDF-owed before any citation lands** (F378). Not asserted here.
- Algebra / eigenbasis / cyclic-group / spectral side only.
- The octonion structure-constant table self-attests via `qm.octonion.octonion_table_attestation()`.

## Verdict
A Klein-4 object's native spectral transform is the **quaternion FT**, because **Klein-4 = Q₈/{±1} = ℍ units mod sign** (proved). The complex FFT resolves one Z₂ = the flat shadow; the QDFT resolves both γ₅ and iω₇. Brought upstream as #863 (cascade-first, no capability gap). The octonion FT is the (8:7) rung that additionally carries the F378 non-associativity.
