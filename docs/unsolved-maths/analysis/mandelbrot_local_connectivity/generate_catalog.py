"""
Mandelbrot Local Connectivity (MLC) conjecture cascade.

Statement: The Mandelbrot set M is locally connected.

Status: OPEN since posed (~1980s); central open problem in complex dynamics.
Yoccoz proved MLC at all finitely renormalizable parameters (1990s); Kahn-
Lyubich proved it at many infinitely renormalizable parameters (2000s). The
full conjecture remains open at certain bifurcation sequences.

If MLC is true, the Mandelbrot set's combinatorial structure is fully
determined by a kneading sequence (Douady-Hubbard parameterization).

Class cascade: A o L o C o I o K o N o M

  - L: Mandelbrot set IS the connectedness locus of the quadratic family
       z -> z^2 + c; Class L cascade-Laplacian on the parameter space
  - C: cascade-orientation -- external rays land via Douady-Hubbard angle
  - I: cyclic -- bifurcation patterns are Class I cyclic
  - K: pin-slot at zero of local-disconnectedness; MLC IS Class K saturation
  - N: rational anchor -- many Mandelbrot constants (e.g., 2 = escape radius)

Per [[feedback_no_lineage_claims_in_notebook]].
"""

import datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import best_rat_signed
from srmech.amsc.format import sha256_bytes


ROSTER = [
    dict(label="MLC at all finitely renormalizable c", year=1990, status="PROVED (Yoccoz)",
         anchor="Yoccoz 1990s; puzzle techniques",
         fermata="finitely renormalizable parameters resolved"),
    dict(label="MLC at infinitely renormalizable c (some)", year=2009,
         status="PROVED (Kahn-Lyubich; many cases)",
         anchor="Kahn-Lyubich 2009; quasi-additivity law",
         fermata="many infinitely renormalizable cases now closed"),
    dict(label="MLC at remaining infinitely renormalizable c", year=2026,
         status="OPEN",
         anchor="various authors 2010s-2020s",
         fermata="MAJOR OPEN PROBLEM in complex dynamics"),
    dict(label="Mandelbrot set connectedness (Douady-Hubbard)", year=1985,
         status="PROVED (Douady-Hubbard 1982-1985)",
         anchor="Douady-Hubbard 1982; uniformization of complement of M",
         fermata="connectedness PROVED; local connectedness is the next question"),
    dict(label="Hausdorff dimension of boundary dM = 2", year=1998,
         status="PROVED (Shishikura 1998)",
         anchor="Shishikura M (1998). Ann. Math. 147:225-267.",
         fermata="boundary has full Hausdorff dimension 2 in R^2"),
    dict(label="Area of Mandelbrot set", year=2026,
         status="numerical estimates (~1.5065918849)",
         anchor="Bittner 2017 + Förstemann 2012; lower bounds via pixel-counting",
         fermata="exact area unknown analytically"),
    dict(label="MLC + density of hyperbolicity conjecture", year=2026,
         status="MLC implies density of hyperbolicity",
         anchor="Douady-Hubbard implications",
         fermata="hyperbolic components dense IF MLC holds"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "mlc.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    for entry in ROSTER:
        payload = json.dumps({"label": entry["label"]}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {**entry, "is_open": "OPEN" in entry["status"].upper(),
               "is_proved": "PROVED" in entry["status"].upper(),
               "class_cascade": "A-compose-L-compose-C-compose-I-compose-K-compose-N-compose-M",
               "computation_hash": chash,
               "source_doi": "https://en.wikipedia.org/wiki/Mandelbrot_set",
               "source_published_date": "2026-05-23",
               "entered_locally_at": now_iso[:10]}
        records.append(rec)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    for entry in ROSTER:
        print(f"  {entry['year']}: {entry['label']} -- {entry['status']}")


if __name__ == "__main__":
    main()
