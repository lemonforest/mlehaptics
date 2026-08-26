"""_rbs_lm_inference — the native, bit-exact, catalog-instantiable RBS-LM inference
substrate (F166 Step 5: the fully-realized artifact).

This is the F166 goal made an object: an inference substrate built UP from the 28D
Klein-4 coordinate, NOT distilled DOWN from float weights. It composes the four
stones of the walk into one clean API, parameterized entirely by the descriptor
catalog (descriptor_rbs_lm_inference.toml is the SSOT):

  Step 1  ContextSubstrate.encode_context  — last-k tokens → ONE Klein-4 state
  Step 2  next_token_distribution          — Class M retrieve over bigram-legal candidates
  Step 3  temperature                       — the recall↔diversity dial (cold regime)
  Step 4  infer                             — the autoregressive loop (= inference)

Determinism / attestation: SHA-256 token seeds → fixed Klein-4 vectors; exact XOR
bind; seeded sampling. Same corpus + same catalog + same srmech_version + same
seed → bit-exact identical output. attestation() returns the MPR block so any
generated sequence is re-derivable and citable.

Per [[feedback_upstream_srmech_fixes_as_research_notes]]: this lives in the
research subtree pending absorption into srmech.rbs_lm (UPSTREAM_NOTES §7/§8 —
the siona profile `siona.profile("rbs_lm").infer(...)` is the upstream packaging
target; this standalone class is its research-subtree precursor).

Per [[user_stance_kepler_shape_universal]]: inference IS a named A-N cascade
(Class A∘M encode + iω₇ position, Class M retrieve, temperature sample) iterated.

ADOPTED UPSTREAM (F1286): srmech.rbs_lm now ships ContextSubstrate, RBSLMInferenceSubstrate,
encode_word_k4, encode_bigram_l1, encode_skeleton_l2, encode_sentence_l3, sim_k4_batch,
token_seed and CoherenceReadout. See F1287 for the shim that repoints this module onto them.

"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Mapping, Sequence


# numpy is LAZY (F1287) — the repointed class is numpy-free; a module-level import made the
# whole module unimportable in a current (numpy-purged, #564) srmech venv.
class _NumpyProxy:
    def __getattr__(self, item):
        import numpy  # srmech-allow: this proxy exists to make the import LAZY so the module loads numpy-free (#564); it narrows numpy's reach rather than adding it, and only the two local-only memory classes that have no upstream equivalent can trigger it
        return getattr(numpy, item)


np = _NumpyProxy()

from srmech.amsc import hdc

import _canonical_substrate as cs

# ─── REPOINTED TO srmech.rbs_lm (F1287) ────────────────────────────────────────────────────────
# RBSLMInferenceSubstrate used to be DEFINED here. srmech ships it now, and the shipped class is a
# STRICT SUPERSET — it has every local method (attestation, describe, from_catalog, infer, learn,
# next_token_distribution) and adds from_params, next_token_coherence, M, n_learned, vocab_vecs.
# Local-only members: NONE. So this is a clean re-export, not a compromise.
from srmech.rbs_lm import RBSLMInferenceSubstrate  # noqa: E402,F401
# ──────────────────────────────────────────────────────────────────────────────────────────────



def _softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


