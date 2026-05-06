/* es_hd_state.c — hyperdimensional state pipeline (Tier 2b, v0.7.0;
 * caller-supplied-scratch refactor v0.13.4 → ABI v6).
 *
 * Three public entry points + a few internal helpers. The pipeline
 * mirrors `_research/bip_hd_lift.py` 1:1; the parity smoke test pins
 * the two paths to within float-ULP.
 *
 *   es_encode_state_hd       BIP encode -> lift to D-dim hypervector
 *   es_bind_observer         Topocentric observer-bind via HDC algebra
 *   es_get_eclipse_probability   Project state onto syzygy operator
 *
 * v0.13.4 — JPL Power-of-Ten Rule 1 + Rule 3 fixes.
 * Pre-v0.13.4 each entry point allocated D-dim complex64 scratch
 * buffers via malloc/free (Rule 3) and used `goto out` to centralise
 * the cleanup-on-error path (Rule 1). The refactor makes scratch
 * caller-supplied, which removes both classes of violation in one
 * pass: the C library no longer calls malloc/free after init, and
 * the cleanup-on-error path collapses to plain early-return because
 * there are no buffers to free. No `stdlib.h` include needed; no
 * `goto` keywords; no dynamic allocation. The math is byte-identical
 * to ABI v5.
 *
 * Scratch buffers must have capacity for D es_complex64_t entries
 * each. Contents on entry are ignored, on return are unspecified.
 * The Python ctypes shim allocates them once per call alongside the
 * existing `out_state` buffer, so the user-facing bridge API is
 * unchanged from v0.7.0.
 */

#include "ephemerides_spectral.h"

#include <assert.h>
#include <math.h>
#include <string.h>

/* ──────────────────────────────────────────────────────────────────
 * Internal helpers
 * ────────────────────────────────────────────────────────────────── */

/* round((phi/2^32) * D) mod D — uint32 phase residue → integer index.
 * Same algorithm as `_phase_uint32_to_residue` in bip_hd_lift.py.
 * Tie case (phi*D mod 2^32 == 2^31) is measure-zero in practice; we
 * use round-half-up via the +(2^31) trick to match the Python side.
 */
static size_t phase_uint32_to_residue(uint32_t phi, size_t D)
{
    assert(D > 0);
    const uint64_t prod = (uint64_t)phi * (uint64_t)D + ((uint64_t)1 << 31);
    const size_t r = (size_t)((prod >> 32) % (uint64_t)D);
    assert(r < D);
    return r;
}

/* Roll `src` by `shift` positions into `dst`. `dst[k] = src[(k - shift) mod D]`,
 * matching numpy's `np.roll(src, shift)` semantics. Buffers are
 * separate (no in-place support — call sites use scratch for this).
 */
static void roll_complex64(const es_complex64_t *src,
                           size_t shift,
                           es_complex64_t *dst,
                           size_t D)
{
    assert(src != NULL);
    assert(dst != NULL);
    assert(D > 0);
    /* numpy np.roll(src, shift) puts src[0] at dst[shift];
     * equivalently dst[k] = src[(k - shift) mod D]. We compute via
     * two memcpys in the common case (no wrap-around in the source).
     */
    shift %= D;
    if (shift == 0) {
        memcpy(dst, src, D * sizeof(es_complex64_t));
        return;
    }
    /* dst[shift..D-1] = src[0..D-1-shift]
     * dst[0..shift-1] = src[D-shift..D-1]
     */
    memcpy(dst + shift, src, (D - shift) * sizeof(es_complex64_t));
    memcpy(dst, src + (D - shift), shift * sizeof(es_complex64_t));
}

/* Compute |state| via sum of squared magnitudes; used for normalisation. */
static double complex64_norm(const es_complex64_t *state, size_t D)
{
    assert(state != NULL);
    double acc = 0.0;
    for (size_t k = 0; k < D; ++k) {
        const double r = (double)state[k].real;
        const double i = (double)state[k].imag;
        acc += r * r + i * i;
    }
    assert(acc >= 0.0);
    return sqrt(acc);
}

