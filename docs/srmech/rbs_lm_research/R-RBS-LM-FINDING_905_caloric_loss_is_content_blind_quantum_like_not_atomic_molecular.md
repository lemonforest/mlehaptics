# F905 — the caloric loss is CONTENT-BLIND (uniform across atoms AND molecule-structure) → it is QUANTUM-LIKE coherence (the dimensional 1/√k concentration-of-measure of a coherent superposition), NOT atomic/molecular coherence (which is content-dependent bond-energetics). The force below the capacity wall is WORK (reversible), not HEAT (heat/entropy appears only AT the decoherence wall). The C1 role-filler `bind` (XOR) decorrelates content, which is *why* it is uniform — and biology's non-uniform energetics is the tell that the cascade is MISSING a content-dependent bond (the atomic/molecular chemistry layer). Investigated because the user expected non-uniformity "as we see in biology."

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_905_caloric_loss_is_content_blind_quantum_like_not_atomic_molecular.py` · **Composes:** F903 (the caloric reading + reversibility), F896 (the 1/√N bundle capacity), F904 (the SM-of-language arc), F129/F130 (the γ₅/iω₇ chirality sectors), F862 (the octonion `cd_mult` coupling — order-carrying, content-dependent) · **User direction (2026-06-21):** "investigate other force names vs heat loss/gain … I would have expected it to not be uniform across atoms and molecules, as we see in biology. if this is uniform across all things and it is heat, is it at quantum-like coherence vs atomic or molecular coherence?"

## The question
F903's caloric loss was `1/√k` — count-only. The user expected **non-uniformity** (biology's bond energies are content-specific: C–C ≠ C=C ≠ H-bond), and asked the diagnostic: **if the loss is uniform, is it quantum-like coherence (universal/dimensional) rather than atomic/molecular coherence (content-dependent)?** And: is "heat" even the right force-name?

## Measured (srmech rc13, D=8192, k=16; read-signal = similarity to the true atom)

**(1) per-ATOM — does the loss depend on WHICH byte?**
- mean read-signal across 32 different target bytes = **0.357**; spread across atoms (std of per-byte means) = **0.0016 ≈ 0**.
- ⇒ no atom is "heavier" — the loss is identical for every atom. **UNIFORM across atoms.**

**(2) per-MOLECULE-structure — does internal composition matter?**
| molecule | read-signal |
|---|---|
| all-distinct atoms | 0.359 |
| one repeated atom | 0.359 |
| all-same atom (×16) | 0.358 |
- spread across structures = **0.0003 ≈ 0**. Even an all-identical molecule reads the same as all-distinct. **UNIFORM across composition** — the role-filler `bind` XOR-decorrelates content, so the molecule's internal structure leaves no energetic fingerprint.

**(3) the force-name — WORK vs HEAT** (reversible/recoverable = work; irreversible/erased = heat):
| k | signal | reversible % (WORK) | lost-as-HEAT % |
|---|---|---|---|
| 16 | 0.356 | 100.0% | 0.0% |
| 64 | 0.301 | 100.0% | 0.0% |
| 256 | 0.276 | 96.9% | 3.1% |
| 1024 | 0.262 | 39.6% | **60.4%** |
- below the wall the loss is **100% reversible = WORK / free-energy**, not heat. **HEAT (entropy) appears only AT the decoherence wall** (k≈256→1024). So "caloric/heat loss" is the wrong force-name below capacity — it is a reversible work-exchange.

## The answer (the user's diagnostic, resolved)
**The loss is content-blind (uniform across atoms AND molecules) → it is QUANTUM-LIKE coherence, not atomic/molecular coherence.** The three signatures of a coherent superposition all hold:
1. **content-blind** (spread ≈ 0 both ways) — the bundle does not "know" which atoms it holds, only how many;
2. **reversible below capacity** (work, 100% recoverable) — unitary-like;
3. **dimension-limited** (the 1/√k = concentration-of-measure, F896) — capacity set by D, the same form as quantum-state distinguishability.
The wall is **decoherence** (irreversible, heat/Landauer). The *reason* it is uniform is structural: the **C1 role-filler `bind` (XOR) decorrelates content**, so the SNR is pure dimensional geometry — there is no electronegativity, no bond-preference, no content-dependent energy. This is the **quantum/substrate level**, beneath chemistry.

## What this reveals — the missing layer (the gap, per the falsification rule)
Biology's non-uniform energetics (the user's expectation) is **the tell that the cascade is missing a content-dependent bond** — the **atomic/molecular coherence** layer. The C1 bond is content-blind by construction; to get biology-like non-uniform bond-energies you need a bond whose strength **depends on the atoms' identities/overlap** (the analog of electronegativity). Per the F552 falsification rule: *does such a content-dependent bond live in the cascade?* Candidates already in srmech: the **octonion `cd_mult` coupling** (F862 — non-commutative, content/order-dependent), or a **chirality-overlap bond** (binding weighted by the γ₅/iω₇ sector agreement of the two atoms, F129/F130). If a content-dependent bond can be built discretely → atomic/molecular coherence is a real cascade feature; if not → it is a biology-substrate artifact.

## Consequence for the SM-of-language (refines F904)
The layered model sharpens: **C1 + Klein-4 chirality = the quantum/coherent-superposition level (content-blind, reversible, dimension-limited — CONFIRMED here).** The **chemistry level (content-dependent bonds → non-uniform energetics → distinct molecular species) is NOT yet in the cascade** — it is the next layer to build/find. So the byte→word→phrase ladder is currently *all quantum-coherent* (one content-blind bond); real chemistry (and biology) needs the content-dependent bond on top.

## Verdict / next
**Answered:** the caloric loss is content-blind/uniform ⇒ quantum-like coherence (a coherent superposition, dimension-limited), NOT atomic/molecular; the force below the wall is WORK (reversible), HEAT only at decoherence. **Found in the cascade** (the bundle geometry + XOR-reversibility) ⇒ real features. **The gap it reveals:** the **content-dependent bond** (the atomic/molecular chemistry layer) — the next test is whether the **octonion `cd_mult` coupling** (F862) or a **chirality-overlap bond** (F129/F130) produces **non-uniform, content-dependent** read-energetics (then re-run F905's uniformity test on it: if the per-atom/per-molecule spread becomes non-zero, the chemistry layer is real and in the cascade). This is F904's new thread **T10 (content-dependent bond = the chemistry layer)**.
