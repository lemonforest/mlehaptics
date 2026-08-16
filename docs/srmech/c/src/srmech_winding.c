/*
 * srmech_winding.c — the One's winding-surface readouts (siona gh#1276; rc137).
 *
 * The winding w lifts SO -> Spin (the double cover). These are the exact
 * INTEGER readouts of the winding TRIAD carried WHOLE by
 * srmech.cascade.one.One. They do NOT touch the S(sigma,theta) adjoint
 * generator (a separate owed-C item; the winding ops are independent of it).
 * Every op here is exact-integer -> BYTE-IDENTICAL to the Python (no float,
 * in contrast to the numeric srmech_eph_propagate).
 *
 * The chirality is a READOUT of w's binary TOWER via divmod (the Z/2 GRADING
 * KEPT), NOT sigma = w mod 2 (the quotient map that throws the carry away and
 * MELDS w=5 == w=7 == 1). No abs(): sigma is the Class-K pin/sign, and a
 * retrograde winding is the Class-C orientation reversal (-w), computed via
 * defined unsigned wraparound (no INT64_MIN undefined behaviour).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — 64 (int64 bit-width)
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (<=60 lines/func): OK
 *   - Rule 5 (>=2 asserts/fn) : OK — arg pointer + post-condition each
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * ABI: additive symbols only -> SRMECH_ABI_VERSION stays 3.
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* int64 bit-width — the bound for every winding-tower / popcount loop. */
#define SRMECH_WINDING_INT64_BITS 64

/* Population count of |w| — the number of set bits of the Class-K magnitude
 * (no abs(); a retrograde winding negates via defined unsigned wrap). Used by
 * srmech_sigma_effective to grade sigma by the FULL tower (every bit counts),
 * NOT the bare low bit `w mod 2`. */
static srmech_status_t srmech_winding_popcount(int64_t w, int32_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    uint64_t m = (w >= 0) ? (uint64_t)w : ((uint64_t)0 - (uint64_t)w);
    int32_t count = 0;
    for (int i = 0; i < SRMECH_WINDING_INT64_BITS; i++) {
        count += (int32_t)(m & 1u);
        m >>= 1;
    }
    *out = count;
    assert(*out >= 0 && *out <= SRMECH_WINDING_INT64_BITS);
    return SRMECH_OK;
}

