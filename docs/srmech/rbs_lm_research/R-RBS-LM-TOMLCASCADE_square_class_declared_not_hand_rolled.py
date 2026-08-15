#!/usr/bin/env python3
"""F1344 — the FULL square_class op, DECLARED as config-driven TOML. F1343 retracted.

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
print("3 - THE FULL OP -- and the RETRACTION of F1343's 'missing leaf' claim")
print("=" * 80)
print("""  F1343 (mine, hours ago) said collapsing the parity vector to the squarefree
  INTEGER needed a leaf that did not exist. THAT WAS WRONG, and it was reasoning
  rather than measurement. Two things I had not checked:

    1. `dead_band` IS a Class-K integer gate. Its own docstring opens
       "Class K (pin-slot dead-band): gate a non-negative magnitude at a band."
       I asserted no Class-K leaf took an integer while one was in the list I printed.

    2. A chain step may name ANY op by DOTTED PATH -- it is not limited to the 13
       leaves at all. My own working descriptor already did this
       (op = "srmech.cascade.leaves.seq_get"), so the evidence against my claim was
       inside the artifact I used to make it.

  And the gate that actually does the job is Class N:
      rational_pow_uint((p, 1), parity)  ->  (p, 1) if parity==1, (1, 1) if parity==0
  Raising to a BIT *is* "admit this prime, or admit the identity". Arithmetic
  selection, no branch -- so the chain stays data-SIZED, never data-DEPENDENT.
""")

full = [(1001000, 10010), (254000, 635), (9081000, 10090), (36, 1),
        (13, 13), (62750, 2510), (1, 1), (4, 1), (2510, 2510)]
for n, want in full:
    got = tuple(D.run_cascade_chain("square_class", {"n": n}))
    ck(f"square_class({n})", got, (want, 1))

print("""
  THE WHOLE OP, declared: J factor -> E seq_get x3 -> I mod_add(e,0,2)
                          -> E pair -> N rational_pow_uint -> N rational_mul FOLD.
  Nine A-N steps, zero Python, zero new C symbols.
""")

print("=" * 80)
print("4 - WHAT IS STILL UNBUILT -- and this time WHY, not a guess")
print("=" * 80)
print("""  The F_2 RANK is NOT built here, and the obstacle is NOT a missing op:
  XOR on parity bits is already `mod_add(a, b, 2)`, which ships.

  The obstacle is a DELIBERATE guarantee. compose.py states the MAP form is
  "data-SIZED, never data-DEPENDENT: no predicate decides continuation" -- that is
  a TOTALITY invariant, not an oversight. Textbook Gaussian elimination branches on
  whether a leading bit is set, so it is out of the form BY DESIGN.

  A branchless fixed-size elimination (mask-multiply instead of if) would be
  data-sized and should therefore fit. I HAVE NOT TRIED IT. That is an untested
  conjecture, not a limitation -- recorded that way precisely because the last
  thing I recorded as a limitation turned out to be one I had not tried.
""")

print("=" * 80)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 80)
raise SystemExit(1 if FAILED else 0)
