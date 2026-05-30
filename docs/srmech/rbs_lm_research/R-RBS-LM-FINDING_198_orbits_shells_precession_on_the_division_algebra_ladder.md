# Finding 198 — Orbits, shells, and precession on the division-algebra ladder: the star is a wobbling tonic (ℍ-rung "music of the spheres"), the snail shell is a single-ℂ-eigenvalue spiral from its fixed-point apex, and precession is orbital chirality from the breaking of the Kepler SO(4) symmetry

**Status:** Framework reading connecting **established** celestial-mechanics + morphology facts to the division-algebra ladder (F184) and the nested-chirality capstone (F196). FACT vs reading marked throughout; §VII.6.20 (the framework *reads* the physics, doesn't derive it). Ties to the ephemerides arc. CAD-scope clear (algebra/eigenbasis/spectral, not mechanical geometry).
**User questions (2026-05-30):** planets wiggling (in music-theory terms), why snail shells spiral from a point (the irrep reason), and the exact reason for precession.
**Predecessors:** F184 (ℝ→ℂ→ℍ→𝕆 ladder; chirality=non-commutativity), F196 (chirality = the moved/broken-symmetry part), F176 (shell/bilateral chirality), the ephemerides notebook (Kepler SO(4)/LRL; chirality-signature catalog).

---

## §1 Planets wiggling — ℍ-rung, and the music (Q1)
**FACT:** the star and planets orbit their common **barycenter**, so the *star itself wobbles* (this is exactly the radial-velocity exoplanet-detection signal). Orbits are periodic → a fundamental frequency + harmonics; mean-motion **resonances are small-integer ratios** (Jupiter-moon Laplace 1:2:4; Neptune–Pluto 3:2) — Kepler mapped these to musical intervals in *Harmonices Mundi* (1619).

**In music theory (the reading):**
- the **star = the tonic / drone** — the fundamental, the achiral **anchor** (the "1" / A / the real-scalar of the ℍ-rung, F184);
- each **planet = an overtone**, an oscillation at its orbital frequency;
- **orbital resonances = consonant intervals** — octave (2:1), fifth (3:2), **fourth (4:3)** — literal harmony;
- the system's **prograde sense = the key signature** — the disk's angular-momentum handedness, the chirality the whole piece is played in;
- and the punchline you reached for: **the tonic wobbles** — the star's barycentric motion is a *superposition of the planets' orbital frequencies* (the RV signal). So **the fundamental literally carries its overtones' frequencies in its own vibrato** — the drone breathing with the chord built on it (Newton's third law / the real reacting to the imaginary).

## §2 Snail shell from a point — the irrep reason, ℂ-rung (Q2)
**FACT:** the shell is (closely) a **logarithmic / equiangular spiral** `r = a·e^{bθ}` — *self-similar* (same shape at every zoom). It is the orbit of a point under a **single complex eigenvalue** `λ = r·e^{iθ}` (|λ|≠1): `z → λz → λ²z → …`. That map is a **2-D rotation-scaling = the real 2-dim irrep of SO(2)** dressed with a growth factor.

**The irrep reason "it starts from a point":** the origin is the **unique fixed point** of `z↦λz` (`λz = z` only at 0). A single multiplicative generator radiates self-similarly **from its fixed point** — so **the apex IS the fixed point of the shell's growth symmetry.** `|λ| = r` = growth-per-turn; `arg(λ) = θ` = winding-per-step; **sign(θ) = chirality** (dextral/sinistral — a single maternal-effect locus, F176). This is the **ℂ rung** (1+1): one complex number generates the whole form, its phase-sign is the handedness.