/* Divide every element of `state` by `scale`. */
static void complex64_scale_inplace(es_complex64_t *state,
                                    size_t D,
                                    double scale)
{
    assert(state != NULL);
    assert(isfinite(scale));
    if (scale == 0.0) return;
    const double inv = 1.0 / scale;
    for (size_t k = 0; k < D; ++k) {
        state[k].real = (float)((double)state[k].real * inv);
        state[k].imag = (float)((double)state[k].imag * inv);
    }
}

/* (lat, lon) → shift index for the observer-coord roll.
 *
 *   lat_res = int((lat+90)/180 * D) mod D
 *   lon_res = int((lon+180)/360 * D) mod D
 *   shift   = (lat_res * ES_COPRIME_LAT
 *             + lon_res * ES_COPRIME_LON) mod D
 *
 * Same conversion as Python `int(((lat+90)/180) * D) % D`. `(int)`
 * truncates toward zero in C; for positive `lat_norm * D` this matches
 * Python's `int(...)`. lat ∈ [-90, 90] and lon ∈ [-180, 180] keep both
 * norms in [0, 1].
 */
static size_t observer_coord_shift(double lat_deg, double lon_deg, size_t D)
{
    assert(D > 0);
    assert(isfinite(lat_deg) && isfinite(lon_deg));
    const double lat_norm = (lat_deg + 90.0) / 180.0;
    const double lon_norm = (lon_deg + 180.0) / 360.0;
    const long long lat_raw = (long long)(lat_norm * (double)D);
    const long long lon_raw = (long long)(lon_norm * (double)D);
    const size_t lat_res = (size_t)(((lat_raw % (long long)D) + (long long)D) % (long long)D);
    const size_t lon_res = (size_t)(((lon_raw % (long long)D) + (long long)D) % (long long)D);
    const size_t shift = (lat_res * (size_t)ES_COPRIME_LAT
                          + lon_res * (size_t)ES_COPRIME_LON) % D;
    assert(shift < D);
    return shift;
}

/* Compute out_state[k] = state_in[k] * observer_op[k] * sqrt(D),
 *   where observer_op[k] = (body_basis[k] / sqrt(D)) * coord_op[k].
 *
 * The two sqrt(D) factors cancel one of the body_basis scalings in
 * the bind, but we keep them explicit for byte-parity with the Python
 * side which writes them out the same way.
 */
static void apply_observer_bind(const es_complex64_t *state_in,
                                const es_complex64_t *body_basis,
                                const es_complex64_t *coord_op,
                                es_complex64_t *out_state,
                                size_t D)
{
    assert(state_in != NULL && body_basis != NULL);
    assert(coord_op != NULL && out_state != NULL);
    const double sqrt_D = sqrt((double)D);
    const double inv_sqrt_D = 1.0 / sqrt_D;
    for (size_t k = 0; k < D; ++k) {
        const double br = (double)body_basis[k].real * inv_sqrt_D;
        const double bi = (double)body_basis[k].imag * inv_sqrt_D;
        const double cr = (double)coord_op[k].real;
        const double ci = (double)coord_op[k].imag;
        /* observer_op = body_basis_scaled * coord_op  (complex mul) */
        const double or_ = br * cr - bi * ci;
        const double oi = br * ci + bi * cr;
        const double sr = (double)state_in[k].real;
        const double si = (double)state_in[k].imag;
        /* out = state * observer_op * sqrt(D) (complex mul × scalar) */
        const double mr = sr * or_ - si * oi;
        const double mi = sr * oi + si * or_;
        out_state[k].real = (float)(mr * sqrt_D);
        out_state[k].imag = (float)(mi * sqrt_D);
    }
}

/* Build the un-normalised syzygy operator
 *   s_op[k] = (sun_b[k] + moon_b[k] + node_b[k]) / sqrt(D)
 * mirroring numpy:
 *   s_op = (sun_b + moon_b) / sqrt(D) + node_b / sqrt(D)
 *        = (sun_b + moon_b + node_b) / sqrt(D)
 * The three-way sum + single multiply is the same float pattern; the
 * factored form keeps it in one pass over the buffer.
 */
