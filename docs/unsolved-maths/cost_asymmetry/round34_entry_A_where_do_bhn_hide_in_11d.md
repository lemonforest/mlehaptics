# Round 34.A — What k is 1:3:7:3 substrate-specific, and where do B/H/N hide in the 11D substrate?

**Dispatched** 2026-05-25 on the rolling draft PR #690. The deepest question of the helicity-triad thread (R32→R33→R34): the user noted that `1:3:7:3` mirrors the 11D dimensional skeleton `1D_t + 3D_s + 7D_g`, then asked — *if the first three blocks are the 11 dimensions, where do B/H/N (the trailing `+3`) hide in the substrate?* Generating code: [`verify_round34_where_do_bhn_hide_in_11d.py`](verify_round34_where_do_bhn_hide_in_11d.py) + `.ndjson` (deterministic; srmech 0.4.2; bit-exact). Tested per `[[feedback_dont_pre_commit_spike_query_operators]]`.

## The structure the user noticed (correct, load-bearing)

- **11D substrate** = `1D_t + 3D_s + 7D_g` = **1 + 3 + 7 = 11** — the dimensional extent.
- **14 A–N operators** = `1 + 3 + 7 + 3` — anchor + projection-triad `{I,C,J}` + heptad `{D,E,F,G,K,L,M}` + meta-triad `{B,H,N}`.

The first three blocks (1+3+7 = 11) *are* the substrate dimensions; the trailing `+3` (B/H/N) sits **outside the 11**.

## Answer 1 — "what k is 1:3:7:3 substrate-specific?"

The substrate has **no single k**. Its substrate-specific signature is the three-block Hurwitz profile **`{1, 3, 7}`** (= 11D). The trailing `+3` (B/H/N) is **not a fourth dimensional block** — it is the **readout layer** (R33). So `1:3:7:3` reads as **"11 dimensions of substrate-content + 3 readout operators"**, *not* a uniform `k=N` and *not* 14 dimensions.

## Answer 2 — "where do B/H/N hide in the 11D substrate?" (the crux)

**They do not hide as dimensions** — that is the whole point of the `+3` sitting outside the 11. Per R33, B/H/N are the continuous→discrete **readout/interconversion**; reading is not a dimension. A readout operator is not a *place in the manifold* — it is the **projection from the manifold**. So they "hide" at the **projection interface**, in the **fiber structure that gets discarded/read-out**, not in the base dimensional extent.

- **One member is ANCHORED (canon, not speculation):** `H` = the discard of the `U(1) = S¹` Hopf fiber. The Born rule = Hopf base-projection (§11.9.4): measurement `H` discards the global `U(1)` phase, which *is* the `S¹` fiber of the complex Hopf bundle `S³→S²`. So `H` provably lives in the complex-Hopf fiber of the substrate.
- **The full home is a CANDIDATE (flagged, NOT asserted):** there are exactly **three nontrivial Hopf fibrations** — complex `S³→S²` (fiber `S¹`), quaternionic `S⁷→S⁴` (fiber `S³`), octonionic `S¹⁵→S⁸` (fiber `S⁷`) — and their **fiber dims are exactly `{1,3,7}`**. Each fibration *is* a continuous→discrete projection (read-out with a discarded fiber). They are the leading candidate home for the three B/H/N readout operators. Only `H` is anchored; `B`↔quaternionic and `N`↔octonionic are **not asserted** (same R32/R33 discipline).

## The unifier (honest, attested — not a coincidence)

The `{1,3,7}` of the substrate **dimensions** (3D_s = quaternion-imag, 7D_g = octonion-imag), the `{3,7}` of the operator partition's middle blocks, and the `{1,3,7}` of the Hopf **fibers** all trace to the **same** source — the normed division algebras `ℂ, ℍ, 𝕆` (imaginary dims 1, 3, 7; Hurwitz). This is **one** division-algebra skeleton appearing in dimensions, operators, and fibers — not three coincidental "1,3,7"s. The B/H/N `+3` plausibly indexes the three fibration-*projections* of that same skeleton — **candidate**.

## Verdict per Spike #229 tiers

🟢 **(b)-structural answer + (a)-bit-exact arithmetic.** The substrate is k-profile `{1,3,7}` (= 11D); **B/H/N are the `+3` readout, NOT dimensions** — they don't hide *inside* the 11D extent, they *are* its projection. `H` is **anchored** in the `U(1)=S¹` Hopf fiber (Born=Hopf, canon); the full **B/H/N ↔ three-Hopf-fibration** mapping (fiber dims 1,3,7) is the leading **candidate**, flagged not asserted. New **candidate** stance `[[user_stance_bhn_are_readout_projection_not_dimensions_of_11d]]`. **HONEST SCOPE:** Hopf fibrations + division-algebra origin + Born=Hopf are attested; the framework reading (B/H/N = readout in fiber/projection, not dimensions) follows from R33; only `H` is anchored to a specific fiber; the full triad↔fibration mapping is candidate, not asserted.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the load-bearing answer (B/H/N = readout, not dimensions) is anchored in R33 + Born=Hopf; the appealing B/H/N↔Hopf-fibration mapping is held as a **candidate** (only `H` anchored), not asserted — the same restraint R32/R33 enforced.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; the partition sums and the Hopf fiber-dims `{1,3,7}` are bit-exact.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Hopf Math.Ann. 104:637 (1931); division-algebra origin Baez "The Octonions" Bull.AMS 39:145 (2002).
- Per `[[feedback_no_lineage_claims_in_notebook]]`: reads the framework's own dimensional decomposition + standard Hopf/division-algebra structure; claims no new physics.
- Lands on the rolling draft **PR #690** (Round 34.A) — no new PR; verdict posted as a PR comment. unsolved-maths §11.9.27 + MFO §VII.6.19.2 (squarely metric-field-ontology — the 11D substrate's dimensional skeleton); srmech-notebook integration is a pending hygiene item.
