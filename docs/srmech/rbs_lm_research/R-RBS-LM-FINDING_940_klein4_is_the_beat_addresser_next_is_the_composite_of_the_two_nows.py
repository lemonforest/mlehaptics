"""F940 — a Klein-4 object IS then+now+now+next, and that's why it addresses: the NEXT address is the
COMPOSITE of the two nows (k = i.j). then(1=anchor) + now(i) + now(j) -> next(k). Both user readings are
one fact: the Klein-4 already carries the beat (recognize it) AND addresses anything, and our recall
failures are mal-formed inputs (half-beat / sector-locked, F843) -- give one now, it lands on a now and
never produces NEXT. srmech rc58; grounded on cd_mult (F939 i.j=k)."""
from srmech.amsc import cascade
def e(a): v=[0,0,0,0]; v[a]=1; return tuple(v)
def cd(a,b): return cascade.cd_mult(a,b)
def sec(r): return [i for i in range(4) if r[i]!=0][0]
then_, now1, now2 = e(0), e(1), e(2)
full = cd(cd(then_, now1), now2); half = cd(then_, now1)
print('FULL beat then.now.now -> sector', sec(full), '= k = i*j (the composite NEXT = a NEW address)')
print('HALF beat then.now     -> sector', sec(half), '= i (one now, stuck, no NEXT)')
print('=> NEXT is the composite of the two nows. Give the full four-position beat -> the correct NEXT address;')
print('   give one now (sector-locked half-beat, F843) -> no NEXT. SAME addresser, mal-formed input.')