static void build_syzygy_operator(const es_complex64_t *sun_b,
                                  const es_complex64_t *moon_b,
                                  const es_complex64_t *node_b,
                                  es_complex64_t *s_op,
                                  size_t D)
{
    assert(sun_b != NULL && moon_b != NULL);
    assert(node_b != NULL && s_op != NULL);
    assert(D > 0);
    const double inv_sqrt_D = 1.0 / sqrt((double)D);
    for (size_t k = 0; k < D; ++k) {
        const double r = ((double)sun_b[k].real
                          + (double)moon_b[k].real
                          + (double)node_b[k].real) * inv_sqrt_D;
        const double i = ((double)sun_b[k].imag
                          + (double)moon_b[k].imag
                          + (double)node_b[k].imag) * inv_sqrt_D;
        s_op[k].real = (float)r;
        s_op[k].imag = (float)i;
    }
}

/* Magnitude of the conj-vdot inner product:
 *   |<a, b>| = | sum conj(a[k]) * b[k] |
 * Matches numpy.vdot(a, b) which conjugates its first argument.
 */
static double complex64_vdot_magnitude(const es_complex64_t *a,
                                       const es_complex64_t *b,
                                       size_t D)
{
    assert(a != NULL);
    assert(b != NULL);
    double acc_r = 0.0, acc_i = 0.0;
    for (size_t k = 0; k < D; ++k) {
        const double ar = (double)a[k].real;
        const double ai = (double)a[k].imag;
        const double br = (double)b[k].real;
        const double bi = (double)b[k].imag;
        /* conj(a) * b = (ar - i*ai) * (br + i*bi)
         *             = (ar*br + ai*bi) + i*(ar*bi - ai*br) */
        acc_r += ar * br + ai * bi;
        acc_i += ar * bi - ai * br;
    }
    return sqrt(acc_r * acc_r + acc_i * acc_i);
}

/* ──────────────────────────────────────────────────────────────────
 * es_encode_state_hd — BIP encode + lift
 * ────────────────────────────────────────────────────────────────── */