srmech_status_t srmech_winding_tower(int64_t w, uint8_t *bits_out,
                                     int32_t bits_cap, int32_t *n_bits_out)
{
    assert(bits_out != NULL);
    assert(n_bits_out != NULL);
    if (bits_out == NULL || n_bits_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (bits_cap < 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Class-K magnitude of the WHOLE winding (no abs()); the tower is over the
     * magnitude, and the caller still holds the orientation -- in the winding
     * triad ITSELF, NOT in sigma and NOT in srmech_sigma_effective.
     *
     * rc440 (`#T1147`): this comment named sigma / sigma_effective as the
     * carrier through rc439, and that was MEASURED FALSE. Over w in [-4,4]^3
     * (729 windings) the triad-wide tower takes 125 values, its fibres being
     * exactly the per-component magnitude classes -- 2092 within-fibre pairs,
     * of which sigma_effective separates 0 (a REFUTED null: the same read
     * separates 132678 pairs overall). It cannot work by construction:
     * srmech_sigma_effective is sigma*(-1)^popcount(tower(w_k)), a pure
     * function of THIS function's own output, so it is constant on every
     * fibre; and sigma is an independent parameter unrelated to w's sign. The
     * orientation is absent from this output (125 values cannot separate 729 --
     * information-theoretic, not a difficulty claim) and fully present in the
     * triad the caller passed in. */
    uint64_t m = (w >= 0) ? (uint64_t)w : ((uint64_t)0 - (uint64_t)w);
    int32_t n = 0;
    for (int i = 0; i < SRMECH_WINDING_INT64_BITS; i++) {
        if (m == 0) {
            break;
        }
        if (n >= bits_cap) {
            return SRMECH_ERR_OVERFLOW;
        }
        bits_out[n] = (uint8_t)(m & 1u);   /* divmod(.,2): the grading bit */
        m >>= 1;                            /* divmod(.,2): the retained carry */
        n++;
    }
    *n_bits_out = n;                        /* LSB-first; w=0 -> empty tower */
    assert(n >= 0 && n <= SRMECH_WINDING_INT64_BITS);
    return SRMECH_OK;
}

srmech_status_t srmech_sigma_effective(int32_t sigma, int64_t w0, int64_t w1,
                                       int64_t w2, int32_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (sigma != 1 && sigma != -1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int32_t p0 = 0;
    int32_t p1 = 0;
    int32_t p2 = 0;
    srmech_status_t st = srmech_winding_popcount(w0, &p0);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_winding_popcount(w1, &p1);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_winding_popcount(w2, &p2);
    if (st != SRMECH_OK) {
        return st;
    }
    /* sigma modulated by the parity of the FULL popcount over the triad's
     * towers (the anti-collapse: 5 has popcount 2, 7 has popcount 3 -> they
     * are DISTINGUISHED, where bare `w mod 2` would meld them). */
    int32_t total = p0 + p1 + p2;
    *out = ((total & 1) == 0) ? sigma : -sigma;
    assert(*out == 1 || *out == -1);
    return SRMECH_OK;
}

srmech_status_t srmech_spinor_sign(int64_t w0, int64_t w1, int64_t w2,
                                   int32_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* The double-cover sign (-1)^(w0+w1+w2). Parity of the sum = XOR of the
     * three low bits (addition mod 2); the two's-complement low bit equals the
     * Python `w % 2` parity for negative w too. This IS Z/2 on the SIGN (the
     * genuine Spin->SO 2:1 lift), while w stays WHOLE in the winding field. */
    uint64_t parity = ((uint64_t)w0 ^ (uint64_t)w1 ^ (uint64_t)w2) & 1u;
    *out = (parity == 0u) ? 1 : -1;
    assert(*out == 1 || *out == -1);
    return SRMECH_OK;
}

srmech_status_t srmech_unwrapped_phase(int64_t w0, int64_t w1, int64_t w2,
                                       int64_t *turns_out)
{
    assert(turns_out != NULL);
    if (turns_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* The per-metacycle-scale unwrapped-phase TURNS (2*pi*w_k + theta): the
     * full integer turns a theta-only (2π-periodic) object folds away. The
     * turns ARE the winding triad, whole; theta is a pass-through rational the
     * caller carries alongside (pi stays a cascade, never a float here). */
    turns_out[0] = w0;
    turns_out[1] = w1;
    turns_out[2] = w2;
    assert(turns_out[0] == w0 && turns_out[2] == w2);
    return SRMECH_OK;
}

/* ================================================================== *
 * rc313 — srmech_genome_discrete_writhe: the EXACT-integer directional
 * discrete writhe of a polygonal backbone.
 *
 * The physical-topology peer of the intrinsic mod-2 center-parity
 * holonomy (srmech_quaternion_cycle_holonomy, rc309). Given a supplied
 * 3D embedding of the backbone (each vertex an EXACT RATIONAL, num/den
 * per coordinate), this computes the DIRECTIONAL signed-crossing writhe
 * in the projection that drops z (view along the z-axis):
 *
 *     Wr = Σ_{i<j, non-adjacent}  ε_ij ,
 *     ε_ij = sign( T_ij )  when segments i,j cross in the xy-projection,
 *            else 0,
 *     T_ij = (B−A) · ((D−C) × (C−A))     (the scalar triple product,
 *            A=P_i, B=P_{i+1}, C=P_j, D=P_{j+1}).
 *
 * This is the DISCRETE Gauss double-sum over segment PAIRS in its
 * exact-integer form — NOT the smooth solid-angle Gauss writhe (which is
 * transcendental and cannot be a rational). The directional writhe is an
 * INTEGER (the signed crossing number of the diagram); the smooth writhe
 * is its average over the direction sphere, which this op does NOT
 * compute (that needs arccos/solid-angles — out of exact-rational
 * scope). We use only its PARITY in the mod-2 CWF check, where +1 ≡ −1,
 * so the absolute sign convention is immaterial to that check.
 *
 * Exactness: every crossing decision (four 2D orientation determinants)
 * and every ε (a 3D triple-product determinant) is the SIGN of an
 * integer determinant computed over srmech_bigint — no float can flip a
 * near-degenerate crossing sign (the W4 lesson). The four vertices of a
 * pair are scaled to a COMMON POSITIVE integer denominator per axis
 * (each coord = num · Π(other three denoms), after normalising each
 * denom > 0), so the determinant sign equals the exact rational sign.
 *
 * A non-generic projection (a vertex projecting onto a segment's line
 * where it would decide a crossing) returns SRMECH_ERR_BAD_INPUT — the
 * caller nudges the embedding (the winding-number "hits a root" nudge).
 * A vanishing triple product AT a proper crossing means the strands meet
 * in 3D (not an embedding) — also SRMECH_ERR_BAD_INPUT.
 *
 * JPL: no goto, no malloc (caller arena), bounded loops, ≤60-line
 * functions, ≥2 asserts/function, srmech_status_t returns. ABI additive
 * (new symbols) → SRMECH_ABI_VERSION stays 10.
 * ------------------------------------------------------------------ */

/* Per-intermediate bigint capacity (limbs). The scaled coords are ≤ 8
 * limbs (int64 num × three int64 denoms); a 3×3 integer determinant of
 * such entries stays well under 64 limbs. 128 is generous headroom. */
#define SRMECH_DW_LIMB_CAP 128u

/* Fixed caller-arena size. All scratch is per-PAIR and rewound each pair
 * (the bump offset resets to 0), so the arena is O(1) in point count.
 * ~40 live bigints × 128 limbs × 4 bytes ≈ 20 KiB; 128 KiB is slack. */
#define SRMECH_DW_ARENA_BYTES (128u * 1024u)

/* A trivial bump arena over caller ws. */
typedef struct srmech_dw_arena {
    unsigned char *base;
    size_t         off;
    size_t         cap;
} srmech_dw_arena_t;

/* Carve one SRMECH_DW_LIMB_CAP-limb bigint (empty = 0) from the arena,
 * 8-byte aligned. OVERFLOW if the arena is exhausted. */
static srmech_status_t srmech_dw_bi(srmech_dw_arena_t *a, srmech_bigint_t *out)
{
    assert(a != NULL);
    assert(out != NULL);
    size_t need = (size_t)SRMECH_DW_LIMB_CAP * sizeof(uint32_t);
    size_t at = (a->off + 7u) & ~(size_t)7u;
    if (at + need > a->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    out->limbs = (uint32_t *)(a->base + at);
    out->cap = SRMECH_DW_LIMB_CAP;
    out->n = 0;
    out->sign = 0;
    a->off = at + need;
    assert(a->off <= a->cap);
    return SRMECH_OK;
}

/* Scale one axis of the 4 pair-vertices to a common positive integer:
 * out[k] = num[k] · Π_{m≠k} den[m], with each (num,den) pre-normalised
 * to den > 0. Writes 4 carved bigints out[0..3]. */
static srmech_status_t srmech_dw_scale4(srmech_dw_arena_t *ar,
                                        const int64_t num[4],
                                        const int64_t den[4],
                                        srmech_bigint_t out[4])
{
    assert(num != NULL && den != NULL);
    assert(out != NULL);
    srmech_bigint_t t1, t2, dn;
    srmech_status_t st = srmech_dw_bi(ar, &t1);
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &t2); }
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &dn); }
    for (int k = 0; k < 4 && st == SRMECH_OK; k++) {
        st = srmech_dw_bi(ar, &out[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&out[k], num[k]); }
        for (int m = 0; m < 4 && st == SRMECH_OK; m++) {
            if (m == k) { continue; }
            st = srmech_bigint_set_i64(&dn, den[m]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&t1, &out[k]); }
            if (st == SRMECH_OK) { st = srmech_bigint_mul(&t2, &t1, &dn); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&out[k], &t2); }
        }
    }
    assert(st != SRMECH_OK || out[0].cap == SRMECH_DW_LIMB_CAP);
    return st;
}

