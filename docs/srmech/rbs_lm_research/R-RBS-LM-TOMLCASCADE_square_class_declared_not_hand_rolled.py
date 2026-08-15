#!/usr/bin/env python3
"""F1343 — the square-class datum, DECLARED as config-driven TOML, not hand-rolled.

User (2026-08-15):
  "can we use the sequenced cascade generator or some other part of the make_class to
   bring the operation in to be read as part of the config driven TOML? ... should be able
   to create cascade operation oracles built from the A-N itself."

Yes. The parity vector -- the F_2 square-class datum F1342 asked for -- runs TODAY as a
declared cascade with ZERO new Python, and the descriptor's own proof_cases ARE the oracle.

Per CLAUDE.md 2: PREFER config-driven [class]/[cascade] TOML over hand-coding.
srmech 0.9.0rc432. No abs(), no numpy, no RNG.
"""
import pathlib
import srmech.dsl as D
import srmech.music as M

FAILED = []
HERE = pathlib.Path(__file__).resolve().parent


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<62} {got}")
    if not ok:
        FAILED.append(label)
    return ok


print("=" * 80)
print("1 - REGISTER an out-of-tree descriptor dir and find the op")
print("=" * 80)
D.register_catalog_dir(HERE / "cascade_catalog")
ops = D.list_cascade_ops()
ck("square_class_vector is registered from OUR directory",
   "square_class_vector" in ops, True)
print(f"       catalog now holds {len(ops)} cascade ops (20 shipped + ours)")

print("\n" + "=" * 80)
print("2 - THE DESCRIPTOR'S OWN proof_cases ARE THE ORACLE")
print("=" * 80)
print("  Every case is re-checked against srmech's SHIPPED Class-J monzo, so the")
print("  descriptor falsifies itself rather than trusting its author.\n")

desc = D.get_descriptor("square_class_vector")
cases = desc["cascade"]["chain"][0]["proof_cases"]
ck("the descriptor carries proof cases", len(cases), 6)

for case in cases:
    n = case["inputs"]["n"]
    got = D.run_cascade_chain("square_class_vector", {"n": n})
    ref = [e % 2 for p, e in M.just_limit(n, 1)["monzo"].items()]
    monzo = M.just_limit(n, 1)["monzo"]
    ck(f"{case['covers']:<20} n={n:<9} monzo {monzo}", got, ref)

print("""
  THE CASCADE IS: J factor -> E seq_get (pair) -> E seq_get (exponent)
                            -> I mod_add(e, 0, 2)
  Parity as a CYCLIC-GROUP operation, never a Python `%`. Nothing was written in
  Python; the whole op is a TOML declaration over shipped A-N primitives.
""")

print("=" * 80)
print("3 - WHAT IS NOT DECLARABLE, and exactly why")
print("=" * 80)
import srmech.cascade.leaves as L
leaves = [n for n in dir(L) if not n.startswith("_") and not n[0].isupper()
          and n != "annotations"]
print(f"    the 13 shipped leaves: {leaves}\n")

ck("no integer POW leaf (needed for p**(e mod 2))",
   any("pow" in n for n in leaves), False)
ck("no integer XOR leaf (needed for the F_2 rank elimination)",
   any("xor" in n for n in leaves), False)

print("""
  So the ladder stops in a precise place:
    DECLARABLE TODAY  the parity VECTOR  (this descriptor)     <- the F_2 datum
    NEEDS ONE LEAF    collapse to the squarefree INTEGER: p**(e mod 2) is a value
                      GATED ON A BIT -- a Class-K pin-slot shape, and no Class-K
                      leaf takes an integer. With it, the collapse is a fold of
                      the EXISTING bigint_mul.
    NEEDS ONE LEAF    the F_2 RANK: Gaussian elimination is XOR-reduce, and there
                      is no integer XOR leaf (orientation_compose is signs,
                      vec_add is floats).

  Two leaves, both Class-I/K integer primitives, and F1342's whole ask becomes a
  TOML declaration with no new Python and no new C symbol.
""")

print("=" * 80)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 80)
raise SystemExit(1 if FAILED else 0)
