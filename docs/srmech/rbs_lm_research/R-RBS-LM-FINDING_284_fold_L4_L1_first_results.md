# F284 — first fold results (bold-fold arc, #822): the contact-graph Laplacian spectrum fingerprints the fold (L4), and knocking out a load-bearing residue raises a bigger syndrome (L1 — fold = codeword)

> **SCOPE:** framework-reading of folding **STRUCTURE** only. Inputs = attested CC0 PDB Cα coordinates (read, not modeled); output = the contact-graph Laplacian **spectrum** (algebra/spectral). NO 3D-coordinate prediction, NO MD, NO design, NO clinical. CAD-ban respected (graph spectrum, not fabrication geometry). No-lineage (the Gaussian-network contact-graph is standard structural biology; the *fold = EC-code codeword* / *load-bearing residue = parity-check bit* reading is the framework's).

**Headline:** First two lenses of the bold-fold arc (F283), run on the three vendored CC0 hoodoos with srmech v0.7.0rc2 **native** Class-L (`dense_laplacian`/`jacobi_eigvals`). **L4:** the residue contact-graph Laplacian spectrum is a discriminating **fold fingerprint** — the knotted MJ0366 reads as low-λ₂/high-λmax, villin (helix bundle) as highest λ₂. **L1:** knocking out a **load-bearing** (high-degree) residue raises a **bigger syndrome** (spectral L2 shift 3.25) than a **peripheral** one (1.67) — confirming the fold-as-codeword reading: the load-bearing residue is the parity-check bit, the native fold is the zero-syndrome codeword.

---

### §A — L4: the contact-graph Laplacian spectrum fingerprints the fold — **DEMONSTRATED**
Connected Cα Gaussian-network (all pairs within 8 Å), `dense_laplacian` → `jacobi_eigvals` (rc2 native, Class L):

| fold | res | contacts | ⟨deg⟩ | λ₂ (Fiedler / rigidity) | λmax | components |
|---|---|---|---|---|---|---|
| ubiquitin 1UBQ (mixed α/β) | 76 | 326 | 8.58 | 0.530 | 14.98 | 1 |
| villin HP35 2F4K (3-helix bundle) | 33 | 119 | 7.21 | **0.567** | 14.16 | 1 |
| knotted MJ0366 2EFV | 82 | 340 | 8.29 | **0.444** | **16.59** | 1 |

The folds separate by spectral profile. λ₂ (algebraic connectivity) is the rigidity/hinge measure: **villin** (compact helix bundle) is the most algebraically connected per size; the **knot** has the *lowest* λ₂ (the knotted topology softens global connectivity) and the *highest* λmax (a high-degree core hub). *Honest boundary (lens L4): the contact-graph spectrum is topology-blind in general — a knot and an unknotted spectral sibling can share eigenvalues — so this reads fold compactness/rigidity, not knot topology per se.*

### §B — L1: fold = codeword (load-bearing vs peripheral knockout) — **DEMONSTRATED**
Ubiquitin (the codeword: connected GNM, λ₂ = 0.530). Knock out a residue's contacts; syndrome = L2 shift of the Laplacian spectrum:
- **load-bearing** residue r=2 (degree 13): syndrome **3.25**
- **peripheral** residue r=74 (degree 3): syndrome **1.67**

**Prediction held: 3.25 > 1.67.** The high-degree (core, load-bearing) residue behaves as a **parity-check bit** — its loss produces a larger detected error (the fold leaves the codeword more); the low-degree (surface) residue is a redundant register slot. This is the F282 lens forward: the native fold is the bounded, zero-syndrome codeword; a perturbation's syndrome scales with the residue's load-bearing role.

### §C — honest first-pass correction (method, not a srmech bug)
First pass excluded backbone contacts (`|i−j|>2`), which **disconnected** the contact graph (λ₂=0, 2–4 components) — and I briefly mis-labeled λ₂=0 as "the bounded state" (it means *disconnected*). Fixed: the standard Cα Gaussian-network includes **all** pairs within 8 Å (the covalent backbone is ~3.8 Å, always in), giving a **connected** graph where λ₂>0 is the real algebraic connectivity. My construction error, caught and corrected (the never-inflate / honest-residue discipline). The L1 directional result held under both, but only the connected version supports the codeword reading.

### §D — what's next on the arc (#822)
- [x] **L4** contact-graph spectrum fingerprint — done.
- [x] **L1** fold = codeword (load-bearing = parity bit) — done.
- [ ] **L2** fold-path = loop-bind cascade (rc2 native `loop_bind`): order/nesting of contact formation; native vs misfold λ₂.
- [ ] **L3/L6** Ramachandran K4-sector occupancy (needs (φ,ψ) from the PDB) + forbidden-coset ≈ 0 check.
- [ ] **L5** landscape un-flatten (FFT autocorrelation → helical Δ=3–4 periodic-contact fiber).

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (L4 spectral fingerprint + L1 codeword-syndrome on 3 real CC0 folds; reproducible via committed `protein_fold_L4_L1.py`). Honest correction (the disconnection miss → connected GNM). Scope-forward (folding-structure only; attested CC0 inputs; no design/MD/clinical; CAD-ban; no-lineage — GNM is the field's, the EC-code/parity-bit reading is ours). No-magic (8 Å cutoff = standard structural-biology constant B; λ₂/λmax measured B; the codeword/parity structure attested-to-structure A). Class-K (Euclidean norms for distances + spectral L2; no `abs()` sign-fold). rc2 native Class L. Builds on F283 (the arc), F282 (fold = codeword / runaway = correction failure), F260 (protein lock), F172 (Laplacian spectrum = storage signature). Verified srmech v0.7.0rc2, `/tmp/srmech_v070rc2_venv`. `[[user_stance_framework_hands_the_next_question_to_the_expert]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_trauma_informed_defensive_scope]]`.