/* sign of the 2×2 determinant (q−p)×(r−p) in the (X,Y) integer plane:
 *   d = (Xq−Xp)(Yr−Yp) − (Yq−Yp)(Xr−Xp).
 * X[],Y[] index the 4 pair-vertices; p,q,r pick three of them. */
static srmech_status_t srmech_dw_orient2d(srmech_dw_arena_t *ar,
                                          const srmech_bigint_t X[4],
                                          const srmech_bigint_t Y[4],
                                          int p, int q, int r, int *sgn)
{
    assert(X != NULL && Y != NULL);
    assert(sgn != NULL);
    srmech_bigint_t xqp, yrp, yqp, xrp, m0, m1, d = {0};
    srmech_status_t st = srmech_dw_bi(ar, &xqp);
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &yrp); }
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &yqp); }
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &xrp); }
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &m0); }
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &m1); }
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &d); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(&xqp, &X[q], &X[p]); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(&yrp, &Y[r], &Y[p]); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(&yqp, &Y[q], &Y[p]); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(&xrp, &X[r], &X[p]); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&m0, &xqp, &yrp); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&m1, &yqp, &xrp); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(&d, &m0, &m1); }
    if (st != SRMECH_OK) { return st; }
    *sgn = d.sign;
    assert(*sgn == -1 || *sgn == 0 || *sgn == 1);
    return SRMECH_OK;
}

