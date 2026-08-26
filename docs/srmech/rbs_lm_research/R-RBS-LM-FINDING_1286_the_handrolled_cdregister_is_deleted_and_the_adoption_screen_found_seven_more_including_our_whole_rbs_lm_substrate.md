# F1286 — **the hand-rolled `CDRegister` is deleted** (F1275's 352/352 reproduces exactly on the shipped op), and the adoption screen found **seven more hand-rolled surfaces srmech now ships — including `srmech.rbs_lm`, which is our entire RBS-LM substrate, upstreamed.**

## (1) `CDRegister` — deleted, and the result re-verified
F1275 built a general-rung register **because srmech had none**. rc297 shipped `cascade.cd_register` plus `cd_navmap` / `cd_navigate` / `cd_basis_product` / `cd_navmap_is_signed_permutation` (and native `_c` peers). The local class is gone; the harness now calls the shipped op and **reproduces 352/352 (100 %) at dim 32**, involution intact at 16/32/64.

**Nothing was lost by deleting it** — which is the test of whether a deletion is safe. Keeping it would have meant maintaining a second, less-tested implementation of a supported surface.

## (2) The screen — what else is hand-rolled and now shipped
Method: AST-collect every local `def`/`class`, diff against srmech's live introspected surface, then filter to same-domain or prototype-file matches. (Raw name-matching produces mostly noise — `bind`, `cos`, `bisect`, `main`, `describe` collide by coincidence and were excluded.)

| our local surface | now ships in | status |
|---|---|---|
| **`ContextSubstrate`, `RBSLMInferenceSubstrate`, `encode_word_k4`, `encode_bigram_l1`, `encode_skeleton_l2`, `encode_sentence_l3`, `sim_k4_batch`, `token_seed`, `CoherenceReadout`** | **`srmech.rbs_lm`** | **the entire substrate, upstreamed** |
| `CDRegister` | `srmech.amsc.cascade` | **DELETED here** |
| `eulerian_path`, `eulerian_circuit` | `srmech.amsc.laplacian` | prototype adopted |
| `graph_to_kernel`, `kernel_to_graph` | `srmech.amsc.genome` | prototype adopted |
| `recover_check` | `srmech.amsc.laplacian` | prototype adopted |
| `cooccurrence_edges` | `srmech.amsc.text` | prototype adopted |
| `cd_mult` | `srmech.amsc.cascade` | prototype adopted |

**`srmech.rbs_lm` is the headline.** The RBS-LM arc opened 2026-05-25 as a research reading; it is now a **shipped srmech module**. `_canonical_substrate.py` and `_rbs_lm_inference.py` are local copies of code that has an upstream home.

## (3) Deleted vs annotated — the distinction, and why it is not the same call
**`CDRegister` was deleted.** T32's premise was *"srmech has no general register, so I built one"* — that premise is now false, so the class is dead weight, and F1275 had already been re-verified against the shipped op when rc297 landed.

**The five prototypes were annotated, not deleted.** Those files *are the record of prototyping* — the local definition is what the finding documents. Deleting it destroys the artifact that produced the result. Each now carries an **ADOPTED UPSTREAM** notice naming the shipped op, so the rule is explicit: *kept as-run, but new code calls the shipped op; do not copy the prototype forward.*

The failure mode this prevents is quiet and real: a prototype gets copy-pasted into new work long after the real op landed, and the branch ends up maintaining a divergent second implementation — which is precisely how the rc256 drift happened (#1454 §1).

## (4) This is the other half of `rcdiff.py`
F1285 built the two-way check and its **ADDED** column flagged `CDRegister` et al. on first run. **This finding is that column being acted on** rather than merely printed — which is the whole point of having it. The standing loop is now complete:

> **after every rc bump: `rcdiff.py` → migrate what BROKE → delete or annotate what was ADOPTED.**

Composes **F1285** (the rcdiff discipline, whose ADDED column this closes), **F1275** (the register, built here and now deleted here), **#1454 §1** (the drift this prevents), `[[feedback_introspect_srmech_before_python_dispatch]]`, `[[project_rbs_lm_arc]]` (the arc that became a module).
