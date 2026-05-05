/*
 * es_patches.c — diagnosed-fiber runtime overlay registry (v0.4.1, ABI v2).
 *
 * Mirrors the Python `diagnosed_fibers` module: a process-global
 * static array of registered patches, plus apply / clear / count /
 * read-back accessors. The encoder hook (in es_encode.c) iterates
 * this registry AFTER the base encode loop and contributes per-body
 * residue deltas BEFORE the final cyclic-group reduction.
 *
 * Threading: not thread-safe. The registry is process-global state;
 * serialise from the caller side if multiple threads are involved.
 *
 * libm: this file calls `sin()` from <math.h>. It only fires when
 * patches are active; the base encode path is integer-ALU pure as
 * before. If you compile in a libm-free environment, leave the
 * registry empty and the libm reference is not pulled in (the linker
 * may still emit a sin reference depending on the toolchain — strip
 * with -Wl,--gc-sections + LTO if footprint matters).
 */

#include <math.h>      /* sin                                            */
#include <string.h>    /* memcpy, memset, strncmp, strnlen              */

#include "ephemerides_spectral.h"

/* ------------------------------------------------------------------ */
/*  Registry                                                          */
/* ------------------------------------------------------------------ */

static es_patch_t es_active_patches[ES_MAX_PATCHES];
static size_t     es_n_patches = 0;

/* ------------------------------------------------------------------ */
/*  Validation                                                        */
/* ------------------------------------------------------------------ */

