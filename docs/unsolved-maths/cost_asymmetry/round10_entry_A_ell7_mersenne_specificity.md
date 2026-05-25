# Round 10 entry-point A — is ℓ=7 individually a Mersenne node? No. The {3,7} signal is the octupole.

**Dispatched** 2026-05-25 (sequential, no subagents). Picks up parking-lot **thread 1**: Round 6.A's
one remaining `(open)` verdict — the Mersenne {1,3,7} prediction, where ℓ=1 (dipole) and ℓ=3 (octupole)
were present and **ℓ=7 was the open testable**. Run on attested, already-committed data — no new
download, no healpy, no fabrication.

Generating code + provenance: [`verify_ell7_mersenne_specificity.py`](verify_ell7_mersenne_specificity.py)
+ `.ndjson`. **Reuses** the attested per-ℓ C_ℓ table committed by Spike #190
([`docs/srmech/notes/spike190_findings_2026-05-19.ndjson`](../../srmech/notes/spike190_findings_2026-05-19.ndjson);
SMICA-nosz anafast; Planck 2018 IV, doi 10.1051/0004-6361/201833881).

## The distinction the round forces

Spike #190 found a **{3,7} aggregate** concentration: 6.19× over uniform null, p = 0.006, on the low-ℓ TT
spectrum. But {3,7} is the *pair together*. Round 6.A's open prediction was about **ℓ=7 specifically**.
Does ℓ=7 individually carry a Mersenne signature, or does ℓ=3 carry the whole {3,7} result?

## Three ℓ=7-specific tests (committed code)

**1. Split of the {3,7} concentration.**

| mode | share of the {3,7} pair-power |
|------|-------------------------------|
| ℓ=3 (octupole) | **80.4%** |
| ℓ=7 | **19.6%** |

The {3,7} signal is **ℓ=3-dominated**. ℓ=7 contributes under a fifth.

**2. Per-mode ranking in the ℓ=2–8 band** (ratio of each mode's power-share to the uniform 1/39 null):

> ranked descending: **ℓ=3 (9.97×) > ℓ=5 (6.29×) > ℓ=4 (4.39×) > ℓ=2 (3.75×) > ℓ=7 (2.42×) > ℓ=6 > ℓ=8**

ℓ=7 ranks **#5 of 7**. It is **outranked by three non-Mersenne modes** — ℓ=5, ℓ=4, and even the famously
*suppressed* quadrupole ℓ=2. A distinguished Mersenne node would not sit below ℓ=4 and ℓ=5.

**3. Local-maximum parity test.** ℓ=7 is a local maximum (> ℓ=6, > ℓ=8) — but so is the **non-Mersenne odd
ℓ=5**. The local maxima in the band are {3, 5, 7}: that is **odd-ℓ parity alternation**, not a Mersenne
fingerprint. ℓ=5 sitting in the same pattern, and ranking *above* ℓ=7, kills the Mersenne-specific reading.

## Verdict per Spike #229 tiers

🟠 **(open) → WEAKENED** on the ℓ=7-specific claim.

- There is **no ℓ=7-specific Mersenne signature** in the attested Planck low-ℓ TT data. ℓ=7 is unremarkable:
  2.42× uniform, 5th of 7, below three non-Mersenne modes, local-max-by-parity not by Mersenne.
- This satisfies Round 6.A's own falsifier criterion ("robust ℓ=7 absence would weaken the Mersenne
  prediction"). The ℓ=7 element of the {1,3,7} prediction is **not supported** and should be **withdrawn**
  as a per-ℓ claim.
- **The {3,7} aggregate result (Spike #190) is untouched** — it stands at 6.19×, p=0.006, but it is now
  correctly understood as **ℓ=3 (octupole)-driven**, not evidence for ℓ=7.

## What this does to §11.9.6 (future promotion-PR)

The §11.9.6 amendment (already queued by Rounds 8.A + 9.A) gains a third correction. The Mersenne reading
should be stated honestly:

1. **ℓ=1** = the observer fiber-coordinate (kinematic dipole; removed from the anisotropy spectrum by
   convention — consistent with the fiber-leak reading of Round 8.A).
2. **ℓ=3** (octupole) = the real low-ℓ concentration carrier; part of the quad-oct alignment.
3. **ℓ=7** = **withdraw** the per-ℓ Mersenne claim. Not distinguished in the data. The {3,7} structural
   pairing (parallelizable-sphere ladder 1+3+7; Hopf-fiber dims) remains valid as an *algebra-layer*
   identity, but its *CMB-multipole projection* does **not** single out ℓ=7.

This is the layered discipline (`[[user_stance_identity_not_implementation_discipline]]`): the
structural 1+3+7 Hopf-fiber identity is unchanged; only its empirical CMB-projection fingerprint contracts
(ℓ=7 drops out).

## Honest scope

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: this is a **negative result on a framework
  prediction**, reported plainly. The {3,7} aggregate was not allowed to stand in for ℓ=7.
- Per `[[feedback_computational_provenance_discipline]]`: committed code; reuses attested Spike #190 input;
  no hand-entered spectrum.
- Pseudo-C_ℓ caveat inherited from Spike #190 (no MASTER mode-coupling correction; for the relative
  ℓ-distribution test this is immaterial, as Spike #190 noted).
- Cosmic variance at low ℓ is large; "WEAKENED" not "FALSIFIED" — but the *direction* is unambiguous:
  ℓ=7 carries no excess over its non-Mersenne neighbours.
- PR #679 stays open; §11 SSoT frozen until a promotion-PR.

## Disposition

- §11.9.6 amendment now three-fold: boosting=β (8.A) + alignment=geometric (9.A) + **ℓ=7 withdrawn,
  {3,7}=ℓ=3-driven (10.A)**.
- Round 6.A's `(open)` ℓ=7 verdict → **resolved: WEAKENED / withdrawn as a per-ℓ claim.**
- The {1+3+7} Hopf-fiber *algebra identity* is preserved; only the CMB-multipole projection of it loses ℓ=7.
