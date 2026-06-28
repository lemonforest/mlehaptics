"""F949 — the beat = 2pi = pi+pi via the BIT-EXACT series at the chiral axis; the rotation-LAST chirality is
the ASYMPTOTIC SHADOW RESIDUE (the alternating-sign tail). NOT octonion grouping/non-associativity (user
rejected). Grounded: cos(1 rad) truncations are exact rationals (bit-exact BODY) whose residue ALTERNATES
sign (over/under/over/under) = the chiral shadow, shrinking asymptotically to the limit (the EDGE). The half-
turn cos(pi)=-1 (the chiral flip); 2pi=(-1)^2=+1 => pi+pi. So rotation-first = the bit-exact body (the
present, F942 collapsed); rotation-last = the asymptotic residue (the future, F942 superposed). srmech rc78."""
from srmech.calculus import cos_series_truncate
from srmech.amsc import cascade
true=0.5403023058681398   # cos(1 rad) limit, for residue-sign display only
print('cos(1 rad) partial sums (exact rationals) -- residue alternates sign = the rotation-last shadow:')
for k in [2,3,4,5,6]:
    n,d=cos_series_truncate(1,1,k); res=true-(n/d)
    print('   %2d terms -> %d/%d ~= %.9f  residue %+.2e (%s)'%(k,n,d,n/d,res,'over' if res<0 else 'under'))
n,d=cos_series_truncate(355,113,34)   # cos(pi) via the 355/113 rational anchor
print('cos(355/113 ~= pi) ~= %.8f : magnitude %.6f (Class-K) , sign - (Class-C) = the -1 chiral flip (half-turn)'%(n/d, float(cascade.magnitude(n))/float(cascade.magnitude(d))))
print('2pi = (-1)*(-1) = +1  => 2pi = pi+pi : body bit-exact (rotation-first=present), residue asymptotic (rotation-last=future shadow)')
