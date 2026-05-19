"""Spike #138 — Proactive cascade-composition explorer.

Orchestrator for the depth-2 exhaustive + depth-3 stochastic enumeration of
the 14-class A-N primitive-class composition space. Each generation cascade
is applied to 5 fixed test substrates (chess / image / ephemeris / quantum /
physarum), then inspected by 5 inspection-cascade orderings, with form
classification recorded per (generation, substrate, inspection).

Schema (per the spike brief):
    {
      "spike": 138,
      "date": "2026-05-18",
      "generation_cascade": ["L", "M"],
      "generation_depth": 2,
      "substrate_id": "chess",
      "inspection_cascade_ordering": "canonical",
      "output_form_classification": "...",
      "inspection_fixed_point_depth": 3,
      "fixed_point_form_sha256": "<64 hex chars>",
      "substrate_invariance_score": 0.82,
      "anomaly_flags": [],
      "per_class_timing_ns": {"A": 1234, "L": 56789, ...},
      "stack_id": "python+c",
      "total_elapsed_ns": 87654
    }

This orchestrator is the Python+C stack. The C-native stack lives at
docs/srmech/c/test/cascade_explorer.c. The Julia driver is optional.

Per the brief's algebra-not-magnitude discipline, this script separates
algebra-level findings (which cascades are identities / which are
substrate-invariant) from magnitude-level findings (timing). The NDJSON
captures both, but the summary report and stance candidates concern only
the algebra-level findings.

Run:
    python notes/spike138_explorer.py [--depth2-only] [--seed 138] [--out PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# Make srmech importable from the source tree without an install.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "python"))

import numpy as np  # noqa: E402

from srmech.amsc import (  # noqa: E402
    _native,
    cyclic,
    dispatch,
    format as amsc_format,
    hdc,
    kepler,
    laplacian,
    naming,
    primes,
    rational,
    search,
    template,
    tlv,
)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

SPIKE_NUMBER = 138
SPIKE_DATE = "2026-05-18"

CLASSES = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N")

# Per the brief: 5 inspection-cascade orderings, fixed-point criterion via
# Class M similarity > 1 - 1e-12, recursion depth cap 5.
INSPECTION_ORDERINGS: Dict[str, Tuple[str, ...]] = {
    "canonical":      ("A", "L", "K", "M", "C", "I", "D"),
    "spectral_first": ("L", "A", "K", "M", "C", "I", "D"),
    "asymptote_first": ("K", "L", "M", "C", "I", "D", "A"),
    "similarity_first": ("M", "L", "C", "K", "I", "A", "D"),
    "cyclic_first":   ("I", "L", "K", "M", "C", "D", "A"),
}

FIXED_POINT_THRESHOLD = 1.0 - 1e-12
INSPECTION_DEPTH_CAP = 5

# HDC vector size (bits = 8 * n_bytes). Default 128 bytes = 1024-bit per
# Kanerva canonical convention. Per srmech.h SRMECH_HDC_MAX_BUNDLE_N = 257.
HDC_NBYTES = 128
HDC_NBITS = HDC_NBYTES * 8

# Form-class taxonomy (from spike brief). Inspection emits one of these.
FORM_TAXONOMY = (
    "identity_attractor",
    "structured_cyclic",
    "sparse",
    "white_noise",
    "hash_like",
    "structured_novel",
    "encoding_pair",
)


# ----------------------------------------------------------------------
# Substrate fixtures
#
# Each substrate produces a canonical "form" — an opaque 128-byte HDC
# vector + an attached spectrum (eigenvalues) + an attached cycle period
# + an attached attestation hash. The 7-class operations transform this
# composite form. We keep substrates small (n ≤ 100 nodes) so everything
# fits the Class L native C bound (256) with room.
# ----------------------------------------------------------------------


def _seeded_rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _laplacian_to_hdc(L: np.ndarray, seed: int) -> bytes:
    """Encode a real-symmetric Laplacian's spectrum into a 128-byte HDC vector.

    The encoding is deterministic given (L, seed). We project the sorted
    eigenvalues into a bit-string by taking sign-bits of a seeded mixing
    matrix * eigenvalue vector. Spectrum is preserved as side metadata.
    """
    n = L.shape[0]
    work = L.copy()
    eigs = laplacian.jacobi_eigvals(work)
    eigs = np.sort(np.asarray(eigs, dtype=np.float64))
    rng = _seeded_rng(seed)
    # Project onto HDC_NBITS random directions.
    proj = rng.standard_normal((HDC_NBITS, n))
    proj_eigs = (proj @ eigs).astype(np.float64)
    bits = (proj_eigs > 0.0).astype(np.uint8)
    # Pack to bytes (big-endian per byte).
    packed = np.packbits(bits, bitorder="big")
    return packed.tobytes()


def make_substrate_chess() -> Dict[str, Any]:
    """8x8 king-adjacency Laplacian (64 nodes)."""
    n = 64
    edges = []
    for r in range(8):
        for c in range(8):
            u = r * 8 + c
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < 8 and 0 <= cc < 8:
                        v = rr * 8 + cc
                        if u < v:
                            edges.append((u, v))
    L = laplacian.dense_laplacian(n, edges)
    return {
        "id": "chess",
        "n": n,
        "L": L,
        "spectrum": None,  # filled by encoder
        "period": 8,       # 8x8 board
        "hdc": _laplacian_to_hdc(L, seed=138_001),
    }


def make_substrate_image() -> Dict[str, Any]:
    """10x10 4-neighbour pixel adjacency Laplacian (100 nodes)."""
    n = 100
    edges = []
    for r in range(10):
        for c in range(10):
            u = r * 10 + c
            # right neighbour
            if c + 1 < 10:
                edges.append((u, r * 10 + c + 1))
            # down neighbour
            if r + 1 < 10:
                edges.append((u, (r + 1) * 10 + c))
    L = laplacian.dense_laplacian(n, edges)
    return {
        "id": "image",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 10,
        "hdc": _laplacian_to_hdc(L, seed=138_002),
    }


def make_substrate_ephemeris() -> Dict[str, Any]:
    """10-body 1/r^2 gravitational-coupling Laplacian.

    Synthetic positions: bodies on a logarithmic spacing in AU, similar
    in shape to the Sun system inner+outer roster.
    """
    n = 10
    rng = _seeded_rng(138_003)
    # Pin first body at origin (Sun); place others log-spaced.
    radii = np.logspace(np.log10(0.39), np.log10(40.0), n - 1)
    angles = rng.uniform(0.0, 2.0 * np.pi, size=n - 1)
    pos = np.zeros((n, 2), dtype=np.float64)
    pos[1:, 0] = radii * np.cos(angles)
    pos[1:, 1] = radii * np.sin(angles)
    edges = []
    weights = []
    for i in range(n):
        for j in range(i + 1, n):
            r2 = float(np.sum((pos[i] - pos[j]) ** 2))
            if r2 < 1e-9:
                continue
            edges.append((i, j))
            weights.append(1.0 / r2)
    L = laplacian.dense_laplacian(n, edges, weights=weights)
    return {
        "id": "ephemeris",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 12,  # 12-month nominal
        "hdc": _laplacian_to_hdc(L, seed=138_003),
    }


def make_substrate_quantum() -> Dict[str, Any]:
    """4-qubit cluster-state graph Laplacian (4 nodes)."""
    n = 4
    # Cluster state on a linear chain.
    edges = [(0, 1), (1, 2), (2, 3)]
    L = laplacian.dense_laplacian(n, edges)
    return {
        "id": "quantum",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 16,  # 2^4 = 16 amplitudes
        "hdc": _laplacian_to_hdc(L, seed=138_004),
    }


def make_substrate_physarum() -> Dict[str, Any]:
    """10-node synthetic tube-network Laplacian (Tero / Nakagaki form)."""
    n = 10
    rng = _seeded_rng(138_005)
    # Random geometric graph on the unit square.
    pts = rng.uniform(0.0, 1.0, size=(n, 2))
    edges = []
    weights = []
    threshold = 0.45
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.linalg.norm(pts[i] - pts[j]))
            if d < threshold:
                edges.append((i, j))
                weights.append(1.0 / (d + 0.01))
    L = laplacian.dense_laplacian(n, edges, weights=weights)
    return {
        "id": "physarum",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 7,
        "hdc": _laplacian_to_hdc(L, seed=138_005),
    }


def build_substrates() -> Dict[str, Dict[str, Any]]:
    return {
        "chess": make_substrate_chess(),
        "image": make_substrate_image(),
        "ephemeris": make_substrate_ephemeris(),
        "quantum": make_substrate_quantum(),
        "physarum": make_substrate_physarum(),
    }


# ----------------------------------------------------------------------
# Form representation
#
# A "form" is a small dict carrying:
#   - hdc:      128-byte HDC vector (the canonical fingerprint)
#   - spectrum: tuple of sorted floats (Laplacian eigenvalues if available)
#   - period:   integer cyclic period (Class I/J output)
#   - tag:      integer dispatch tag (Class D output)
#   - keymap:   tuple of (key, value) bytes pairs (Class E/F output)
#   - rendered: bytes from template render (Class F output)
#   - tlv_blob: bytes from TLV pack (Class B output)
#   - sha:      hex sha256 of the canonical serialisation (Class A output)
#
# Class operators read from / write to this dict. We keep the dict small.
# ----------------------------------------------------------------------


def init_form(substrate: Dict[str, Any]) -> Dict[str, Any]:
    """Initialise the working form from a substrate."""
    L = substrate["L"]
    work = L.copy()
    eigs = laplacian.jacobi_eigvals(work)
    eigs = np.sort(np.asarray(eigs, dtype=np.float64))
    return {
        "hdc": substrate["hdc"],
        "spectrum": tuple(float(x) for x in eigs.tolist()),
        "period": int(substrate["period"]),
        "tag": 0,
        "keymap": tuple(
            (b"k%d" % i, ("v%d" % int(round(e * 100))).encode("ascii"))
            for i, e in enumerate(eigs[:8])
        ),
        "rendered": substrate["hdc"][:32],
        "tlv_blob": b"",
        "sha": "",
        "L": L,            # carry Laplacian along so Class L is repeatable
        "L_n": L.shape[0],
        "substrate_id": substrate["id"],
    }


def form_canonical_bytes(form: Dict[str, Any]) -> bytes:
    """Canonical-byte representation of the (substrate-invariant) form payload.

    Used for sha256 attestation and fixed-point detection. Excludes the
    Laplacian matrix itself (which never changes mid-cascade) and the
    substrate_id (so fixed-point hashes are comparable across substrates).
    """
    chunks = [
        b"HDC:",
        form["hdc"],
        b"|SPEC:",
        ",".join("%.10g" % v for v in form["spectrum"]).encode("ascii"),
        b"|PER:",
        str(form["period"]).encode("ascii"),
        b"|TAG:",
        str(form["tag"]).encode("ascii"),
        b"|KEYS:",
        b";".join(k + b"=" + v for (k, v) in form["keymap"]),
        b"|REND:",
        form["rendered"],
        b"|TLV:",
        form["tlv_blob"],
    ]
    return b"".join(chunks)


# ----------------------------------------------------------------------
# Class operators (the 14 primitives)
#
# Each operator takes (form, rng) and returns (form_new, op_id_str). The
# op_id_str is just the class letter; for timing we record per-class
# wall-clock ns from time.perf_counter_ns().
# ----------------------------------------------------------------------


def op_A(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class A — content-addressing (SHA-256)."""
    canon = form_canonical_bytes(form)
    sha = amsc_format.sha256_bytes(canon)
    new = dict(form)
    new["sha"] = sha
    # Mix sha bytes into HDC (XOR first 32 bytes).
    sha_bytes = bytes.fromhex(sha)
    hdc_arr = bytearray(new["hdc"])
    for i in range(32):
        hdc_arr[i] ^= sha_bytes[i]
    new["hdc"] = bytes(hdc_arr)
    return new


