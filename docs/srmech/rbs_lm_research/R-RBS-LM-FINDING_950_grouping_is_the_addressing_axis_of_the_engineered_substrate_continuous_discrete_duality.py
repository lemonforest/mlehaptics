"""F950 — grouping (octonion non-associativity) is the ADDRESSING axis of the ENGINEERED/DISCRETE substrate,
NOT the beat's chirality (which is ORDER = non-commutativity, F948). Grounded: order [i,j]!=0 (beat chirality,
lives at H) and grouping (i,j,l)!=0 (addressing, lives at O) are SEPARATE -- a quaternion triple (i,j,k)
ASSOCIATES (grouping=0) yet does NOT commute (order!=0). So a REAL resonator carries its past inherently
(continuous, math-in-construction = the resonant modes); an ENGINEERED resonator must ADDRESS the past
(discrete) and grouping is the address tree (F465). The continuous/discrete duality (DUALITY.md). srmech rc78."""
from srmech.amsc import cascade
def e(i): v=[0]*8; v[i]=1; return tuple(v)
def nz(v): return [(i,int(v[i])) for i in range(8) if v[i]!=0]
def mul(a,b): return cascade.cd_mult(a,b)
a,b,c=e(1),e(2),e(4)
print('ORDER    [i,j]      ->', nz(tuple(x-y for x,y in zip(mul(a,b),mul(b,a)))), '(non-commutativity = beat chirality, H-rung, CONTINUOUS)')
print('GROUPING (i,j,l)    ->', nz(tuple(x-y for x,y in zip(mul(mul(a,b),c),mul(a,mul(b,c))))), '(non-associativity = ADDRESSING, O-rung, DISCRETE)')
qa,qb,qc=e(1),e(2),e(3)
print('quaternion (i,j,k) associator ->', nz(tuple(x-y for x,y in zip(mul(mul(qa,qb),qc),mul(qa,mul(qb,qc))))) or 0, '(ASSOCIATES) yet [i,j]!=0 => order & grouping are SEPARATE axes')
