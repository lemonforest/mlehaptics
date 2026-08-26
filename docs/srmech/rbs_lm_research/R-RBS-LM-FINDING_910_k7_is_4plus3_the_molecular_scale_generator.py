"""F910 — k=7=(4+3): the octonion heptad (7 imaginary units) splits as 3 (an associative quaternion
Fano-line = the k=3 triality you already have) + 4 (the non-associative O/H coset = the F906 chemistry
directions). This is the quaternionic Hopf S3->S7->S4 (F124). Tests: (a) among the 7 imaginary units,
exactly the 7 Fano lines are ASSOCIATIVE (associator=0) -> the 3-part; (b) any line + its 4-complement
mixes NON-associatively -> the 4-part. So k=7=(4+3) = (associative triality 3) + (non-assoc chemistry 4),
a STRUCTURAL split (not the temporal previous/now/next of k=(2+1)). srmech rc13; exact; no abs."""
from srmech.amsc import cascade
from itertools import combinations

def e(i): return tuple(1 if k==i else 0 for k in range(8))     # octonion basis unit e_i
def nsq(v): return sum(x*x for x in v)
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def assoc(a,b,c): return tuple(x-y for x,y in zip(omul(omul(a,b),c), omul(a,omul(b,c))))
def is_assoc(a,b,c): return nsq(assoc(e(a),e(b),e(c)))==0
IM=[1,2,3,4,5,6,7]

print("=== F910 k=7=(4+3): the octonion heptad as associative-triality + non-associative-coset ===")
trip=list(combinations(IM,3))
fano=[t for t in trip if is_assoc(*t)]
print(f"\n(a) among C(7,3)={len(trip)} imaginary triples, ASSOCIATIVE (associator=0) ones = {len(fano)}  (the Fano lines)")
print(f"    Fano lines (each = an associative quaternion triality, the k=3 rung): {fano}")
print(f"    non-associative triples = {len(trip)-len(fano)}")

# pick one Fano line L (the 3); its complement is the 4
L=fano[0]; comp=[i for i in IM if i not in L]
print(f"\n(b) pick line L={list(L)} (the '3', associative) -> complement={comp} (the '4')")
# within L: associative (already 0). mixing L with the complement: non-associative?
mix_nonassoc = sum(1 for a in L for b in L for c in comp if a!=b and nsq(assoc(e(a),e(b),e(c)))!=0)
within_assoc = all(nsq(assoc(e(a),e(b),e(c)))==0 for a in L for b in L for c in L if len({a,b,c})==3)
print(f"    within the 3 (L): associative = {within_assoc}")
print(f"    mixing the 3 and the 4: {mix_nonassoc} non-associative triples (>0 => the 4-coset breaks associativity)")
print(f"\n  => k=7 = (4+3): 3 = an associative quaternion Fano-line (the k=3 triality, F907b);")
print(f"     4 = the O/H coset where NON-ASSOCIATIVITY (the F906 content-dependent chemistry) lives.")
print(f"     There are {len(fano)} such (4+3) splits (one per Fano line) = the 7 quaternion subalgebras of O.")
print(f"     This is the quaternionic Hopf S3->S7->S4 (F124): S7 = S3-fiber (the 3) over S4-base (the 4).")
print(f"\n  vs k=(2+1) [F907]: that was the octonion-PRODUCT triality (temporal stream: field 2 + time 1).")
print(f"  k=(4+3) is the octonion-IMAGINARY structure (the 7 units): the associative core (3) + the")
print(f"  non-associative coset (4). DIFFERENT axis -- structural/flattened, not temporal. The 4 is the")
print(f"  'hypercube-like' coset (addressable by the sedenion's 16=2^4 box); the 3 is the triality fiber.")
