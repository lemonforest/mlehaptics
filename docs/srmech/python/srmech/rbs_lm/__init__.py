"""srmech.rbs_lm — the §9 RBS-LM inference substrate (F166 walk), packaged.

This module ports the **Relationship-Bound-State Language-Model** inference
substrate out of the research subtree (``docs/srmech/rbs_lm_research/`` on the
parallel ``research/rbs-lm-rolling-2`` branch; UPSTREAM_NOTES §9) into the
shipped ``srmech`` package as a top-level surface — the upstream-absorption
target named in the research artifact's own header.

What it is
----------
An inference substrate built **UP** from the 28-D Klein-4 chirality coordinate,
NOT distilled DOWN from float weights. Tokens are minted to fixed Klein-4
hypervectors via SHA-256 seeds (Class A content-addressing), positionally
role-filler **bound** (Class M) and **bundled** (per-bit majority) into ONE
rolling context state, and the next-token distribution is a Class M associative
retrieve over the bigram-legal candidate set, temperature-sampled. Iterating
that loop IS autoregressive inference.

Determinism + numpy-free (v0.7.5rc113)
--------------------------------------
The encode helpers compose the Klein-4 sector algebra of
:mod:`srmech.amsc.hdc` (``klein4_random`` / ``klein4_bind`` / ``klein4_bundle``
/ the fractional-agreement ``klein4_similarity``) over the framework-native
:class:`~srmech.amsc.hv.HV` carrier — **numpy-free end-to-end** (#564). numpy
was only ever an *incidental* deterministic source here (the per-token vector
seed + the memory subsample + the infer sampler), never a correctness oracle,
so as of rc113 those three sites run on the stdlib ``random.Random`` stream and
the softmax on the Class-N ``rational.exp`` cascade. The values were
re-baselined onto our own RNG ONCE; a generated sequence is re-derivable
forever after: same corpus + params + ``srmech_version`` + seed → bit-identical
output, now with **no numpy present at all** (no eager ``[scientific]`` gate).

Public surface
--------------
* :class:`ContextSubstrate` — the rolling context-state encoder (the "hidden
  state": last-k tokens → ONE Klein-4 vector).
* :class:`RBSLMInferenceSubstrate` — the catalog-/params-instantiable
  inference substrate (``from_catalog`` / ``from_params`` / ``learn`` /
  ``next_token_distribution`` / ``infer`` / ``attestation`` / ``describe``).
* The encode helpers :func:`token_seed`, :func:`encode_word_k4`,
  :func:`encode_bigram_l1`, :func:`encode_skeleton_l2`,
  :func:`encode_sentence_l3`, :func:`sim_k4_batch`.
"""
from __future__ import annotations

# numpy-free as of v0.7.5rc113 (#564 carrier arc): the encode path is the
# framework-native HV surface, and the three former numpy-RNG sites run on the
# stdlib `random` stream. No eager `_require_numpy` gate — `import
# srmech.rbs_lm` succeeds with numpy genuinely absent.
from .substrate import (
    ContextSubstrate,
    encode_bigram_l1,
    encode_sentence_l3,
    encode_skeleton_l2,
    encode_word_k4,
    sim_k4_batch,
    token_seed,
)
from .inference import CoherenceReadout, RBSLMInferenceSubstrate

__all__ = [
    "ContextSubstrate",
    "RBSLMInferenceSubstrate",
    "CoherenceReadout",
    "token_seed",
    "encode_word_k4",
    "encode_bigram_l1",
    "encode_skeleton_l2",
    "encode_sentence_l3",
    "sim_k4_batch",
]
