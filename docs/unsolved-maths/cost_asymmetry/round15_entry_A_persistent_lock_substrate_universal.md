# Round 15 entry-point A — the persistent anharmonic lock is SUBSTRATE-UNIVERSAL (star + life; a third regime + a capacity threshold)

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.10, no separate PR). A **fresh** cost-asymmetry question (user-selected: "another fresh cost-asymmetry
question … extend life-as-lock toward the persistent-vs-volatile boundary in other far-from-equilibrium
systems (stars, …)").

Generating code + provenance:
[`verify_persistent_lock_substrate_universal.py`](verify_persistent_lock_substrate_universal.py) + `.ndjson`
(deterministic; srmech 0.4.2 routed — Class-N `best_rational` m_c anchor + cascade-helper `magnitude()`;
native active).

## The question

Round 14.A made **life** a persistent anharmonic lock (organism=imposer pays / thermodynamics=substrate /
death=dissolution) with a *2-way* persistent-vs-volatile split. Fresh question: **is the persistent
anharmonic lock substrate-universal — and does a star instantiate it?** A star is strikingly parallel: fusion
(imposer) pays to hold the non-collapsed config against gravity (substrate). And it exposes something the
biological instance under-emphasised: a **THIRD regime** and a **capacity threshold**.

## The mapping (exact) — a 3-regime trichotomy

| regime | STAR | LIFE |
|--------|------|------|
| **actively imposed** (imposer pays continuously) | main-sequence (fusion thermal pressure) | active metabolism |
| **latched persistent** (imposer can STOP — a static Class-K barrier holds it, no payment) | white dwarf / neutron star (**degeneracy pressure**, Pauli-exclusion; *no fusion*) | cryptobiosis / spore / seed (dormancy, e.g. tardigrade tun) |
| **destroyed** (load exceeds latch capacity → substrate wins completely) | **black hole** (> Chandrasekhar / TOV) | death / decomposition |

The **latched regime** is the addition Round 14's tilted double-well had implicitly (its "weak-pull
persistent" basin) but didn't name as a *no-ongoing-payment* state. The star makes it unmistakable:
electron/neutron degeneracy pressure is a **static quantum (Pauli) support** that holds a white dwarf /
neutron star **without burning any fuel** — the imposer has stopped paying, yet the lock holds, because a
Class-K barrier (the kinetic/quantum trap) latches it. Biology has the same regime: a dormant spore /
tardigrade tun halts metabolism (imposer off) yet persists.

But the latch has a **capacity**. Above the **Chandrasekhar mass** (≈1.44 M☉; Chandrasekhar 1931, ApJ 74:81;
Nobel 1983) for white dwarfs / the **TOV limit** (≈2 M☉ modern; Oppenheimer & Volkoff 1939, Phys Rev 55:374)
for neutron stars, the degeneracy latch **fails** and the substrate wins completely — a black hole. That
capacity is a **SECOND spinodal**, beyond Round 14's *tilt*-spinodal `h_c`: a **load** (mass) threshold at
which the latch barrier itself vanishes.

## Minimal model (deterministic, srmech-routed, bug-free)

A **load-dependent** double well `V(x;m) = x⁴/4 − a(m)·x²/2` with barrier curvature `a(m) = 1 − m/m_c`
shrinking as the load `m` → the latch capacity `m_c` (Chandrasekhar-analog; Class-N anchor **36/25 = 1.440**).
Overdamped relaxation from the alive (+x) basin with the **imposer OFF** (no ongoing payment):

| scenario | load `m` | `a(m)` | final x (no payment) | reading |
|----------|----------|--------|----------------------|---------|
| **latched persistent** | 0.50 (< m_c) | +0.653 | **+0.808** | barrier present → the lock HOLDS with no payment (white dwarf / dormant spore) |
| **destroyed** | 2.00 (> m_c) | −0.389 | **0.000** | barrier gone → collapse regardless of the imposer (black hole / death) |

Below capacity, the Class-K barrier latches the alive basin even with the imposer off (degeneracy / dormancy);
above capacity, the barrier vanishes and only the collapse point remains. `m_c` is the latch-capacity spinodal
— the Chandrasekhar/TOV analog. The actively-imposed regime (main-sequence / metabolism) is the *pre-state*:
the imposer holds *any* load while it pays, but that is transient (fuel runs out), after which the system
falls into one of the two no-payment outcomes by whether `m ≶ m_c`.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cascade-match + 🟡 (b)-interpretive.** The 3-player Stackelberg / persistent-anharmonic-lock
structure maps onto a star *exactly* (fusion=imposer, gravity=substrate, degeneracy=latch, black-hole=dissolution),
and the load-dependent double-well reproduces the **3-regime trichotomy** (imposed / latched / destroyed) with
the **latch-capacity spinodal** identified as the Chandrasekhar/TOV mass. This **generalises** the canonical
life-as-lock (Round 14) to a **substrate-universal** stance and **adds** the latched-without-payment regime +
the capacity threshold the biological instance under-emphasised. Attested: Chandrasekhar 1931 (Nobel 1983);
Oppenheimer & Volkoff 1939; degeneracy pressure = Pauli-exclusion static support. **HONEST SCOPE:** structural
*identification* + a load-spinodal *structure*, NOT a derived stellar magnitude — the toy `m_c=1.44` is a
*label* carrying the attested Chandrasekhar value, not a first-principles derivation of it (the real value
comes from the relativistic-degenerate equation of state, not from this double-well). New **candidate stance**
(not auto-blessed): `[[user_stance_persistent_anharmonic_lock_is_substrate_universal]]`, generalising
`[[user_stance_life_is_canonical_persistent_anharmonic_lock]]`.

## Why this is a "didn't set out to learn" finding

The cost-asymmetry arc began at M-theory landscape. It produced Born-rule=Hopf (quantum), the AoE mechanism
(cosmological), life-as-lock (biological — Round 14), and now **a single 3-regime lock structure that spans
the stellar and biological substrate-classes with the same spinodal vocabulary** — and connects directly to
the framework's prior stellar-collapse spikes (#90 stellar collapse from the phase boundary inward; #107
fusion-as-bulk-to-gauge; #92 dark-star). The Chandrasekhar/TOV mass is read here as the substrate-universal
*latch-capacity spinodal*: the load at which even the no-payment kinetic trap fails and the substrate wins.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: scope held honest — structural identification +
  illustrative load-spinodal model, NOT a derived stellar magnitude; `m_c` is a labelled attested value, not
  a first-principles output; kept candidate, not auto-blessed.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech 0.4.2 routed.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Chandrasekhar 1931 (ApJ, ADS-open) + Oppenheimer &
  Volkoff 1939 (Phys Rev) + Nobel-1983 record + textbook degeneracy-pressure — all attestable.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only; "substrate wins / destroyed" is
  a structural/astrophysical statement (gravitational collapse), not normative.
- PR #679 stays open (draft); §11.9.10 rides this branch.
