"""
Smooth 4-dimensional Poincaré conjecture cascade.

Statement: Every smooth manifold homeomorphic to S^4 is diffeomorphic to S^4.

Status by dimension:
  - Topological Poincaré (every homotopy n-sphere is homeomorphic to S^n):
      * n=1, 2: classical
      * n=3: Perelman 2003 (Millennium Prize)
      * n=4: Freedman 1981 PROVED
      * n>=5: Smale 1961
  - Smooth Poincaré (homeomorphic ⇒ diffeomorphic):
      * n<=3: PROVED (trivially)
      * n=4: OPEN (the LAST remaining dimension)
      * n=5: Newman/Mazur PROVED
      * n=6: Milnor 1956 -- exotic 7-spheres exist; smooth Poincaré FAILS for n=7 etc.

The 4-dimensional case is uniquely hard: Freedman proved topological version
but smooth version is open. Casson handles, Akbulut-Kirby corks, etc.

Class cascade: A o L o C o K o N o I o M

Per [[feedback_no_lineage_claims_in_notebook]].
"""

import datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import best_rat_signed
from srmech.amsc.format import sha256_bytes


ROSTER = [
    dict(n=1, topo_status="trivially PROVED", smooth_status="trivially PROVED",
         anchor="classical; n=1 case trivial"),
    dict(n=2, topo_status="trivially PROVED", smooth_status="trivially PROVED",
         anchor="Riemann; classical n=2"),
    dict(n=3, topo_status="PROVED (Perelman 2003)",
         smooth_status="PROVED (Moise 1952; trivially via topological-smooth equivalence in dim 3)",
         anchor="Perelman 2003 Ricci flow; Millennium Prize"),
    dict(n=4, topo_status="PROVED (Freedman 1981)",
         smooth_status="OPEN (the LAST open Poincaré case)",
         anchor="Freedman 1981 topological; Fields Medal; Donaldson 1982 smooth 4-manifold structure constraints",
         fermata="MAJOR OPEN PROBLEM in topology; involves Casson handles, Akbulut-Kirby corks, Heegaard Floer homology"),
    dict(n=5, topo_status="PROVED (Smale 1961)",
         smooth_status="PROVED (smooth coincides with topological for n=5)",
         anchor="Smale 1961 h-cobordism theorem"),
    dict(n=6, topo_status="PROVED (Smale 1961)",
         smooth_status="PROVED (smooth coincides for n=6)",
         anchor="Smale 1961"),
    dict(n=7, topo_status="PROVED",
         smooth_status="FAILS: Milnor 1956 exotic 7-spheres exist!",
         anchor="Milnor 1956 -- 28 distinct smooth structures on S^7; Hurwitz heptadic anchor",
         fermata="EXOTIC 7-SPHERES: Hurwitz heptadic dimension exhibits first smooth-structure multiplicity"),
    dict(n=8, topo_status="PROVED", smooth_status="PROVED (no exotic 8-spheres modulo specific)",
         anchor="Smale + Milnor-Kervaire calculations"),
    dict(n=15, topo_status="PROVED", smooth_status="exotic 15-spheres exist",
         anchor="Kervaire-Milnor 1963 -- 16256 distinct smooth structures on S^15"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "case.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    for entry in ROSTER:
        payload = json.dumps({"n": entry["n"]}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {
            "n": int(entry["n"]),
            "topological_poincare_status": entry["topo_status"],
            "smooth_poincare_status": entry["smooth_status"],
            "is_open_smooth": "OPEN" in entry["smooth_status"].upper(),
            "is_hurwitz_dim": entry["n"] in {1, 3, 7},
            "literature_anchor": entry["anchor"],
            "open_fermata": entry.get("fermata", ""),
            "class_cascade": "A-compose-L-compose-C-compose-K-compose-N-compose-I-compose-M",
            "computation_hash": chash,
            "source_doi": "https://en.wikipedia.org/wiki/Generalized_Poincaré_conjecture",
            "source_published_date": "2026-05-23",
            "entered_locally_at": now_iso[:10],
        }
        records.append(rec)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print(f"{'n':>4} {'topological':<35} {'smooth':<45} {'Hurwitz?':>9}")
    for entry in ROSTER:
        print(f"  {entry['n']:>2} {entry['topo_status'][:33]:<33} {entry['smooth_status'][:43]:<43} {str(entry['n'] in {1,3,7}):>9}")


if __name__ == "__main__":
    main()
