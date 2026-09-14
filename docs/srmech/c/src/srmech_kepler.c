/*
 * srmech_kepler.c — Class K primitive: equation-of-centre / pin-slot.
 *
 * Task #217 Phase C1 rc7 — Class K earns its C surface per the per-class
 * parity discipline. Continuous projection-shadow of the integer-cyclic
 * upstream (Class I cyclic groups + Class J prime-period). Trig routes through
 * the Class-N cascade (srmech_sin / srmech_cos / srmech_atan2, rc43); the
 * convergence magnitude is a Class-K sign-branch (never fabs, rc46) — so this
 * file holds NO libm call. Double precision throughout.
 *
 * Three load-bearing operations:
 *
 *   - srmech_pin_slot           : era-appropriate Antikythera pin-and-slot
 *                                 transform (Freeth 2021 Supp S9 reconstruction)
 *   - srmech_kepler_solve       : Newton-Raphson on Kepler's equation
 *                                 M = E - e * sin(E)  (Kepler 1609 + Smith 1979)
 *   - srmech_equation_of_centre : Fourier-series principal-term-per-harmonic
 *                                 nu - M in eccentricity e (Brouwer & Clemence
 *                                 1961 §3.2 + Murray & Dermott 1999 §2.5)
 *
 * Per [[user_stance_kepler_shape_universal]] + PR #416 F2/F15/F17:
 * Kepler-equation algebra IS pin-slot composition. The bronze instantiates
 * Class K natively (pin-on-eccentric-disc + radial slot follower); the
 * universe instantiates the same algebra via gravitational dynamics. Same
 * Kepler-shape primitive cascade at different dimensional reaches per
 * [[user_stance_1d_t_as_storage_extraction]].
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Pin-slot transform        : Freeth (2021) Nature Sci Rep, Supp S9.
 *   - Kepler equation           : Kepler (1609) Astronomia Nova.
 *   - Newton-Raphson starter    : Smith (1979) Celestial Mech 19, 163.
 *   - Equation-of-centre series : Brouwer & Clemence (1961) Methods of
 *                                 Celestial Mechanics, §3.2; Murray &
 *                                 Dermott (1999) Solar System Dynamics,
 *                                 §2.5 eq 2.84-2.88.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — Newton-Raphson capped at max_iter
 *                              (caller; default 30); equation-of-centre
 *                              bounded at SRMECH_KEPLER_EOC_MAX_TERMS = 6
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/fn)  : OK — entry-pointer assert +
 *                              precondition / post-condition invariant
 *                              (per [[feedback_jpl_rule_5_two_assert_habit]])
 *   - Rule 7 (return-value)   : OK as of 0.9.0rc473 — every srmech_status_t
 *                              returned inside this file is captured and
 *                              checked. It was VIOLATED through rc472 at
 *                              SEVEN sites, and this line read "OK —
 *                              srmech_status_t throughout" from the file's
 *                              first commit to rc472; every one of those
 *                              discards was already present. Rule 7 is about
 *                              CHECKING a returned value, not about declaring
 *                              a return type, and "srmech_status_t
 *                              throughout" answers the second question while
 *                              appearing to answer the first.
 *
 *                              It survived because Rule 7 HAD no detector in
 *                              the pytest ratchet: tests/test_jpl_audit.py
 *                              mechanically ratcheted Rules 1, 3, 4, 5, 8 and
 *                              9, and carried no RULE_7 symbol at all, so
 *                              this claim was never measured against
 *                              anything. (The rc473 pre-publish pass shipped
 *                              one — four test_rule_7_* functions, 13 passed
 *                              -> 17 passed, and 32 RULE_7 occurrences in
 *                              that file. Those three clauses stood in the
 *                              PRESENT tense until the A6 repair pass; the
 *                              CHANGELOG entry corrected its own paraphrase
 *                              of this very sentence at A4 and left the
 *                              source file it paraphrases untouched.)
 *                              Measured at rc473 by planting
 *                              warn_unused_result on the seven Class-N
 *                              callees and compiling c/src unmodified: 24
 *                              -Wunused-result diagnostics across 7 files,
 *                              the same file:line set the
 *                              `(void)srmech_<callee>(` grep finds, 0 other
 *                              diagnostics. Seven of the 24 were here.
 *
 *                              What replaces the missing detector for this
 *                              family is SRMECH_NODISCARD in srmech.h: the
 *                              seven Class-N callees and their seven clean
 *                              _q61 peers carry warn_unused_result, and on
 *                              gcc neither a bare call nor an explicit
 *                              (void) cast silences it, so re-introducing
 *                              any of the 24 is a -Werror build failure
 *                              rather than a quiet regression. That is a
 *                              compile-time guard on this ONE family, not a
 *                              Rule-7 detector over the whole library; the
 *                              general ratchet is still owed.
 *
 *                              Corrected rather than deleted, per the
 *                              in-place-correction precedent JPL_AUDIT.md
 *                              sets for its own headline.
 *   - Rule 10 (warnings clean): OK
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_trig_internal.h"

#include <assert.h>
#include <stddef.h>

/* Principal sin(kM) coefficient at lowest-order e^k contribution.
 * Index i = k-1 (i.e., coefficients[0] is the sin(M) coefficient at e^1).
 * Values per Brouwer & Clemence 1961 §3.2; cross-checked against Murray &
 * Dermott 1999 §2.5 Table 2.5 + eq 2.84-2.88. Capped at k = 6 to keep
 * coefficient verification straightforward; higher orders can extend the
 * table without ABI changes. */