/* out = a·b − c·d (a 2×2 minor), all carved. */
static srmech_status_t srmech_dw_cross2(srmech_dw_arena_t *ar,
                                        const srmech_bigint_t *a,
                                        const srmech_bigint_t *b,
                                        const srmech_bigint_t *c,
                                        const srmech_bigint_t *d,
                                        srmech_bigint_t *out)
{
    assert(a != NULL && b != NULL && c != NULL && d != NULL);
    assert(out != NULL);
    srmech_bigint_t p0, p1;
    srmech_status_t st = srmech_dw_bi(ar, &p0);
    if (st == SRMECH_OK) { st = srmech_dw_bi(ar, &p1); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&p0, a, b); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&p1, c, d); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(out, &p0, &p1); }
    assert(st != SRMECH_OK || out->cap == SRMECH_DW_LIMB_CAP);
    return st;
}

/* sign of the scalar triple product T = u·(v×w), u=B−A, v=D−C, w=C−A,
 * for pair-vertices A=0,B=1,C=2,D=3 in the (X,Y,Z) integer coords.
 * T = ux(vy·wz − vz·wy) − uy(vx·wz − vz·wx) + uz(vx·wy − vy·wx). */
static srmech_status_t srmech_dw_triple(srmech_dw_arena_t *ar,
                                        const srmech_bigint_t X[4],
                                        const srmech_bigint_t Y[4],
                                        const srmech_bigint_t Z[4], int *sgn)
{
    assert(X != NULL && Y != NULL && Z != NULL);
    assert(sgn != NULL);
    srmech_bigint_t u[3], v[3], w[3], m0, m1, m2, t0, t1, t2, s, T = {0};
    srmech_status_t st = SRMECH_OK;
    srmech_bigint_t *slots[17] = { &u[0], &u[1], &u[2], &v[0], &v[1], &v[2],
                                   &w[0], &w[1], &w[2], &m0, &m1, &m2,
                                   &t0, &t1, &t2, &s, &T };
    for (int q = 0; q < 17 && st == SRMECH_OK; q++) { st = srmech_dw_bi(ar, slots[q]); }
    /* u=B−A (idx 1−0), v=D−C (3−2), w=C−A (2−0), per axis */
    const srmech_bigint_t *AX[3] = { X, Y, Z };
    for (int c = 0; c < 3 && st == SRMECH_OK; c++) {
        st = srmech_bigint_sub(&u[c], &AX[c][1], &AX[c][0]);
        if (st == SRMECH_OK) { st = srmech_bigint_sub(&v[c], &AX[c][3], &AX[c][2]); }
        if (st == SRMECH_OK) { st = srmech_bigint_sub(&w[c], &AX[c][2], &AX[c][0]); }
    }
    if (st == SRMECH_OK) { st = srmech_dw_cross2(ar, &v[1], &w[2], &v[2], &w[1], &m0); }
    if (st == SRMECH_OK) { st = srmech_dw_cross2(ar, &v[0], &w[2], &v[2], &w[0], &m1); }
    if (st == SRMECH_OK) { st = srmech_dw_cross2(ar, &v[0], &w[1], &v[1], &w[0], &m2); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&t0, &u[0], &m0); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&t1, &u[1], &m1); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&t2, &u[2], &m2); }
    if (st == SRMECH_OK) { st = srmech_bigint_sub(&s, &t0, &t1); }
    if (st == SRMECH_OK) { st = srmech_bigint_add(&T, &s, &t2); }
    if (st != SRMECH_OK) { return st; }
    *sgn = T.sign;
    assert(*sgn == -1 || *sgn == 0 || *sgn == 1);
    return SRMECH_OK;
}

/* One pair (A=P_i,B=P_{i+1}) × (C=P_j,D=P_{j+1}): fold the four vertices'
 * coords to den>0, scale each axis to a common positive integer, run the
 * projected-crossing test, and (if a proper crossing) set ε = sign(T).
 * *eps ∈ {-1,0,+1}; SRMECH_ERR_BAD_INPUT on a degenerate/singular pair. */
