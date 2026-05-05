/* es_hd_state.c — hyperdimensional state pipeline (Tier 2b, v0.7.0).
 *
 * Three new public entry points + a few internal helpers. The pipeline
 * mirrors `_research/bip_hd_lift.py` 1:1; the parity smoke test pins
 * the two paths to within float-ULP.
 *
 *   es_encode_state_hd       BIP encode -> lift to D-dim hypervector
 *   es_bind_observer         Topocentric observer-bind via HDC algebra
 *   es_get_eclipse_probability   Project state onto syzygy operator
 *
 * These functions allocate working buffers on the heap (one D-dim
 * complex64 buffer per body for the channel basis, plus a few
 * D-dim scratch buffers for the rolled / multiplied state). The
 * allocation cost is bounded by D * sizeof(complex64) * O(1) per call;
 * at D=65536 that's 512 KB per scratch buffer.
 */

#include "ephemerides_spectral.h"

#include <math.h>
#include <stdlib.h>
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
    const uint64_t prod = (uint64_t)phi * (uint64_t)D + ((uint64_t)1 << 31);
    return (size_t)((prod >> 32) % (uint64_t)D);
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
    double acc = 0.0;
    for (size_t k = 0; k < D; ++k) {
        const double r = (double)state[k].real;
        const double i = (double)state[k].imag;
        acc += r * r + i * i;
    }
    return sqrt(acc);
}

/* Divide every element of `state` by `scale`. */
static void complex64_scale_inplace(es_complex64_t *state,
                                    size_t D,
                                    double scale)
{
    if (scale == 0.0) return;
    const double inv = 1.0 / scale;
    for (size_t k = 0; k < D; ++k) {
        state[k].real = (float)((double)state[k].real * inv);
        state[k].imag = (float)((double)state[k].imag * inv);
    }
}

/* ──────────────────────────────────────────────────────────────────
 * es_encode_state_hd — BIP encode + lift
 * ────────────────────────────────────────────────────────────────── */

