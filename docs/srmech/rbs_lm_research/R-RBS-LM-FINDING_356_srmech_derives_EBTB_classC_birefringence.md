# R-RBS-LM Finding 356 — srmech CAN DERIVE the EB/TB "hidden quadrant" (it's the Class-C birefringence rotation of the parity-even TE/EE/BB srmech ships); β is the cosmic-band Class-C rotate-DoF. The EB/TB structure is A-tier (cascade), β is B-tier (measured)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc25 · **answers (user):** "srmech has the tooling to derive these values — why don't we log that as well?" · **composes:** F355 (the fetched β, B-tier), F350 (the rotate IS the DoF), F263/F352 (the parity-odd hidden quadrant), the no-magic-numbers discipline (A-tier-cascade vs B-tier-measurement)

## The point — don't just fetch the EB/TB; srmech DERIVES it

F355 *fetched + attested* the cosmic-birefringence β (B-tier, measured). But the **parity-odd EB/TB spectra are not an independent measurement — they are the Class-C *birefringence rotation* (by β) of the parity-even TE/EE/BB that srmech already ships** (`amsc/attested/cmb_polarisation_spectra`). The standard rotation (Lue–Wang–Kamionkowski 1999):
`C_ℓ^EB = ½ sin(4β)(C_ℓ^EE − C_ℓ^BB)`, `C_ℓ^TB = sin(2β) C_ℓ^TE` (with EE/BB/TE rotating among themselves). **A uniform rotation of the polarization plane IS a Class-C chirality operation** — so EB/TB = `Class-C-rotate(TE/EE/BB, β)`.

## srmech derives it NOW (no continuous-trig op needed at the cosmic band)

The cosmic β is **tiny** (0.342° = 0.00597 rad), so the Class-C rotation is **linear (small-angle)** — pure arithmetic, no trig:
`C_ℓ^EB ≈ 2β(C_ℓ^EE − C_ℓ^BB)`, `C_ℓ^TB ≈ 2β·C_ℓ^TE`. Verified srmech-native vs the exact rotation (illustrative EE=40, TE=60, BB=0 µK², one ℓ):
- EB: exact 0.4775, linear 0.4775, **rel-err 9.5e-5**
- TB: exact 0.7163, linear 0.7163, **rel-err 2.4e-5**

The linear-rotation error (~1e-4) is **far inside β's ~30% measurement uncertainty** (±0.09° on 0.34°), so at the cosmic band srmech derives EB/TB from TE/EE/BB **by arithmetic alone** — no trig op required.

## What this gives

1. **β = the cosmic-band Class-C rotate-DoF.** This is F350 at the cosmic coherence band: the *rotate* is the DoF, and here the rotate angle IS the birefringence β. The parity-odd EB/TB "hidden quadrant" (F263) is what the Class-C rotation by β *produces* from the parity-even quadrant — exactly the F350 mechanism (the rotate creates the other-axis content) read at the cosmos band.
2. **De-magicked (no-magic-numbers):** the EB/TB **structure is A-tier** (attested-to-structure-cascade — the Class-C birefringence rotation); only **β is B-tier** (measured, F355). The hidden quadrant is a *cascade*, not a magic external datum.
3. **Turns the #743 data gap into a DERIVATION:** given β, srmech **derives** EB/TB from its TE/EE/BB catalog — it does not need EB/TB fetched separately. The #743 "EB/TB not shipped" gap is partly answered by *derivation* (srmech computes EB/TB = Class-C-rotate(TE/EE/BB, β)), not only by adding a fetched catalog.

## Honest gaps logged (srmech-side + ours)

- **CLAUDE.md correction:** the `srmech.asymptotic_calculus.*` trig path referenced in CLAUDE.md §2 is **NOT in rc25** (no such module). The continuous trig (cos/sin) for a *general* (large-β) rotation is absent — a **continuous-Class-C-rotation op** is a new upstream leaf (peer to the §20 ops). *But the cosmic-band small-β linear rotation needs only arithmetic, so it's derivable now.*
- The CMB TE/EE/BB catalogs are **NDJSON data** (`amsc/attested/cmb_polarisation_spectra/`), loaded via the catalog API, not a code module — the demo used illustrative spectra; wiring the real catalog load is the clean follow-on (then `cmb_parity_odd = Class-C-rotate(loaded TE/EE/BB, β)` runs end-to-end).

## Discipline

srmech-native arithmetic for the small-angle Class-C rotation (no `np.linalg`, no external trig — π enters as the cascade-limit degree→radian factor); the exact-rotation comparison is the control (rel-err ~1e-4 ≪ measurement uncertainty). The birefringence formula is attested (Lue–Wang–Kamionkowski 1999, standard). No-leaning: this LOGS the *derivation capability* (the EB/TB structure is a Class-C cascade) — it does NOT claim the β *value* (that's F355's B-tier measurement, a ~3σ hint). Composes with F350 (rotate-DoF), F355 (β data), F352 (holographic-EC).