def op_B(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class B — TLV byte-canonical pack."""
    new = dict(form)
    packed = tlv.tlv_pack(0x42, form["hdc"][:64])
    new["tlv_blob"] = packed
    return new


def op_C(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class C — cascade-orientation (streaming-equivalent reorder).

    The C-port form is NDJSON streaming; the algebraic content at this
    level is "consume tokens in order and produce a transformed stream".
    We instantiate by reversing the HDC byte stream (a length-preserving
    deterministic stream re-orientation) and rotating the spectrum.
    """
    new = dict(form)
    new["hdc"] = form["hdc"][::-1]
    # Spectrum rotation by 1.
    spec = form["spectrum"]
    if spec:
        new["spectrum"] = spec[1:] + (spec[0],)
    return new


def op_D(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class D — dispatch (multi-needle pattern match)."""
    rules = [
        (b"\x00" * 4, 1),
        (b"\xff" * 4, 2),
        (b"\xaa\x55", 3),
        (b"\x55\xaa", 4),
    ]
    matched, tag = dispatch.match(form["hdc"], rules)
    new = dict(form)
    new["tag"] = int(tag) if matched else 0
    return new


def op_E(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class E — catalog (sorted-key lookup)."""
    new = dict(form)
    # Look up tag-derived key in current keymap.
    key = ("k%d" % (form["tag"] % max(1, len(form["keymap"])))).encode("ascii")
    val = naming.lookup(key, list(form["keymap"]))
    if val is not None:
        # Update keymap so the looked-up pair is promoted to front.
        promoted = [(key, val)]
        for (k, v) in form["keymap"]:
            if k != key:
                promoted.append((k, v))
        new["keymap"] = tuple(promoted)
    return new


def op_F(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class F — template render."""
    new = dict(form)
    if not form["keymap"]:
        return new
    tpl = b"<{" + form["keymap"][0][0] + b"}>"
    try:
        rendered = template.render(tpl, dict(form["keymap"]))
    except Exception:
        rendered = tpl
    new["rendered"] = rendered[: max(1, len(form["hdc"]) // 4)]
    return new


def op_G(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class G — byte search."""
    new = dict(form)
    needle = form["hdc"][:4]
    # Wrap-around search: find needle elsewhere in HDC.
    hay = form["hdc"][4:] + form["hdc"][:4]
    off = search.byte_search(hay, needle)
    new["period"] = int(off) % max(1, form["period"]) if off is not None else form["period"]
    return new


def op_H(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class H — self-introspection.

    Read the srmech version + ABI, fold into form as a stable string. This
    is deliberately near-identity per the brief's framing: H is the
    inspector's own self-check.
    """
    new = dict(form)
    # Mix a stable 8-byte fingerprint of ABI+version into HDC.
    fp_str = ("srm:" + str(_native.EXPECTED_ABI_VERSION)).encode("ascii")[:8]
    fp_bytes = fp_str + b"\x00" * (8 - len(fp_str))
    hdc_arr = bytearray(new["hdc"])
    for i in range(8):
        hdc_arr[i] ^= fp_bytes[i]
    new["hdc"] = bytes(hdc_arr)
    return new


def op_I(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class I — cyclic-group modular arithmetic."""
    new = dict(form)
    n = max(2, form["period"])
    # (period * 3 + tag) mod n + 1, keeping it inside [1, n-1].
    val = cyclic.mod_pow(3, max(1, form["period"]), n)
    new["period"] = (int(val) + form["tag"]) % n + 1
    return new


def op_J(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class J — prime-factorisation / period."""
    new = dict(form)
    p = max(2, form["period"])
    if primes.is_prime(p):
        # Already prime; leave as-is but bump tag.
        new["tag"] = (form["tag"] + 1) % 256
    else:
        factored = primes.factor(p)  # List[Tuple[prime, exponent]]
        new["period"] = int(factored[0][0]) if factored else p
    return new


def op_K(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class K — asymptotic-DOF / pin-slot Kepler."""
    new = dict(form)
    # Use first eigenvalue magnitude as M (mean anomaly); fixed eccentricity.
    if not form["spectrum"]:
        return new
    M = (abs(form["spectrum"][0]) + abs(form["spectrum"][-1])) / 2.0
    M = M - (M // (2.0 * 3.141592653589793)) * (2.0 * 3.141592653589793)
    e = 0.3
    try:
        E = kepler.kepler_solve(M, e, 1e-10, 60)
    except Exception:
        E = M
    phi = kepler.pin_slot(E, 0.5, 1.0)
    # Mix phi into HDC top 16 bytes.
    phi_bytes = bytes.fromhex(("%016x" % (abs(int(phi * 1e15)) & ((1 << 64) - 1))).rjust(16, "0"))
    phi_bytes = (phi_bytes + b"\x00" * 16)[:16]
    hdc_arr = bytearray(new["hdc"])
    for i in range(16):
        hdc_arr[i] ^= phi_bytes[i]
    new["hdc"] = bytes(hdc_arr)
    return new


def op_L(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class L — graph Laplacian / eigendecomp.

    Re-spectrum the carried Laplacian (idempotent on spectrum but cheap).
    Then permute the spectrum tuple by a small fixed shift derived from tag.
    """
    new = dict(form)
    L = form["L"]
    work = L.copy()
    eigs = laplacian.jacobi_eigvals(work)
    eigs = np.sort(np.asarray(eigs, dtype=np.float64))
    spec = tuple(float(x) for x in eigs.tolist())
    new["spectrum"] = spec
    return new


def op_M(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class M — HDC binding (XOR)."""
    new = dict(form)
    # Bind HDC with a tag-derived mask so the operation is observable but
    # invertible (M is self-inverse under XOR).
    mask = bytes(((form["tag"] + i) & 0xFF) for i in range(len(form["hdc"])))
    bound = hdc.bind(form["hdc"], mask)
    new["hdc"] = bound
    return new


def op_N(form: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    """Class N — rational approximation / continued fraction."""
    new = dict(form)
    if not form["spectrum"]:
        return new
    s = form["spectrum"][0] + 1.0  # shift away from zero
    if s <= 0:
        s = 1.0
    num = int(round(s * 1_000_000))
    den = 1_000_000
    p, q = rational.best_rational(num, den, 1024)
    new["period"] = max(2, int(q))
    return new


OPS: Dict[str, Callable[[Dict[str, Any], np.random.Generator], Dict[str, Any]]] = {
    "A": op_A, "B": op_B, "C": op_C, "D": op_D, "E": op_E, "F": op_F, "G": op_G,
    "H": op_H, "I": op_I, "J": op_J, "K": op_K, "L": op_L, "M": op_M, "N": op_N,
}


# ----------------------------------------------------------------------
# Form classifier (the inspector emits one of FORM_TAXONOMY per
# (generation_output, inspection_ordering)).
# ----------------------------------------------------------------------


def _bit_entropy(b: bytes) -> float:
    """Shannon bit-entropy over bit values in 0..1."""
    if not b:
        return 0.0
    bits = np.unpackbits(np.frombuffer(b, dtype=np.uint8))
    p1 = float(bits.mean())
    p0 = 1.0 - p1
    h = 0.0
    for p in (p0, p1):
        if p > 0:
            h -= p * np.log2(p)
    return h


def _hdc_similarity(a: bytes, b: bytes) -> float:
    """+1 = identical, 0 = orthogonal (HDC convention)."""
    return float(hdc.similarity(a, b))


def _spectral_beta(spec: Sequence[float]) -> float:
    """Estimate spectral slope beta from log-log fit.

    Returns 0 if the spectrum is too short or degenerate. Positive beta
    means power-law-like decay (1/f^beta in spectral density).
    """
    if len(spec) < 4:
        return 0.0
    s = np.array(sorted(spec, reverse=True), dtype=np.float64)
    s = s[s > 1e-12]
    if len(s) < 4:
        return 0.0
    rank = np.arange(1, len(s) + 1)
    try:
        slope, _ = np.polyfit(np.log(rank), np.log(s), 1)
    except Exception:
        return 0.0
    return float(-slope)


def classify_form(initial: Dict[str, Any], final: Dict[str, Any], depth: int) -> str:
    """Emit a single FORM_TAXONOMY label for the (initial -> final) transition.

    Decision rules (algebra-first, magnitude-second). Order matters — rules
    are evaluated top-to-bottom; first matching rule wins.

      1. identity_attractor: HDC similarity > FIXED_POINT_THRESHOLD AND
         spectrum unchanged AND period unchanged.
      2. structured_cyclic: HDC differs but period is a small integer
         (in [2..6]) AND spectrum unchanged.
      3. sparse: top-k of |spectrum| accounts for > 95% of L1 mass.
      4. hash_like: bit-entropy(HDC) > 0.99 AND a sha attestation has been
         attached (Class A or downstream).
      5. white_noise: bit-entropy(HDC) > 0.99 AND no sha attached.
      6. encoding_pair: HDC changed significantly (sim < 0.5) AND the
         Hamming-distance between initial.hdc and final.hdc is mostly in
         a contiguous span (the "encoded mask" signature) AND spectrum +
         period are unchanged. We approximate "contiguous span" by checking
         that > 75% of the differing bits cluster in one half of the
         vector.
      7. structured_novel: anything not caught above.

    Note: XOR-self-inverse trivially holds for any pair under bind, so we
    do NOT use that as the encoding_pair signal — it is vacuous.
    """
    sim = _hdc_similarity(initial["hdc"], final["hdc"])
    spec_changed = initial["spectrum"] != final["spectrum"]
    period_changed = initial["period"] != final["period"]
    hdc_entropy = _bit_entropy(final["hdc"])

    # Rule 1: identity attractor (most stringent: nothing changed).
    if (sim > FIXED_POINT_THRESHOLD) and (not spec_changed) and (not period_changed):
        return "identity_attractor"

    # Rule 2: structured cyclic — period landed in a small-integer band.
    if (2 <= final["period"] <= 6) and not spec_changed and sim < FIXED_POINT_THRESHOLD:
        return "structured_cyclic"

    # Rule 3: sparse — top-k mass concentration.
    if final["spectrum"]:
        s = np.abs(np.array(final["spectrum"], dtype=np.float64))
        total = float(s.sum())
        if total > 1e-9:
            s_sorted = np.sort(s)[::-1]
            top_k = max(1, len(s) // 4)
            mass = float(s_sorted[:top_k].sum())
            if mass / total > 0.95:
                return "sparse"

    # Rule 4 / 5: high-entropy → hash_like or white_noise.
    if hdc_entropy > 0.99:
        if final.get("sha"):
            return "hash_like"
        return "white_noise"

    # Rule 6: encoding_pair — HDC changed but the change is structured.
    if sim < 0.5 and (not spec_changed) and (not period_changed):
        diff_bits = np.unpackbits(np.frombuffer(
            bytes(a ^ b for a, b in zip(initial["hdc"], final["hdc"])),
            dtype=np.uint8,
        ))
        n_diff = int(diff_bits.sum())
        if n_diff > 0:
            half = len(diff_bits) // 2
            first_half = int(diff_bits[:half].sum())
            second_half = int(diff_bits[half:].sum())
            max_half = max(first_half, second_half)
            if max_half / max(1, n_diff) > 0.75:
                return "encoding_pair"

    return "structured_novel"


# ----------------------------------------------------------------------
# Cascade application
# ----------------------------------------------------------------------


def apply_cascade(
    initial_form: Dict[str, Any],
    cascade: Sequence[str],
    rng: np.random.Generator,
) -> Tuple[Dict[str, Any], Dict[str, int], int]:
    """Apply a cascade (sequence of class letters) to a form.

    Returns (final_form, per_class_ns, total_ns).
    """
    form = initial_form
    per_class_ns: Dict[str, int] = {}
    total_start = time.perf_counter_ns()
    for cls in cascade:
        op = OPS[cls]
        t0 = time.perf_counter_ns()
        form = op(form, rng)
        elapsed = time.perf_counter_ns() - t0
        per_class_ns[cls] = per_class_ns.get(cls, 0) + elapsed
    total_ns = time.perf_counter_ns() - total_start
    return form, per_class_ns, total_ns


def run_inspection(
    initial_form: Dict[str, Any],
    generation_output: Dict[str, Any],
    inspection_cascade: Sequence[str],
    rng: np.random.Generator,
) -> Tuple[str, int, str, List[str]]:
    """Run the inspection cascade recursively until fixed-point or depth-cap.

    The inspection cascade's job is to find the cascade output's attractor
    — apply iteratively until consecutive iterations agree (Class M
    similarity > 1 - 1e-12 AND spectrum + period unchanged) or the
    depth cap is reached. We track cycle-of-length-> 1 separately.

    Form classification is based on the GENERATION-output's relation to
    the INITIAL form (algebra-level question: what did the generation
    cascade do to the substrate?). The inspection's role is to verify
    the cascade output is stable; it does NOT relabel.

    Returns (form_classification, fixed_point_depth, fixed_point_sha, anomaly_flags).
    """
    flags: List[str] = []
    cur = generation_output
    prev_canon = form_canonical_bytes(cur)
    seen_canons = {prev_canon}
    fixed_depth = INSPECTION_DEPTH_CAP
    for depth in range(1, INSPECTION_DEPTH_CAP + 1):
        new, _per_class, _total = apply_cascade(cur, inspection_cascade, rng)
        sim = _hdc_similarity(cur["hdc"], new["hdc"])
        if (sim > FIXED_POINT_THRESHOLD
                and cur["spectrum"] == new["spectrum"]
                and cur["period"] == new["period"]):
            fixed_depth = depth
            cur = new
            break
        canon = form_canonical_bytes(new)
        if canon in seen_canons:
            cur = new
            fixed_depth = depth
            flags.append("recursion_cycles")
            break
        seen_canons.add(canon)
        cur = new

    # Classify the GENERATION output relative to the INITIAL form.
    classification = classify_form(initial_form, generation_output, fixed_depth)
    # Final-form-sha (post-inspection) — used for fixed-point catalog.
    final_canon = form_canonical_bytes(cur)
    final_sha = hashlib.sha256(final_canon).hexdigest()
    return classification, fixed_depth, final_sha, flags


# ----------------------------------------------------------------------
# Cascade generator pass
# ----------------------------------------------------------------------


def enumerate_depth2() -> List[Tuple[str, ...]]:
    return [(a, b) for a in CLASSES for b in CLASSES]


def sample_depth3(n_samples: int, seed: int) -> List[Tuple[str, ...]]:
    rng = random.Random(seed)
    seen: set[Tuple[str, ...]] = set()
    out: List[Tuple[str, ...]] = []
    while len(out) < n_samples:
        tri = (rng.choice(CLASSES), rng.choice(CLASSES), rng.choice(CLASSES))
        if tri in seen:
            continue
        seen.add(tri)
        out.append(tri)
    return out


# ----------------------------------------------------------------------
# Run a single (generation, substrate, inspection) cell.
# ----------------------------------------------------------------------


def run_cell(
    generation_cascade: Sequence[str],
    substrate: Dict[str, Any],
    inspection_name: str,
    inspection_cascade: Sequence[str],
    rng_seed: int,
    stack_id: str,
) -> Dict[str, Any]:
    rng = _seeded_rng(rng_seed)
    initial = init_form(substrate)
    gen_output, per_class_ns, total_ns = apply_cascade(initial, generation_cascade, rng)
    classification, fp_depth, fp_sha, flags = run_inspection(
        initial, gen_output, inspection_cascade, rng
    )
    return {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "generation_cascade": list(generation_cascade),
        "generation_depth": len(generation_cascade),
        "substrate_id": substrate["id"],
        "inspection_cascade_ordering": inspection_name,
        "output_form_classification": classification,
        "inspection_fixed_point_depth": fp_depth,
        "fixed_point_form_sha256": fp_sha,
        "anomaly_flags": flags,
        "per_class_timing_ns": per_class_ns,
        "stack_id": stack_id,
        "total_elapsed_ns": total_ns,
    }


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth2-only", action="store_true",
                    help="Skip depth-3 sampling (4900 cells, fast smoke).")
    ap.add_argument("--depth3-samples", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=138)
    ap.add_argument("--stack-id", default="python+c")
    ap.add_argument("--out", default=str(HERE / "spike138_findings_2026-05-18.ndjson"))
    args = ap.parse_args()

    print(f"spike138: HAS_NATIVE={_native.HAS_NATIVE}, ABI={_native.NATIVE_ABI_VERSION}")
    print(f"spike138: stack_id={args.stack_id}, seed={args.seed}, out={args.out}")

    substrates = build_substrates()
    print(f"spike138: built {len(substrates)} substrates")

    cascades_d2 = enumerate_depth2()
    print(f"spike138: depth-2 cascades = {len(cascades_d2)}")
    if args.depth2_only:
        cascades_d3 = []
    else:
        cascades_d3 = sample_depth3(args.depth3_samples, args.seed)
    print(f"spike138: depth-3 cascades = {len(cascades_d3)}")

    all_cascades = cascades_d2 + cascades_d3
    total_cells = len(all_cascades) * len(substrates) * len(INSPECTION_ORDERINGS)
    print(f"spike138: total cells = {total_cells}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    classify_counter: Counter[str] = Counter()
    identity_by_cascade: defaultdict[Tuple[str, ...], List[str]] = defaultdict(list)
    invariance_by_cascade: defaultdict[Tuple[str, ...], Dict[str, Counter]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    fingerprint_by_cascade: defaultdict[Tuple[str, ...], List[str]] = defaultdict(list)
    per_class_total_ns: Counter[str] = Counter()
    per_class_call_count: Counter[str] = Counter()
    cells_done = 0

    t0 = time.perf_counter()
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        # First row: framing.
        framing = {
            "spike": SPIKE_NUMBER,
            "date": SPIKE_DATE,
            "kind": "framing",
            "stack_id": args.stack_id,
            "has_native": bool(_native.HAS_NATIVE),
            "native_abi": int(_native.NATIVE_ABI_VERSION or 0),
            "n_classes": len(CLASSES),
            "n_substrates": len(substrates),
            "n_cascades_depth2": len(cascades_d2),
            "n_cascades_depth3": len(cascades_d3),
            "n_inspection_orderings": len(INSPECTION_ORDERINGS),
            "total_cells": total_cells,
            "fixed_point_threshold": FIXED_POINT_THRESHOLD,
            "inspection_depth_cap": INSPECTION_DEPTH_CAP,
            "anchor_citation": "Spike #138 brief; depth-2 exhaustive + depth-3 stochastic; 5 inspection orderings",
        }
        fh.write(json.dumps(framing) + "\n")

        for cas in all_cascades:
            for sub_id, sub in substrates.items():
                for ins_name, ins_cas in INSPECTION_ORDERINGS.items():
                    rec = run_cell(cas, sub, ins_name, ins_cas, args.seed, args.stack_id)
                    fh.write(json.dumps(rec) + "\n")
                    classify_counter[rec["output_form_classification"]] += 1
                    if rec["output_form_classification"] == "identity_attractor":
                        identity_by_cascade[tuple(cas)].append(f"{sub_id}/{ins_name}")
                    invariance_by_cascade[tuple(cas)][ins_name][sub_id] = (
                        rec["output_form_classification"]
                    )
                    fingerprint_by_cascade[tuple(cas)].append(rec["fixed_point_form_sha256"])
                    for cls, ns in rec["per_class_timing_ns"].items():
                        per_class_total_ns[cls] += ns
                        per_class_call_count[cls] += 1
                    cells_done += 1
                    if cells_done % 1000 == 0:
                        elapsed = time.perf_counter() - t0
                        rate = cells_done / max(elapsed, 1e-9)
                        eta = (total_cells - cells_done) / max(rate, 1e-9)
                        print(f"  {cells_done}/{total_cells} cells, "
                              f"{elapsed:.1f}s elapsed, ETA {eta:.0f}s, "
                              f"rate {rate:.0f} cells/s")

        # Summary rows.
        summary = {
            "spike": SPIKE_NUMBER,
            "date": SPIKE_DATE,
            "kind": "summary",
            "stack_id": args.stack_id,
            "cells_done": cells_done,
            "wall_seconds": time.perf_counter() - t0,
            "classification_counts": dict(classify_counter),
            "per_class_total_ns": dict(per_class_total_ns),
            "per_class_call_count": dict(per_class_call_count),
        }
        fh.write(json.dumps(summary) + "\n")

        # Identity-attractor catalog.
        # A cascade is a "universal identity attractor" if it produces
        # identity_attractor on ALL (substrate, inspection) pairs.
        n_required = len(substrates) * len(INSPECTION_ORDERINGS)
        universal_identities = []
        partial_identities = []
        for cas, occurrences in identity_by_cascade.items():
            if len(occurrences) == n_required:
                universal_identities.append(list(cas))
            elif len(occurrences) >= n_required // 2:
                partial_identities.append({"cascade": list(cas), "n_hits": len(occurrences),
                                           "n_total": n_required})
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "identity_attractor_catalog",
            "stack_id": args.stack_id,
            "universal_count": len(universal_identities),
            "partial_count": len(partial_identities),
            "universal_identities": universal_identities,
            "partial_identities": partial_identities[:50],  # cap
        }) + "\n")

        # Substrate-invariant cascades — same classification across ALL 5
        # substrates for at least one inspection ordering.
        substrate_invariant = []
        for cas, by_ins in invariance_by_cascade.items():
            for ins_name, by_sub in by_ins.items():
                if len(by_sub) == len(substrates) and len(set(by_sub.values())) == 1:
                    substrate_invariant.append({
                        "cascade": list(cas),
                        "inspection_ordering": ins_name,
                        "classification": next(iter(by_sub.values())),
                    })
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "substrate_invariant_catalog",
            "stack_id": args.stack_id,
            "count": len(substrate_invariant),
            "samples": substrate_invariant[:100],
        }) + "\n")

        # Inspection-ordering robustness — for each cascade, count distinct
        # classifications across the 5 inspection orderings (per substrate).
        ordering_dependent = []
        for cas, by_ins in invariance_by_cascade.items():
            for sub_id in substrates.keys():
                seen_class = set()
                for ins_name, by_sub in by_ins.items():
                    if sub_id in by_sub:
                        seen_class.add(by_sub[sub_id])
                if len(seen_class) > 1:
                    ordering_dependent.append({
                        "cascade": list(cas),
                        "substrate_id": sub_id,
                        "distinct_classifications": sorted(seen_class),
                    })
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "ordering_dependent_cases",
            "stack_id": args.stack_id,
            "count": len(ordering_dependent),
            "samples": ordering_dependent[:100],
        }) + "\n")

        # Form-attractor catalog: distinct fixed-point fingerprints per cascade.
        fingerprint_buckets = Counter()
        for cas, fps in fingerprint_by_cascade.items():
            distinct = len(set(fps))
            fingerprint_buckets[distinct] += 1
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "fingerprint_distribution",
            "stack_id": args.stack_id,
            "histogram_distinct_fp_per_cascade": dict(fingerprint_buckets),
        }) + "\n")

    print(f"spike138: done in {time.perf_counter() - t0:.1f}s, wrote {cells_done} cells to {out_path}")
    print(f"spike138: classifications = {dict(classify_counter)}")
    print(f"spike138: universal identities = {len(universal_identities)}")
    print(f"spike138: substrate-invariant occurrences = {len(substrate_invariant)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