es_status_t es_encode_state_hd(double delta_t_days,
                               es_complex64_t *out_state,
                               size_t D)
{
    if (out_state == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (D == 0) {
        return ES_ERR_INVALID_INDEX;
    }

    /* 1. BIP integer encode -> 38 phase residues. */
    uint32_t phases[ES_N_BODIES];
    es_status_t rc = es_encode_state(delta_t_days, phases);
    if (rc != ES_OK) return rc;

    /* 2. Allocate a per-body channel-basis scratch + a rolled scratch.
     *    Reuse them across bodies. */
    es_complex64_t *basis = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    es_complex64_t *rolled = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    if (basis == NULL || rolled == NULL) {
        free(basis); free(rolled);
        return ES_ERR_NULL_OUTPUT;  /* OOM — same code as null-out */
    }

    /* 3. Zero the accumulator. */
    memset(out_state, 0, D * sizeof(es_complex64_t));

    const double sqrt_D = sqrt((double)D);
    const double inv_sqrt_D = 1.0 / sqrt_D;

    for (size_t b = 0; b < ES_N_BODIES; ++b) {
        const uint64_t seed = ES_BODY_BASIS_SEED_BASE + (uint64_t)b;
        rc = es_channel_basis(seed, basis, D);
        if (rc != ES_OK) { free(basis); free(rolled); return rc; }

        const size_t residue = phase_uint32_to_residue(phases[b], D);
        roll_complex64(basis, residue, rolled, D);

        /* Accumulate `rolled / sqrt(D)` into out_state. */
        for (size_t k = 0; k < D; ++k) {
            out_state[k].real = (float)((double)out_state[k].real
                                        + (double)rolled[k].real * inv_sqrt_D);
            out_state[k].imag = (float)((double)out_state[k].imag
                                        + (double)rolled[k].imag * inv_sqrt_D);
        }
    }

    free(basis);
    free(rolled);

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
                             size_t D)
{
    if (state_in == NULL || out_state == NULL) {
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

    es_complex64_t *body_basis = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    es_complex64_t *coord_basis = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    es_complex64_t *coord_op = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    if (body_basis == NULL || coord_basis == NULL || coord_op == NULL) {
        free(body_basis); free(coord_basis); free(coord_op);
        return ES_ERR_NULL_OUTPUT;
    }

    es_status_t rc = es_channel_basis(
        ES_BODY_BASIS_SEED_BASE + (uint64_t)body_idx, body_basis, D);
    if (rc != ES_OK) goto out;

    rc = es_channel_basis(ES_OBSERVER_COORD_BASIS_SEED, coord_basis, D);
    if (rc != ES_OK) goto out;

    /* lat_res = int((lat+90)/180 * D) mod D
     * lon_res = int((lon+180)/360 * D) mod D
     * Same conversion as Python `int(((lat+90)/180) * D) % D`.
     */
    const double lat_norm = (lat_deg + 90.0) / 180.0;
    const double lon_norm = (lon_deg + 180.0) / 360.0;
    /* `(int)` truncates toward zero in C; for positive `lat_norm * D`
     * this matches Python's `int(...)`. Negative inputs out of range
     * would behave differently, but lat ∈ [-90, 90] and lon ∈
     * [-180, 180] keep both norms in [0, 1]. */
    const long long lat_raw = (long long)(lat_norm * (double)D);
    const long long lon_raw = (long long)(lon_norm * (double)D);
    const size_t lat_res = (size_t)(((lat_raw % (long long)D) + (long long)D) % (long long)D);
    const size_t lon_res = (size_t)(((lon_raw % (long long)D) + (long long)D) % (long long)D);

    const size_t shift = (lat_res * (size_t)ES_COPRIME_LAT
                          + lon_res * (size_t)ES_COPRIME_LON) % D;
    roll_complex64(coord_basis, shift, coord_op, D);

    /* observer_op = (body_basis / sqrt(D)) * coord_op       (elementwise complex mul)
     * out[k]      = state[k] * observer_op[k] * sqrt(D)
     * The two sqrt(D) factors cancel one of the body_basis scalings
     * in the bind, but we keep them explicit for byte-parity with
     * the Python side which writes them out the same way.
     */
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

    rc = ES_OK;
out:
    free(body_basis);
    free(coord_basis);
    free(coord_op);
    return rc;
}

/* ──────────────────────────────────────────────────────────────────
 * es_get_eclipse_probability — syzygy projection
 * ────────────────────────────────────────────────────────────────── */

es_status_t es_get_eclipse_probability(const es_complex64_t *state,
                                       size_t D,
                                       size_t sun_body_idx,
                                       size_t moon_body_idx,
                                       double *out_prob)
{
    if (state == NULL || out_prob == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (sun_body_idx >= ES_N_BODIES || moon_body_idx >= ES_N_BODIES) {
        return ES_ERR_INVALID_INDEX;
    }
    if (D == 0) {
        return ES_ERR_INVALID_INDEX;
    }

    es_complex64_t *sun_b = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    es_complex64_t *moon_b = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    es_complex64_t *node_b = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    es_complex64_t *s_op = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
    if (sun_b == NULL || moon_b == NULL || node_b == NULL || s_op == NULL) {
        free(sun_b); free(moon_b); free(node_b); free(s_op);
        return ES_ERR_NULL_OUTPUT;
    }

    es_status_t rc = es_channel_basis(
        ES_BODY_BASIS_SEED_BASE + (uint64_t)sun_body_idx, sun_b, D);
    if (rc != ES_OK) goto out;
    rc = es_channel_basis(
        ES_BODY_BASIS_SEED_BASE + (uint64_t)moon_body_idx, moon_b, D);
    if (rc != ES_OK) goto out;
    rc = es_channel_basis(ES_SYZYGY_NODE_BASIS_SEED, node_b, D);
    if (rc != ES_OK) goto out;

    const double sqrt_D = sqrt((double)D);
    const double inv_sqrt_D = 1.0 / sqrt_D;

    /* s_op = (sun_b + moon_b) / sqrt(D) + node_b / sqrt(D) */
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
    /* Normalise. */
    const double n = complex64_norm(s_op, D);
    if (n > 0.0) complex64_scale_inplace(s_op, D, n);

    /* prob = |<state, s_op>| = |sum conj(state[k]) * s_op[k]|
     * (numpy.vdot is conj-on-first-arg) */
    double acc_r = 0.0, acc_i = 0.0;
    for (size_t k = 0; k < D; ++k) {
        const double sr = (double)state[k].real;
        const double si = (double)state[k].imag;
        const double or_ = (double)s_op[k].real;
        const double oi = (double)s_op[k].imag;
        /* conj(state) * s_op = (sr - i*si) * (or + i*oi)
         *                   = (sr*or + si*oi) + i*(sr*oi - si*or) */
        acc_r += sr * or_ + si * oi;
        acc_i += sr * oi - si * or_;
    }
    *out_prob = sqrt(acc_r * acc_r + acc_i * acc_i);
    rc = ES_OK;
out:
    free(sun_b); free(moon_b); free(node_b); free(s_op);
    return rc;
}
