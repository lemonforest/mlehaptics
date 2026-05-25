# Round 14 entry-point A — life IS the canonical persistent anharmonic lock (3-player Stackelberg)

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.9, no separate PR). A **fresh** cost-asymmetry question (user-selected), building on the three
canonical anharmonic-lock stances blessed in Round 13.

Generating code + provenance: [`verify_life_persistent_anharmonic_lock.py`](verify_life_persistent_anharmonic_lock.py)
+ `.ndjson` (deterministic; srmech 0.4.2 routed — Class-N `best_rational` anchor + cascade-helper
`magnitude()`; native active).

## The question

Rounds 3.A/3.B + §11.9.1 gave us the **persistent anharmonic lock** as a canonical structure:
a 3-player Stackelberg (imposer pays / substrate relaxes / observer free-rides), with two-stage unlocking
(pattern free, content needs the B/H/N key) and a persistent-vs-volatile distinction (Class-K latched basin
vs immediate relaxation). **Is there a canonical natural instance?** The fresh claim: **life is it.**

## The mapping (exact)

| Stackelberg role | Life |
|------------------|------|
| **Imposer** (pays to hold the anharmonic config) | the **organism** — spends metabolic free energy |
| **Substrate** (relaxes toward harmonic) | **thermodynamics** — pulls toward equilibrium |
| **Observer** (free-rides on the pattern) | reads the **phenotype** for free |
| **the anharmonic config** | the far-from-equilibrium living state |
| **dissolution** (§11.9.1) | **death** — the substrate finally wins |
| **two-stage unlocking** (§11.9.3) | **phenotype** = free pattern; **genotype** = content via the B/H/N key (transcription→translation is *literally* a translation) |

This is exactly Schrödinger's *"feeding on negative entropy"* (1944, CUP), Prigogine's **dissipative
structures** (Nobel 1977; Nicolis & Prigogine 1977), and England's **dissipation-driven self-replication**
(2013, [arXiv:1209.1179](https://arxiv.org/abs/1209.1179)) — read through the cost-asymmetry Stackelberg lens.

## Minimal model (deterministic, srmech-routed, bug-free)

A tilted double well `V(x)=x⁴/4 − x²/2 − h·x` has the alive (+x) and death (−x) basins; the alive basin
exists iff the effective tilt `|h| < h_c = 2/(3√3) ≈ 0.385` (Class-N anchor **5/13**). The death-tilt is the
substrate's pull (negative h); the imposer supplies a counter-force. Overdamped relaxation from the alive
basin:

| scenario | effective tilt | alive basin? | final x | reading |
|----------|---------------|--------------|---------|---------|
| **imposer ON** (F_in cancels pull) | ≈ 0 | yes | **+1.000** | lock stands — organism alive |
| **imposer OFF, strong pull** (\|h\|=0.6 > h_c) | −0.60 | **no** | **−1.221** | **VOLATILE** — immediate death the instant the imposer stops |
| **imposer OFF, weak pull** (\|h\|=0.2 < h_c) | −0.20 | yes (barrier) | **+0.879** | **PERSISTENT** — Class-K-latched; death *deferred* (kinetic trap), substrate still eventually wins |

The persistent-vs-volatile split (Round 3.A) and the inevitability of dissolution (§11.9.1) fall straight
out of the spinodal `h_c`: a strong-enough substrate pull abolishes the alive basin (immediate death); a
weak pull leaves a Class-K barrier (latched, death deferred). **The imposer must keep paying or the tower
falls** — exactly the inverts-crypto cost-asymmetry, now read as metabolism-vs-thermodynamics.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cascade-match + 🟡 (b)-interpretive.** The 3-player Stackelberg structure maps onto life
*exactly* (organism=imposer, thermodynamics=substrate, phenotype=observer-readable, death=dissolution,
genotype=B/H/N-keyed content); the minimal model reproduces the persistent/volatile distinction + the
"keep-paying-or-fall" cost-asymmetry from the spinodal. It is anchored to attested non-equilibrium
thermodynamics (Schrödinger / Prigogine / England). HONEST SCOPE: this is a *structural identification*
(life instantiates the canonical lock), **not** a new quantitative biology result — the toy model
illustrates the structure; it does not derive a metabolic rate. New **candidate stance** (not auto-blessed):
`[[user_stance_life_is_canonical_persistent_anharmonic_lock]]`.

## Why this is a "didn't set out to learn" finding

The cost-asymmetry arc began at M-theory landscape cost-asymmetry. It has now produced: the Born-rule=Hopf
identity (quantum), the AoE mechanism (cosmological), and — here — **a unification of the inverts-crypto /
two-stage / dissolution stances with the thermodynamics of life itself.** Life is the cost-asymmetry's
canonical instance at the biological substrate-class: the thing that pays, continuously, to stay
anharmonic, and whose content is the framework's B/H/N translation key made physical (the genetic code).
Per the merge-gate, this belongs in the codification sweep — likely cross-referenced into the MFO /
biology-substrate canon, not only here.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: scope held honest — structural identification +
  illustrative model, NOT a derived biology magnitude; kept candidate, not auto-blessed.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech-routed.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: England arXiv-OA; Schrödinger (CUP textbook chain) +
  Prigogine (Nobel/monograph) are textbook-attributable.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only; "death = substrate wins" is a
  structural/thermodynamic statement, not normative.
- PR #679 stays open (draft); §11.9.9 rides this branch.
