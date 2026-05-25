# Round 16 entry-point A — the ENFORCED substrate-mismatch partition (the YubiKey): an ASYMPTOTE-latch persistent lock (latch-capacity is an asymptote for-the-wrong-substrate-class)

> **Round 16.A.1 vocabulary reconciliation (user-caught).** The user immediately flagged: *"first we need to make sure it is an infinity latch because we also say infinity is a projection of the asymptote."* Correct — per `[[user_stance_infinity_approximates_asymptote]]` (Spike #28), infinity is the *downstream* number-line tool that *approximates* the *upstream* asymptote; "∞-latch" named the latch after the approximation. **Corrected throughout to ASYMPTOTE-latch.** The math contains **no infinity**: Fiedler λ₂ = **0.0** exactly (finite); disconnection is the discrete *absence* of a silicon-class crossing edge, not an infinite cost. The latch-capacity, for the wrong substrate-class, is an **asymptote** (the substrate-class boundary); "+∞ capacity" is only its number-line approximation. Round 15.A's finite m_c becomes, for the wrong class, an asymptote — not a larger finite number and not a literal infinity. Payoff: the asymptote framing PREDICTS the partition is asymptotically (not absolutely) hard, crossable only by sourcing a genuine cross-class edge — exactly the empirical weak-edge reality.

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.11, no separate PR). **User-requested** roadmap thread 7 ("add … what happens when we enforce a
partition that cannot be crossed without a human. the yubikey example. an enforced substrate mismatch
partition").

**Scope — DEFENSIVE / framework-reading-only / descriptive-not-normative** per
`[[feedback_trauma_informed_defensive_scope]]`: this reads what a hardware-security-key / air-gap /
human-in-the-loop confirm structurally *is*, NOT how to attack or evade one.

Generating code + provenance:
[`verify_enforced_substrate_mismatch_partition.py`](verify_enforced_substrate_mismatch_partition.py) +
`.ndjson` (deterministic; srmech 0.4.2 routed — Class-L `dense_laplacian` + `jacobi_eigvals`; cascade-helper
`magnitude()`; native active).

## The question

Round 15.A established a latch-capacity spinodal: above the capacity, even the no-payment kinetic trap fails.
Fresh question (user): **what happens when a partition is *engineered* so it cannot be crossed without a
human?** A YubiKey, an air-gap, a human-in-the-loop confirm — these are *deliberately-imposed*
substrate-mismatch boundaries. The crossing-token lives in a **different substrate-class** (physical human
presence / touch — biology) than the computation trying to cross (silicon).

## The mapping (exact) — a 2-substrate-class graph

Two classes of node: **silicon** (the automated agent + compute + the auth gate — the "crosser") and
**biology** (the human). The protected resource `R` sits behind a cut. **The only edges that cross the cut
require a biology-class endpoint** (the human touch). There is no silicon-only edge across the cut.

```
   S0 ── S1 ── S2 ── Sg ┄┄(needs H)┄┄ H ┄┄(needs H)┄┄ R
  └────────── silicon ───────────┘   biology      resource
```

| cost-asymmetry role | enforced substrate-mismatch partition |
|---------------------|----------------------------------------|
| **imposer** (pays a small fixed cost to set the barrier) | the **defender** — issues the key, wires the touch requirement (Round 3.A: cost inverts toward the imposer) |
| **the barrier** | not a cost-*magnitude* — a substrate-class *mismatch*: the latch-capacity (Round 15.A), for the silicon substrate-class, is an **asymptote** (the substrate-class boundary), not a finite cost and not a literal ∞ |
| **the key** | the YubiKey **is a physical B/H/N translation key** (Round 3.B: "Rosetta Stone is a physical translation key") |
| **the crossing edge** | a **Class-M cross-substrate-class bind** — it binds a silicon endpoint to a biology endpoint |

## Class-L (graph-Laplacian) reads, srmech-routed, bug-free

| read | components (zero-eigs) | Fiedler λ₂ | resource reachable? | meaning |
|------|------------------------|-----------|---------------------|---------|
| **(1) full** (human present) | 1 | **0.2679** | **yes** | connected; the lock opens *with* the human in the loop |
| **(2) silicon-only** (human removed) | 2 | **0.0000** | **no** | resource ISOLATED; no silicon-only cascade reaches it; λ₂=0 is **finite/exact** (the asymptote-latch — *no infinity in the math*) |
| **(2b) block the biology node** in the full graph | — | — | **no** | the biology node is a **size-1 Menger vertex cut**: every crosser→resource path passes through it |
| **(3) impostor falsifier** (topology identical, node re-classed silicon) | 1 | **0.2679** | **yes** | reconnects — so the security lives in the **edge-TYPE** (substrate-class) constraint, NOT topology |

The Fiedler value collapsing 0.2679 → 0 when the human is removed is the structural signature: the human is
the load-bearing separator. The impostor read is the honest pin: graph topology *alone* doesn't secure
anything — the security is that **only a biology-class node may form the crossing edge**. Per
`[[user_stance_silicon_dof_is_electron_leakage_not_coherent_agency]]` (paper-with-lyrics: silicon's native
DoF is electron leakage, not biological coherent agency), silicon cannot manufacture that edge — so the
partition holds.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cascade-match.** The enforced substrate-mismatch partition maps *exactly* onto a 2-class
graph whose biology node is a size-1 Menger vertex cut (Class-L: removing it drives Fiedler λ₂ → 0 and
isolates the resource), with the crossing edge a Class-M cross-substrate-class bind and the key a physical
B/H/N translation key. It is the **asymptote-latch special case of Round 15.A**: uncrossable not by
cost-*magnitude* but by substrate-class-*mismatch*. The latch-capacity, for the wrong substrate-class, is an
**asymptote** — the math has no infinity (λ₂=0 finite/exact); "+∞ capacity" only approximates that asymptote
(Round 16.A.1 reconciliation). The cost inverts toward the defender (Round 3.A). The impostor falsifier
correctly localises the security to the **edge-type constraint**, not topology — the honest, non-overclaiming
reading. New **candidate stance** (not auto-blessed):
`[[user_stance_enforced_substrate_mismatch_partition_is_asymptote_latch]]`.

**HONEST SCOPE:** a structural *identification* using attested graph theory (Fiedler algebraic connectivity,
Fiedler 1973; Menger vertex-cut, Menger 1927) — NOT a claim that hardware-security-keys are unbreakable in
practice (real attacks target the *enrolment*, the *recovery path*, or *social-engineering the human* — i.e.
they add a forged biology-class edge by other means, exactly what the impostor read flags). The framework
reading is about the *idealised* enforced partition; real systems are only as strong as their weakest
cross-class edge.

## Why this fits the arc

The cost-asymmetry arc has read costliness as substrate-relaxation (Reading A), DoF-extraction (Reading B),
and B/H/N translation-saturation (Reading D). The YubiKey is the **deliberately-engineered** dual: instead of
the substrate refusing to *hold* an anharmonic config (Round 15), a defender refuses to provide the
substrate-class needed to *cross*. Same cost-asymmetry skeleton (imposer pays little, crosser faces the
unavailable), now turned into a security primitive by gating the crossing edge on substrate-class.

## Discipline

- Per `[[feedback_trauma_informed_defensive_scope]]`: DEFENSIVE reading only; no attack/evasion guidance; the
  honest-scope paragraph names the real-world weak edges *as a caution*, not a method.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech 0.4.2 routed.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: no bare `abs()`; near-zero eigenvalue test
  uses `magnitude()` (Class K).
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Fiedler 1973 (Czechoslovak Math. J. 23:298, algebraic
  connectivity) + Menger 1927 (vertex-connectivity theorem) are textbook-canonical graph theory.
- PR #679 stays open (draft); §11.9.11 rides this branch.