static const double SRMECH_KEPLER_EOC_COEFFS[SRMECH_KEPLER_EOC_MAX_TERMS] = {
    2.0,                     /* k=1: 2 e            sin(M)  */
    5.0 / 4.0,               /* k=2: (5/4) e^2      sin(2M) */
    13.0 / 12.0,             /* k=3: (13/12) e^3    sin(3M) */
    103.0 / 96.0,            /* k=4: (103/96) e^4   sin(4M) */
    1097.0 / 960.0,          /* k=5: (1097/960) e^5 sin(5M) */
    1223.0 / 960.0           /* k=6: (1223/960) e^6 sin(6M) */
};

/* Finiteness inline, the srmech_eph_propagate_sparse idiom: x == x rejects
 * NaN, x - x == 0 rejects ±Inf (Inf - Inf is NaN). No libm, no dedicated
 * predicate function (a pure single-scalar predicate would need a JPL Rule-5
 * exemption; the inline form does not). Single-line macro — Rule 8. */
#define KEP_FINITE(x) (((x) == (x)) && ((x) - (x) == 0.0))

/* rc473 repair pass (`#T1188`) — THE GEOMETRY ARGUMENTS, and the comment
 * lives above the signature for the same JPL Rule-4 reason the eccentricity
 * band's does below: lines BETWEEN the braces are what the cap counts.
 *
 * theta was already refused for the whole Class-N cascade domain (the
 * srmech_cos / srmech_sin / srmech_atan2 statuses this function propagates).
 * pin_offset and pin_distance were not checked at all, and they never reach
 * a callee that could check them — they enter at the bare double arithmetic
 * `x = pin_distance + pin_offset * cs`, so this function is the only place
 * the argument exists. MEASURED at rc473 on an authenticated cell (ABI 26):
 *   srmech_pin_slot(0.0, 1.0, +Inf) -> (SRMECH_OK, 0.0)
 *   srmech_pin_slot(0.0, 1.0, -Inf) -> (SRMECH_OK, 3.141592653589793)
 * while the pure peer raises on the SAME arguments — `pin_distance +
 * pin_offset * cos(theta)` is `float + Q`, and Q is the finite-rational
 * carrier, so it refuses a non-finite float. That is ADR-0009 §2.4, a
 * serve-vs-refuse divergence at a slot NO filed row named: §1.2's row 52
 * files kepler_solve at a large M, a different argument.
 *
 * rc473 repair round 1 (`#T1188`): this note said a non-finite pin_offset
 * "already refused here, but only by accident ... at no change of status".
 * That was true only where the Q61 sin(theta) is exactly 0 (`Inf * 0.0` is
 * NaN, which srmech_atan2 refuses), and every row that pinned it drove
 * theta = 0.0. MEASURED at 1ab8d405b on an authenticated WSL2 gcc cell (ABI
 * 26), over theta in {0, 1e-300, 0.3, 1, pi/2, 3, pi, -2, 100, 2^54}:
 * pin_offset = +Inf or -Inf with pin_distance = 1.0 returned SRMECH_OK at 8
 * of the 10 angles, e.g. srmech_pin_slot(0.3, +Inf, 1.0) -> (SRMECH_OK,
 * 0.7853981633974483), and was refused only at theta = 0.0 and 1e-300, whose
 * Q61 sine is 0. So the guard below DID change the status, at every other
 * angle. Both are PRECONDITIONS on this function's own arguments, which is why
 * they sit beside the (0, 0) refusal rather than inside a callee. */
