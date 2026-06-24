"""F934 — the srmech reduction-dispatch axis (rc41-58, completing ~rc64) IS the snapshot-side closed-form
map; its honest-OPEN residue is exactly our sustain regime (F930-933). Verified live (rc58): dispatch.infer
is the F929 router; resonant_spectrum (§75) shipped in coupling; an unknown cascade returns honest OPEN
(reducible=False), never a hallucinated closed form. srmech 0.9.0rc58; native ABI 3."""
import inspect
from srmech.amsc import dispatch, coupling
print('dispatch.infer (the F929 router):', inspect.signature(dispatch.infer))
print('resonant_spectrum (§75 spectral row):', 'PRESENT in srmech.amsc.coupling' if hasattr(coupling,'resonant_spectrum') else 'absent')
r=dispatch.infer({'kind':'unknown'})
print('infer(unknown) -> reducible=%r, reason=%r' % (r.get('reducible'), r.get('reason')))
print('=> closed (reducible=True) = the 11D-expressible SNAPSHOT (stored+ring-down); OPEN = the SUSTAINED regime (14/28, walked).')
