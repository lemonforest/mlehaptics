/* es_channel_bases.c — channel-basis construction (Tier 2a).
 *
 * Mirrors python/ephemerides_spectral/_research/portable_prng.py +
 * the `_initialize_bases` step in
 * python/ephemerides_spectral/_research/ephemeris_reference_instrument.py
 *
 * Two construction routes are exposed (v0.29.0rc1, ABI v10):
 *
 *   ES_BASIS_METHOD_LEGACY (default, byte-parity with Python):
 *     state = seed
 *     for k in range(D):
 *         state, u = splitmix64_next(state)
 *         phi      = (u >> 11) * (2π / 2**53)    in [0, 2π)
 *         out[k]   = (cosf(phi), sinf(phi))      complex64
 *
 *   ES_BASIS_METHOD_COSPI (v0.29.0rc1 spike, bench-and-quantify):
 *     state = seed
 *     for k in range(D):
 *         state, u = splitmix64_next(state)
 *         x        = (u >> 11) * (2 / 2**53)     in [0, 2)  half-turns
 *         out[k]   = (cospif(x), sinpif(x))      complex64
 *
 * The COSPI route uses C23 libm `cospi`/`sinpi` (or Apple libsystem
 * `__cospi`/`__sinpi`) when available, falling back to `cos(π · x)` /
 * `sin(π · x)` otherwise — see `es_has_native_cospi()`.
 *
 * The public `es_channel_basis()` entry is preserved as-is: it
 * delegates to the LEGACY route so the Python-vs-C byte-parity test
 * (test_channel_basis_parity.py) continues to hold without changing
 * any caller.
 */

#include "ephemerides_spectral.h"
#include "es_prng.h"

#include <assert.h>
#include <math.h>
#include <stddef.h>

/* ------------------------------------------------------------------ *
 * cospi/sinpi feature detection
 * ------------------------------------------------------------------ *
 *
 * Single inline per function with the toolchain branch internalized
 * via #if/#elif/#else. This keeps the function-count discipline (the
 * JPL audit ratchet) simple — one es_cospi_d, one es_sinpi_d — rather
 * than the heuristic detecting three duplicate definitions per branch.
 *
 *   ES_COSPI_BACKEND = 1 → native (Apple __cospi / C23 cospi)
 *   ES_COSPI_BACKEND = 0 → fallback (cos(π·x), same rounding as LEGACY)
 *
 * Bench reports include `es_has_native_cospi()` so results are
 * labelled with the toolchain's actual route.
 */

#if defined(__APPLE__)
    #define ES_COSPI_BACKEND 1
#elif defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 202311L)
    #define ES_COSPI_BACKEND 1
#else
    #define ES_COSPI_BACKEND 0
#endif

static inline double es_cospi_d(double x)
{
#if defined(__APPLE__)
    return __cospi(x);
#elif defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 202311L)
    return cospi(x);
#else
    /* Apple libsystem ships __cospi / __sinpi as non-standard
     * extensions; C23 added cospi / sinpi to <math.h>. On other
     * toolchains we fall back to cos(π · x), which has the same
     * software `× π` rounding loss as LEGACY — so under fallback the
     * COSPI route is byte-equivalent to LEGACY and the spike
     * collapses to a no-op precision-wise.
     */
    static const double PI_D = 3.141592653589793238462643383279502884;
    return cos(PI_D * x);
#endif
}

static inline double es_sinpi_d(double x)
{
#if defined(__APPLE__)
    return __sinpi(x);
#elif defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 202311L)
    return sinpi(x);
#else
    static const double PI_D = 3.141592653589793238462643383279502884;
    return sin(PI_D * x);
#endif
}

int es_has_native_cospi(void)
{
    /* Returns 1 if the COSPI route uses native libm cospi/sinpi (or
     * Apple's __cospi/__sinpi); 0 if it falls back to cos(π·x). The
     * value is fixed at compile time so the call is branch-free.
     */
    return ES_COSPI_BACKEND;
}

/* ------------------------------------------------------------------ *
 * LEGACY route — shipped path, byte-parity with Python
 * ------------------------------------------------------------------ */

static es_status_t es_channel_basis_legacy(uint64_t seed,
                                           es_complex64_t *out,
                                           size_t D)
{
    assert(out != NULL);
    assert(D == 0 || out != NULL);  /* pin: out is valid for D > 0 */
    uint64_t state = seed;
    for (size_t k = 0; k < D; ++k) {
        const uint64_t u = es_splitmix64_next(&state);
        const double phi = es_splitmix64_uniform_2pi(u);
        assert(phi >= 0.0 && phi < 6.283185307179587);
        /* cos/sin in double precision; cast to float for storage.
         * Deterministic float-truncation is the only place the C and
         * Python sides could disagree at the bit level — verified by
         * the parity test that compares float32 cast of Python's
         * complex128 output against C's complex64.
         */
        out[k].real = (float)cos(phi);
        out[k].imag = (float)sin(phi);
    }
    return ES_OK;
}

/* ------------------------------------------------------------------ *
 * COSPI route — v0.29.0rc1 spike
 * ------------------------------------------------------------------ */

static es_status_t es_channel_basis_cospi_route(uint64_t seed,
                                                es_complex64_t *out,
                                                size_t D)
{
    assert(out != NULL);
    assert(D == 0 || out != NULL);  /* pin: out is valid for D > 0 */
    uint64_t state = seed;
    for (size_t k = 0; k < D; ++k) {
        const uint64_t u = es_splitmix64_next(&state);
        const double x = es_splitmix64_uniform_half_turns(u);
        assert(x >= 0.0 && x < 2.0);
        /* Quarter-turn channels (x ∈ {0, 1/2, 1, 3/2}) collapse to
         * (±1, 0) / (0, ±1) bit-exactly under native cospi/sinpi —
         * the bench script's quarter_turn_exact test pins this.
         */
        out[k].real = (float)es_cospi_d(x);
        out[k].imag = (float)es_sinpi_d(x);
    }
    return ES_OK;
}

/* ------------------------------------------------------------------ *
 * Public entry points
 * ------------------------------------------------------------------ */

es_status_t es_channel_basis(uint64_t seed,
                             es_complex64_t *out,
                             size_t D)
{
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    assert(out != NULL);
    return es_channel_basis_legacy(seed, out, D);
}

es_status_t es_channel_basis_method(uint64_t seed,
                                    es_complex64_t *out,
                                    size_t D,
                                    es_basis_method_t method)
{
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    assert(out != NULL);
    switch (method) {
        case ES_BASIS_METHOD_LEGACY:
            return es_channel_basis_legacy(seed, out, D);
        case ES_BASIS_METHOD_COSPI:
            return es_channel_basis_cospi_route(seed, out, D);
        default:
            return ES_ERR_INVALID_KIND;
    }
}
