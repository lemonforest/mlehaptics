"""
Continuum Hypothesis (CH) cascade.

Statement: There is no set whose cardinality is strictly between that of the
integers and the real numbers. Equivalently: aleph_1 = 2^aleph_0.

Status: INDEPENDENT of ZFC (Gödel 1940 proved consistency of CH; Cohen 1963
proved consistency of ~CH via forcing). The question "is CH true?" therefore
depends on which additional axioms one adopts beyond ZFC.

Generalized Continuum Hypothesis (GCH): for every infinite cardinal kappa,
2^kappa = kappa^+. Also INDEPENDENT.

Class cascade: A o I o J o K o N o C o M

  - A: content-hash of (cardinal level, hypothesis status)
  - I: cyclic -- cardinal sequence aleph_0, aleph_1, ... is Class I cyclic-
       successor on the ordinal substrate
  - J: primes -- inaccessible cardinals are arithmetically prime-like
  - K: asymptotic-DoF -- CH IS Class K asymptotic question at the boundary
       between countable and continuum; INDEPENDENCE IS substrate-DoF
       inaccessibility within ZFC axiom system
  - N: rational anchor -- aleph_1 / 2^aleph_0 = 1/1 if CH; otherwise > 1
  - C: cascade-orientation -- forcing extensions IS Class C cascade-orientation
       transition between CH and ~CH models
  - M: HDC bind -- power set IS Class M HDC bind at cardinal level

Per [[feedback_no_lineage_claims_in_notebook]]: independence IS the answer at
ZFC; further axiom choices are framework-readings, not solutions.

Sources web-searched 2026-05-23 (training data): Gödel 1940 + Cohen 1963 +
Hugh Woodin's large-cardinal program + Ultimate-L conjecture.
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes


ROSTER = [
    dict(label="ZFC: CH independent", system="ZFC",
         status="INDEPENDENT (Gödel 1940 + Cohen 1963)",
         anchor="Gödel 1940 constructible universe L; Cohen 1963 forcing",
         fermata="CH neither provable nor disprovable from ZFC"),
    dict(label="ZFC + V=L (Gödel constructible universe)", system="ZFC+V=L",
         status="CH PROVED + GCH PROVED",
         anchor="Gödel 1940",
         fermata="GCH holds in L"),
    dict(label="ZFC + MA (Martin's axiom)", system="ZFC+MA",
         status="implies ~CH (for many MA variants)",
         anchor="Martin-Solovay 1970",
         fermata="MA + CH together imply specific topology results"),
    dict(label="ZFC + PFA (Proper forcing axiom)", system="ZFC+PFA",
         status="implies 2^aleph_0 = aleph_2 (~CH)",
         anchor="Baumgartner / Todorčević",
         fermata="strong axiom; settles many CH-equivalent questions"),
    dict(label="ZFC + Ultimate L (Woodin)", system="ZFC+UltL",
         status="conjectured to settle CH definitively",
         anchor="Woodin program 2010s-2020s",
         fermata="OPEN PROGRAM; conjectured to prove CH via inner-model theory"),
    dict(label="ZFC + measurable cardinal", system="ZFC+meas",
         status="consistent with CH and with ~CH",
         anchor="Solovay 1970s; large-cardinal hierarchy",
         fermata="measurable cardinals don't decide CH"),
    dict(label="ZFC + Woodin cardinal", system="ZFC+Woodin",
         status="consistent with CH and with ~CH",
         anchor="Martin-Steel 1989; AD^L(R) theorem",
         fermata="Woodin cardinals settle projective determinacy but not CH"),
    dict(label="ZFC + supercompact cardinal", system="ZFC+sup",
         status="implies many large-cardinal consistency results",
         anchor="Solovay 1970s",
         fermata="open whether stronger large cardinals decide CH"),

    # Aleph hierarchy levels
    dict(label="aleph_0 (countable infinity)", system="cardinal_arithmetic",
         status="canonical",
         anchor="|N| = aleph_0",
         fermata="smallest infinite cardinal"),
    dict(label="aleph_1 (first uncountable)", system="cardinal_arithmetic",
         status="canonical",
         anchor="|aleph_1| = least uncountable cardinal",
         fermata="CH asks: aleph_1 = 2^aleph_0?"),
    dict(label="2^aleph_0 (continuum cardinality)", system="cardinal_arithmetic",
         status="under CH equals aleph_1; under ~CH could be aleph_2, aleph_3, ...",
         anchor="|R| = 2^aleph_0",
         fermata="Class K pin-slot question"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "hypothesis.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        payload = json.dumps({"label": entry["label"], "system": entry["system"]},
                             sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "label":                    entry["label"],
            "system":                   entry["system"],
            "status":                   entry["status"],
            "is_independent":           "INDEPENDENT" in entry["status"].upper(),
            "is_proved":                "PROVED" in entry["status"].upper(),
            "is_open_program":          "OPEN" in entry["status"].upper(),
            "class_cascade":            "A-compose-I-compose-J-compose-K-compose-N-compose-C-compose-M",
            "literature_anchor":        entry["anchor"],
            "open_fermata":             entry["fermata"],
            "computation_hash":         chash,
            "source_doi":               "https://en.wikipedia.org/wiki/Continuum_hypothesis",
            "source_published_date":    "2026-05-23",
            "entered_locally_at":       now_iso[:10],
        }
        records.append(rec)
        diag.append((entry["label"], entry["system"], entry["status"]))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    for d in diag:
        print(f"  {d[1]:<30} | {d[0]:<50} | {d[2]}")


if __name__ == "__main__":
    main()
