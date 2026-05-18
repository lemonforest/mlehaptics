# Spike #96 — anomaly investigation: cascade-on-circles identity domain
#
# Anomaly: max |Im^2 - (2 Re - Re^2)| = 2.802 (not ~1e-16) at centered unit circle.
# Spike #79 noted: identity holds on SHIFTED unit circle (Re-1)^2 + Im^2 = 1,
# not centered. Verify by direct substitution.

import math
import cmath

# Centered unit circle: z = e^(i theta), Re = cos, Im = sin
# 2 Re - Re^2 = 2 cos - cos^2
# Im^2 = sin^2 = 1 - cos^2
# 2 Re - Re^2 - Im^2 = 2 cos - cos^2 - 1 + cos^2 = 2 cos - 1
# So on centered unit circle, identity does NOT hold; the residual is 2 cos(theta) - 1.

print("Centered unit circle check:")
for k in range(7):
    z = cmath.exp(1j * 2 * math.pi * k / 7)
    Re, Im = z.real, z.imag
    res = Im*Im - (2*Re - Re*Re)
    print(f"  k={k}: Re={Re:+.6f}, Im={Im:+.6f}, residual = {res:+.6e}")

# Shifted unit circle: w = 1 + e^(i theta) = (1 + cos) + i sin
# Re = 1 + cos, Im = sin
# Re^2 = 1 + 2 cos + cos^2
# 2 Re - Re^2 = 2 + 2 cos - 1 - 2 cos - cos^2 = 1 - cos^2 = sin^2 = Im^2  -- IDENTITY HOLDS

print("\nShifted unit circle (1 + e^(i theta)) check:")
for k in range(7):
    z = 1 + cmath.exp(1j * 2 * math.pi * k / 7)
    Re, Im = z.real, z.imag
    res = Im*Im - (2*Re - Re*Re)
    print(f"  k={k}: Re={Re:+.6f}, Im={Im:+.6f}, residual = {res:+.6e}")

# Conclusion: cascade-on-circles identity is REGISTERED on the shifted unit circle.
# This is consistent with Spike #79 finding: cascade lives on circle ROOTED at 1,
# not centered at origin. Cl(7) idempotent eigenvalues +/- i lie on CENTERED unit
# circle by contrast. Same algebraic species, different rooting.
#
# For Spike #96 lensing chain: substrate-mode-propagation eigenphase content uses
# the SHIFTED-circle identity. Light's phase content along null geodesic accumulates
# as cascade-composition on the shifted circle.
