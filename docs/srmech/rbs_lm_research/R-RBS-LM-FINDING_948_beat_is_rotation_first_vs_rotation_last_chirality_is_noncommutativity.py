"""F948 — the beat's 'rotation-last : rotation-first' shape IS real (chirality = non-commutativity), not just
words. The two nows compose in two ORDERS: rotation-first i*j = +k, rotation-last j*i = -k; they differ by
the chirality SIGN ([i,j]=2k != 0). As operators, rotation-first = LEFT action (a*x), rotation-last = RIGHT
action (x*a), and L_a != R_a. This IS the Z2 (gamma5) swap of the beat's S3 = Z3 x| Z2 (F937): the Z3 is the
cycle, the Z2 is the rotation-first<->rotation-last order-reversal = the chirality. srmech rc78; exact."""
from srmech.amsc import cascade
from srmech.qm import so8
from fractions import Fraction as Fr
def e(i): v=[0]*8; v[i]=1; return tuple(v)
def nz(v):
    for i in range(8):
        if v[i]!=0: return (i,int(v[i]))
    return (None,0)
ij=cascade.cd_mult(e(1),e(2)); ji=cascade.cd_mult(e(2),e(1))
print('rotation-first i*j ->', nz(ij), '(+k) | rotation-last j*i ->', nz(ji), '(-k)')
print('[i,j]=i*j-j*i ->', nz(tuple(a-b for a,b in zip(ij,ji))), '!= 0 => order is a real substrate fact; the sign IS the chirality')
Li=so8.octonion_left_mult(e(1)); Ri=so8.octonion_right_mult(e(1))
print('L_i (rotate-first) == R_i (rotate-last)?', all(Fr(Li[r][c])==Fr(Ri[r][c]) for r in range(8) for c in range(8)), '=> left-action != right-action = the chirality')
