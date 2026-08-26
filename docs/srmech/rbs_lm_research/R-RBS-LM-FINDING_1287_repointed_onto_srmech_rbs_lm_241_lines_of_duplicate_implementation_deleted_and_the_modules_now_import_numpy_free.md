# F1287 — **the local RBS-LM copies are repointed onto `srmech.rbs_lm`: 241 lines of duplicate implementation deleted, 59 added.** Eight surfaces now re-export from upstream, the four with no upstream equivalent stay local, and both modules **now import numpy-free** — which the local copies could not, since #564 purged numpy from srmech.

## What was repointed
| surface | before | now |
|---|---|---|
| `token_seed`, `encode_word_k4`, `encode_bigram_l1`, `encode_skeleton_l2`, `encode_sentence_l3`, `sim_k4_batch`, `ContextSubstrate` | defined in `_canonical_substrate.py` | **re-exported from `srmech.rbs_lm`** |
| `RBSLMInferenceSubstrate` | defined in `_rbs_lm_inference.py` | **re-exported from `srmech.rbs_lm`** |
| `CanonicalVariableLengthMemory`, `CanonicalHierarchicalMemory`, `build_substrate`, `build_hierarchical_substrate` | local | **stay local — no upstream equivalent** |

**Net: −241 / +59 lines.** Verified live: `cs.encode_word_k4 is srmech.rbs_lm.encode_word_k4` → `True`; same for `ContextSubstrate` and `RBSLMInferenceSubstrate`. **Consumers are untouched** — `cs.encode_word_k4(...)` still resolves, it just resolves upstream.

## Three checks that had to pass before the swap
1. **Signatures already matched.** My first read said they didn't — I had listed only positional args and missed that the local defs carry the same keyword-only `D` / `sector` / `hex_chars`. They were compatible all along; **only the implementations differed** (token-similarity: `token_seed` 1.00, `encode_word_k4` 0.53, `sim_k4_batch` 0.10).
2. **`RBSLMInferenceSubstrate` is a strict superset.** Local methods: `attestation`, `describe`, `from_catalog`, `infer`, `learn`, `next_token_distribution`. Shipped has **all six** plus `from_params`, `next_token_coherence`, `M`, `n_learned`, `vocab_vecs`. **Local-only members: none.** A clean re-export, not a compromise.
3. **The shipped code is not merely equivalent — it is better on the axis that bit us.** `token_seed` is **SHA-256-derived** (`amsc_format.sha256_bytes`), so it is stable across processes and PYTHONHASHSEED-independent. **The shipped module already fixes the #1454 salted-hash defect class**, which the local copy could not.

## The numpy blocker, and the fix
Both local modules did `import numpy as np` **at module level**, and #564 removed numpy from srmech — so **the entire module was unimportable in a current venv, including the parts that never touch numpy.** Only the two local-only memory classes actually need it.

Replaced with a lazy proxy that defers the import until an attribute is touched. **Importing the module no longer requires numpy; only *using* the numpy-dependent local classes does.** Both modules now import clean in a numpy-free environment.

## Honest scope — what this does NOT fix
The three consumers I ran (`R-RBS-LM-131`, `-222`, `-229`) **still fail — because they import numpy themselves**, at their own line 40. Verified identical before and after the repoint by stashing the change. **That is separate #564 debt and this finding does not touch it.** The repoint is clean; the consumers have their own problem.

Also flagged rather than fixed: **`encode_word_k4` does not preserve morphology** — `cat`/`cats` **0.2416** vs `cat`/`dog` **0.2465**, both at the 0.25 orthogonality floor. It is seed-based (`token_seed` → expand), so it is **stable but not resonant** in exactly F1277's sense. That is upstream's design call for the L0 word layer, not a repoint blocker — but it means this layer carries the F899/F1260 limitation in a *stable* form, and anything needing morphology must use `klein4_encode_bytes` instead.

## A defect of mine, corrected
F1286's adoption notice was prepended **above** `from __future__ import annotations`, which must be the first statement — that broke `_canonical_substrate.py` and shipped in the previous commit. The notice now lives **inside** the module docstring, where placement cannot matter. Caught here because the equivalence check could not import the module.

Composes **F1286** (the adoption screen that identified these; its misplaced notice corrected here), **F1285** (`rcdiff.py`), **#1454** (the defect class the shipped module already fixes), **#564** (the numpy purge that made the local copies unimportable), `[[project_rbs_lm_arc]]`.