es_status_t es_encode_state_hd(double delta_t_days,
                               es_complex64_t *out_state,
                               es_complex64_t *scratch_basis,
                               es_complex64_t *scratch_rolled,
                               size_t D)
{
    if (out_state == NULL || scratch_basis == NULL || scratch_rolled == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (D == 0) {
        return ES_ERR_INVALID_INDEX;
    }
    assert(out_state != NULL && scratch_basis != NULL && scratch_rolled != NULL);
    assert(D > 0);

    /* 1. BIP integer encode -> 38 phase residues. */
    uint32_t phases[ES_N_BODIES];
    es_status_t rc = es_encode_state(delta_t_days, phases);
    if (rc != ES_OK) return rc;

    /* 2. Zero the accumulator. */
    memset(out_state, 0, D * sizeof(es_complex64_t));

    const double sqrt_D = sqrt((double)D);
    const double inv_sqrt_D = 1.0 / sqrt_D;

    /* 3. For each body, fill scratch_basis + scratch_rolled, accumulate. */
    for (size_t b = 0; b < ES_N_BODIES; ++b) {
        const uint64_t seed = ES_BODY_BASIS_SEED_BASE + (uint64_t)b;
        rc = es_channel_basis(seed, scratch_basis, D);
        if (rc != ES_OK) return rc;

        const size_t residue = phase_uint32_to_residue(phases[b], D);
        roll_complex64(scratch_basis, residue, scratch_rolled, D);

        /* Accumulate `scratch_rolled / sqrt(D)` into out_state. */
        for (size_t k = 0; k < D; ++k) {
            out_state[k].real = (float)((double)out_state[k].real
                                        + (double)scratch_rolled[k].real * inv_sqrt_D);
            out_state[k].imag = (float)((double)out_state[k].imag
                                        + (double)scratch_rolled[k].imag * inv_sqrt_D);
        }
    }

    /* 4. Normalise. */
    const double n = complex64_norm(out_state, D);
    if (n > 0.0) {
        complex64_scale_inplace(out_state, D, n);
    }
    return ES_OK;
}

/* ──────────────────────────────────────────────────────────────────
 * es_bind_observer — topocentric HDC bind
 * ────────────────────────────────────────────────────────────────── */

es_status_t es_bind_observer(const es_complex64_t *state_in,
                             size_t body_idx,
                             double lat_deg,
                             double lon_deg,
                             es_complex64_t *out_state,
                             es_complex64_t *scratch_body_basis,
                             es_complex64_t *scratch_coord_basis,
                             es_complex64_t *scratch_coord_op,
                             size_t D)
{
    if (state_in == NULL || out_state == NULL
        || scratch_body_basis == NULL || scratch_coord_basis == NULL
        || scratch_coord_op == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (!isfinite(lat_deg) || !isfinite(lon_deg)) {
        return ES_ERR_NON_FINITE_INPUT;
    }
    if (body_idx >= ES_N_BODIES) {
        return ES_ERR_INVALID_INDEX;
    }
    if (D == 0) {
        return ES_ERR_INVALID_INDEX;
    }
    assert(body_idx < ES_N_BODIES);
    assert(D > 0);

    es_status_t rc = es_channel_basis(
        ES_BODY_BASIS_SEED_BASE + (uint64_t)body_idx, scratch_body_basis, D);
    if (rc != ES_OK) return rc;

    rc = es_channel_basis(ES_OBSERVER_COORD_BASIS_SEED, scratch_coord_basis, D);
    if (rc != ES_OK) return rc;

    const size_t shift = observer_coord_shift(lat_deg, lon_deg, D);
    roll_complex64(scratch_coord_basis, shift, scratch_coord_op, D);

    apply_observer_bind(state_in, scratch_body_basis, scratch_coord_op,
                        out_state, D);
    return ES_OK;
}

/* ──────────────────────────────────────────────────────────────────
 * es_get_eclipse_probability — syzygy projection
 * ────────────────────────────────────────────────────────────────── */

es_status_t es_get_eclipse_probability(const es_complex64_t *state,
                                       size_t D,
                                       size_t sun_body_idx,
                                       size_t moon_body_idx,
                                       es_complex64_t *scratch_sun_b,
                                       es_complex64_t *scratch_moon_b,
                                       es_complex64_t *scratch_node_b,
                                       es_complex64_t *scratch_s_op,
                                       double *out_prob)
{
    if (state == NULL || out_prob == NULL
        || scratch_sun_b == NULL || scratch_moon_b == NULL
        || scratch_node_b == NULL || scratch_s_op == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (sun_body_idx >= ES_N_BODIES || moon_body_idx >= ES_N_BODIES) {
        return ES_ERR_INVALID_INDEX;
    }
    if (D == 0) {
        return ES_ERR_INVALID_INDEX;
    }
    assert(sun_body_idx < ES_N_BODIES && moon_body_idx < ES_N_BODIES);
    assert(D > 0);

    es_status_t rc = es_channel_basis(
        ES_BODY_BASIS_SEED_BASE + (uint64_t)sun_body_idx, scratch_sun_b, D);
    if (rc != ES_OK) return rc;
    rc = es_channel_basis(
        ES_BODY_BASIS_SEED_BASE + (uint64_t)moon_body_idx, scratch_moon_b, D);
    if (rc != ES_OK) return rc;
    rc = es_channel_basis(ES_SYZYGY_NODE_BASIS_SEED, scratch_node_b, D);
    if (rc != ES_OK) return rc;

    build_syzygy_operator(scratch_sun_b, scratch_moon_b, scratch_node_b,
                          scratch_s_op, D);
    const double n = complex64_norm(scratch_s_op, D);
    if (n > 0.0) complex64_scale_inplace(scratch_s_op, D, n);

    *out_prob = complex64_vdot_magnitude(state, scratch_s_op, D);
    return ES_OK;
}
