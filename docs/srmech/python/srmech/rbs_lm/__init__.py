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

Bit-exactness
-------------
The encode helpers compose the SAME Klein-4 sector algebra as
:mod:`srmech.amsc.hdc` (``klein4_random`` / ``klein4_bind`` / ``klein4_bundle``
/ the fractional-agreement similarity), but at **numpy-array granularity** —
the research code uses its own numpy-level encode helpers rather than the
bytes-based ``hdc.klein4_*`` public API surface, and that numpy semantics is
preserved here verbatim so a generated sequence is re-derivable: same corpus +
same params + same ``srmech_version`` + same seed → bit-identical output.

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

# Scientific tier: numpy is optional as of v0.7.0 (the cascade core is numpy-
# free). Fail with an actionable [scientific] hint, not a bare numpy error.
from srmech._scientific import require_numpy as _require_numpy

_require_numpy("srmech.rbs_lm")

from .substrate import (
    ContextSubstrate,
    encode_bigram_l1,
    encode_sentence_l3,
    encode_skeleton_l2,
    encode_word_k4,
    sim_k4_batch,
    token_seed,
)
from .inference import RBSLMInferenceSubstrate

__all__ = [
    "ContextSubstrate",
    "RBSLMInferenceSubstrate",
    "token_seed",
    "encode_word_k4",
    "encode_bigram_l1",
    "encode_skeleton_l2",
    "encode_sentence_l3",
    "sim_k4_batch",
]
