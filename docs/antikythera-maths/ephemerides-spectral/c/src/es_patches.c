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

#include <assert.h>
#include <math.h>      /* sin, cos, atan2, sqrt, floor                  */
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
    assert(p != NULL);  /* post-validation */
    if (p->kind != ES_PATCH_KIND_SINUSOID &&
        p->kind != ES_PATCH_KIND_COUPLED_SINUSOID &&
        p->kind != ES_PATCH_KIND_ECCENTRICITY_CORRECTION) {
        return ES_ERR_PATCH_BAD_KIND;
    }
    if (p->body_idx_a < 0 || p->body_idx_a >= (int32_t)ES_N_BODIES) {
        return ES_ERR_PATCH_BAD_INDEX;
    }
    if (p->kind == ES_PATCH_KIND_SINUSOID ||
        p->kind == ES_PATCH_KIND_COUPLED_SINUSOID) {
        if (!(p->period_days > 0.0)) {  /* rejects NaN, -0.0, -inf */
            return ES_ERR_PATCH_BAD_PARAM;
        }
        if (p->kind == ES_PATCH_KIND_COUPLED_SINUSOID) {
            if (p->body_idx_b < 0 || p->body_idx_b >= (int32_t)ES_N_BODIES) {
                return ES_ERR_PATCH_BAD_INDEX;
            }
            if (p->correlation != 1 && p->correlation != -1) {
                return ES_ERR_PATCH_BAD_PARAM;
            }
        }
        assert(p->period_days > 0.0);  /* post-validation invariant */
    } else {  /* ES_PATCH_KIND_ECCENTRICITY_CORRECTION (v0.28.0rc5) */
        /* Bounded eccentricity [0, 1). Hyperbolic / parabolic
         * trajectories (e >= 1) are out of scope; the BIP encoder
         * only models closed orbits. */
        if (!(p->eccentricity >= 0.0) || !(p->eccentricity < 1.0)) {
            return ES_ERR_PATCH_BAD_PARAM;
        }
        /* Mean motion must be finite + non-zero. n=0 would mean an
         * infinitely-slow body — the patch would be a no-op (M(t)=M0
         * for all t, EOC delta = 0) but the math degenerates; reject
         * to surface the configuration error at apply time. */
        if (!(p->n_rad_per_day != 0.0) ||
            !(p->n_rad_per_day > -1.0e10) ||
            !(p->n_rad_per_day < 1.0e10)) {
            return ES_ERR_PATCH_BAD_PARAM;
        }
        assert(p->eccentricity >= 0.0);
        assert(p->eccentricity < 1.0);
        assert(p->n_rad_per_day != 0.0);
    }
    return ES_OK;
}

static int es_name_equal(const char *a, const char *b) {
    assert(a != NULL);
    assert(b != NULL);
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
    assert(patch != NULL);  /* validated above */
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
    assert(es_n_patches < ES_MAX_PATCHES);  /* invariant before write */
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
    assert(n_prior <= ES_MAX_PATCHES);
    /* Zero the array so any leftover bytes don't confuse a later
     * read-back accessor; cheap (32 * 96 bytes ~= 3 KB).
     */
    memset(es_active_patches, 0, sizeof(es_active_patches));
    es_n_patches = 0;
    assert(es_n_patches == 0);  /* post-condition */
    return n_prior;
}

size_t es_clear_eoc_patches(void) {
    /* v0.28.0rc5 (ABI v9): selective clear by kind. Mirrors
     * _eoc_catalog.clear_eoc_patches() on the Python side. */
    assert(es_n_patches <= ES_MAX_PATCHES);
    size_t write_idx = 0;
    size_t n_removed = 0;
    /* Bounded loop: ES_MAX_PATCHES = 32. */
    for (size_t read_idx = 0; read_idx < es_n_patches; ++read_idx) {
        if (es_active_patches[read_idx].kind ==
                ES_PATCH_KIND_ECCENTRICITY_CORRECTION) {
            n_removed += 1;
            continue;  /* skip writing — this slot drops out */
        }
        if (write_idx != read_idx) {
            memcpy(&es_active_patches[write_idx],
                   &es_active_patches[read_idx],
                   sizeof(es_patch_t));
        }
        write_idx += 1;
    }
    /* Zero out the trailing slots we just compacted out. */
    if (write_idx < es_n_patches) {
        memset(&es_active_patches[write_idx], 0,
               sizeof(es_patch_t) * (es_n_patches - write_idx));
    }
    es_n_patches = write_idx;
    assert(es_n_patches + n_removed <= ES_MAX_PATCHES);
    return n_removed;
}

size_t es_n_active_patches(void) {
    assert(es_n_patches <= ES_MAX_PATCHES);
    /* The registry never exceeds the cap; double-checked. */
    assert(ES_MAX_PATCHES > 0);
    return es_n_patches;
}

