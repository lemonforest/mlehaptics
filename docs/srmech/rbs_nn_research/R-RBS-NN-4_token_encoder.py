"""R-RBS-NN-4 — Token → hypervector encoder with variant-choice protocol

Implements the substrate-native two-tier encoding pattern from
ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md.

Per-token-class encoding decision:
  - 'content'    -> bipolar HDC (existing srmech default; capacity-oriented)
  - 'chirality'  -> Klein-4 HDC with sector tag (F132/F139; chirality-axis encoding)
  - 'plasticity' -> Polar HDC {-1, 0, +1} (F141; graceful decay tolerance)
  - 'hybrid'     -> Klein-4 + plasticity overlay (research path; not standard yet)

The encoder is deterministic from token-string + class-hint via SHA-256
seeding (Class A content-mint).

Per RBS-NN README §0 end-user goal: the user's vocabulary becomes the
binding alphabet directly. The class_hint comes from the user (or from
a token-classifier upstream), not from learned embeddings.

Cross-references:
  - RBS-NN README §0 end-user goal
  - R-RBS-NN-2 user lexicon native binding alphabet
  - R-RBS-NN-3a/3b cascade decomposition (MLP + transformer)
  - ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md (this work's foundation)
  - srmech v0.4.3 catalog (Klein-4 + Polar primitives)
"""
from __future__ import annotations

import hashlib
from typing import Literal

import numpy as np

from srmech.amsc import format as amsc_format
from srmech.amsc import hdc

TokenClass = Literal['content', 'chirality', 'plasticity', 'hybrid']
ChiralitySector = Literal[0, 1, 2, 3]


def token_seed(token: str) -> int:
    """Class A content-mint: SHA-256 of UTF-8 token → deterministic seed."""
    digest = amsc_format.sha256_bytes(token.encode("utf-8"))
    # Take first 8 hex chars (32 bits) as seed
    return int(digest[:8], 16)


def encode_token_bipolar(token: str, D: int) -> np.ndarray:
    """Content-tier: bipolar HDC. Existing srmech default."""
    rng = np.random.default_rng(token_seed(token))
    return rng.choice([-1, 1], size=D).astype(np.int8)


def encode_token_klein4(
    token: str, D: int, chirality_sector: ChiralitySector = 0
) -> np.ndarray:
    """Chirality-tier: Klein-4 HDC with sector tag (F132).

    The 4 chirality sectors per F132 §3:
      0 = RH+ visible matter   (no flip)
      1 = RH- dark antimatter  (iω₇ flip)
      2 = LH+ visible antimat. (γ₅ flip)
      3 = LH- dark matter      (CPT mirror)
    """
    if chirality_sector not in (0, 1, 2, 3):
        raise ValueError(f"chirality_sector must be in {{0,1,2,3}}; got {chirality_sector}")
    rng = np.random.default_rng(token_seed(token))
    base = hdc.klein4_random(D, rng)
    sector_mask = np.full(D, chirality_sector, dtype=np.uint8)
    return hdc.klein4_bind(base, sector_mask)


def encode_token_polar(
    token: str, D: int, density: float = 0.67
) -> np.ndarray:
    """Plasticity-tier: polar HDC {-1, 0, +1} (F141).

    density: fraction of positions that are non-zero (active bindings).
    Lower density = more 'uncertain' / dead-band positions.
    Default 0.67 matches polar_random default.
    """
    if not (0.0 < density <= 1.0):
        raise ValueError(f"density must be in (0, 1]; got {density}")
    rng = np.random.default_rng(token_seed(token))

    # polar_random uses upstream default density
    base = hdc.polar_random(D, rng)
    if density != 0.67:
        # Adjust density manually if user requests different fraction
        # (upstream polar_random doesn't take density param; this is a wrapper)
        current_nz = base != 0
        current_density = float(np.mean(current_nz))
        if density < current_density:
            # Zero out some non-zero positions
            n_to_zero = int((current_density - density) * D)
            nz_indices = np.where(current_nz)[0]
            zero_these = rng.choice(nz_indices, size=n_to_zero, replace=False)
            base[zero_these] = 0
        elif density > current_density:
            # Activate some zero positions
            n_to_activate = int((density - current_density) * D)
            z_indices = np.where(~current_nz)[0]
            n_to_activate = min(n_to_activate, len(z_indices))
            if n_to_activate > 0:
                activate_these = rng.choice(z_indices, size=n_to_activate, replace=False)
                base[activate_these] = rng.choice([-1, 1], size=n_to_activate)
    return base


