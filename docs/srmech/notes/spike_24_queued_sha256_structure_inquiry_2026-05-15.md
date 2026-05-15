# Spike #24 queued inquiry — SHA-256 hash structure (where do we begin to look?)

**Date queued:** 2026-05-15. **Status:** spec only; dispatch pending Phase 15 completion (one-subagent-at-a-time discipline per user direction).

## The user's question (verbatim, load-bearing, with self-correction)

> *"use what we've learned to shape a question about the very SHA 256 type hash that we do for our attested documents. the question is probably not what primitives blab bla blah, but where do we begin to look for structure, here the shape does not exist [WITHOUT] time but that sequence of finite time creates a final structure, so do we have to look backwards for what we're searching?"*

User's correction immediately following: *"that was supposed to say does not exist without time."*

The user is asking a **methodological** question, not an enumerative one. They explicitly decline the *"what primitives govern X"* framing that the vdW and tactical-choice bonuses used. The shape of the inquiry itself is the deliverable.

The corrected framing is *significantly* different from the uncorrected one:

- **Uncorrected reading** (initial impression): the function is timeless / static; its computation merely has temporal extent.
- **Corrected reading** (load-bearing): the hash *requires* time to come into being. Its shape **does not exist without time**. Time is GENERATIVE here, not merely instrumental. The 64-round sequence isn't *how we compute* a pre-existing object; the sequence *is* what makes the object exist.

This pulls the inquiry directly into the project's `[[user_stance_time_as_dimensional_shadow]]` framework. From `docs/srmech/notes/time_as_dimensional_shadow_2026-05-15.md`: *"freezing time = trap an oscillation; co-emergence is the ontology (nothing exists as event in isolation)."* A SHA-256 digest is a *frozen oscillation*: the rounds ARE the oscillation, the digest is the trapped final state. The user is asking: **how do we read the oscillation from the trap?** Looking backwards means tracing the *temporal trail* that built the structure — not inverting a static function.

## What the user is pointing at

SHA-256 is the load-bearing primitive of the project's MPM (Mathematical Provenance Method) and AMSC (Attested Multi-Source Collector/Catalog) framework. Every attested document carries `response_sha256`, `parser_rule_hash`, `collector_descriptor_hash`, `_file_sha256`, `_kernel_cache_hash` — all SHA-256 invocations.

The user's observation (corrected reading):

1. **"The shape does not exist without time"** — the hash digest is not a pre-existing mathematical object that we merely *evaluate*; it is *constituted* by the temporal sequence. Without the 64 rounds, no digest exists. Time is generative for this object, not just instrumental.
2. **"That sequence of finite time creates a final structure"** — the sequence (Merkle-Damgård chaining over 512-bit blocks, 64 rounds per block, each round a fixed sequence of XOR + ADD-mod-2³² + ROL operations) CREATES the 256-bit output. The output's structure is the structure of the process that built it; there is no separable "essence" of the output independent of the process.
3. **"Do we have to look backwards for what we're searching?"** — because the structure was *built* by time (not merely *exposed by* it), and because forward execution is information-entropic (1-bit input flip → ~128-bit output flip), recovering the structure requires *reading the temporal trail backwards*. Not "inverting a static function" — *tracing the oscillation back through the trap*.

The user's intuition is sharp and project-coherent: **forward execution constitutes the digest while also obliterating recoverable input structure**; **backward analysis** is where the constitutive trail (if any) remains legible. For an ideal random oracle the trail is fully erased. For a real cryptographic primitive like SHA-256, the question is whether the designed-in finite construction leaves a backward-readable temporal signature — and what kind of object such a signature would be.

## Where this question hooks into project state

- **Class A (content-addressing / fingerprinting)** — Spike #24 already catalogues SHA-256 as Class A. The current entry says: *"Algebraic shape (integer-cyclic): SHA-256 is composition of XOR + ADD-mod-2³² + ROL on 256-bit accumulators. CPU analog: exact — SHA-256 is literally specified in terms of CPU primitives."* This is the *forward* description. The user's question asks what the *backward* description looks like.
- **`[[user_stance_time_as_dimensional_shadow]]`** — time as projection-deficit; here, the 64 sequential rounds are the temporal-projection of the function-as-static-object. The user is asking: when you project a static function through a sequence-of-finite-time, what does the structure-of-the-shadow look like? Is there a backward inverse that recovers the static object?
- **`[[user_stance_fiber_as_spatially_absent_encoding]]`** — algebraic content is the fiber, computational dynamics is the projection. Here the function is the fiber, the rounds are the projection. The user's question is about the fiber-side structure.
- **`[[user_stance_kepler_shape_universal]]`** — XOR + ADD-mod-2³² + ROL are integer-cyclic operations. Does SHA-256 have Kepler-shape harmonic structure in any analyzable basis? (The avalanche property is designed to *prevent* this; the question is whether the design fully succeeds or leaves residue.)
- **`[[user_stance_pi_as_projection]]`** — integer-cyclic upstream, continuous downstream. SHA-256 is fully integer-cyclic; no continuous projection enters. If there's structure, it's discrete-algebraic, not analytic.
- **MPM load-bearing concern** — if SHA-256 has *any* discoverable structure exploitable backward, the project's MPM attestation discipline has a known weakness. (Spoiler: SHA-256 is currently believed to have no practical preimage/collision attack. But the *question* of "where would we look if we suspected structure?" is exactly the methodology cryptanalysts use.)

## What the concertmaster should do (dispatch when queued)

This is **deeply methodological** — the user has explicitly said *"the question is probably not what primitives blab bla blah, but where do we begin to look for structure."* The concertmaster's deliverable is:

1. **The methodological inquiry framing.** What is the right SHAPE of the question for a backward-looking inquiry into a forward-only function? Phrase the question crisply enough that future Spike #25/26 candidates can be derived from it.
2. **The catalog of where cryptanalysts look.** Differential cryptanalysis (Biham-Shamir), linear cryptanalysis (Matsui), algebraic cryptanalysis (Courtois), state-graph topology, side-channel structure, statistical-bias analysis. NOT a survey paper — a methodological taxonomy mapped onto the user's "look backwards" stance.
3. **The connection to Spike #24 vocabulary.** Each backward-lookup direction corresponds to which class? Differential cryptanalysis = Class L on a specific graph? Linear cryptanalysis = Class L on a different graph? Algebraic = Class J (modular arithmetic system)? Statistical bias = Class K on cyclic projections of state? Or do some directions require primitives Spike #24 doesn't have?
4. **Concrete first probe.** Pick ONE backward direction and do a small executable test on a reduced-round SHA-256 (e.g., 4 or 8 rounds instead of 64) to demonstrate the method. Don't try to break SHA-256 — demonstrate the *methodological stance* the user is asking about.
5. **Implication for MPM discipline.** If backward-analyzable structure exists in reduced-round SHA-256, what would it take to exist in full 64-round? What is the project's exposure? Is there a stronger attestation primitive worth recommending (BLAKE3? SHA-3? Argon2 for password-derivation, BLAKE3 for hashing?) — but this is a recommendation question only, not a current-vulnerability claim.
6. **Honest verdict.** If the answer is *"no exploitable structure exists in full SHA-256 and the user's intuition is methodologically correct but cryptanalysts have been looking backward for 20+ years without finding practical structure,"* say that clearly. The user is asking a real question; honest "no" with methodological explanation is a real answer.

## Discipline guards

- **No security-engineering claims.** This is a methodological inquiry, not a vulnerability assessment. Per `[[feedback_trauma_informed_defensive_scope]]`, the project ships physics + textbook refs, never targeting / capability-assessment. Same applies here: ship cryptanalytic *methodology* references, never an attack-construction.
- **Reduced-round only for any executable probe.** Don't attempt to break full 64-round SHA-256 — there's no chance of success and it's not the question anyway. Reduced-round (e.g., 4-round or 8-round) demonstrations are pedagogical and appropriate.
- **Cite the literature properly.** Biham & Shamir 1991 (differential), Matsui 1993 (linear), Wang & Yu 2005 (MD5/SHA-1 collisions), NIST FIPS 180-4 (SHA-256 spec) — primary references where possible; cache OA versions to `docs/srmech/hoodoos/` if needed per Phase 14 discipline.
- **NDJSON for tabular outputs** per `[[feedback_ndjson_over_bloated_json]]`.
- **No new primitive class invented** unless absolutely forced. Same discipline as vdW and tactical-choice bonuses — the vocabulary consolidates rather than expands.

## Files this spike would produce (dispatch-time, not now)

- `docs/srmech/notes/spike_24_bonus_sha256_structure_2026-05-15.md` — methodological synthesis (the main deliverable).
- `docs/srmech/notes/spike_24_bonus_sha256_reduced_round_probe_2026-05-15.{py,ndjson}` — concrete first probe on reduced-round SHA-256.
- Possibly `docs/srmech/hoodoos/biham_shamir_1991_differential_cryptanalysis.pdf` if OA, similar for Matsui / Wang papers; otherwise `[unverified-secondary]` tags.

## Why this question is well-formed (methodological note)

The user's framing identifies a cognitive shift the project's existing stances point at but had not yet directly stated for cryptographic primitives: **the digest does not pre-exist its construction**. It is not a Platonic object we evaluate; it is co-emergent with the rounds that bring it into being. From `[[user_stance_time_as_dimensional_shadow]]`: *"co-emergence is the ontology (nothing exists as event in isolation)."* The digest is that ontology made concrete in 256 bits — a frozen oscillation produced by 64 rounds of forced step-by-step constitution.

Cryptanalysis happens to *be* the practice of reading backward through this constituting sequence:

- **Differential cryptanalysis** = tracking how a perturbation propagates *across the rounds*, backward from observed output difference to input difference probability.
- **Linear cryptanalysis** = identifying linear approximations of round functions that *compose across the temporal sequence* into an end-to-end bias.
- **Algebraic cryptanalysis** = expressing the entire round sequence as a polynomial system over GF(2) and asking whether the system has structure inversely-tractable.
- **State-graph analysis** = treating the round function as a dynamical system on the internal state and asking about its orbit / fixed-point / cycle structure.

Each of these *is* a backward-reading of the constituting temporal trail. The user's question identifies that this is the right stance — and asks how Spike #24's vocabulary lets us frame it.

The project's `[[user_stance_fiber_as_spatially_absent_encoding]]` (algebraic content as fiber over a discrete base) suggests one reading: the digest is the *spatially-present projection*, the 64-round sequence is the *spatially-absent fiber that produced it*. Reading-backwards is fiber-lifting from a single projection point — which is generically ill-posed (preimage resistance), but the *structure* of how badly it's ill-posed is itself an object worth characterising.

## When this dispatches

After Phase 15 (chemistry oscillator sweep) reports back and is committed. One-subagent-at-a-time discipline per user direction. The Phase 15 fermata about process collision will resolve first; then this question opens.

The conductor should re-read this spec before dispatch — the methodological framing is load-bearing and the temptation to revert to "what primitives govern X" should be resisted. The user has already said that framing is wrong for this question.