srmech_status_t srmech_pin_slot(double  theta,
                                double  pin_offset,
                                double  pin_distance,
                                double *out_phi)
{
    assert(out_phi != NULL);
    assert(pin_distance != 0.0 || pin_offset != 0.0);
    if (out_phi == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_phi = 0.0;
    /* Degenerate case: zero baseline AND zero pin offset. atan2(0, 0) is
     * implementation-defined; refuse rather than silently return 0. */
    if (pin_distance == 0.0 && pin_offset == 0.0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* rc473 (`#T1188`): the geometry must be finite — see the note above. */
    if (!KEP_FINITE(pin_offset) || !KEP_FINITE(pin_distance)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Standard Antikythera pin-and-slot: pin position relative to follower
     * axis is (d + i*cos(theta), i*sin(theta)); follower angle is the
     * angle to that point. Per Freeth 2021 Supp S9. */
    /* Class-N cascade trig (srmech_cos/sin/atan2), not libm — so the native
     * executable runs the same cascade as the Python source (rc43, C-transpile
     * triality coherence). */
    /* Each cascade call's status is CAPTURED and CHECKED (rc473, `#T1188`).
     * *out_phi was set to 0.0 above, so a refusal leaves a defined value that
     * is not an answer, and the caller learns which it is from the status. */
    double cs;
    double sn;
    srmech_status_t st = srmech_cos(theta, &cs);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sin(theta, &sn);
    if (st != SRMECH_OK) { return st; }
    double x = pin_distance + pin_offset * cs;
    double y = pin_offset * sn;
    return srmech_atan2(y, x, out_phi);
}

/* rc473 (`#T1188`): the srmech_sin / srmech_cos statuses inside the Newton
 * iteration were captured and checked. Through rc472 they were discarded, and
 * the consequence was not a NaN but a plausible number: srmech_sin(2^55)
 * already refused and wrote 0.0, so E was never moved off its M initial guess
 * and the caller was handed E == M with SRMECH_OK. Measured at rc472,
 * srmech_kepler_solve(2^55, 0.3, 1e-12, 20) -> (SRMECH_OK,
 * 3.602879701896397e+16), and 3.602879701896397e+16 IS 2^55.
 *
 * rc473 repair round 1 (`#T1188`): the iteration no longer calls srmech_sin
 * or srmech_cos at all. It runs on the Q61 quarter-turn carrier in
 * srmech_trig.c (srmech_trig_kepler_q61), which reduces M ONCE and refuses an
 * M with no reduction before any iterate exists, so there is no mid-iteration
 * refusal left to propagate: E = M + eps with |eps| bracketed by round(e *
 * 2^61) Q61 units (at most 2^-62 rad above e), and the residue re-reduction
 * cannot leave the carrier. It is Newton-Raphson over the Q61 Taylor cores at
 * a declared 2^-61 rad precision, not an exact root of Kepler's equation. */
/* rc473 repair pass (`#T1188`) — THE ECCENTRICITY BAND, and the comment lives
 * HERE rather than beside the guard on purpose: JPL Rule 4 counts lines
 * BETWEEN the braces, and this function measured 58 against a cap of 60 with
 * six comment lines inside it. Two lines of headroom is a trap for the next
 * edit, and the ratchet is down-only, so the design moves rather than the
 * ratchet. With the prose out here it was 52 again — the figure it carried
 * before the repair — and srmech_equation_of_centre 32, both read with the
 * audit's own _scan_functions rather than by counting. (Repair round 1 moved
 * the Newton iteration into srmech_trig.c; the same scanner now reads this
 * function at 34 and srmech_equation_of_centre at 32.) A comment above a
 * signature costs nothing under Rule 4; the same comment one line lower costs
 * its full length.
 *
 * Both eccentricity guards in this file were spelled `e < 0.0 || e >= 1.0`,
 * which is NaN-BLIND: both comparisons are false for a NaN, so the rejecting
 * branch is not taken and the NaN flows on. The Python peer has always
 * spelled it `if not (0.0 <= e < 1.0)` (srmech/math/kepler.py, in
 * kepler_solve and equation_of_centre alike), which IS NaN-catching — so the
 * two projections differed in which inputs they serve, ADR-0009 §2.4, the
 * exact class this rc exists to close. Both are now the NEGATION of the
 * accepted band.
 *
 * rc473 SECOND repair (`#T1188`) — THE TOLERANCE, a slot no filed row named.
 * Until repair round 1 `tolerance` reached no callee either: it was only ever
 * the right-hand side of `adelta < tolerance`, so a non-finite one was never
 * examined. MEASURED on an authenticated cell (ABI 26), M = pi/2, e = 0.0549,
 * max_iter = 20, before the guard below existed:
 *   tolerance = +Inf  -> (SRMECH_OK, 1.625613861425157)   [pure RAISED]
 *   tolerance =  NaN  -> (SRMECH_ERR_OVERFLOW, ...)       [pure RAISED]
 *   tolerance = -Inf  -> (SRMECH_ERR_OVERFLOW, ...)       [pure RAISED]
 * The +Inf row was the serve-vs-refuse divergence: `adelta < +Inf` was true
 * on the first step, so C returned the ONE-Newton-step estimate and called it
 * converged. The other two were the same defect wearing a different answer —
 * `adelta < NaN` is never true, so the loop ran out and the caller was told
 * "did not converge" about an argument that was never a tolerance. The pure
 * peer refused all three at `Q < float`, Q being the finite-rational carrier.
 * The guard below left every FINITE tolerance to the iteration. Since repair
 * round 1 the tolerance reaches srmech_trig_kepler_q61, where CONVERGED means
 * |step| * 2^-61 < tolerance, so a finite tolerance's verdict and value are
 * the Q61 iteration's: kepler_solve(pi/2, 0.9) is 2.263415106356943 in both
 * cells, where the pre-round double loop gave 2.2634151063569425. Zero and
 * negative tolerances are still never met. srmech.h v26 clause (c). */
srmech_status_t srmech_kepler_solve(double    M_rad,
                                    double    e,
                                    double    tolerance,
                                    uint32_t  max_iter,
                                    double   *out_E_rad)
{
    assert(out_E_rad != NULL);
    assert(max_iter > 0 || e == 0.0);
    if (out_E_rad == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_E_rad = M_rad;
    if (!(e >= 0.0 && e < 1.0)) {                    /* NaN-catching; see above */
        return SRMECH_ERR_BAD_INPUT;
    }
    if (max_iter == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!KEP_FINITE(tolerance)) {           /* rc473: see the note above    */
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Circular orbit (e = 0): E = M exactly. */
    if (e == 0.0) {
        return SRMECH_OK;
    }
    /* rc473 repair round 1 (`#T1188`): the Smith (1979) starter and the
     * Newton iteration run on the Q61 quarter-turn carrier, in srmech_trig.c,
     * as ONE integer cascade the pure peer runs too; the note above the
     * function explains why. An M with no Q61 reduction is refused there with
     * *out_E_rad left at M_rad (set above). Non-convergence is still
     * SRMECH_ERR_OVERFLOW with the best-effort E, so the caller can tighten
     * the tolerance, raise max_iter, or accept the partial result. */
    return srmech_trig_kepler_q61(M_rad, e, tolerance, max_iter, out_E_rad);
}

/* rc473 (`#T1188`) — THE row this rc is named for. 4 * (2^53 + 1) is exactly
 * 2^55, which srmech_sin already refused at rc472, and the sin call inside
 * the harmonic loop discarded that refusal: the C projection answered
 * (SRMECH_OK, -0.08984990210223018) for an input the Python projection
 * raised ValueError on. The status is now propagated; *out_delta_rad stays
 * at the 0.0 set on entry, which is a defined value and not an answer.
 *
 * rc473 REPAIR PASS: the eccentricity guard below carried the SAME NaN-blind
 * spelling as kepler_solve's (see that function's block above), and HERE it
 * was reachable. MEASURED at the branch head before the repair, native cell,
 * ABI 26 == 26: srmech_equation_of_centre(0.7, NaN, 4) -> status 0
 * (SRMECH_OK), out = nan, while kepler.equation_of_centre(0.7, nan, 4) raised
 * "e must satisfy 0 <= e < 1; got nan". kepler_solve was saved only
 * INCIDENTALLY — a NaN e poisons E and srmech_sin now refuses NaN — and this
 * one had no such backstop, because e never reaches a callee that validates
 * it: it is only ever MULTIPLIED. Its NaN row is pinned in the C-host gate
 * anyway, because "saved incidentally" is a property of today's callees and
 * not a contract. */
srmech_status_t srmech_equation_of_centre(double    M_rad,
                                          double    e,
                                          uint32_t  n_terms,
                                          double   *out_delta_rad)
{
    assert(out_delta_rad != NULL);
    assert(n_terms <= SRMECH_KEPLER_EOC_MAX_TERMS);
    if (out_delta_rad == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_delta_rad = 0.0;
    if (!(e >= 0.0 && e < 1.0)) {                    /* NaN-catching; see above */
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n_terms == 0 || n_terms > SRMECH_KEPLER_EOC_MAX_TERMS) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Sum principal-term-per-harmonic: c_k * e^k * sin(k * M) for k = 1..n.
     * e_power accumulates e^k iteratively to avoid pow() calls. */
    double delta = 0.0;
    double e_power = 1.0;
    for (uint32_t k_idx = 0; k_idx < n_terms; k_idx++) {
        e_power *= e;
        double harmonic = (double)(k_idx + 1) * M_rad;
        double sin_h;
        srmech_status_t st = srmech_sin(harmonic, &sin_h);
        if (st != SRMECH_OK) { return st; }
        delta += SRMECH_KEPLER_EOC_COEFFS[k_idx] * e_power * sin_h;
    }
    *out_delta_rad = delta;
    return SRMECH_OK;
}
