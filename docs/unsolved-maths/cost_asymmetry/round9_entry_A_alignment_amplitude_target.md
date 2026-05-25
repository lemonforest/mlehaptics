# Round 9 entry-point A — the quad-oct alignment amplitude: wrong mechanism, not wrong framework

**Dispatched** 2026-05-25 (sequential, no subagents). Picks up the sharp open target
left by Round 8.A (parking-lot **thread 2′**): the Axis-of-Evil quad-oct **alignment
amplitude** has no derived magnitude, and the kinematic fiber-leak (β = v/c) is ruled out
as its source. *Does any framework mechanism predict an order-unity ℓ=2,3 alignment?*

Generating code + provenance: [`verify_alignment_mechanism_discriminator.py`](verify_alignment_mechanism_discriminator.py)
+ `.ndjson`.

## The reframing that the round turns on

Round 8.A refuted "AoE alignment = observer fiber-leak" **at magnitude β** — a kinematic
0.12% modulation cannot repoint the quadrupole. But the framework's **prior** readings of
the AoE were **never kinematic**. They are geometric / topological:

- **Spike #33** — AoE direction = a local **Class K** (pin-slot / sign-flip) signature.
- **Spike #35** — AoE as an **off-centre-observer** signature (Brouwer-Clemence ladder).
- **Spike #26 / MFO §VII.6.3.1** — AoE / precession as a **bundle-projection reconfiguration**.

§11.9.6 (Round 6.A) mis-stated the mechanism — it described the AoE as "the observer Hopf-fiber
leak" and Round 8.A correctly read *that phrasing* as kinematic and refuted it. The framework's
actual AoE mechanism is the **geometric off-centre-observer / Class-K offset**, which is a
different object.

## The discriminator — amplitude separates the two mechanism classes

A geometric offset δ (an off-centre observer in the Hopf-bundle base) imprints the observer's
preferred axis on the low-ℓ sky with amplitude **∝ δ**, *not* ∝ β. It is **not β-suppressed**.
So the order-of-magnitude argument that killed the kinematic reading does not touch it. Quantified
(committed code):

| Mechanism class | amplitude | decades below O(1) | viable for O(1) alignment? |
|-----------------|-----------|--------------------|-----------------------------|
| **Kinematic** (β = v/c) | 1.23×10⁻³ | **2.91** | ❌ EXCLUDED (Round 8.A) |
| **Geometric** (δ, off-centre-observer / Class K) | ~0.04 (Spike #35 prior) | **1.40** | ✅ VIABLE — clears the bar by ~1.5 decades |

The amplitude is the discriminator: it **excludes** the kinematic mechanism and **admits** the
geometric one. The framework's own prior AoE reading (geometric) **survives the very
order-of-magnitude test that killed the kinematic mis-statement**.

There is also a **directional** consistency: an off-centre observer imprints the alignment axis
along its *offset direction*. The observed AoE points near the ecliptic / kinematic-dipole
direction — consistent with the offset being co-aligned with our motion. (Direction alone does
**not** discriminate — the kinematic reading predicts the same axis — so the amplitude, above, is
the load-bearing discriminator.)

## What the round did NOT do — stated plainly

It did **not** derive the alignment amplitude. The ~4% offset scale is a **framework-internal
prior** (Spike #35), not a value computed from first principles this round, and the geometric
mechanism is "viable" in the sense of *not excluded by the order-of-magnitude argument* — it sits
right at the edge of the viability band (1.40 vs a 1.5-decade threshold). No multipole-vector
alignment was computed from a concrete geometry.

## Verdict per Spike #229 tiers

🟡 **(b) REFINED + (open).** The round **reframes** the mechanism (kinematic → geometric) and shows
the geometric class is **viable where the kinematic class is excluded** — a real correction to
§11.9.6. But the alignment-amplitude **target is not achieved**: no derived magnitude. The honest
net is "right mechanism identified, wrong one excluded, magnitude still open" — not a derivation.

## What this does to §11.9.6 (future promotion-PR)

The §11.9.6 amendment already queued by Round 8.A gets sharper. Three-way split:

1. **Boosting** = confirmed observer-fiber-leak at β (Round 8.A; 🟢 toward (a)).
2. **Quad-oct alignment** = a **geometric** off-centre-observer / Class-K signature (Spikes
   #33/#35/#26), **not** the kinematic fiber-leak; viable at the right order of magnitude; amplitude
   derivation open.
3. **Low quadrupole** = Class K suppression (untouched; no magnitude attempted).

## Sharp open target (thread 2″)

Compute the ℓ=2,3 multipole-vector alignment from a **specified Class-K offset** (magnitude δ +
direction) in the Hopf-bundle base, and compare to the observed alignment amplitude + ecliptic
correlation. That is a concrete, dispatchable calculation — and the honest place a real
(a)-lift of the alignment would have to come from.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the round did not reach its target and
  says so; the "viable" verdict is hedged (edge of band; prior not derived).
- Per `[[feedback_computational_provenance_discipline]]`: committed discriminator code.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: Spikes #33/#35/#26 are this framework's own
  prior arc (own-lineage, permitted); no external-lineage claim.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- PR #679 stays open; §11 SSoT frozen until a promotion-PR.