static srmech_status_t srmech_dw_pair(srmech_dw_arena_t *ar,
                                      const int64_t *xn, const int64_t *xd,
                                      const int64_t *yn, const int64_t *yd,
                                      const int64_t *zn, const int64_t *zd,
                                      const uint32_t idx[4], int *eps)
{
    assert(ar != NULL && eps != NULL);
    assert(idx != NULL);
    int64_t nx[4], dx[4], ny[4], dy[4], nz[4], dz[4];
    for (int k = 0; k < 4; k++) {
        uint32_t g = idx[k];
        if (xd[g] == 0 || yd[g] == 0 || zd[g] == 0) { return SRMECH_ERR_BAD_INPUT; }
        nx[k] = (xd[g] > 0) ? xn[g] : -xn[g];  dx[k] = (xd[g] > 0) ? xd[g] : -xd[g];
        ny[k] = (yd[g] > 0) ? yn[g] : -yn[g];  dy[k] = (yd[g] > 0) ? yd[g] : -yd[g];
        nz[k] = (zd[g] > 0) ? zn[g] : -zn[g];  dz[k] = (zd[g] > 0) ? zd[g] : -zd[g];
    }
    srmech_bigint_t X[4], Y[4], Z[4];
    srmech_status_t st = srmech_dw_scale4(ar, nx, dx, X);
    if (st == SRMECH_OK) { st = srmech_dw_scale4(ar, ny, dy, Y); }
    if (st == SRMECH_OK) { st = srmech_dw_scale4(ar, nz, dz, Z); }
    if (st != SRMECH_OK) { return st; }
    int o1 = 0, o2 = 0, o3 = 0, o4 = 0;
    st = srmech_dw_orient2d(ar, X, Y, 0, 1, 2, &o1);           /* orient(A,B,C) */
    if (st == SRMECH_OK) { st = srmech_dw_orient2d(ar, X, Y, 0, 1, 3, &o2); }
    if (st == SRMECH_OK) { st = srmech_dw_orient2d(ar, X, Y, 2, 3, 0, &o3); }
    if (st == SRMECH_OK) { st = srmech_dw_orient2d(ar, X, Y, 2, 3, 1, &o4); }
    if (st != SRMECH_OK) { return st; }
    *eps = 0;
    if (o1 * o2 > 0 || o3 * o4 > 0) { return SRMECH_OK; }       /* no crossing */
    if (o1 == 0 || o2 == 0 || o3 == 0 || o4 == 0) {
        return SRMECH_ERR_BAD_INPUT;                            /* non-generic */
    }
    int tsign = 0;
    st = srmech_dw_triple(ar, X, Y, Z, &tsign);
    if (st != SRMECH_OK) { return st; }
    if (tsign == 0) { return SRMECH_ERR_BAD_INPUT; }            /* meet in 3D */
    *eps = tsign;
    return SRMECH_OK;
}

size_t srmech_genome_discrete_writhe_arena_bytes(uint32_t n_points)
{
    (void)n_points;   /* all scratch is per-pair and rewound each pair */
    size_t bytes = (size_t)SRMECH_DW_ARENA_BYTES;
    assert(bytes > 0u);
    assert(bytes >= (size_t)SRMECH_DW_LIMB_CAP * sizeof(uint32_t));
    return bytes;
}

srmech_status_t srmech_genome_discrete_writhe(
    const int64_t *xn, const int64_t *xd,
    const int64_t *yn, const int64_t *yd,
    const int64_t *zn, const int64_t *zd,
    uint32_t n_points, int32_t closed,
    void *ws, size_t ws_len,
    int64_t *out_num, int64_t *out_den)
{
    assert(out_num != NULL && out_den != NULL);
    if (xn == NULL || xd == NULL || yn == NULL || yd == NULL ||
        zn == NULL || zd == NULL || out_num == NULL || out_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws == NULL && ws_len != 0) { return SRMECH_ERR_NULL_ARG; }
    *out_num = 0;
    *out_den = 1;
    uint32_t n_seg = (closed != 0) ? n_points : (n_points > 0 ? n_points - 1 : 0);
    if (n_seg < 2) { return SRMECH_OK; }                        /* no pair */
    srmech_dw_arena_t ar;
    ar.base = (unsigned char *)ws;
    ar.off = 0;
    ar.cap = ws_len;
    int64_t wr = 0;
    for (uint32_t i = 0; i < n_seg; i++) {
        uint32_t a = i, b = (i + 1u) % n_points;
        for (uint32_t j = i + 1u; j < n_seg; j++) {
            uint32_t c = j, d = (j + 1u) % n_points;
            if (a == c || a == d || b == c || b == d) { continue; } /* adjacent */
            ar.off = 0;                                          /* rewind pair */
            uint32_t idx[4] = { a, b, c, d };
            int eps = 0;
            srmech_status_t st = srmech_dw_pair(&ar, xn, xd, yn, yd, zn, zd,
                                                idx, &eps);
            if (st != SRMECH_OK) { return st; }
            wr += eps;
        }
    }
    *out_num = wr;
    *out_den = 1;
    assert(*out_den == 1);
    return SRMECH_OK;
}

