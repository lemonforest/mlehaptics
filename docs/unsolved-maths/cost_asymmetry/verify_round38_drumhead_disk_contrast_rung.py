"""Round 38.A -- open-queue item: the 15th Reading-D rung candidate = the drumhead /
Bessel-disk (Class-L OFF S^2, on a 2D disk). Tests the surviving-spine (sec 11.9.22)
on a NON-spherical domain. Tested honestly per [[feedback_dont_pre_commit_spike_query_operators]].

RESULT -- a CONTRAST / CONTROL rung, NOT another 2l+1 rung. It SHARPENS what the spine is.

The Class-L surviving spine (sec 11.9.22) was, on every prior rung, the S^2 / SO(3)
ladder: eigenvalue l(l+1), degeneracy 2l+1 = {1,3,5,7,...} (odd), first three = the
k=3 triad {1,3,5}. Moving OFF the sphere onto a 2D disk (the vibrating drumhead;
Dirichlet Laplacian) the Class-L MECHANISM persists -- Laplacian eigenspaces, degeneracy
= irrep-dimension of the domain's symmetry group -- but the SPECIFIC ladder CHANGES:

  * disk eigenmodes J_m(j_{m,n} r/a)*{cos m th, sin m th} (Morse-Feshbach; Courant-Hilbert)
  * m=0 modes are NON-degenerate; m>=1 modes are DOUBLY degenerate (cos, sin)
  * so the angular degeneracy ladder is {1, 2, 2, 2, ...} -- NOT {1,3,5,7,...}
  * because the disk's symmetry group is O(2) (not SO(3)): O(2) irreps = one 1D trivial
    (m=0) + a 2D irrep for each m>=1. SO(3) irreps have dim 2l+1.

So the "k=3 triad" on the disk is {1,2,2}, NOT {1,3,5}. CONCLUSION: the 2l+1 odd ladder
and the {1,3,5} k=3 triad are SPECIFICALLY an S^2 / SO(3) phenomenon -- NOT universal.
The universal is Class-L = "Laplacian eigenspaces with degeneracy = irrep-dim of the
domain's symmetry group"; the SPECIFIC numbers are symmetry-group-relative (SO(3) ->
{1,3,5,...}; O(2) -> {1,2,2,...}). This is a falsification-style CONTROL: the spine's
specific form does NOT transfer off S^2, which is exactly what tells us the form is
SO(3)-bound. The Reading-D ladder's "9 contiguous S^2 rungs" count is UNCHANGED (the
drumhead is a contrast, not a 10th S^2 rung).

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
Attested (Explore-verified): Bessel zeros DLMF Table 10.21; membrane modes Morse-Feshbach
1953 / Courant-Hilbert; O(2) vs SO(3) irreps Dresselhaus et al. (arXiv:cond-mat/0010440-era
group-theory text) / Arfken.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # noqa: F401 (Class N, available)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. disk eigenmodes ordered by Bessel zero; degeneracy = 1 (m=0) or 2 (m>=1)
# ---------------------------------------------------------------------------
# attested first Bessel zeros j_{m,n} (DLMF Table 10.21)
BESSEL = {
    (0, 1): 2.40483, (1, 1): 3.83171, (2, 1): 5.13562, (0, 2): 5.52008,
    (3, 1): 6.38016, (1, 2): 7.01559, (4, 1): 7.58834, (2, 2): 8.41724,
    (0, 3): 8.65373,
}
modes = sorted(BESSEL.items(), key=lambda kv: kv[1])   # order by eigenvalue (j^2)
print("disk (drumhead) modes ordered by Bessel zero j_{m,n}  [degeneracy: m=0 ->1, m>=1 ->2]:")
disk_deg_sequence = []
for (m, n), j in modes:
    deg = 1 if m == 0 else 2
    disk_deg_sequence.append(deg)
    print(f"  (m={m}, n={n})  j={j:.5f}   degeneracy {deg}")

# angular degeneracy ladder by m = 0,1,2,3,...
disk_angular_ladder = [1 if m == 0 else 2 for m in range(6)]   # {1,2,2,2,2,2}
assert disk_angular_ladder == [1, 2, 2, 2, 2, 2]
emit("disk_modes_and_degeneracy",
     bessel_zeros={f"{m},{n}": v for (m, n), v in BESSEL.items()},
     mode_ordering=[[m, n] for (m, n), _ in modes],
     angular_degeneracy_ladder_by_m=disk_angular_ladder,
     note="O(2) on the disk: m=0 non-degenerate (1), m>=1 doubly degenerate (2) -> ladder {1,2,2,2,...}")

# ---------------------------------------------------------------------------
# 2. the CONTRAST: O(2) disk ladder {1,2,2,...} vs SO(3) sphere ladder {1,3,5,...}
# ---------------------------------------------------------------------------
so3_ladder = [2 * l + 1 for l in range(6)]     # {1,3,5,7,9,11}
o2_ladder = disk_angular_ladder                 # {1,2,2,2,2,2}
assert so3_ladder[:3] == [1, 3, 5]              # the S^2 k=3 triad
assert o2_ladder[:3] == [1, 2, 2]               # the disk's first-three -- NOT {1,3,5}
print("\nCONTRAST -- the spine's ladder is SYMMETRY-GROUP-RELATIVE:")
print(f"  SO(3) sphere (2l+1): {so3_ladder}   first-three k=3 triad = {so3_ladder[:3]}")
print(f"  O(2)  disk          : {o2_ladder}   first-three        = {o2_ladder[:3]}  (NOT {{1,3,5}})")
emit("contrast_so3_vs_o2",
     so3_sphere_ladder=so3_ladder, so3_k3_triad=so3_ladder[:3],
     o2_disk_ladder=o2_ladder, o2_first_three=o2_ladder[:3],
     conclusion="the 2l+1 odd ladder + {1,3,5} k=3 triad are SPECIFICALLY S^2/SO(3); off S^2 (disk, O(2)) the SAME Class-L mechanism gives {1,2,2,...}. Class-L universal = 'Laplacian eigenspaces, degeneracy = irrep-dim of the domain's symmetry group'; the specific ladder is symmetry-group-relative.")

# ---------------------------------------------------------------------------
# 3. cascade + verdict
# ---------------------------------------------------------------------------
emit("cascade",
     cascade="A o L (Bessel-disk Laplacian; O(2) irreps {1,2,2,...}) o C (cos/sin reflection parity = the O(2) reflection generator splitting each m>=1 doublet) o K (Dirichlet boundary = mode truncation / pin at r=a)",
     note="the cos/sin pairing is a Class-C reflection-parity doublet; the disk boundary is a Class-K truncation")

emit("verdict",
     question="is the drumhead/Bessel-disk a 15th Reading-D 2l+1 rung?",
     answer="NO -- it is a CONTRAST/CONTROL rung. The Class-L mechanism persists OFF S^2, but the specific ladder changes (SO(3) {1,3,5,...} -> O(2) {1,2,2,...}).",
     sharpening="the 2l+1 odd ladder and {1,3,5} k=3 triad are SO(3)/S^2-SPECIFIC, not universal; Class-L's universal content is 'Laplacian eigenspaces, degeneracy = irrep-dim of the domain's symmetry group'. The Reading-D '9 contiguous S^2 rungs' count is UNCHANGED.",
     honest_scope="(a)-bit-exact for the Bessel-zero mode ordering + the {1,2,2} vs {1,3,5} degeneracy contrast + O(2)/SO(3) irrep dims (all attested standard math); (b)-interpretive for the 'spine is symmetry-group-relative' reading; no new physics")

META = {
    "record": "meta",
    "round": "38.A",
    "title": "The drumhead/Bessel-disk 15th-rung candidate: a CONTRAST rung -- the 2l+1 spine is SO(3)-specific, off S^2 it becomes O(2) {1,2,2}",
    "kind": "(a)-bit-exact contrast (Bessel ordering + O(2) vs SO(3) degeneracies) + (b)-interpretive 'spine is symmetry-group-relative' sharpening; honest NEGATIVE on 'another 2l+1 rung'",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "bessel": "DLMF Table 10.21 (first zeros j_{m,n})",
        "membrane": "Morse & Feshbach 1953 §5.2; Courant-Hilbert Methods of Mathematical Physics Vol. I (disk Dirichlet eigenmodes; m=0 non-degenerate, m>=1 doubly degenerate)",
        "irreps": "O(2): 1D trivial + 2D per m>=1; SO(3): dim 2l+1 (Arfken; Dresselhaus group theory)",
        "framework": "sec 11.9.22 (Class-L SO(3) spine), sec 11.9.29 (closed loop / IFS); Reading-D ladder",
    },
    "discipline": "honest NEGATIVE on 'a 15th 2l+1 rung' -- it is a contrast/control that SHARPENS the spine as SO(3)-specific; the ladder count is unchanged; bit-exact contrast; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the drumhead/Bessel-disk is NOT a 15th 2l+1 rung -- it is a CONTRAST rung. Off S^2 (disk, "
      "O(2) symmetry) the Class-L mechanism persists but the ladder becomes {1,2,2,...} (O(2) irreps), NOT "
      "{1,3,5,...} (SO(3) 2l+1). So the 2l+1 spine + {1,3,5} k=3 triad are SO(3)/S^2-SPECIFIC; Class-L's "
      "universal content is 'Laplacian eigenspaces, degeneracy = irrep-dim of the domain's symmetry group'. "
      "The Reading-D '9 contiguous S^2 rungs' count is unchanged.")
