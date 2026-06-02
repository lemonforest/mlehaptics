#!/usr/bin/env python3
"""Spike #254 — social-amoeba self-partition distributed-body cascade-match.

Generating code for the load-bearing numerical results in
``spike254_social_amoeba_self_partition_distributed_body_cascade_match.md``
(computational-provenance discipline per
``[[feedback_computational_provenance_discipline]]``).

ALL math is routed through **srmech** (Stored-Relationship Mechanism); no stdlib
``math`` and no bare-numpy arithmetic carries a load-bearing result. Per the
monorepo CLAUDE.md §2 ("use srmech for all maths"). No Python ``abs()`` — sign /
boundary handling stays Class-K-pin-slot + Class-C honest per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`` (none needed here:
the Fiedler value is read as the second-smallest eigenvalue, not |λ|).

srmech channel note: the monorepo discipline is "rc-to-TestPyPI first". This
session's sandbox network policy returns HTTP 403 from ``test-files.pythonhosted.org``
(the TestPyPI file host), so the latest 0.7.0rcN wheel could not be installed here.
The math below runs on the graduated **srmech 0.6.0** from production PyPI
(``HAS_NATIVE = True``), which ships the full 14-class A-N vocabulary — Class A
(``sha256_bytes``), Class B (``tlv.tlv_pack``) and Class L (``dense_laplacian`` /
``jacobi_eigvals``) are all present and native-dispatched. The result is
channel-independent.

What this demonstrates
----------------------
(1) **Class B (TLV-framing) IS the self-secreted-partition operator.** The social
    amoeba's slime sheath frames the distributed body into one length-delimited,
    content-addressable object (A∘B). The eusocial-insect colony (spike219 §2.1)
    lacks this *body-scale* Class B — its framing is externalised into the
    environmental pheromone field; the moving collective carries no self-secreted
    envelope.

(2) **Class L algebraic-connectivity signature of the partition-mode.** Open /
    environment-partition (path ``P_n``; ant-like, free ends leak into the
    environment) vs closed / self-partition (cycle ``C_n``; the amoeba slug wrapped
    by its own self-secreted sheath = the closing boundary edge). The self-secreted
    closing boundary raises the Fiedler value λ₂ — the distributed body becomes one
    bounded composite rather than an open chain dissipating into the environment.
"""
from __future__ import annotations

import datetime
import json

from srmech.amsc import tlv  # Class B — TLV (type-length-value) framing
from srmech.amsc.format import sha256_bytes  # Class A — content-addressing
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals  # Class L


def fiedler_lambda2(n: int, edges: list[tuple[int, int]]) -> float:
    """Algebraic connectivity λ₂ = second-smallest Laplacian eigenvalue (Class L).

    λ₁ ≈ 0 is the trivial constant-vector mode (Class K pin-slot at the spectral
    floor); λ₂ is read directly as the second entry of the sorted spectrum — no
    ``abs()`` is taken.
    """
    lap = dense_laplacian(n, edges)
    spectrum = sorted(float(x) for x in jacobi_eigvals(lap))
    return spectrum[1]


def main() -> None:
    records: list[dict] = []

    # ---- (1) Class B: self-secreted sheath == TLV frame around the distributed body
    body_cells = [b"prestalk", b"prespore", b"anterior_like"]  # slug cell-type tokens

    # Ant "distributed body": an unframed token stream living in the shared
    # environment — no self-delimiter, the boundary is wherever the pheromone field
    # reaches (externalised framing).
    ant_stream = b"".join(body_cells)

    # Amoeba "distributed body": each cell TLV-framed (Class B), then the whole
    # bundle framed ONCE MORE by the sheath envelope. The outer length field IS the
    # self-partition boundary — the operator that says "this is where the body ends".
    inner = b"".join(tlv.tlv_pack(i, c) for i, c in enumerate(body_cells))
    amoeba_framed = tlv.tlv_pack(255, inner)  # tag 255 = self-secreted sheath envelope

    # A∘B: the self-framed body is now ONE content-addressable object.
    ant_addr = sha256_bytes(ant_stream)
    amoeba_addr = sha256_bytes(amoeba_framed)

    records.append(
        {
            "record": "class_B_self_framing",
            "ant_body_unframed_len": len(ant_stream),
            "ant_body_has_self_delimiter": False,
            "amoeba_body_framed_len": len(amoeba_framed),
            "amoeba_body_has_self_delimiter": True,
            "amoeba_sheath_envelope_tag": 255,
            "amoeba_outer_length_field_value": len(inner),
            "ant_content_address": ant_addr,
            "amoeba_content_address": amoeba_addr,
            "note": (
                "Class B (TLV) length field = the self-partition boundary; the "
                "ant distributed body is an unframed stream (framing externalised "
                "to the pheromone field), the amoeba body is self-framed (A∘B)."
            ),
        }
    )

    # ---- (2) Class L: open (environment) vs closed (self-sheath) partition spectra
    for n in (4, 6, 8, 12, 24):
        path_edges = [(i, i + 1) for i in range(n - 1)]  # P_n  open / environment-partition
        cycle_edges = path_edges + [(n - 1, 0)]  # C_n  closed / self-partition (sheath edge)
        lam2_open = fiedler_lambda2(n, path_edges)
        lam2_closed = fiedler_lambda2(n, cycle_edges)
        records.append(
            {
                "record": "class_L_partition_spectrum",
                "n_body_segments": n,
                "lambda2_open_env_partition_P_n": lam2_open,
                "lambda2_closed_self_partition_C_n": lam2_closed,
                "closed_over_open_ratio": lam2_closed / lam2_open,
                "note": (
                    "Self-secreted closing boundary (sheath edge) raises algebraic "
                    "connectivity λ₂ — the distributed body becomes one bounded loop "
                    "rather than an open chain dissipating into the environment."
                ),
            }
        )

    stamp = datetime.date.today().isoformat()
    out_path = f"spike254_findings_{stamp}.ndjson"
    with open(out_path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")

    # Echo to stdout for the spike-note transcription.
    for rec in records:
        print(json.dumps(rec, sort_keys=True))


if __name__ == "__main__":
    main()