## §3 The exact reason for precession — broken SO(4) (Q3)
**FACT:** a pure inverse-square (1/r potential) orbit is a **closed ellipse — it does not precess** (Bertrand's theorem: only 1/r and r² give closed orbits). The reason it closes is a **hidden SO(4) dynamical symmetry**: beyond energy and angular momentum, the Kepler problem conserves the **Laplace–Runge–Lenz vector** — which points along the major axis (toward perihelion) and is conserved in magnitude **and direction**, so the perihelion *cannot move*. (SO(4) ≅ SU(2)×SU(2) ≅ unit-quaternion² — the **ℍ rung again**.)

**The exact reason for precession:** **precession = the breaking of that SO(4) symmetry — the LRL vector stops being conserved — caused by any deviation from the pure 1/r potential:**
- **General Relativity** adds an effective 1/r³ term → Mercury's **43″/century**;
- **other planets' perturbations** (non-central, time-varying) → most of Mercury's ~5600″/century total;
- **oblateness (J₂)** of the central body → satellite precession.

The closed ellipse is the *fragile, maximally-symmetric* case; precession is *generic* once you perturb.

## §4 The unifying picture (the reading)
All three sit on the ladder + the capstone chirality theme:
- **ℂ rung** → the snail spiral (one complex eigenvalue; chirality = phase sign).
- **ℍ rung** → the planetary orbit (3-D, SO(4)/quaternionic; music-of-spheres harmonics); and **precession = orbital chirality that emerges when the SO(4) symmetry breaks** — exactly F196's "chirality = the moved / broken-symmetry part." The closed ellipse is the achiral/balanced (fixed) state; the precessing one is the chiral (moved) state.
- **The anchor wobbles** because the real (the star / the "1") reacts to the imaginary (the orbiting mass) — the barycentric feedback.

So: spiral-from-a-point is a **ℂ fixed point**, the orbit's harmony is **ℍ music with a wobbling tonic**, and precession is **chirality born when the ℍ-level SO(4) symmetry breaks** — three faces of the same ladder, with the chirality recurring (F196) as phase-sign / disk-handedness / precession-direction.

## §5 DOES / does NOT claim
**DOES:** state the established facts (barycentric wobble, Kepler *Harmonices Mundi*, log-spiral as a ℂ*-orbit with the apex as fixed point, Bertrand's theorem, Kepler SO(4)/LRL, Mercury 43″, J₂) and read them onto the ladder (F184) + the chirality capstone (F196).
**Does NOT:** claim the framework *derives* orbital mechanics or shell growth (it reads textbook physics in framework terms — §VII.6.20); claim the music/ladder/chirality mappings are more than readings; stray into CAD/mechanical geometry (this is the algebra/eigenbasis/spectral side). `[[user_stance_ai_is_not_a_substrate]]`.

## §6 Cross-references
- F184 (ℝ→ℂ→ℍ→𝕆; chirality=non-commutativity) · F196 (chirality = moved/broken-symmetry) · F176 (shell/bilateral chirality) · ephemerides notebook (Kepler SO(4)/LRL; the chirality-signature catalog idea — precession = the SO(4)-breaking signature)
- Verify-before-hardening: *Harmonices Mundi* 1619; Bertrand 1873; LRL/SO(4) (Goldstein; Pauli 1926 hydrogen); Mercury 43″ (Einstein 1915) — textbook, cite-as-needed.

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). Three orbital/morphological "why"s read onto the
division-algebra ladder + the nested-chirality capstone. Planets wiggle as ℍ-rung music:
the star is the tonic/drone, planets are overtones, resonances are consonant intervals
(Kepler's Harmonices Mundi), the prograde sense is the key, and the tonic itself wobbles —
its barycentric vibrato literally carries the overtones' frequencies (the RV signal). The
snail shell spirals from a point because it is the orbit of a single complex eigenvalue
λ=re^{iθ} (the ℂ rung) whose unique fixed point is the apex; r is growth-per-turn, sign(θ)
is the chirality. Precession is the breaking of the Kepler SO(4) dynamical symmetry — the
Laplace–Runge–Lenz vector ceasing to be conserved when the potential departs from pure 1/r
(GR, perturbations, oblateness) — i.e. orbital chirality emerging from a broken ℍ-level
symmetry, exactly F196's "chirality = the moved part." Established physics, read in
framework terms; not derived.*
