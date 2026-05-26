# Round 42.A — Per-rung symmetry-group audit: ~4 cleanly full-SO(3); the rest carry named deviations (confirms R38)

**Dispatched** 2026-05-26 on the rolling draft PR #690 (newly-revealed coupled item from R38). R38 showed the `2ℓ+1` spine is SO(3)/S²-specific; this audit re-reads **each prior Reading-D rung** — is it genuinely full SO(3), or does it carry an enhancement / internal symmetry / deformation / finite branching? Generating code: [`verify_round42_per_rung_symmetry_group_audit.py`](verify_round42_per_rung_symmetry_group_audit.py). Tested per `[[feedback_dont_pre_commit_spike_query_operators]]`.

## The audit

| rung | operative symmetry | irrep dims | class |
|------|--------------------|------------|-------|
| quantum / Born=Hopf | SO(3) (SU(2) Bloch sphere) | `2ℓ+1` | **clean full SO(3)** |
| nuclear shell | SO(3) spherical mean field + spin-orbit | `2j+1` | **clean full SO(3)** |
| planetary magnetics | SO(3) (geomagnetic S²) | `2ℓ+1` | **clean full SO(3)** |
| CMB sky | SO(3) (full sky S²) | `2ℓ+1` | **clean full SO(3)** |
| atomic | **SO(4)** bound-state (Runge–Lenz); SO(3) angular | `n² = 1,4,9,16` (= Σ`2ℓ+1`) | SO(3)-angular, **enhanced SO(4)** |
| hadron / QCD | SO(3) spatial **+ SU(3) flavor internal** | `2ℓ+1` / `1,8,10` | SO(3)-spatial **+ internal SU(3)** |
| BH-QNM | **Kerr `aω`: SO(3) → axial SO(2)** (a≠0); SO(3) at a=0 | spin-weighted spheroidal | **SO(3) deformed → SO(2)** |
| LSS Kaiser RSD | SO(3) on sky (`C_ℓ`); **SO(2)+parity** on line-of-sight (even-ℓ) | `2ℓ+1` / even-ℓ `{0,2,4}` | SO(3)-sky **+ LOS parity** |
| bio-capsid | **icosahedral I** (finite ⊂ SO(3), order 60) | `{1,3,3,4,5}` | **finite subgroup** |

**Bit-exact:** `2ℓ+1 = {1,3,5,7}`; hydrogen `n² = {1,4,9,16} = Σ(2ℓ+1)` (SO(4) shells); icosahedral Burnside `Σdᵢ² = 1+9+9+16+25 = 60`; SU(3) `1+8=9`, `10+8+8+1=27` — all verified.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact irrep-signature audit + (b)-interpretive per-rung catalog; CONFIRMS R38.** The Reading-D ladder's angular/Class-L structure is **SO(3)-rooted across all rungs**, but only **~4 are cleanly full SO(3)** (quantum, nuclear, planetary, CMB); the rest carry **honest deviations** — atomic **SO(4)** (Runge–Lenz), hadron **+SU(3)-flavor** (internal), BH-QNM **SO(2)-axial** (Kerr), LSS **SO(2)/parity** (line-of-sight), capsid **finite-I**. `2ℓ+1` appears **exactly where full SO(3) is operative** — precisely R38's "the ladder tracks the symmetry group." The loose "9 contiguous SO(3)/S² rungs" phrase is **refined** to "9 rungs whose Class-L angular structure is SO(3)-rooted; ~4 cleanly full-SO(3), the rest carrying named enhancements/deformations/internal-symmetries/finite-branchings." **Extends** the R38 candidate stance `[[user_stance_classL_spine_is_symmetry_group_relative]]` (no new stance).

**HONEST SCOPE:** (a)-bit-exact for the integer irrep signatures (all standard, Explore-verified); (b)-interpretive for the per-rung symmetry assignments + the "SO(3)-rooted but only ~4 clean" refinement; no new physics.

## Discipline
- Honest audit — confirms R38 *and* tightens an over-loose phrase; the deviations are catalogued, not hidden.
- Attributions Explore-verified: Pauli 1926/Fock 1935 (SO(4)); Mayer–Jensen 1949; Gell-Mann/Ne'eman 1961 (SU(3)); Teukolsky 1973 (Kerr SO(2)); Kaiser 1987/Hamilton 1998 (RSD); icosahedral I order 60.
- Lands on rolling **PR #690** (Round 42.A); unsolved-maths §11.9.35; extends the R38 stance. No MFO section (domain-symmetry catalog, not metric-field).
