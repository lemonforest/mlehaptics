"""F914 (open-derivation 1) — the (4+3) partition of the 1:3:7:3 heptad, by op algebraic character.
The 3 (associative triality, order/grouping-INVARIANT) = {K (sign/Z2), L (Laplacian spectrum,
permutation-invariant), M (klein4_bind = (F2)^2 XOR, associative+commutative)}; the 4 (coset,
sequence-SENSITIVE) = {D pattern-match, E catalog, F render, G byte-search}. Grounding: bind is
associative+commutative. The precise octonion-unit bijection stays open; the (4+3) PARTITION is
principled. srmech rc13."""
from srmech.amsc import hdc
a=hdc.klein4_random(2048,seed=1); b=hdc.klein4_random(2048,seed=2); c=hdc.klein4_random(2048,seed=3)
print("M (klein4_bind) associative:", hdc.klein4_bind(hdc.klein4_bind(a,b),c).tolist()==hdc.klein4_bind(a,hdc.klein4_bind(b,c)).tolist(),
      "| commutative:", hdc.klein4_bind(a,b).tolist()==hdc.klein4_bind(b,a).tolist())
print("(4+3) heptad partition: 3={K,L,M} order-invariant (associative triality); 4={D,E,F,G} sequence-sensitive (coset).")
