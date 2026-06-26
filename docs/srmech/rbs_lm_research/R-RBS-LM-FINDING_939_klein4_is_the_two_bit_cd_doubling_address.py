"""F939 — the Klein-4 boolean belly IS the literal 2-bit address of two Cayley-Dickson doublings (R->C->H).
Grounded: cd_mult on the quaternion basis lands on index a XOR b (= the Klein-4 / V4 group); the sign is
the chirality cocycle (i*j=+k, j*i=-k, i*i=-1); klein4_bind is the (F2)^2 XOR (self-inverse) = V4. So the 4
sectors {0,1,2,3}={1,i,j,k} = the 2-bit CD address; XOR = the quaternion index product; sign = chirality."""
from srmech.amsc import cascade, hdc
def e(a): v=[0,0,0,0]; v[a]=1; return tuple(v)
def prod(a,b):
    r=cascade.cd_mult(e(a),e(b)); idx=[i for i in range(4) if r[i]!=0]
    return (idx[0], int(r[idx[0]])) if len(idx)==1 else ('multi',r)
print('cd_mult index == a XOR b (the Klein-4/V4 group):', all(prod(a,b)[0]==(a^b) for a in range(4) for b in range(4)))
print('sign cocycle: i*j=', prod(1,2), ' j*i=', prod(2,1), ' i*i=', prod(1,1), '(opposite signs = chirality)')
a=hdc.klein4_random(256,seed=1); b=hdc.klein4_random(256,seed=2)
print('klein4_bind self-inverse (a^b^b==a) => (F2)^2 = V4:', hdc.klein4_bind(hdc.klein4_bind(a,b),b).tolist()==a.tolist())
print('=> 4 sectors {0,1,2,3}={1,i,j,k} = 2-bit CD-doubling address; addressing ladder 2:4:8:16 = stacked Klein-4 bits.')
