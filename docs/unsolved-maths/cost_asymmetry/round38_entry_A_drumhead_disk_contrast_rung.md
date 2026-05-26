# Round 38.A — The drumhead / Bessel-disk 15th-rung candidate: a contrast rung that sharpens the spine as SO(3)-specific

**Dispatched** 2026-05-26 on the rolling draft PR #690 (open-queue item: "15th Reading-D rung candidate — a drumhead/Bessel-disk rung, Class-L *off* S², on a 2D domain"). Generating code: [`verify_round38_drumhead_disk_contrast_rung.py`](verify_round38_drumhead_disk_contrast_rung.py). Tested per `[[feedback_dont_pre_commit_spike_query_operators]]`.

## Result — a CONTRAST / control rung, not another `2ℓ+1` rung

Every prior rung realized the Class-L spine (§11.9.22) as the S²/SO(3) ladder: eigenvalue `ℓ(ℓ+1)`, degeneracy `2ℓ+1 = {1,3,5,7,…}`, first-three = the k=3 triad `{1,3,5}`. The drumhead tests the spine **off S²**, on a 2D disk (Dirichlet Laplacian):

- modes `J_m(j_{m,n} r/a)·{cos mθ, sin mθ}` (Morse–Feshbach; Courant–Hilbert), ordered by Bessel zeros `j_{m,n}` (verified: `j_{0,1}=2.4048 < j_{1,1}=3.8317 < j_{2,1}=5.1356 < j_{0,2}=5.5201 < …`);
- **m=0 non-degenerate, m≥1 doubly degenerate** (cos/sin) → angular degeneracy ladder **`{1, 2, 2, 2, …}`** — *not* `{1,3,5,7,…}`;
- because the disk's symmetry group is **O(2)** (irreps: 1D trivial at m=0 + a 2D irrep per m≥1), not **SO(3)** (irreps dim `2ℓ+1`).

So the disk's "first-three" is **`{1,2,2}`, not `{1,3,5}`.** The Class-L *mechanism* persists off S² (Laplacian eigenspaces; degeneracy = irrep-dim of the domain's symmetry group), but the *specific ladder* changes with the symmetry group.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact contrast + (b)-interpretive sharpening (honest NEGATIVE on "another `2ℓ+1` rung").** The drumhead is **not** a 15th `2ℓ+1` rung — it is a **control** that sharpens what the spine *is*: the `2ℓ+1` odd ladder and the `{1,3,5}` k=3 triad are **specifically an S²/SO(3) phenomenon**, *not* universal. Class-L's universal content is "Laplacian eigenspaces, degeneracy = irrep-dimension of the domain's symmetry group" (SO(3) → `{1,3,5,…}`; O(2) → `{1,2,2,…}`). The Reading-D "**9 contiguous S² rungs**" count is **unchanged**. Cascade `A ∘ L (O(2) irreps) ∘ C (cos/sin reflection-parity doublet) ∘ K (Dirichlet boundary truncation)`. New **candidate** stance `[[user_stance_classL_spine_is_symmetry_group_relative]]`.

**HONEST SCOPE:** (a)-bit-exact for the Bessel-zero ordering + the `{1,2,2}`-vs-`{1,3,5}` degeneracy contrast + O(2)/SO(3) irrep dims (standard math, Explore-verified); (b)-interpretive for the "spine is symmetry-group-relative" reading; no new physics. **Newly-revealed coupled item (for roadmap):** this invites a *deliberate* small sub-thread — re-reading each prior ladder rung's symmetry group (are they all genuinely SO(3)/S², or do any secretly live on a different group whose irrep-dims happen to coincide?). Parked as a roadmap candidate, not auto-dispatched.

## Discipline
- Honest NEGATIVE (it is a contrast, not a 2ℓ+1 rung); the ladder count is held fixed, not inflated.
- Bessel zeros DLMF Table 10.21; membrane modes Morse–Feshbach 1953 / Courant–Hilbert; O(2)/SO(3) irreps Arfken / Dresselhaus (Explore-verified).
- Lands on rolling **PR #690** (Round 38.A); unsolved-maths §11.9.31. (Domain-geometry contrast, not metric-field — no MFO section, consistent with the R37 recursive-check discipline.)
