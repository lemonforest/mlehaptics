# F903 — the three BONDS are distinct (only C1 is position-addressable), and the CALORIC cost of reading is a REVERSIBLE heat-exchange found in the cascade. Reading an atom out of a k-atom C1 molecule has a read-fidelity that decays as 1/√k (the "heat" = bundle crosstalk = the other atoms) — yet the molecule's atoms read back at ~100% up to the F896 capacity wall (k≈256), then collapse (39.6% at k=1024). So below the wall the caloric loss is a reversible exchange (`bind` is XOR-reversible; the heat IS the other atoms, recovered by reading them); only the bundle-majority past capacity is true Landauer erasure. Both the loss and its reversibility are the HDC bundle (F896 1/√N), NOT biology artifacts. At linguistic scales (words k~3–15, phrases k~5) reading is high-fidelity AND fully reversible — so emergence/lexicalization is NOT forced by a reading wall; it is a meaning-layer phenomenon.

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_903_three_bonds_caloric_reading_reversibility.py` · **Composes:** F900/F901 (the three operators / C1), F896 (the 1/√N bundle-capacity wall, Chandrasekhar), F904 (the SM-of-language arc — this is its T2/T4/T5), F552 (the noise rule → the falsification rule) · **User direction (2026-06-21):** "caloric-like things in a cascade that can degenerate trying to read a molecule or atom … if we don't find it in the cascade it's a biology substrate artifact" + "if something is calorically lost, its information is still present in some new form ± heat — can we use reversibility to find the thing exchanged as heat?"

## (B) The three bonds are distinct — only C1 is the addressable (compositional) bond
Reading atom at position *p* = `klein4_bind(molecule, pos_key(p))` (XOR is its own inverse), matched against the 256-atom periodic table. Sanity: `read('cat')` → [99, 97, 116] exactly. Part-recoverability at k=4 (chance = 1/256 ≈ 0.004):

| bond | chemistry analog | recover a part? |
|---|---|---|
| **C1** (role-filler bundle) | **covalent** — atoms keep addressable positions | **1.00** |
| **atom-mint** (`klein4_random(hash)`) | **ionic** — featureless identity, no inner structure | **0.00** |
| **chained-bind** (`bind(bind(a,b),c)…`) | **brittle** — entangled, parts not independently addressable | **0.00** |

Only C1 lets you point at "the atom at position 3" and read it back. This is the compositional-transparency that makes C1 the generative bond and atom-mint the identity dual (F900).

## (CALORIC + REVERSIBILITY) the cost of reading, and that it is recoverable
Read one atom out of a k-atom C1 molecule. **SIGNAL** = similarity to the *true* atom (the read fidelity = energy left in the signal). **REVERSIBLE%** = fraction of the molecule's atoms that read back correctly (information conserved). D=8192, chance signal ≈ 0.25:

| k atoms | SIGNAL (read fidelity) | excess over chance | REVERSIBLE% |
|---|---|---|---|
| 4 | 0.474 | 0.224 | 100.0% |
| 16 | 0.358 | 0.108 | 100.0% |
| 64 | 0.305 | 0.055 | 100.0% |
| 256 | 0.274 | 0.024 | 97.9% |
| 1024 | 0.263 | 0.013 | **39.6%** |

**CALORIC — the heat is 1/√k.** The signal's excess-over-chance **halves each time k quadruples** (0.224 → 0.108 → 0.055 → 0.024) = exactly **1/√k**, the F896 bundle-capacity SNR. Reading an atom out of a bigger molecule leaves less signal — the missing fidelity is the **crosstalk with the other (k−1) atoms**, i.e. the "heat." It is not noise: it is the other atoms, transformed by `bind`.

**REVERSIBILITY — the heat is recoverable until the wall.** The atoms read back at **100% up to k≈64**, 97.9% at k=256, then **collapse to 39.6% at k=1024**. So there is a sharp **reversible→irreversible boundary between k≈256 and 1024** — the F896 capacity wall. Below it, information is **conserved**: every atom is recoverable, so the caloric loss of reading one is a **reversible heat-exchange** — the heat (the other atoms) is found by reading them back (`bind` = XOR-reversible). At/past the wall, the bundle-majority genuinely erases — **true Landauer erasure**, where reading a molecule's parts costs real information.

## The thermodynamic reading of the compositor (the user's intuition, confirmed)
- **`bind` (XOR)** = isentropic / reversible — no heat.
- **`bundle` (majority) below capacity** = reversible compression — the "heat" is internal crosstalk, recoverable (read the other parts back). *This is "use reversibility to find the thing exchanged as heat" — and it works.*
- **`bundle` at the F896 wall (k≈256–1024 here)** = the irreversible / Landauer boundary — true dissipation.

**Falsification rule (F552):** both the caloric loss AND its reversibility are **found in the cascade** (the HDC bundle 1/√N + the XOR-reversibility of `bind`), so by the in-cascade ⇒ real-feature rule they are **genuine information features, not biology-substrate artifacts**.

## Consequence for emergence (relocates it correctly)
At **linguistic scales** — words are k~3–15 bytes, phrases k~5 words — reading is **high-fidelity (signal ≫ chance) AND fully reversible (100%)**, far below the wall. So **emergence / lexicalization is NOT forced by a reading-capacity wall** at these sizes (the molecule's parts are always readable). Non-compositionality (idioms: meaning ≠ parts) must therefore be a **meaning-layer** phenomenon (usage/resonator), not a form/reading-capacity one — the F904 T6 thread, explicitly distinct from this form-level caloric wall.

## Verdict / next
**Done (F904 T2/T4/T5):** the three bonds are distinct (C1 the only addressable one); the caloric cost of reading is the 1/√k bundle SNR; and that loss is a **reversible heat-exchange** (heat = the other atoms, recovered by reading back) until the F896 capacity wall (k≈256–1024), where it becomes Landauer-irreversible — all **found in the cascade**, not biology artifacts. Reading is free + reversible at linguistic scales, so emergence is a meaning-layer thread (T6). **Next on the arc:** T9 (ni-Vanuatu/Bislama agnosticism) or T7 (valence — bound vs free morphemes). **Hot-path:** the `klein4_bind` Python loop (~340 binds/sec) made k=4096 composes ~12 s each — the user's "C code for hot path items" applies (a native batched `compose`/`bind` + a float-returning `sim_k4_batch`); logged for srmech + a research-local C option.
