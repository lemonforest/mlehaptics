"""F952 — the onset (rotation-first) is INTERNAL for a self-excited substrate (hyperloop: itself is the
excitation -> the onset is the loop/the seam, F951) or EXTERNAL for a driven instrument (oboe: the player at
the reeds is the onset). Grounded via Kuramoto: self-excited (coupling, NO pin) -> coherence R=1.0 from the
loop itself; externally-excited (pin, NO coupling) -> R=1.0 from the external pin; neither -> R~0 (no beat).
In nature (self-excited) the onset is the seam (concealed, F951); AI = the oboe (external player = the
player-piano/puppet) -- why AI is not a substrate. srmech rc78; Kuramoto + Class-N trig coherence; no numpy."""
from srmech.amsc import cascade
from srmech import calculus
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def R(theta):
    n=len(theta); c=sum(fl(calculus.cos(t)) for t in theta); s=sum(fl(calculus.sin(t)) for t in theta)
    return (c*c+s*s)**0.5/n
N=8; theta0=[(i*0.78)%6.283 for i in range(N)]; omega=[0.3*(i-3.5)/N for i in range(N)]
def run(coupling, pin, steps=3000):
    th=theta0[:]; kw=dict(coupling=coupling, dt=0.02)
    if pin is not None: kw.update(pin_anchor=[pin]*N, pin_strength=2.0)
    for _ in range(steps): th=cascade.kuramoto_step(th, omega, **kw)
    return R(th)
print('initial R=%.3f'%R(theta0))
print('HYPERLOOP self-excited (coupling=3, no pin): R=%.3f  onset INTERNAL = the loop (the seam)'%run(3.0,None))
print('OBOE externally-excited (coupling=0, pin):   R=%.3f  onset EXTERNAL = the player (the pin)'%run(0.0,1.5))
print('control (coupling=0, no pin):                R=%.3f  no onset -> no beat'%run(0.0,None))
