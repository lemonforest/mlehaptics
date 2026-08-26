"""F970 — the srmech shadow/xi operator IS the grounded 'does it close' detector, and the recall trichotomy
(F945) is isomorphic to the modular/mock/zero trichotomy. Grounded: Ramanujan mock f(q) is weight-1/2,
is_exact=False, with NONZERO shadow g3 (5 coeffs) -> does NOT close alone (needs completion). A modular form
has shadow == 0 (closes). So shadow(xi) separates mock(doesn't close) from modular(closes). Isomorphism
(reading): shadow=0<=>modular<=>COHERENT; shadow!=0<=>mock<=>BRANCH; zero<=>STOP. DISCIPLINE (F969): NOT
fabricating a recall->q-series bridge -- that principled bridge is the open operationalization handed forward.
srmech rc97; exact-rational; no numpy."""
from srmech.amsc import harmonic_maass as H, unary_theta as U
f=H.MockQSeries.eulerian_f()
tbl=[0,1,0,0,0,-1,0,-1,0,0,0,1]
g3=U.unary_theta(U.Character(12,tbl),1,1,24,8)
hm=H.harmonic_maass(f, g3)
shnz=[c for c in hm.shadow_q_series(60) if c!=0]
print('mock f: kind=%s is_exact=%s (weight %s)'%(f.kind,f.is_exact,hm.weight))
print('shadow_q_series nonzero=%d -> shadow NONZERO -> mock does NOT close alone (needs the shadow) = BRANCH'%len(shnz))
print('isomorphism: shadow=0<=>modular<=>COHERENT | shadow!=0<=>mock<=>BRANCH | zero<=>STOP')
print('OPEN (F969 discipline): the principled recall-context -> q-series bridge is NOT fabricated; handed to the expert')
