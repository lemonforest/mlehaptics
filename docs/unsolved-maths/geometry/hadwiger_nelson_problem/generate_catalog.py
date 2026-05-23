"""
Hadwiger-Nelson problem cascade.

Question: chromatic number chi(R^2) of the plane. What is the minimum number
of colors needed to color the plane so that no two points at unit distance
share a color?

Status:
  - 5 <= chi(R^2) <= 7 (current bounds)
  - 1950 Nelson posed: lower bound 4 (from Moser spindle)
  - 2018 de Grey: improved lower bound to 5 (Polymath16 follow-up)
  - Upper bound 7 (regular-hexagonal tiling, diameter < 1)
  - OPEN: is it 5, 6, or 7?

Class cascade: A o L o I o C o K o N o M

Per [[feedback_no_lineage_claims_in_notebook]].
"""

import datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import best_rat_signed
from srmech.amsc.format import sha256_bytes


ROSTER = [
    dict(label="Lower bound 4 (Moser spindle)", year=1961, bound_type="lower",
         bound_value=4, anchor="Moser-Moser 1961; 7-vertex graph with chi=4",
         fermata="historical first non-trivial lower bound"),
    dict(label="Lower bound 5 (de Grey breakthrough)", year=2018, bound_type="lower",
         bound_value=5, anchor="de Grey 2018; 1581-vertex unit-distance graph",
         fermata="major breakthrough; Polymath16 reduced size to ~510 vertices"),
    dict(label="Upper bound 7 (hexagonal tiling)", year=1950, bound_type="upper",
         bound_value=7, anchor="Nelson 1950; regular-hexagonal tiling with diameter < 1",
         fermata="canonical 7-coloring; tight construction"),
    dict(label="Current OPEN range 5 <= chi(R^2) <= 7", year=2026, bound_type="range",
         bound_value=-1, anchor="Polymath16 + de Grey 2018",
         fermata="OPEN: precise value unknown"),
    dict(label="Hadwiger-Nelson in higher dim chi(R^3)", year=2026, bound_type="higher_dim",
         bound_value=15, anchor="Cantwell 1996: chi(R^3) >= 6; Coulson 2002: chi(R^3) <= 15",
         fermata="OPEN for d >= 3 in general"),
    dict(label="chi(R^d) general asymptotic", year=2026, bound_type="higher_dim",
         bound_value=-1, anchor="Larman-Rogers 1972: chi(R^d) >= (1+o(1)) * (1.2)^d",
         fermata="OPEN exact growth rate"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "bound.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    for entry in ROSTER:
        payload = json.dumps(entry, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {**entry, "class_cascade": "A-compose-L-compose-I-compose-C-compose-K-compose-N-compose-M",
               "computation_hash": chash,
               "source_doi": "https://en.wikipedia.org/wiki/Hadwiger%E2%80%93Nelson_problem",
               "source_published_date": "2026-05-23",
               "entered_locally_at": now_iso[:10]}
        records.append(rec)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    for entry in ROSTER:
        print(f"  {entry['year']}: {entry['label']}")


if __name__ == "__main__":
    main()
