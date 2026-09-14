/*
 * srmech_trig_internal.h -- the Q61 quarter-turn Newton iteration for
 * Kepler's equation (rc473 repair round 1, `#T1188`).
 *
 * The iteration lives in srmech_trig.c because it reads the Q61 carrier's own
 * reduction and Taylor cores (trig_reduce, trig_sin_core, trig_cos_core) and
 * its 128-bit helpers, and one copy of those is the rule. srmech_kepler.c's
 * srmech_kepler_solve checks its own arguments and then calls this.
 *
 * Like srmech_ellbase_internal.h and srmech_thetasum_internal.h this is NOT
 * public API: no srmech.h exposure, no ctypes binding, no ABI surface. The
 * srmech_trig_ prefix is for link-level uniqueness only. License: MIT.
 */
#ifndef SRMECH_TRIG_INTERNAL_H
#define SRMECH_TRIG_INTERNAL_H

#include "srmech.h"

#include <stdint.h>

/* Preconditions (the caller's): 0 < e < 1, max_iter > 0, tolerance finite,
 * out_E_rad non-NULL. Returns SRMECH_ERR_BAD_INPUT, leaving *out_E_rad
 * untouched, when M_rad has no Q61 octant reduction (NaN, +-Inf, |M| >= 2^55);
 * SRMECH_OK with the converged E; SRMECH_ERR_OVERFLOW with the last iterate
 * when max_iter steps did not converge. */
SRMECH_NODISCARD srmech_status_t srmech_trig_kepler_q61(double    M_rad,
                                                        double    e,
                                                        double    tolerance,
                                                        uint32_t  max_iter,
                                                        double   *out_E_rad);

#endif /* SRMECH_TRIG_INTERNAL_H */