static int es_validate_patch(const es_patch_t *p) {
    if (p == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (p->kind != ES_PATCH_KIND_SINUSOID &&
        p->kind != ES_PATCH_KIND_COUPLED_SINUSOID) {
        return ES_ERR_PATCH_BAD_KIND;
    }
    if (!(p->period_days > 0.0)) {  /* also rejects NaN, -0.0, -inf */
        return ES_ERR_PATCH_BAD_PARAM;
    }
    if (p->body_idx_a < 0 || p->body_idx_a >= (int32_t)ES_N_BODIES) {
        return ES_ERR_PATCH_BAD_INDEX;
    }
    if (p->kind == ES_PATCH_KIND_COUPLED_SINUSOID) {
        if (p->body_idx_b < 0 || p->body_idx_b >= (int32_t)ES_N_BODIES) {
            return ES_ERR_PATCH_BAD_INDEX;
        }
        if (p->correlation != 1 && p->correlation != -1) {
            return ES_ERR_PATCH_BAD_PARAM;
        }
    }
    return ES_OK;
}

static int es_name_equal(const char *a, const char *b) {
    /* Patch names are NUL-terminated within ES_PATCH_NAME_MAX bytes;
     * a strncmp over the full buffer length is safe even if the
     * caller didn't NUL-terminate (we'll still compare the full
     * fixed-length window).
     */
    return strncmp(a, b, ES_PATCH_NAME_MAX) == 0;
}

/* ------------------------------------------------------------------ */
/*  Public API                                                        */
/* ------------------------------------------------------------------ */

int es_apply_patch(const es_patch_t *patch) {
    int rc = es_validate_patch(patch);
    if (rc != ES_OK) {
        return rc;
    }
    /* Duplicate-name check. Mirrors the Python registry's
     * apply_patch behaviour: same name twice is almost always a
     * bug, so we surface as a hard error rather than silently
     * shadowing.
     */
    for (size_t i = 0; i < es_n_patches; ++i) {
        if (es_name_equal(es_active_patches[i].name, patch->name)) {
            return ES_ERR_PATCH_DUPLICATE_NAME;
        }
    }
    if (es_n_patches >= ES_MAX_PATCHES) {
        return ES_ERR_PATCH_FULL;
    }
    /* Copy in. Zero the destination first so any unused trailing
     * bytes in `name` are reproducible (helps byte-exact read-back
     * and serialisation).
     */
    memset(&es_active_patches[es_n_patches], 0, sizeof(es_patch_t));
    memcpy(&es_active_patches[es_n_patches], patch, sizeof(es_patch_t));
    es_n_patches += 1;
    return ES_OK;
}

size_t es_clear_patches(void) {
    const size_t n_prior = es_n_patches;
    /* Zero the array so any leftover bytes don't confuse a later
     * read-back accessor; cheap (32 * 96 bytes ~= 3 KB).
     */
    memset(es_active_patches, 0, sizeof(es_active_patches));
    es_n_patches = 0;
    return n_prior;
}

size_t es_n_active_patches(void) {
    return es_n_patches;
}

int es_get_patch_at(size_t idx, es_patch_t *out) {
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (idx >= es_n_patches) {
        return ES_ERR_PATCH_OUT_OF_RANGE;
    }
    memcpy(out, &es_active_patches[idx], sizeof(es_patch_t));
    return ES_OK;
}

/* ------------------------------------------------------------------ */
/*  Internal: encoder hook                                            */
/* ------------------------------------------------------------------ */
/*
 * Apply every active patch's contribution to the per-body uint64
 * accumulator. Called from es_encode_state AFTER the base chunk
 * loop and the sub-day remainder, BEFORE the final cyclic-group
 * reduction.
 *
 * The Python BIP encoder uses Python-`round()` (banker's, half-to-
 * even); this routine uses es_banker_round (defined in es_encode.c)
 * to match byte-exactly. We forward-declare it here so the linker
 * can resolve at link time without exposing the helper publicly.
 *
 * Math reference (mirrors diagnosed_fibers.SinusoidPatch.evaluate):
 *
 *     ang = 2*pi * delta_t_days / period_days + phase_rad
 *     amp_residue = round(amplitude_deg / 360 * 2^32)
 *     delta = round(amp_residue * sin(ang))
 *
 *     SINUSOID:           phases[idx_a] += delta
 *     COUPLED_SINUSOID:   phases[idx_a] += delta
 *                         phases[idx_b] += correlation * delta
 *
 * The two-step rounding (amp_residue first, then the final delta)
 * matches the Python evaluate() exactly. Doing this as a single
 * compound `round(amp_deg / 360 * 2^32 * sin(ang))` would drift by
 * 1-2 ULP on certain JD/period combinations.
 */

extern int64_t es_banker_round(double x);

static const double ES_TWO_PI = 6.283185307179586476925286766559;
static const double ES_MODULO_DOUBLE = 4294967296.0;  /* 2^32 */

void es_apply_overlay_to_phases(double delta_t_days, uint64_t curr_phases[ES_N_BODIES]) {
    if (es_n_patches == 0) {
        return;  /* hot-path zero-cost when no patches active */
    }
    for (size_t k = 0; k < es_n_patches; ++k) {
        const es_patch_t *p = &es_active_patches[k];
        const double ang = ES_TWO_PI * delta_t_days / p->period_days + p->phase_rad;
        const double amp_residue_d = p->amplitude_deg / 360.0 * ES_MODULO_DOUBLE;
        /* Mirror Python: round(amp_residue * sin(ang)). The
         * intermediate `int(round(amp_residue))` from Python
         * matters only for the amplitude itself — for the final
         * delta we round once. (Python: int(round(amp_residue *
         * math.sin(ang))) — single round on the product.)
         */
        const int64_t delta = es_banker_round(
            (double)es_banker_round(amp_residue_d) * sin(ang)
        );
        if (p->kind == ES_PATCH_KIND_SINUSOID) {
            curr_phases[p->body_idx_a] += (uint64_t)delta;
        } else {  /* COUPLED_SINUSOID */
            curr_phases[p->body_idx_a] += (uint64_t)delta;
            const int64_t paired = (int64_t)p->correlation * delta;
            curr_phases[p->body_idx_b] += (uint64_t)paired;
        }
    }
}
