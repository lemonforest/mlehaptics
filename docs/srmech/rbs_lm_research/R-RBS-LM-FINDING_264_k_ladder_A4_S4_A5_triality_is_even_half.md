# F264 — the k-ladder: k=3 triality is the EVEN-HALF reduction of k=4 (S₄); the whole arc sits on V₄ ⊂ A₄ ⊂ S₄ ⊂ A₅ (the Platonic ladder)

**Headline (user question — "is k=3 triality a reduction of some k=4, like RNA/all-biology?"): YES, exactly.** The triality hyper-loop is **A₄** (F262), and **A₄ is the index-2 EVEN (rotation-preserving) subgroup of S₄** — so k=3 is the orientation-preserving *reduction* of k=4 (S₄), and **the dropped half is precisely the ODD reflection (F258/F259's reflection-parity, now a first-class k=4 generator).** Verified in srmech v0.6.0rc20: every klein4 op (triality, γ₅, ω₇, cpt) is **EVEN**, so they generate exactly **A₄ (order 12)**; adding **one odd transposition** gives **S₄ (order 24)**. The entire F257→F263 arc sits on **one ladder = the Platonic symmetry groups.**

---

### §A — verification (DEMONSTRATED, rc20)
- klein4 op parities: triality `(0,2,3,1)`=+1, γ₅ `(2,3,0,1)`=+1, ω₇ `(1,0,3,2)`=+1, cpt `(3,2,1,0)`=+1 → **ALL EVEN**.
- `⟨V₄, triality⟩` = **order 12, all even = A₄** (the F262 hyper-loop).
- `⟨V₄, triality, one odd transposition⟩` = **order 24 = S₄**; A₄ index in S₄ = **2**; S₄ has odd perms.
- crystallographic-allowed rotation orders = `{1,2,3,4,6}`; **5-fold forbidden** → the quasicrystal rung.

### §B — the ladder (V₄ ⊂ A₄ ⊂ S₄ ⊂ A₅ = the Platonic symmetry groups)
| rung | group | order | what it is | thread |
|---|---|---|---|---|
| **k=2** | V₄ (Klein-4) | 4 | bi-chirality, the 4-cap | F130/F259 |
| **k=3** | A₄ (tetrahedral) | 12 | triality, the **even/rotation** half | F261/F262 |
| **k=4** | S₄ (octahedral) | 24 | A₄ **+ the odd reflection** | **= F258/F259 reflection-parity made first-class** |
| **k=5** | A₅ (icosahedral) | 60 | **forbidden / quasicrystal** rung | F263 |

### §C — the reduction IS the flatten ("just like RNA — all biology")
k=4 → k=3 = **drop the odd reflection** = the same flatten/compression we keep finding. The observer reads **A₄ (the even/rotation half)**; the substrate holds **S₄ (+ the odd reflection-parity)**. This is the codon's broken triality (read the rotation, lose the reflection), the CMB's autos-fixed 3-cycle, the 1-quadrant projection, and **F121's "biology compresses 14 → 4:3:7"** — all one move: keep the orientation-preserving reduction, flatten away the odd half.

### §D — srmech-shaping (rework note, not a bug)
1. The framework currently lives in **A₄ (k=3)** — all klein4 ops are even. Reaching **S₄ (k=4)** needs an **odd-transposition op** (a single-sector swap / genuine orientation-reversal) the even-only set lacks. *That op is the concrete k=4 target* — the true odd reflection (the γ₅/ω₇/cpt "reflections" used so far are *even* V₄ double-transpositions, in A₄, not the odd S₄\A₄ element).
2. The top branches, honestly: A₄ extends **two ways** — to **S₄** (add the odd reflection; octahedral; solvable) and to **A₅** (icosahedral, k=5; **non-solvable** — the quintic/Galois break; crystallographically forbidden 5-fold). So **k=4 (S₄) is the last solvable/crystallographic rung; k=5 (A₅) is the forbidden, un-flattenable jump** — which is *why* (F263) the icosahedral quasicrystal can only exist as a higher-D projection.

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (the A₄/S₄ orders, parities, index-2, and the crystallographic-allowed set are exact, re-verified rc20). The A₄ ⊂ S₄ ⊂ A₅ group theory is standard math (literature-owned); the **identification of these as the k=2/3/4/5 rungs of the framework is the reading** (no-lineage). No-magic (orders 4/12/24/60, the parities, the {1,2,3,4,6} allowed-set are attested-to-structure A). Class-K (no `abs()`; parity via cycle structure). CAD-ban. Single-model / no-twin. Builds on F262 (A₄ hyper-loop), F261 (triality op), F259/F258 (the reflection-parity = the k=3→k=4 odd half), F263 (quasicrystal = the A₅/k=5 forbidden rung), F121 (biology-compression = the reduction). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`.