def encode_token(
    token: str,
    D: int = 8192,
    class_hint: TokenClass = "content",
    chirality_sector: ChiralitySector = 0,
    plasticity_density: float = 0.67,
) -> dict:
    """Token → hypervector encoder with variant-choice protocol.

    Args:
      token: the user-vocabulary string to encode
      D: hypervector dimension (default 8192 per RBS-NN canonical)
      class_hint: one of {'content', 'chirality', 'plasticity', 'hybrid'}
      chirality_sector: 0-3 (only used when class_hint='chirality' or 'hybrid')
      plasticity_density: 0..1 (only used when class_hint='plasticity' or 'hybrid')

    Returns:
      dict with:
        'variant': 'bipolar' | 'klein4' | 'polar' | 'hybrid'
        'hv':      np.ndarray (D,)
        'metadata': {'token', 'class_hint', 'D', 'seed_hex', 'sector', 'density'}
    """
    seed_hex = amsc_format.sha256_bytes(token.encode("utf-8"))[:16]

    if class_hint == "content":
        hv = encode_token_bipolar(token, D)
        variant = "bipolar"
        meta_extra = {}
    elif class_hint == "chirality":
        hv = encode_token_klein4(token, D, chirality_sector)
        variant = "klein4"
        meta_extra = {"sector": chirality_sector}
    elif class_hint == "plasticity":
        hv = encode_token_polar(token, D, plasticity_density)
        variant = "polar"
        meta_extra = {"density_target": plasticity_density,
                      "density_actual": float(hdc.polar_density(hv))}
    elif class_hint == "hybrid":
        # Klein-4 base + plasticity decay overlay
        # Step 1: Klein-4 with chirality tag
        k4 = encode_token_klein4(token, D, chirality_sector)
        # Step 2: convert to polar via sign-bit-of-state extraction
        #  klein4 0 (00) → +1 (visible matter)
        #  klein4 1 (01) → -1 (visible antimatter / iω₇)
        #  klein4 2 (10) → -1 (dark matter / γ₅)
        #  klein4 3 (11) → +1 (CPT-conjugate)
        # XOR with (γ₅ XOR iω₇) bit gives the polar sign
        polar_signs = np.where(((k4 >> 1) ^ (k4 & 1)) == 0, 1, -1).astype(np.int8)
        # Step 3: apply plasticity decay (zero out (1-density) fraction)
        n_zero = int((1.0 - plasticity_density) * D)
        rng = np.random.default_rng(token_seed(token) + 1)  # different rng stream
        zero_positions = rng.choice(D, size=n_zero, replace=False)
        polar_signs[zero_positions] = 0
        hv = polar_signs
        variant = "hybrid"
        meta_extra = {
            "sector": chirality_sector,
            "density_target": plasticity_density,
            "density_actual": float(np.mean(hv != 0)),
        }
    else:
        raise ValueError(
            f"Unknown class_hint: {class_hint}. "
            f"Expected one of: 'content', 'chirality', 'plasticity', 'hybrid'"
        )

    return {
        "variant": variant,
        "hv": hv,
        "metadata": {
            "token": token,
            "class_hint": class_hint,
            "D": D,
            "seed_hex": seed_hex,
            **meta_extra,
        },
    }


def bind_pair(token_a_result: dict, token_b_result: dict) -> dict:
    """Bind two encoded tokens. Variants must match.

    Returns:
      dict with 'hv' and 'metadata' (records the bind pair).
    """
    va = token_a_result["variant"]
    vb = token_b_result["variant"]
    if va != vb:
        raise ValueError(
            f"Cannot bind different variants: {va} vs {vb}. "
            f"Use a variant-converting layer first or match the class_hints."
        )

    a = token_a_result["hv"]
    b = token_b_result["hv"]

    if va == "bipolar":
        bound = (a * b).astype(np.int8)
    elif va == "klein4":
        bound = hdc.klein4_bind(a, b)
    elif va == "polar":
        bound = hdc.polar_bind(a, b)
    elif va == "hybrid":
        # Hybrid uses polar multiplicative bind
        bound = hdc.polar_bind(a, b)
    else:
        raise ValueError(f"Unknown variant for binding: {va}")

    return {
        "variant": va,
        "hv": bound,
        "metadata": {
            "operation": "bind",
            "operand_a_token": token_a_result["metadata"]["token"],
            "operand_b_token": token_b_result["metadata"]["token"],
        },
    }


def similarity(token_result_a: dict, token_result_b: dict) -> float:
    """Variant-aware similarity. Variants must match."""
    va = token_result_a["variant"]
    vb = token_result_b["variant"]
    if va != vb:
        raise ValueError(f"Cannot compare variants: {va} vs {vb}")

    a = token_result_a["hv"]
    b = token_result_b["hv"]

    if va == "bipolar":
        return float(np.mean(a == b) * 2 - 1)
    elif va == "klein4":
        return float(hdc.klein4_similarity(a, b))
    elif va in ("polar", "hybrid"):
        return float(hdc.polar_similarity(a, b))
    else:
        raise ValueError(f"Unknown variant for similarity: {va}")


def random_baseline(variant: str, D: int = 8192, N_trials: int = 100, seed: int = 0) -> float:
    """Compute random-pair similarity baseline for the variant."""
    rng = np.random.default_rng(seed)
    sims = []
    for _ in range(N_trials):
        if variant == "bipolar":
            a = rng.choice([-1, 1], size=D).astype(np.int8)
            b = rng.choice([-1, 1], size=D).astype(np.int8)
            sims.append(float(np.mean(a == b) * 2 - 1))
        elif variant == "klein4":
            a = hdc.klein4_random(D, rng)
            b = hdc.klein4_random(D, rng)
            sims.append(float(hdc.klein4_similarity(a, b)))
        elif variant in ("polar", "hybrid"):
            a = hdc.polar_random(D, rng)
            b = hdc.polar_random(D, rng)
            sims.append(float(hdc.polar_similarity(a, b)))
        else:
            raise ValueError(f"Unknown variant: {variant}")
    return float(np.mean(sims))
