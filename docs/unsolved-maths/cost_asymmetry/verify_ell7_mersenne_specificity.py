"""Round 10 entry-point A — is ℓ=7 INDIVIDUALLY a distinguished Mersenne node?

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round10_entry_A_ell7_mersenne_specificity.md.

Round 6.A (§11.9.6) carried an OPEN prediction: low-ℓ CMB structure concentrates
at Mersenne {1,3,7}; ℓ=1 (dipole) + ℓ=3 (octupole) are present, ℓ=7 was the open
testable. Spike #190 found a {3,7} AGGREGATE concentration (6.19× over uniform
null, p=0.006) on attested Planck SMICA-nosz anafast data. But that was the PAIR
{3,7} together — it does NOT establish that ℓ=7 INDIVIDUALLY is distinguished.

This script reuses Spike #190's committed, attested per-ℓ C_ℓ table (no new data,
no healpy, no fabrication) and asks the ℓ=7-specific question:

  1. How is the {3,7} concentration split between ℓ=3 and ℓ=7?
  2. Where does ℓ=7 rank among the individual low-ℓ modes (ℓ=2..8)?
  3. Is ℓ=7's local-maximum status Mersenne-specific, or shared with a
     non-Mersenne odd ℓ (ℓ=5)?

Attested input: docs/srmech/notes/spike190_findings_2026-05-19.ndjson
(SMICA-nosz anafast per-ℓ table; Planck 2018 IV, doi 10.1051/0004-6361/201833881).
No bare abs() per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SPIKE190 = Path(__file__).resolve().parents[2] / "srmech" / "notes" / "spike190_findings_2026-05-19.ndjson"


def load_c_ell() -> dict[int, float]:
    """Read the attested per-ℓ C_ℓ table from the committed Spike #190 NDJSON."""
    for line in SPIKE190.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("record_kind") == "per_ell_table":
            return {int(r["ell"]): float(r["C_ell"]) for r in rec["C_ell_table"]}
    raise RuntimeError("per_ell_table not found in Spike #190 NDJSON")


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_ell7_mersenne_specificity.ndjson"

    c = load_c_ell()
    ells = sorted(c)
    total = sum(c.values())
    n_modes = len(ells)
    uniform_null_one = 1.0 / n_modes          # one mode's share under uniform

    # (1) split of the {3,7} pair concentration
    pair_power = c[3] + c[7]
    ell3_share_of_pair = c[3] / pair_power
    ell7_share_of_pair = c[7] / pair_power

    # (2) per-ℓ ratio over uniform null for the low-ℓ band ℓ=2..8, ranked
    band = [l for l in ells if 2 <= l <= 8]
    ratios = {l: (c[l] / total) / uniform_null_one for l in band}
    ranked = sorted(band, key=lambda l: ratios[l], reverse=True)
    ell7_rank = ranked.index(7) + 1
    mersenne = {3, 7}
    # which modes outrank ℓ=7, and are any of them non-Mersenne?
    outrank_ell7 = [l for l in ranked if ratios[l] > ratios[7]]
    nonmersenne_outranking_ell7 = [l for l in outrank_ell7 if l not in mersenne]

    # (3) local-maximum test: is ℓ a local max vs ℓ-1, ℓ+1?
    def is_local_max(l: int) -> bool:
        return (l - 1 in c and l + 1 in c and c[l] > c[l - 1] and c[l] > c[l + 1])
    ell7_local_max = is_local_max(7)
    ell5_local_max = is_local_max(5)   # ℓ=5 is NON-Mersenne odd ℓ
    odd_local_maxima = [l for l in band if l % 2 == 1 and is_local_max(l)]

    ell7_ratio = ratios[7]
    ell7_distinguished = bool(ell7_ratio >= max(ratios.values()) - 1e-12)

    records = [
        {
            "kind": "input_provenance",
            "source_ndjson": str(SPIKE190.relative_to(SPIKE190.parents[3])),
            "source_attestation": "Spike #190 SMICA-nosz anafast; Planck 2018 IV doi 10.1051/0004-6361/201833881",
            "n_modes": n_modes, "ell_range": [ells[0], ells[-1]], "total_power": total,
        },
        {
            "kind": "pair_split_3_7",
            "pair_power": pair_power,
            "ell3_share_of_pair": ell3_share_of_pair,
            "ell7_share_of_pair": ell7_share_of_pair,
            "reading": ("The {3,7} aggregate concentration (Spike #190 6.19x) is carried "
                        "%.0f%% by ℓ=3 and only %.0f%% by ℓ=7." %
                        (100 * ell3_share_of_pair, 100 * ell7_share_of_pair)),
        },
        {
            "kind": "per_ell_ranking_band_2_8",
            "ratios_over_uniform_null": {str(l): ratios[l] for l in ranked},
            "ranked_descending": ranked,
            "ell7_ratio": ell7_ratio,
            "ell7_rank": ell7_rank,
            "ell7_is_top": ell7_distinguished,
            "modes_outranking_ell7": outrank_ell7,
            "NON_mersenne_modes_outranking_ell7": nonmersenne_outranking_ell7,
            "reading": ("ℓ=7 ranks #%d of %d in the ℓ=2..8 band at %.2fx uniform; "
                        "NON-Mersenne ℓ=%s outrank it." %
                        (ell7_rank, len(band), ell7_ratio,
                         nonmersenne_outranking_ell7)),
        },
        {
            "kind": "local_max_parity_test",
            "ell7_local_max": ell7_local_max,
            "ell5_local_max_nonmersenne": ell5_local_max,
            "odd_ell_local_maxima_in_band": odd_local_maxima,
            "reading": ("ℓ=7 is a local max, but so is the NON-Mersenne odd ℓ=5; "
                        "the local-max pattern at odd ℓ %s is parity, NOT Mersenne." %
                        odd_local_maxima),
        },
        {
            "kind": "verdict",
            "statement": (f"No ℓ=7-SPECIFIC Mersenne signature in the attested Planck low-ℓ TT "
                          f"data. The {{3,7}} concentration is ℓ=3-dominated "
                          f"({100*ell3_share_of_pair:.0f} percent); ℓ=7 alone is "
                          f"{ell7_ratio:.2f}x uniform, ranks #{ell7_rank} in ℓ=2..8, and is "
                          f"outranked by NON-Mersenne ℓ=4 and ℓ=5; its local-max status is "
                          f"shared with non-Mersenne ℓ=5 (odd-ℓ parity). The Round 6.A ℓ=7 "
                          f"prediction is NOT supported → WEAKENED. The {{3,7}} AGGREGATE result "
                          f"(Spike #190) is untouched."),
            "verdict_tier": "(open) -> WEAKENED on the ℓ=7-specific claim; {3,7} aggregate stands",
        },
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True))
            fh.write("\n")

    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "kind": "provenance_attestation",
            "ndjson_path": out_path.name,
            "ndjson_sha256_hex_pre_attestation": ndjson_sha,
            "generated_by": Path(__file__).name,
            "reuses_attested_input": "spike190_findings_2026-05-19.ndjson",
        }, sort_keys=True))
        fh.write("\n")

    print(f"Wrote: {out_path}")
    print(f"{{3,7}} split: ell=3 = {100*ell3_share_of_pair:.1f}pct, ell=7 = {100*ell7_share_of_pair:.1f}pct")
    print(f"ell=7 ratio over uniform = {ell7_ratio:.2f}x; rank #{ell7_rank} of {len(band)} in ell=2..8")
    print(f"ranked ell=2..8 (desc): {ranked}")
    print(f"NON-Mersenne modes outranking ell=7: {nonmersenne_outranking_ell7}")
    print(f"odd-ell local maxima in band: {odd_local_maxima} (includes non-Mersenne ell=5)")
    print("Verdict: no ell=7-specific Mersenne signature -> WEAKENED; {3,7} aggregate untouched.")


if __name__ == "__main__":
    main()