/* ================================================================== *
 * rc313 — srmech_genome_cwf_consistency_mod2: the mod-2 Călugăreanu–
 * White–Fuller check as a WHOLE-OP C peer (genome-fully-in-C). It
 * ORCHESTRATES the existing C ops — Lk = the single cycle's center
 * parity (srmech_quaternion_cycle_holonomy), Wr = the directional
 * writhe (srmech_genome_discrete_writhe) — plus Tw = the Q₈
 * negative-coset SIGN-accumulation parity, and the verdict
 * (Tw + Wr) mod 2 == Lk mod 2. Byte-identical to the pure Python (both
 * read the SAME center parity + writhe integer). No embedding →
 * intrinsic mod-2 Lk only (out_wr_mod2 / out_consistent = -1). ABI
 * additive → SRMECH_ABI_VERSION stays 10.
 * ------------------------------------------------------------------ */

/* Carve `nbytes` raw 8-byte-aligned scratch from the bump arena, or NULL. */
static void *srmech_cwf_carve(srmech_dw_arena_t *a, size_t nbytes)
{
    assert(a != NULL);
    size_t at = (a->off + 7u) & ~(size_t)7u;
    if (at + nbytes > a->cap) {
        return NULL;
    }
    void *p = a->base + at;
    a->off = at + nbytes;
    assert(a->off <= a->cap);
    return p;
}

/* The per-turn central sign of a Q₈ gain (4 doubles): +1 for the positive
 * coset {1,i,j,k}, -1 for {-1,-i,-j,-k} — the sign of the first component past
 * `tol` (Class-K pin-slot; no fabs). */
static int srmech_cwf_gain_sign(const double *g4)
{
    assert(g4 != NULL);
    const double tol = 1e-9;
    int sign = 1;
    for (int c = 0; c < 4; c++) {
        if (g4[c] > tol) { sign = 1; break; }
        if (g4[c] < -tol) { sign = -1; break; }
    }
    assert(sign == 1 || sign == -1);
    return sign;
}

/* Lk: the center parity of the strand's SINGLE fundamental cycle, via the
 * existing srmech_quaternion_cycle_holonomy (its outputs + ws are carved from
 * `ar`). SRMECH_ERR_BAD_INPUT unless there is exactly one cycle. */