int es_get_patch_at(size_t idx, es_patch_t *out) {
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (idx >= es_n_patches) {
        return ES_ERR_PATCH_OUT_OF_RANGE;
    }
    assert(out != NULL);
    assert(idx < es_n_patches);
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
static const double ES_PI     = 3.141592653589793238462643383279;
static const double ES_MODULO_DOUBLE = 4294967296.0;  /* 2^32 */

/* ------------------------------------------------------------------ */
/*  v0.28.0rc5 (ABI v9) — Newton-Kepler evaluator                     */
/* ------------------------------------------------------------------ */
/*
 * Mirror of `EccentricityCorrectionPatch._solve_kepler` and
 * `_true_anomaly` from `_research/diagnosed_fibers.py`. JPL Power-
 * of-Ten clean:
 *
 *  - Rule 1: no goto.
 *  - Rule 2: Newton iteration bounded at 30 steps.
 *  - Rule 3: no malloc.
 *  - Rule 4: each helper is well under 60 lines.
 *  - Rule 5: every function carries >= 2 asserts (entry pre-cond + post).
 *
 * libm calls used here: sin, cos, atan2, sqrt, floor. These are the
 * same libm names the existing sinusoidal patch evaluator pulls;
 * the EOC kind doesn't introduce a new libm dependency class.
 */

/* Solve Kepler's equation E - e*sin(E) = M for E.
 * Warm-start: E = M + e*sin(M) when e > 0.6 (per the Python ref).
 * Newton step: E -= (E - e*sin(E) - M) / (1 - e*cos(E)).
 * Tolerance: 1e-14 rad. Iteration cap: 30 (bounded loop per Rule 2).
 */
static double es_solve_kepler(double M, double e) {
    assert(e >= 0.0);
    assert(e < 1.0);
    double E = (e > 0.6) ? (M + e * sin(M)) : M;
    for (int i = 0; i < 30; ++i) {
        const double f  = E - e * sin(E) - M;
        const double fp = 1.0 - e * cos(E);
        /* fp >= 1 - e > 0 for e in [0, 1); no division-by-zero. */
        assert(fp > 0.0);
        const double delta = f / fp;
        E -= delta;
        if (fabs(delta) < 1e-14) {
            return E;
        }
    }
    /* Fall through after the bounded loop. The 30-iter cap is well
     * past typical convergence (4-6 iters for e < 0.5; 8-12 for
     * e ~ 0.7). Returning the last estimate keeps the residue
     * contribution bounded. */
    return E;
}

/* True anomaly via the half-angle formula:
 *   nu = 2 * atan2( sqrt(1+e) * sin(E/2), sqrt(1-e) * cos(E/2) ).
 * Avoids the +/- ambiguity that bites a direct cos(nu) inversion.
 */
static double es_true_anomaly(double E, double e) {
    assert(e >= 0.0);
    assert(e < 1.0);
    const double E_half = E * 0.5;
    const double s = sqrt(1.0 + e) * sin(E_half);
    const double c = sqrt(1.0 - e) * cos(E_half);
    /* IEEE 754 atan2(0, 0) = 0 — safe degenerate behaviour at e=0,E=0
     * (the BIP encoder calibrates initial phases at J2000 so this
     * path triggers only at the calibration epoch itself). */
    return 2.0 * atan2(s, c);
}

/* One EOC patch's residue contribution at delta_t_days.
 *
 * The patch is J2000-anchored: returns
 *   (nu(t) - M(t)) - (nu(J2000) - M_0)
 * mapped to a uint32 residue. By construction returns 0 at
 * delta_t = 0 (no double-counting with BIP's L_true(J2000)
 * calibration).
 *
 * The wrap-to-principal-branch uses floor-based modulo (single libm
 * call) instead of a while loop — keeps the function bounded with
 * no risk of unbounded iteration on extreme inputs.
 */
static int64_t es_eval_eoc_residue(const es_patch_t *p, double delta_t_days) {
    assert(p != NULL);
    assert(p->kind == ES_PATCH_KIND_ECCENTRICITY_CORRECTION);
    const double M_t = p->mean_anomaly_at_j2000_rad
                       + p->n_rad_per_day * delta_t_days;
    const double M_0 = p->mean_anomaly_at_j2000_rad;
    const double E_t = es_solve_kepler(M_t, p->eccentricity);
    const double E_0 = es_solve_kepler(M_0, p->eccentricity);
    const double nu_t = es_true_anomaly(E_t, p->eccentricity);
    const double nu_0 = es_true_anomaly(E_0, p->eccentricity);
    /* (nu(t) - M(t)) - (nu(J2000) - M_0). */
    double correction_rad = (nu_t - M_t) - (nu_0 - M_0);
    /* Wrap to principal branch (-pi, +pi]. */
    correction_rad -= ES_TWO_PI * floor((correction_rad + ES_PI) / ES_TWO_PI);
    assert(correction_rad > -ES_PI - 1.0e-12);
    assert(correction_rad <= ES_PI + 1.0e-12);
    /* rad -> uint32 residue: residue = round(rad / (2*pi) * 2^32). */
    return es_banker_round(correction_rad / ES_TWO_PI * ES_MODULO_DOUBLE);
}

void es_apply_overlay_to_phases(double delta_t_days, uint64_t curr_phases[ES_N_BODIES]) {
    assert(curr_phases != NULL);
    assert(es_n_patches <= ES_MAX_PATCHES);
    if (es_n_patches == 0) {
        return;  /* hot-path zero-cost when no patches active */
    }
    for (size_t k = 0; k < es_n_patches; ++k) {
        const es_patch_t *p = &es_active_patches[k];
        if (p->kind == ES_PATCH_KIND_ECCENTRICITY_CORRECTION) {
            /* v0.28.0rc5 EOC kind: Newton-Kepler residue, J2000-
             * anchored. The Python BIP encoder evaluator (mirrored
             * here) produces byte-identical phase residues —
             * pinned by test_eoc_catalog's both-backends parity
             * test. */
            assert(p->eccentricity >= 0.0);
            assert(p->eccentricity < 1.0);
            const int64_t delta = es_eval_eoc_residue(p, delta_t_days);
            curr_phases[p->body_idx_a] += (uint64_t)delta;
            continue;
        }
        /* SINUSOID / COUPLED_SINUSOID (v0.4.1, ABI v2). */
        assert(p->period_days > 0.0);  /* registered patches passed validate */
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
