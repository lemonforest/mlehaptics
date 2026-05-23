"""
Reverse mathematics cascade (Big Five subsystems).

Reverse mathematics: which axioms are required to prove which theorems of
ordinary mathematics. The Big Five subsystems of second-order arithmetic:

  RCA_0   <  WKL_0  <  ACA_0  <  ATR_0  <  Pi_1_1-CA_0

Most ordinary-mathematics theorems are equivalent to exactly ONE of the Big
Five. Friedman's Grand Conjecture: all theorems of "concrete" mathematics
provable in ZFC are already provable in EFA (Elementary Function Arithmetic);
OPEN.

Class cascade: A o I o C o K o N o J o M

  - A: content-hash of (system, equivalence)
  - I: cyclic -- 5 systems form a Class I cyclic-ordinal hierarchy
  - C: cascade-orientation -- containment direction (proof-strength
       ordering) IS Class C orientation
  - K: pin-slot at zero -- each theorem's "axiom strength" IS Class K
       saturation depth in the proof-theoretic substrate
  - N: rational anchor -- 5 = 1+3+1 partition? 5 = Hurwitz-adjacent
       (between 3 triadic and 7 heptadic)
  - J: primes -- consistency strengths anchored at large-cardinal primes
  - M: HDC bind -- theorem-to-axiom mapping IS Class M bind

Friedman's grand conjecture remains OPEN. Per [[feedback_no_lineage_claims_in_notebook]].
"""

import datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import best_rat_signed
from srmech.amsc.format import sha256_bytes


ROSTER = [
    dict(label="RCA_0 (Recursive Comprehension Axiom)", level=1,
         theorems=["Pigeonhole", "intermediate value theorem (continuous)", "basic computable math"],
         anchor="Friedman 1975; Simpson 2009 (Subsystems of Second-Order Arithmetic)",
         fermata="weakest Big Five system; proves basic-computable theorems"),
    dict(label="WKL_0 (Weak König's Lemma)", level=2,
         theorems=["Heine-Borel for [0,1]", "Brouwer fixed-point theorem (continuous functions)", "Hahn-Banach (separable)"],
         anchor="Simpson 2009 chap. IV; Friedman-Simpson 1980s",
         fermata="proves compactness-style theorems"),
    dict(label="ACA_0 (Arithmetical Comprehension Axiom)", level=3,
         theorems=["Bolzano-Weierstrass", "Cantor-Bendixson", "Ramsey for pairs (RT^2_k)"],
         anchor="Simpson 2009 chap. III",
         fermata="proves convergence-style theorems; Hurwitz triadic level"),
    dict(label="ATR_0 (Arithmetical Transfinite Recursion)", level=4,
         theorems=["Determinacy for open games", "perfect set theorem", "comparability of well-orderings"],
         anchor="Simpson 2009 chap. V",
         fermata="proves transfinite-recursion-style theorems"),
    dict(label="Pi^1_1-CA_0 (Pi^1_1 Comprehension Axiom)", level=5,
         theorems=["Cantor-Bendixson on Polish spaces", "Determinacy for Sigma^0_2 games"],
         anchor="Simpson 2009 chap. VI",
         fermata="strongest Big Five; proves descriptive-set-theoretic theorems"),

    # Friedman's Grand Conjecture
    dict(label="Friedman's Grand Conjecture", level=0,
         theorems=["all of ZFC concrete mathematics provable in EFA"],
         anchor="Friedman 1999+; OPEN conjecture",
         fermata="OPEN: would imply most working math fits in very weak system"),

    # Reverse-math equivalences
    dict(label="Brouwer fixed-point theorem", level=2,
         theorems=["equivalent to WKL_0 (Simpson 2009)"],
         anchor="Reverse-math equivalence; WKL_0 level",
         fermata="proved in WKL_0; NOT provable in RCA_0"),
    dict(label="Bolzano-Weierstrass", level=3,
         theorems=["equivalent to ACA_0"],
         anchor="Reverse-math equivalence; ACA_0 level",
         fermata="proved in ACA_0; NOT provable in WKL_0"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "subsystem.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    for entry in ROSTER:
        payload = json.dumps({"label": entry["label"], "level": entry["level"]}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {
            "label": entry["label"], "level": entry["level"],
            "theorems": entry["theorems"], "literature_anchor": entry["anchor"],
            "open_fermata": entry["fermata"],
            "class_cascade": "A-compose-I-compose-C-compose-K-compose-N-compose-J-compose-M",
            "computation_hash": chash,
            "source_doi": "https://en.wikipedia.org/wiki/Reverse_mathematics",
            "source_published_date": "2026-05-23",
            "entered_locally_at": now_iso[:10],
        }
        records.append(rec)

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    for entry in ROSTER:
        print(f"  level {entry['level']}: {entry['label']}")


if __name__ == "__main__":
    main()
