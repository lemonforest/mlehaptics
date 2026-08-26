# Finding 206 — The hardware (RISC-minimality) lens stratifies A–N / `cascade.*` into silicon-able ATOMS vs software COMPOSITES; the lean A–N ISA core is a Klein-4 chirality unit + sign/magnitude riding on the *existing* SHA-NI / modular units

**Status:** Framework / **architecture design-reading** (instruction-set level — which ops are primitive, the orthogonal basis, mapping to existing extension precedent). **NOT** CAD / VLSI / gate-layout / fabrication — the F202 scope-ban holds (no chip, no transistor counts, no benchmarks). Builds on the **rc22 `srmech.amsc.cascade.*` landing**.
**Predecessors:** F202 (quad-DNA as a chirality-typed CPU cascade/threading model; the A-N-as-ISA thread), the rc22 `cascade.*` module (native `pin_slot_at_zero`/`reorient`/`magnitude`/`chiral_flip`/`chiral_dual`/`net_chirality`/`best_rational_signed`/`cyclic_gcd`), F132/F192 (Klein-4 + triality bit-exact), F168/F200 (storage substrate is order-2 Klein-4), the ROADMAP forward-architecture thread, `[[user_stance_epicycle_via_gear_plus_pin]]`.
**User direction (2026-05-30):** "is [`cascade.*`] close to the software version of [the A-N processor extension set], or would looking more into a hardware implementation make our software version much more lean?" + "very interested in the learn-to-lean-by-hardware path; I don't care how much research we put into this for the knowledge."

---

## §1 `cascade.*` IS the software intrinsics layer of the ISA
The rc22 `srmech.amsc.cascade.*` module is the software *reference model* of the proposed A–N ISA — the relationship a C intrinsic (`_mm_aesenc_si128`) has to a hardware instruction (`AESENC`). Each `cascade.*` function is a candidate **single-instruction primitive**. The software face of the ISA already exists; the question is which primitives are real silicon.

## §2 The RISC-minimality forcing function → atom / composite split
Silicon costs gates, decode, and verification, so hardware design prunes to a minimal orthogonal basis. That lens splits the 14 A–N / the cascade ops / the 174 `tool_schema` entries into two tiers the flat software namespace hides:

| tier | members | why |
|---|---|---|
| **silicon-able ATOMS** (≈1 instruction) | `chiral_flip`/`chiral_dual`/`net_chirality` (mask + parity on the 2-bit γ₅×iω₇ sector tag), Klein-4 `bind` (= XOR), `pin_slot_at_zero` (Class K sign-test), `magnitude` (clear sign bit ≈ `ANDPS`), `reorient` (Class C sign/mask), content-hash (Class A — **already silicon: SHA-NI**), modular add/mul (Class I — existing units) | combinational / one-shot |
| **iterative COMPOSITES** (software/microcode over atoms — NOT instructions) | `best_rational_signed` (Stern-Brocot iteration), `cyclic_gcd` (Euclid), `pi_cascade_digits` (spigot), Class L eigendecomp (Jacobi sweeps), Class J factorization | loops, not gates — no "diagonalize" instruction exists |

## §3 The lean ISA core
The minimal extension is **not** 14 classes or 174 tools — it is a **chirality unit operating on a 2-bit Klein-4 sector tag (γ₅ × iω₇)** + sign/magnitude, riding on the *already-existing* SHA-NI (Class A) and modular (Class I) units. A handful of new instructions. Everything else **composes in software over that core** — exactly F202's chirality-typed lanes + leading/lagging dual-handed pair. (Storage substrate is order-2 Klein-4 per F200; the addressing/turning is the chirality unit.)

## §4 The software gets leaner by mirroring the split
The hardware reading pushes the same stratification *into* the software: expose the atoms as thin 1:1 intrinsics (each = a future instruction), demote the composites to clearly-labeled algorithms built *on* the atoms — `cascade.atoms.*` vs `cascade.compose.*`, not one flat namespace. Leaner, maps 1:1 to the ISA, **and** it is the honest cascade-count: an atom is one cascade-step; a composite is a named multi-step. (`cascade.magnitude` is both the 1-instruction silicon atom *and* the honesty op — it records the Class-K modulus-fold instead of `abs()` silently discarding the sign.)

## §5 Epicycle-prescience / siona — minimality is the mercy
The "all-or-none" burden of the 28D/so(8) laws-of-everything ALU becomes bearable exactly when it reduces to an irreducible few — ~6 chirality/sign atoms + the rule that everything composes, not 174 ops or 28 dimensions held in a mind. This is epicycle-prescience (`[[user_stance_epicycle_via_gear_plus_pin]]`): epicycles were a tiny turning-basis the continuous-math world bloated to infinity; the A–N atoms are the discrete irreducible turning-set. The lean ISA is the epicycle-basis made honest. (Sibling to F207: minimality makes the *knowledge* bearable; safe-being-wrong makes *learning* it bearable.)

## §6 DOES / does NOT claim
**DOES:** read `cascade.*` as the software intrinsics layer; apply RISC-minimality to stratify A–N/cascade into silicon-able atoms vs iterative composites; name the lean ISA core (Klein-4 chirality unit + sign/magnitude + existing SHA-NI/modular); recommend the software mirror the split.
**Does NOT:** present a chip, microarchitecture, gate layout, transistor counts, or any fabrication/VLSI/benchmark claim (CAD-ban); claim the atom/composite partition is final — it is a design-reading to be verified op-by-op (the deeper pass is queued as a research item); §VII.6.20 form-reading; `[[feedback_trauma_informed_defensive_scope]]` (edge-compute / accessibility thesis, not weapons-substrate).

## §7 Cross-references
F202 · rc22 `cascade.*` landing · F132/F192 (Klein-4 / triality) · F168/F200 (order-2 storage) · ROADMAP forward-architecture thread · `[[user_stance_epicycle_via_gear_plus_pin]]` · AES-NI / SHA-NI / AVX-512 / ARM-SVE / RISC-V-custom-opcode precedent (the design-reading anchors) · F207 (lean-knowledge sibling)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The rc22 `cascade.*` module is the software
intrinsics layer of the A–N ISA; the RISC-minimality (hardware) lens stratifies it — and
the 14 A–N / 174 tools — into silicon-able ATOMS (the Klein-4 chirality ops on a 2-bit
sector tag, sign, magnitude, content-hash via existing SHA-NI, modular via existing units)
versus iterative COMPOSITES (eigendecomp, factorization, gcd, best-rational, π-spigot)
that stay software over the atoms. The lean ISA core is a chirality unit + sign/magnitude
on the existing SHA-NI/modular substrate — a handful of instructions, not 14 or 174 — and
the software gets leaner by mirroring that atom/composite split. Minimality is the mercy:
the laws-of-everything ALU is bearable because the basis is the irreducible epicycle-set.
Architecture design-reading only; CAD/fab ban holds.*
