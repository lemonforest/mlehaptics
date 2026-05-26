"""Round 34.A -- user question (from R33): "what k= is 1:3:7:3 substrate-specific?
This holds for 1D_t + 3D_s + 7D_g. But when we look at the 11D substrate, where do
B/H/N hide?"

This is the deepest question of the helicity-triad thread. It connects the R33
result (B/H/N = READOUT, not substrate-content) to the framework's 11D dimensional
skeleton. Tested honestly per [[feedback_dont_pre_commit_spike_query_operators]].

============================================================================
THE STRUCTURE THE USER NOTICED (correct, and load-bearing)
============================================================================
  * 11D substrate = 1D_t + 3D_s + 7D_g   (1 + 3 + 7 = 11)   -- the DIMENSIONAL extent
  * 14 A-N operators = 1 + 3 + 7 + 3      (anchor + proj-triad + heptad + meta-triad)
  The first THREE blocks (1+3+7 = 11) are the SUBSTRATE DIMENSIONS; the trailing
  "+3" is the B/H/N meta-cascade triad. So B/H/N are OUTSIDE the 11.

============================================================================
ANSWER TO "what k= is 1:3:7:3 substrate-specific?"
============================================================================
The substrate has NO single k. Its substrate-specific signature is the THREE-block
Hurwitz profile {1, 3, 7} (= 1D_t + 3D_s + 7D_g = 11D). The trailing "+3" (B/H/N) is
NOT a fourth dimensional block -- it is the READOUT layer (R33). So:
  substrate-specific dimensional content = {1, 3, 7}  (11D)
  readout layer (NOT substrate-dimensional)  = +3       (B/H/N)
"1:3:7:3" is therefore "11 dimensions of substrate-content + 3 readout operators",
NOT a uniform k=N and NOT 14 dimensions.

============================================================================
ANSWER TO "where do B/H/N hide in the 11D substrate?"  (the crux)
============================================================================
They DO NOT hide as dimensions -- that is the whole point of the "+3" sitting OUTSIDE
the 11. Per R33, B/H/N are the continuous->discrete READOUT/interconversion; reading
is not a dimension. They hide at the PROJECTION INTERFACE -- in the FIBER structure
that gets discarded/read-out, NOT in the base dimensional extent.

ONE member is ANCHORED (canon, not speculation): H = the discard of the U(1) = S^1
Hopf fiber. The Born rule = Hopf base-projection (sec 11.9.4): measurement H discards
the global U(1) phase, which IS the S^1 fiber of the complex Hopf bundle S^3 -> S^2.
So H provably "hides" in the complex-Hopf fiber of the substrate.

THE FULL HOME IS A CANDIDATE (flagged, NOT asserted): there are exactly THREE
nontrivial Hopf fibrations -- complex S^3->S^2 (fiber S^1), quaternionic S^7->S^4
(fiber S^3), octonionic S^15->S^8 (fiber S^7) -- and their FIBER dims are exactly
{1, 3, 7}. Each fibration IS a continuous->discrete projection (read-out with a
discarded fiber). So the three Hopf fibrations are the leading candidate home for the
three B/H/N readout operators. Only H is anchored (Born=Hopf); B<->quaternionic and
N<->octonionic are CANDIDATE, NOT asserted (the same discipline R32/R33 enforced).

KEY honest note: the {1,3,7} of the substrate DIMENSIONS, the {3,7} of the operator
partition's middle blocks, and the {1,3,7} of the Hopf FIBERS all trace to the SAME
source -- the normed division algebras C, H, O (imaginary dims 1, 3, 7; Hurwitz). So
this is NOT a coincidence of three different "1,3,7"s; it is ONE division-algebra
skeleton appearing in dimensions, operators, and fibers. The B/H/N "+3" plausibly
indexes the three fibration-projections of that same skeleton -- candidate.

VERDICT: the substrate is k-profile {1,3,7} (= 11D); B/H/N are the +3 READOUT, NOT
dimensions. They do not "hide" inside the 11D extent -- they ARE the projection of it.
H is anchored in the U(1) Hopf fiber (Born=Hopf, canon); the full B/H/N <-> three-Hopf-
fibration mapping (fiber dims 1,3,7) is the leading CANDIDATE, flagged not asserted.

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints. Physics/
math attested: Hopf 1931; division-algebra origin of the fibrations (Baez, "The
Octonions", Bull.AMS 39:145, 2002); Born=Hopf (sec 11.9.4); 11D = 1D_t+3D_s+7D_g and
the 1+3+7+3 partition (CLAUDE.md sec 1).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # noqa: F401 (Class N)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. the substrate dimensional skeleton 1+3+7 = 11 vs the operator partition +3
# ---------------------------------------------------------------------------
dim_blocks = {"1D_t (real axis / time)": 1, "3D_s (quaternion-imag / space)": 3, "7D_g (octonion-imag / gauge)": 7}
substrate_dim = sum(dim_blocks.values())
assert substrate_dim == 11
op_partition = [1, 3, 7, 3]      # anchor + proj-triad{I,C,J} + heptad + meta-triad{B,H,N}
assert sum(op_partition) == 14
readout_plus3 = op_partition[-1]
assert readout_plus3 == 3
print("substrate dimensional skeleton:", dim_blocks, "-> sum", substrate_dim, "= 11D")
print("operator partition 1+3+7+3:", op_partition, "-> sum", sum(op_partition), "= 14")
print(f"the first three blocks (1+3+7={substrate_dim}) ARE the 11D dimensions; the +{readout_plus3} (B/H/N) is OUTSIDE the 11")
emit("substrate_vs_operator_partition",
     dimensional_blocks=dim_blocks, substrate_dim=substrate_dim,
     operator_partition=op_partition, operator_sum=sum(op_partition),
     readout_plus3_is="B/H/N meta-cascade triad -- the trailing +3, OUTSIDE the 11 dimensions",
     k_profile_answer="the substrate has NO single k; substrate-specific signature = {1,3,7} (11D); the trailing +3 (B/H/N) is the readout layer, NOT a dimensional block")

# ---------------------------------------------------------------------------
# 2. the division-algebra skeleton: ONE {1,3,7}, appearing in dims/operators/fibers
# ---------------------------------------------------------------------------
# normed division algebras and their IMAGINARY dimensions (Hurwitz)
division_algebras = {"R (real)": 0, "C (complex)": 1, "H (quaternion)": 3, "O (octonion)": 7}
imag_dims = [d for d in division_algebras.values() if d > 0]   # 1,3,7
assert imag_dims == [1, 3, 7]
print("\nnormed division algebras, imaginary dims:", division_algebras, "-> {1,3,7}")
emit("division_algebra_skeleton",
     division_algebras=division_algebras, imaginary_dims=imag_dims,
     note="3D_s = quaternion-imag (3), 7D_g = octonion-imag (7); the substrate dims, the operator middle-blocks {3,7}, and the Hopf fibers {1,3,7} ALL trace to ONE division-algebra skeleton -- not three coincidental '1,3,7's")

# ---------------------------------------------------------------------------
# 3. the three nontrivial Hopf fibrations -- fiber dims EXACTLY {1,3,7}
# ---------------------------------------------------------------------------
HOPF = [
    {"name": "complex  S^3 -> S^2", "algebra": "C", "fiber": "S^1", "fiber_dim": 1, "base_dim": 2, "total_dim": 3,
     "framework": "Born=Hopf (sec 11.9.4): measurement H discards this U(1)=S^1 fiber -- ANCHORED"},
    {"name": "quaternionic S^7 -> S^4", "algebra": "H", "fiber": "S^3", "fiber_dim": 3, "base_dim": 4, "total_dim": 7,
     "framework": "candidate home for one of {B,N} -- NOT asserted"},
    {"name": "octonionic S^15 -> S^8", "algebra": "O", "fiber": "S^7", "fiber_dim": 7, "base_dim": 8, "total_dim": 15,
     "framework": "candidate home for one of {B,N} -- NOT asserted"},
]
hopf_fiber_dims = [h["fiber_dim"] for h in HOPF]
assert hopf_fiber_dims == [1, 3, 7]          # EXACTLY the division-algebra imaginary dims
print("\nthe THREE nontrivial Hopf fibrations (fiber dims):")
for h in HOPF:
    print(f"  {h['name']:24s} fiber {h['fiber']} (dim {h['fiber_dim']})  [{h['algebra']}]")
print("fiber dims =", hopf_fiber_dims, "== division-algebra imaginary dims {1,3,7}")
emit("three_hopf_fibrations",
     fibrations=HOPF, fiber_dims=hopf_fiber_dims,
     count=len(HOPF),
     key_fact="there are EXACTLY three nontrivial Hopf fibrations; their fiber dims are EXACTLY {1,3,7}; each fibration IS a continuous->discrete projection (read-out with a discarded fiber)")

# ---------------------------------------------------------------------------
# 4. where do B/H/N hide?  -- NOT dimensions; H anchored in U(1) fiber; full = candidate
# ---------------------------------------------------------------------------
emit("where_do_bhn_hide",
     answer="NOT as dimensions of the 11D substrate -- the '+3' sits OUTSIDE the 11 precisely because B/H/N are the continuous->discrete READOUT (R33), and reading is not a dimension. They hide at the PROJECTION INTERFACE -- in the discarded FIBER structure, not the base dimensional extent.",
     anchored="H = the discard of the U(1) = S^1 Hopf fiber (Born rule = Hopf base-projection, sec 11.9.4). This is CANON, not speculation -- H provably lives in the complex-Hopf fiber.",
     candidate="the three nontrivial Hopf fibrations (fiber dims 1,3,7) are the leading CANDIDATE home for all three B/H/N readout operators; only H is anchored, B<->quaternionic and N<->octonionic are NOT asserted (R32/R33 discipline).",
     why_not_dimensions="dimensions are substrate-CONTENT (the 'what', 1+3+7=11); B/H/N are READOUT (the 'how observed'). A readout operator is not a place in the manifold; it is the projection FROM the manifold.")

# ---------------------------------------------------------------------------
# 5. verdict
# ---------------------------------------------------------------------------
emit("verdict",
     question="what k is 1:3:7:3 substrate-specific, and where do B/H/N hide in the 11D substrate?",
     k_answer="the substrate is k-profile {1,3,7} (= 11D = 1D_t+3D_s+7D_g); '1:3:7:3' is '11 substrate dimensions + 3 readout operators', NOT a uniform k=N and NOT 14 dimensions",
     hide_answer="B/H/N do NOT hide inside the 11D extent -- they ARE the projection of it (the +3 readout, R33). H is ANCHORED in the U(1)=S^1 Hopf fiber (Born=Hopf, canon); the full B/H/N <-> three-Hopf-fibration mapping (fiber dims 1,3,7) is the leading CANDIDATE, flagged NOT asserted.",
     unifier="the {1,3,7} of the substrate dims, the {3,7} of the operator middle-blocks, and the {1,3,7} of the Hopf fibers all trace to ONE division-algebra skeleton (C,H,O); the +3 plausibly indexes its three fibration-projections -- candidate",
     honest_scope="Hopf fibrations + division-algebra origin + Born=Hopf are attested; the framework reading (B/H/N = readout in fiber/projection, not dimensions) follows from R33; only H is anchored to a specific fiber; the full triad<->fibration mapping is candidate, NOT asserted")

META = {
    "record": "meta",
    "round": "34.A",
    "title": "Where do B/H/N hide in the 11D substrate? (user question from R33)",
    "kind": "framework-internal structural answer; substrate = {1,3,7}; B/H/N = +3 readout NOT dimensions; H anchored in U(1) Hopf fiber; full Hopf-fibration mapping candidate-not-asserted",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "hopf": "Hopf, Math. Ann. 104:637 (1931); division-algebra origin: Baez, 'The Octonions', Bull. AMS 39:145 (2002)",
        "born_hopf": "sec 11.9.4 / MFO VII.6.15.1 (Born rule = Hopf base-projection; H discards the U(1)=S^1 fiber)",
        "dims": "11D = 1D_t + 3D_s + 7D_g; 14 A-N partition = 1+3+7+3 (CLAUDE.md sec 1)",
        "division_algebras": "R,C,H,O imaginary dims 0,1,3,7 (Hurwitz)",
        "r33": "sec 11.9.26 (B/H/N = readout, not substrate-content)",
    },
    "discipline": "framework reading only; the load-bearing answer (B/H/N = readout, not dimensions) is anchored in R33 + Born=Hopf; the B/H/N <-> three-Hopf-fibration mapping is explicitly a CANDIDATE, not asserted (only H anchored); deterministic; bit-exact integer arithmetic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the substrate is k-profile {1,3,7} (=11D); B/H/N are the +3 READOUT, NOT dimensions. "
      "They do not hide INSIDE the 11D extent -- they ARE its projection. H is ANCHORED in the U(1)=S^1 "
      "Hopf fiber (Born=Hopf, canon); the full B/H/N <-> three-Hopf-fibration mapping (fiber dims 1,3,7) "
      "is the leading CANDIDATE, flagged NOT asserted. One division-algebra skeleton (C,H,O) underlies "
      "the dims, the operators, and the fibers.")