static srmech_status_t srmech_cwf_lk(srmech_dw_arena_t *ar,
                                     const uint32_t *eu, const uint32_t *ev,
                                     const double *gains, uint32_t n_edges,
                                     uint32_t n_nodes, int32_t *cp_out)
{
    assert(ar != NULL && cp_out != NULL);
    uint32_t e = (n_edges == 0u) ? 1u : n_edges;
    uint32_t *ocls = srmech_cwf_carve(ar, (size_t)e * sizeof(uint32_t));
    int32_t *opar = srmech_cwf_carve(ar, (size_t)e * sizeof(int32_t));
    uint32_t *ocu = srmech_cwf_carve(ar, (size_t)e * sizeof(uint32_t));
    uint32_t *ocv = srmech_cwf_carve(ar, (size_t)e * sizeof(uint32_t));
    double *ohol = srmech_cwf_carve(ar, (size_t)e * 4u * sizeof(double));
    size_t hb = srmech_quaternion_cycle_holonomy_arena_bytes(n_nodes, n_edges);
    void *hws = srmech_cwf_carve(ar, hb);
    if (ocls == NULL || opar == NULL || ocu == NULL || ocv == NULL ||
        ohol == NULL || hws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint32_t ncyc = 0;
    srmech_status_t st = srmech_quaternion_cycle_holonomy(
        n_nodes, n_edges, eu, ev, gains, ocls, opar, ocu, ocv, ohol, &ncyc,
        hws, hb);
    if (st != SRMECH_OK) { return st; }
    if (ncyc != 1u) { return SRMECH_ERR_BAD_INPUT; }
    *cp_out = opar[0];
    assert(*cp_out >= -1 && *cp_out <= 1);
    return SRMECH_OK;
}

size_t srmech_genome_cwf_consistency_mod2_arena_bytes(uint32_t n_nodes,
                                                      uint32_t n_edges,
                                                      uint32_t n_points)
{
    uint32_t e = (n_edges == 0u) ? 1u : n_edges;
    size_t holo = srmech_quaternion_cycle_holonomy_arena_bytes(n_nodes, n_edges);
    size_t obuf = (size_t)e * (3u * sizeof(uint32_t) + sizeof(int32_t)
                               + 4u * sizeof(double)) + 64u;
    size_t writhe = srmech_genome_discrete_writhe_arena_bytes(n_points);
    size_t head = holo + obuf + 64u;                 /* Lk phase footprint */
    size_t total = (head > writhe ? head : writhe) + 64u;
    assert(total > writhe);
    assert(total >= holo);
    return total;
}

srmech_status_t srmech_genome_cwf_consistency_mod2(
    const uint32_t *edges_u, const uint32_t *edges_v, const double *gains,
    uint32_t n_edges, uint32_t n_nodes, int32_t has_embedding,
    const int64_t *xn, const int64_t *xd, const int64_t *yn, const int64_t *yd,
    const int64_t *zn, const int64_t *zd, uint32_t n_points, int32_t closed,
    void *ws, size_t ws_len,
    int32_t *out_lk_mod2, int32_t *out_lk_center_parity, int32_t *out_tw_mod2,
    int32_t *out_wr_mod2, int32_t *out_consistent)
{
    assert(out_lk_mod2 != NULL && out_consistent != NULL);
    if (edges_u == NULL || edges_v == NULL || out_lk_mod2 == NULL ||
        out_lk_center_parity == NULL || out_tw_mod2 == NULL ||
        out_wr_mod2 == NULL || out_consistent == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws == NULL && ws_len != 0) { return SRMECH_ERR_NULL_ARG; }
    *out_lk_center_parity = 0;  *out_lk_mod2 = -1;  *out_tw_mod2 = 0;
    *out_wr_mod2 = -1;          *out_consistent = -1;
    srmech_dw_arena_t ar;
    ar.base = (unsigned char *)ws;  ar.off = 0;  ar.cap = ws_len;
    int32_t cp = 0;
    srmech_status_t st = srmech_cwf_lk(&ar, edges_u, edges_v, gains, n_edges,
                                       n_nodes, &cp);
    if (st != SRMECH_OK) { return st; }
    *out_lk_center_parity = cp;
    int32_t lk = (cp == 0) ? -1 : ((cp == -1) ? 1 : 0);
    *out_lk_mod2 = lk;
    int32_t tw = 0;
    if (gains != NULL) {
        for (uint32_t k = 0; k < n_edges; k++) {
            if (srmech_cwf_gain_sign(gains + (size_t)4u * k) == -1) { tw++; }
        }
    }
    int32_t tw2 = tw & 1;
    *out_tw_mod2 = tw2;
    if (has_embedding == 0) {
        return SRMECH_OK;                       /* wr / consistent stay -1 */
    }
    ar.off = 0;                                 /* Lk scratch done; reuse */
    size_t wb = srmech_genome_discrete_writhe_arena_bytes(n_points);
    void *wws = srmech_cwf_carve(&ar, wb);
    if (wws == NULL) { return SRMECH_ERR_OVERFLOW; }
    int64_t wr_num = 0, wr_den = 1;
    st = srmech_genome_discrete_writhe(xn, xd, yn, yd, zn, zd, n_points, closed,
                                       wws, wb, &wr_num, &wr_den);
    if (st != SRMECH_OK) { return st; }
    int32_t wr2 = (int32_t)(((wr_num % 2) + 2) % 2);
    *out_wr_mod2 = wr2;
    if (lk >= 0) {
        *out_consistent = (((tw2 + wr2) & 1) == lk) ? 1 : 0;
    }
    assert(*out_consistent >= -1 && *out_consistent <= 1);
    return SRMECH_OK;
}
