/*
 * srmech_factor_poly.c — EXACT integer-polynomial factorization (Zassenhaus):
 * the C peer of srmech.amsc.cascade.matrix_cascades.factor_integer_poly
 * (Qalg TAIL Batch 8). Factors an integer polynomial into its irreducible
 * factors over ℚ (Gauss's lemma: factoring over ℚ ≡ factoring over ℤ).
 *
 * The classical Zassenhaus stack, byte/structurally-identical to the pure
 * Python factor_integer_poly:
 *   1. content + primitive part, then Yun square-free decomposition over ℚ
 *      (srmech_poly_gcd chains) so each multiplicity is exact;
 *   2. per square-free primitive f (deg >= 1): choose a prime p ∤ lead with f
 *      square-free mod p; factor f mod p in 𝔽_p[x] (distinct-degree then
 *      Cantor–Zassenhaus equal-degree, over a DETERMINISTIC xorshift64 rng that
 *      reproduces the Python rng stream byte-for-byte); Hensel-lift the mod-p
 *      factors to mod p^k with p^k >= 2·B+1 (B = the Mignotte coefficient bound);
 *      recombine over increasing subset sizes (product mod p^k, symmetric
 *      integer reps, leading-coeff cofactor, exact ℤ trial-division) guarded by a
 *      subset-size cap;
 *   3. merge identical factors + sort by (len, coeffs).
 *
 * The mod-p arithmetic is plain u64 (p < 100000, so every product < 2^34); the
 * Hensel lift + recombination + Mignotte bound are exact srmech_bigint (NO
 * malloc, JPL Rule 3). Every working carrier is carved from the caller arena
 * `ws` (>= srmech_factor_integer_poly_ws_bound); the ℚ[x] Yun composes the
 * exact-ℚ srmech_poly_* kernels over their own sub-arena. Any overflow returns
 * SRMECH_ERR_OVERFLOW (never a silent wrap) and the Python falls back to its
 * byte-identical pure path (the parity oracle) — so the standalone-complete
 * honor holds.
 *
 * The srmech factorization is UNIQUE (the irreducible factors of ℤ[x] are unique
 * up to order + sign), so any correct Zassenhaus yields the same factors; the
 * final sort fixes the order identically on both paths. The rng match makes the
 * WHOLE internal computation identical too (defensive byte-identity).
 *
 * Class L (the algebraic content) ∘ Class J (the prime-field reduction + Hensel
 * lift) ∘ Class I (the 𝔽_p modular arithmetic) ∘ Class K (the symmetric-rep sign
 * pin-slots — never an ALU abs).
 *
 * Additive symbols -> SRMECH_ABI_VERSION unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are degree / factor counts
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Native degree cap: an exact-symbolic factorization is small in practice; the
 * Python wrapper caps the native path below this and falls to the byte-identical
 * pure path above it (correct, just larger-arena). */
#define FAC_MAX_DEG 128

/* The recombination subset-size cap (mirrors the pure subset_cap=18). */
#define FAC_SUBSET_CAP 18

/* The Python xorshift64 rng seed constant (byte-identity: same stream). */
#define FAC_RNG_SEED UINT64_C(0x2545F4914F6CDD1D)

/* ---- caller-arena bump allocator ---------------------------------- */

typedef struct fac_arena {
    unsigned char *base;
    size_t off;
    size_t cap;   /* total bytes */
} fac_arena_t;

/* Bump `nbytes` at `align` from the arena. NULL on exhaustion (never past cap). */
static void *fac_take(fac_arena_t *a, size_t nbytes, size_t align)
{
    size_t start;
    assert(a != NULL);
    assert(align != 0u && (align & (align - 1u)) == 0u);
    start = (a->off + (align - 1u)) & ~(align - 1u);
    if (start > a->cap || nbytes > a->cap - start) {
        return NULL;
    }
    a->off = start + nbytes;
    return a->base + start;
}

/* Carve `count` srmech_bigint headers + `cap`-limb runs (each initialised to
 * the integer 0). Returns the header array, or NULL on exhaustion. */
static srmech_bigint_t *fac_carve_bigints(fac_arena_t *a, size_t count,
                                          uint32_t cap)
{
    srmech_bigint_t *arr;
    size_t k;
    assert(a != NULL);
    assert(cap > 0u && count > 0u);
    arr = (srmech_bigint_t *)fac_take(a, count * sizeof(srmech_bigint_t),
                                      sizeof(void *));
    if (arr == NULL) {
        return NULL;
    }
    for (k = 0u; k < count; k++) {
        uint32_t *limbs = (uint32_t *)fac_take(a, (size_t)cap * sizeof(uint32_t),
                                               sizeof(uint32_t));
        if (limbs == NULL) {
            return NULL;
        }
        arr[k].limbs = limbs;
        arr[k].cap = cap;
        arr[k].n = 0u;
        arr[k].sign = 0;
    }
    return arr;
}

/* Carve a `count`-slot uint64 array (8-aligned), or NULL on exhaustion. */
static uint64_t *fac_carve_u64(fac_arena_t *a, size_t count)
{
    uint64_t *p;
    assert(a != NULL && count > 0u);
    p = (uint64_t *)fac_take(a, count * sizeof(uint64_t), sizeof(uint64_t));
    assert(p != NULL || a->off <= a->cap);
    return p;
}

/* Carve a `count`-slot int array, or NULL on exhaustion. */
static int *fac_carve_int(fac_arena_t *a, size_t count)
{
    int *p;
    assert(a != NULL && count > 0u);
    p = (int *)fac_take(a, count * sizeof(int), sizeof(int));
    assert(p != NULL || a->off <= a->cap);
    return p;
}

/* ================================================================== *
 *  𝔽_p[x] over u64 (p < 100000, so every scalar product < 2^34)
 * ================================================================== */

/* r = (a * b) mod q (a, b < q < 2^17 -> product < 2^34, no overflow). */
static uint64_t fp_mulmod_s(uint64_t a, uint64_t b, uint64_t q)
{
    assert(q > 0u);
    assert(a < q && b < q);
    return (a * b) % q;
}

/* r = base^e mod q (scalar Fermat-style square-and-multiply). */
static uint64_t fp_powmod_s(uint64_t base, uint64_t e, uint64_t q)
{
    uint64_t r = 1u % q;
    uint64_t b = base % q;
    assert(q > 0u);
    while (e != 0u) {
        if ((e & 1u) != 0u) {
            r = fp_mulmod_s(r, b, q);
        }
        e >>= 1;
        if (e != 0u) {
            b = fp_mulmod_s(b, b, q);
        }
    }
    assert(r < q);
    return r;
}

/* Trim trailing (high-degree) zero coefficients; length stays >= 1. */
static int fp_trim(const uint64_t *c, int len)
{
    assert(c != NULL);
    assert(len >= 1);
    while (len > 1 && c[len - 1] == 0u) {
        len--;
    }
    return len;
}

/* out = a - b (coefficientwise mod q), trimmed. Returns out length. */
static int fp_sub(uint64_t *out, const uint64_t *a, int la,
                  const uint64_t *b, int lb, uint64_t q)
{
    int n = (la > lb) ? la : lb;
    int i;
    assert(out != NULL && q > 0u);
    assert(la >= 1 && lb >= 1);
    for (i = 0; i < n; i++) {
        uint64_t av = (i < la) ? a[i] : 0u;
        uint64_t bv = (i < lb) ? b[i] : 0u;
        out[i] = (av + q - bv) % q;
    }
    return fp_trim(out, n);
}

/* out = derivative of p over 𝔽_p, trimmed. Returns out length. */
static int fp_deriv(uint64_t *out, const uint64_t *p, int lp, uint64_t q)
{
    int i;
    assert(out != NULL);
    assert(p != NULL && q > 0u);
    if (lp <= 1) {
        out[0] = 0u;
        return 1;
    }
    for (i = 1; i < lp; i++) {
        out[i - 1] = fp_mulmod_s(p[i], (uint64_t)i % q, q);
    }
    return fp_trim(out, lp - 1);
}

/* out = a * b (convolution mod q), trimmed. out holds la+lb-1 slots. */
static int fp_mul(uint64_t *out, const uint64_t *a, int la,
                  const uint64_t *b, int lb, uint64_t q)
{
    int n = la + lb - 1;
    int i, j;
    assert(out != NULL && q > 0u);
    assert(la >= 1 && lb >= 1);
    for (i = 0; i < n; i++) {
        out[i] = 0u;
    }
    for (i = 0; i < la; i++) {
        if (a[i] == 0u) {
            continue;
        }
        for (j = 0; j < lb; j++) {
            uint64_t t = fp_mulmod_s(a[i], b[j], q);
            out[i + j] = (out[i + j] + t) % q;
        }
    }
    return fp_trim(out, n);
}

/* out = a (make monic: divide by leading coeff's inverse), trimmed. */
static int fp_make_monic(uint64_t *out, const uint64_t *a, int la, uint64_t q)
{
    int len = fp_trim(a, la);
    uint64_t inv;
    int i;
    assert(out != NULL);
    assert(q > 0u);
    if (len == 1 && a[0] == 0u) {
        out[0] = 0u;
        return 1;
    }
    inv = fp_powmod_s(a[len - 1] % q, q - 2u, q);
    for (i = 0; i < len; i++) {
        out[i] = fp_mulmod_s(a[i] % q, inv, q);
    }
    return len;
}

/* (quo, rem) of a / b over 𝔽_p. rem width = la; quo width = max(la-lb+1,1).
 * Returns via *qlen / *rlen. b must be nonzero. */
static void fp_divmod(uint64_t *quo, int *qlen, uint64_t *rem, int *rlen,
                      const uint64_t *a, int la, const uint64_t *b, int lb,
                      uint64_t q)
{
    uint64_t inv;
    int rl = la, i, d;
    assert(quo != NULL && rem != NULL && q > 0u);
    assert(lb >= 1 && b[lb - 1] != 0u);
    inv = fp_powmod_s(b[lb - 1] % q, q - 2u, q);
    for (i = 0; i < ((la - lb + 1 > 1) ? la - lb + 1 : 1); i++) {
        quo[i] = 0u;
    }
    for (i = 0; i < la; i++) {
        rem[i] = a[i] % q;
    }
    rl = fp_trim(rem, rl);
    while (rl >= lb && !(rl == 1 && rem[0] == 0u)) {
        uint64_t c = fp_mulmod_s(rem[rl - 1], inv, q);
        d = rl - lb;
        quo[d] = c;
        for (i = 0; i < lb; i++) {
            rem[d + i] = (rem[d + i] + q - fp_mulmod_s(c, b[i], q)) % q;
        }
        rl = fp_trim(rem, rl);
    }
    *qlen = fp_trim(quo, (la - lb + 1 > 1) ? la - lb + 1 : 1);
    *rlen = rl;
}

/* out = monic gcd(a, b) over 𝔽_p, trimmed. Scratch qs/rs each >= max(la,lb). */
static int fp_gcd(uint64_t *out, const uint64_t *a, int la,
                  const uint64_t *b, int lb, uint64_t q,
                  uint64_t *ua, uint64_t *ub, uint64_t *qs, uint64_t *rs)
{
    int lua = fp_trim(a, la), lub = fp_trim(b, lb), i, ql, rl;
    assert(out != NULL);
    assert(q > 0u);
    for (i = 0; i < lua; i++) { ua[i] = a[i] % q; }
    for (i = 0; i < lub; i++) { ub[i] = b[i] % q; }
    while (!(lub == 1 && ub[0] == 0u)) {
        fp_divmod(qs, &ql, rs, &rl, ua, lua, ub, lub, q);
        for (i = 0; i < lub; i++) { ua[i] = ub[i]; }
        lua = lub;
        for (i = 0; i < rl; i++) { ub[i] = rs[i]; }
        lub = rl;
    }
    return fp_make_monic(out, ua, lua, q);
}

/* ================================================================== *
 *  Context + srmech_bigint scalar helpers (exact ℤ; caller-arena `bws`)
 * ================================================================== */

#define FAC_BT_N 16   /* general bignum temporaries bt[0..15] */

typedef struct fac_ctx {
    uint64_t q;          /* the reduction prime p                        */
    int deg;             /* the square-free primitive input degree       */
    uint32_t cap;        /* per-coefficient limb capacity                */
    int cw;              /* coeff width of a stored factor = deg + 1      */
    int fw;              /* 𝔽_p scratch width = 2*deg + 2                */
    fac_arena_t ar;      /* the bump arena                               */
    void  *bws;          /* srmech_bigint op scratch                     */
    size_t bws_len;
    /* ---- 𝔽_p scratch (u64) ---- */
    uint64_t *g0, *g1, *g2, *g3;    /* fp_gcd scratch                    */
    uint64_t *mr0, *mr1, *mr2;         /* mulreduce scratch                 */
    uint64_t *pm_r, *pm_b, *pm_t;   /* polypowmod scratch                */
    uint64_t *dd_fs, *dd_xq, *dd_x, *dd_sb, *dd_g, *dd_qt, *dd_t2; /* distinct */
    uint64_t *ed_g, *ed_r, *ed_h, *ed_gg, *ed_ot, *ed_qt, *ed_mn; /* equal   */
    uint64_t *hp;        /* Hensel-phase 𝔽_p pool (FAC_HP_N * fw)        */
    uint64_t *st_flat; int *st_len; int st_top;   /* equal-degree stack   */
    uint64_t *db_flat; int *db_deg; int *db_len; int db_n; /* distinct buckets */
    uint64_t *mp_flat; int *mp_len; int mp_n;     /* mod-p factor list    */
    /* ---- bignum scratch (srmech_bigint) ---- */
    srmech_bigint_t *bt;      /* general scalar temporaries bt[0..15]      */
    srmech_bigint_t *mod;     /* the Hensel modulus p^k                    */
    srmech_bigint_t *modhalf; /* mod >> 1 (the symmetric-rep pivot)        */
    srmech_bigint_t *m2;      /* the doubled modulus modn^2 (Hensel step)  */
    srmech_bigint_t *modn;    /* the running Hensel modulus (lift loop)     */
    srmech_bigint_t *pool;    /* FAC_BP_N poly buffers, each cw wide       */
    srmech_bigint_t *ip;      /* the input integer poly (cw)               */
    srmech_bigint_t *lifted;  /* the lifted mod-m factors (nlist*cw)       */
    int *lif_len;             /* per-lifted-factor length                  */
    srmech_bigint_t *irr;     /* the irreducible ℤ factors (nlist*cw)      */
    int *irr_len; int irr_n;
    int *rem_idx; int rem_n;  /* recombination remaining indices           */
    int *combo;               /* recombination position combo (size slots) */
} fac_ctx_t;

#define FAC_BP_N 30   /* bignum poly working buffers */
#define FAC_HP_N 14   /* Hensel-phase 𝔽_p working buffers */

/* Poly buffer k (0-based) in the bignum working pool. */
static srmech_bigint_t *bp_buf(fac_ctx_t *c, int k)
{
    assert(c != NULL);
    assert(k >= 0 && k < FAC_BP_N);
    return c->pool + (size_t)k * (size_t)c->cw;
}

/* 𝔽_p Hensel-phase scratch buffer k (0-based), each fw-wide. */
static uint64_t *hp_buf(fac_ctx_t *c, int k)
{
    assert(c != NULL);
    assert(k >= 0 && k < FAC_HP_N);
    return c->hp + (size_t)k * (size_t)c->fw;
}

/* out = a (mod m), floor-reduced into [0, m). m > 0. Calls the fixed
 * srmech_bigint_divmod directly with q = NULL (the divmod now carves its
 * own throwaway quotient off the arena — the old cap-0 NULL-sink bug that
 * forced a caller-owned qsink workaround here is FIXED at the root). */
static srmech_status_t fbi_mod(fac_ctx_t *c, srmech_bigint_t *out,
                               const srmech_bigint_t *a, const srmech_bigint_t *m)
{
    assert(c != NULL && out != NULL);
    assert(m != NULL && m->sign > 0);
    return srmech_bigint_divmod(NULL, out, a, m, c->bws, c->bws_len);
}

/* out = a * b ; out = a + b ; out = a - b ; out = a (exact ℤ). */
static srmech_status_t fbi_mul(srmech_bigint_t *out, const srmech_bigint_t *a,
                               const srmech_bigint_t *b)
{
    assert(out != NULL);
    assert(a != NULL && b != NULL);
    return srmech_bigint_mul(out, a, b);
}
static srmech_status_t fbi_add(srmech_bigint_t *out, const srmech_bigint_t *a,
                               const srmech_bigint_t *b)
{
    assert(out != NULL);
    assert(a != NULL && b != NULL);
    return srmech_bigint_add(out, a, b);
}
static srmech_status_t fbi_sub(srmech_bigint_t *out, const srmech_bigint_t *a,
                               const srmech_bigint_t *b)
{
    assert(out != NULL);
    assert(a != NULL && b != NULL);
    return srmech_bigint_sub(out, a, b);
}
static srmech_status_t fbi_copy(srmech_bigint_t *out, const srmech_bigint_t *a)
{
    assert(out != NULL);
    assert(a != NULL);
    return srmech_bigint_copy(out, a);
}
static srmech_status_t fbi_seti(srmech_bigint_t *out, int64_t v)
{
    assert(out != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    return srmech_bigint_set_i64(out, v);
}

/* out = a^-1 mod m (extended Euclid; gcd(a,m) must be 1). Result in [0, m).
 * Uses ctx temporaries bt[8..15] as the Euclid registers. */
static srmech_status_t fbi_modinv(fac_ctx_t *c, srmech_bigint_t *out,
                                  const srmech_bigint_t *a,
                                  const srmech_bigint_t *m)
{
    srmech_bigint_t *r0 = &c->bt[8], *r1 = &c->bt[9], *s0 = &c->bt[10];
    srmech_bigint_t *s1 = &c->bt[11], *qq = &c->bt[12], *tp = &c->bt[13];
    srmech_bigint_t *tp2 = &c->bt[14];
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(a != NULL && m != NULL && m->sign > 0);
    st = fbi_mod(c, r0, a, m);       if (st != SRMECH_OK) { return st; }
    st = fbi_copy(r1, m);            if (st != SRMECH_OK) { return st; }
    st = fbi_seti(s0, 1);            if (st != SRMECH_OK) { return st; }
    st = fbi_seti(s1, 0);            if (st != SRMECH_OK) { return st; }
    while (!srmech_bigint_is_zero(r1)) {
        st = srmech_bigint_divmod(qq, tp, r0, r1, c->bws, c->bws_len);
        if (st != SRMECH_OK) { return st; }
        st = fbi_copy(r0, r1);       if (st != SRMECH_OK) { return st; }
        st = fbi_copy(r1, tp);       if (st != SRMECH_OK) { return st; }
        st = fbi_mul(tp2, qq, s1);   if (st != SRMECH_OK) { return st; }
        st = fbi_sub(tp, s0, tp2);   if (st != SRMECH_OK) { return st; }
        st = fbi_copy(s0, s1);       if (st != SRMECH_OK) { return st; }
        st = fbi_copy(s1, tp);       if (st != SRMECH_OK) { return st; }
    }
    return fbi_mod(c, out, s0, m);   /* s0 = a^-1 (mod m), normalized to [0,m) */
}

/* ================================================================== *
 *  𝔽_p poly powmod + the Cantor–Zassenhaus rng
 * ================================================================== */

/* out = (a * b) mod (mod) over 𝔽_p, trimmed. Returns out length. Scratch:
 * c->mr0/mr1/mr2. out must not alias a, b, or mod. */
static int fp_mulreduce(fac_ctx_t *c, uint64_t *out, const uint64_t *a, int la,
                        const uint64_t *b, int lb, const uint64_t *mod, int lm)
{
    int pl, ql, rl, i;
    assert(c != NULL && out != NULL);
    assert(lm >= 1 && mod[lm - 1] != 0u);
    pl = fp_mul(c->mr0, a, la, b, lb, c->q);
    if (pl < lm) {
        for (i = 0; i < pl; i++) { out[i] = c->mr0[i]; }
        return pl;
    }
    fp_divmod(c->mr1, &ql, c->mr2, &rl, c->mr0, pl, mod, lm, c->q);
    for (i = 0; i < rl; i++) { out[i] = c->mr2[i]; }
    return rl;
}

/* out = base^e mod (mod), e a u64 exponent. Returns out length. out != base. */
static int fp_polypow_u64(fac_ctx_t *c, uint64_t *out, const uint64_t *base,
                          int lb, uint64_t e, const uint64_t *mod, int lm)
{
    int lr = 1, lbb = 0, i, ql, rl;
    assert(c != NULL);
    assert(out != NULL && lm >= 1);
    c->pm_r[0] = 1u % c->q;
    fp_divmod(c->mr1, &ql, c->mr2, &rl, base, lb, mod, lm, c->q);
    for (i = 0; i < rl; i++) { c->pm_b[i] = c->mr2[i]; }
    lbb = rl;
    while (e != 0u) {
        if ((e & 1u) != 0u) {
            lr = fp_mulreduce(c, c->pm_t, c->pm_r, lr, c->pm_b, lbb, mod, lm);
            for (i = 0; i < lr; i++) { c->pm_r[i] = c->pm_t[i]; }
        }
        e >>= 1;
        if (e != 0u) {
            lbb = fp_mulreduce(c, c->pm_t, c->pm_b, lbb, c->pm_b, lbb, mod, lm);
            for (i = 0; i < lbb; i++) { c->pm_b[i] = c->pm_t[i]; }
        }
    }
    for (i = 0; i < lr; i++) { out[i] = c->pm_r[i]; }
    return lr;
}

/* out = base^e mod (mod), e the srmech_bigint exponent (bits LSB->MSB).
 * Returns out length. out != base. */
static int fp_polypow_big(fac_ctx_t *c, uint64_t *out, const uint64_t *base,
                          int lb, const srmech_bigint_t *e,
                          const uint64_t *mod, int lm)
{
    int lr = 1, lbb = 0, i, ql, rl;
    uint32_t topbit = 0u, bit, hi;
    uint64_t nbits;
    assert(c != NULL);
    assert(out != NULL && lm >= 1);
    if (e->sign == 0) { out[0] = 1u % c->q; return 1; }
    hi = e->limbs[e->n - 1u];
    while (hi != 0u) { hi >>= 1; topbit++; }
    nbits = (uint64_t)(e->n - 1u) * 32u + topbit;
    c->pm_r[0] = 1u % c->q;
    fp_divmod(c->mr1, &ql, c->mr2, &rl, base, lb, mod, lm, c->q);
    for (i = 0; i < rl; i++) { c->pm_b[i] = c->mr2[i]; }
    lbb = rl;
    for (bit = 0u; (uint64_t)bit < nbits; bit++) {
        if (((e->limbs[bit >> 5] >> (bit & 31u)) & 1u) != 0u) {
            lr = fp_mulreduce(c, c->pm_t, c->pm_r, lr, c->pm_b, lbb, mod, lm);
            for (i = 0; i < lr; i++) { c->pm_r[i] = c->pm_t[i]; }
        }
        if ((uint64_t)bit + 1u < nbits) {
            lbb = fp_mulreduce(c, c->pm_t, c->pm_b, lbb, c->pm_b, lbb, mod, lm);
            for (i = 0; i < lbb; i++) { c->pm_b[i] = c->pm_t[i]; }
        }
    }
    for (i = 0; i < lr; i++) { out[i] = c->pm_r[i]; }
    return lr;
}

/* The Python xorshift64 rng: x^=(x<<13); x^=(x>>7); x^=(x<<17); return x % q.
 * uint64 wraparound reproduces the Python `& 0xFFFF...FFFF` masks exactly. */
static uint64_t fac_rng_next(uint64_t *state, uint64_t q)
{
    uint64_t x = *state;
    assert(state != NULL);
    assert(q > 0u);
    x ^= (x << 13);
    x ^= (x >> 7);
    x ^= (x << 17);
    *state = x;
    return x % q;
}

/* Two trimmed monic 𝔽_p polys equal? (same length + coefficients.) */
static int fp_equal(const uint64_t *a, int la, const uint64_t *b, int lb)
{
    int i;
    assert(a != NULL);
    assert(b != NULL);
    if (la != lb) { return 0; }
    for (i = 0; i < la; i++) { if (a[i] != b[i]) { return 0; } }
    return 1;
}

/* Append a trimmed monic 𝔽_p poly (make_monic first) to the mod-p factor list. */
static void fp_mp_append(fac_ctx_t *c, const uint64_t *g, int lg)
{
    uint64_t *dst;
    int i, lm;
    assert(c != NULL);
    assert(c->mp_n < c->deg + 1);
    dst = c->mp_flat + (size_t)c->mp_n * (size_t)c->cw;
    lm = fp_make_monic(dst, g, lg, c->q);
    for (i = lm; i < c->cw; i++) { dst[i] = 0u; }
    c->mp_len[c->mp_n] = lm;
    c->mp_n++;
}

/* Push / pop the equal-degree working stack (stores monic 𝔽_p polys). */
static void fp_st_push(fac_ctx_t *c, const uint64_t *g, int lg)
{
    uint64_t *dst;
    int i;
    assert(c != NULL);
    assert(c->st_top < c->deg + 1);
    dst = c->st_flat + (size_t)c->st_top * (size_t)c->cw;
    for (i = 0; i < lg; i++) { dst[i] = g[i]; }
    c->st_len[c->st_top] = lg;
    c->st_top++;
}

/* Distinct-degree factorization of a SQUARE-FREE monic f over 𝔽_p:
 * fills db_flat/db_deg/db_n with (g_d, d) — g_d the product of the monic
 * irreducibles of degree exactly d (von zur Gathen–Gerhard §14.2). */
static void fp_distinct_degree(fac_ctx_t *c, const uint64_t *f, int lf)
{
    int lfs, lxq, lsb, lg, ql, rl, d = 1;
    uint64_t *bd;
    int i;
    assert(c != NULL);
    assert(f != NULL);
    lfs = fp_make_monic(c->dd_fs, f, lf, c->q);
    c->dd_x[0] = 0u; c->dd_x[1] = 1u % c->q;
    c->dd_xq[0] = 0u; c->dd_xq[1] = 1u % c->q; lxq = 2;
    c->db_n = 0;
    while (lfs - 1 >= 2 * d) {
        lxq = fp_polypow_u64(c, c->dd_t2, c->dd_xq, lxq, c->q, c->dd_fs, lfs);
        for (i = 0; i < lxq; i++) { c->dd_xq[i] = c->dd_t2[i]; }
        lsb = fp_sub(c->dd_sb, c->dd_xq, lxq, c->dd_x, 2, c->q);
        lg = fp_gcd(c->dd_g, c->dd_sb, lsb, c->dd_fs, lfs, c->q,
                    c->g0, c->g1, c->g2, c->g3);
        if (!(lg == 1 && c->dd_g[0] == 0u) && !(lg == 1 && c->dd_g[0] == 1u)) {
            bd = c->db_flat + (size_t)c->db_n * (size_t)c->cw;
            lg = fp_make_monic(bd, c->dd_g, lg, c->q);
            c->db_deg[c->db_n] = d; c->db_len[c->db_n] = lg; c->db_n++;
            fp_divmod(c->dd_qt, &ql, c->dd_t2, &rl, c->dd_fs, lfs, bd, lg, c->q);
            lfs = fp_make_monic(c->dd_fs, c->dd_qt, ql, c->q);
        }
        d++;
    }
    if (!(lfs == 1 && c->dd_fs[0] == 1u) && lfs > 1) {
        bd = c->db_flat + (size_t)c->db_n * (size_t)c->cw;
        for (i = 0; i < lfs; i++) { bd[i] = c->dd_fs[i]; }
        c->db_deg[c->db_n] = lfs - 1; c->db_len[c->db_n] = lfs; c->db_n++;
    }
}

/* exp = (q^d - 1) / 2 into `out` (the equal-degree Cantor–Zassenhaus power). */
static srmech_status_t fp_ed_exp(fac_ctx_t *c, srmech_bigint_t *out, int d)
{
    srmech_bigint_t *qd = &c->bt[1], *qb = &c->bt[2], *one = &c->bt[3];
    srmech_status_t st;
    assert(c != NULL);
    assert(out != NULL && d >= 1);
    st = fbi_seti(qb, (int64_t)c->q);        if (st != SRMECH_OK) { return st; }
    st = fbi_seti(one, 1);                   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_pow_u32(qd, qb, (uint32_t)d, c->bws, c->bws_len);
    if (st != SRMECH_OK) { return st; }
    st = fbi_sub(out, qd, one);              if (st != SRMECH_OK) { return st; }
    return srmech_bigint_shr_bits(out, out, 1u);   /* (q^d - 1) >> 1 */
}

/* Cantor–Zassenhaus equal-degree split of the product of degree-d monic
 * irreducibles in f (over 𝔽_p, p odd), appending each irreducible to the mod-p
 * factor list. Deterministic-seeded rng (byte-identity). */
static srmech_status_t fp_equal_degree(fac_ctx_t *c, const uint64_t *f, int lf,
                                       int d, uint64_t *state)
{
    srmech_bigint_t *exp = &c->bt[0];
    int lg, lr, lh, lgg, ql, rl, lot, i;
    srmech_status_t st;
    assert(c != NULL);
    assert(f != NULL && d >= 1);
    lg = fp_make_monic(c->ed_g, f, lf, c->q);
    if (lg - 1 == d) { fp_mp_append(c, c->ed_g, lg); return SRMECH_OK; }
    st = fp_ed_exp(c, exp, d);               if (st != SRMECH_OK) { return st; }
    c->st_top = 0;
    fp_st_push(c, c->ed_g, lg);
    while (c->st_top > 0) {
        c->st_top--;
        lg = c->st_len[c->st_top];
        for (i = 0; i < lg; i++) {
            c->ed_g[i] = c->st_flat[(size_t)c->st_top * (size_t)c->cw + (size_t)i];
        }
        if (lg - 1 == d) { fp_mp_append(c, c->ed_g, lg); continue; }
        do {
            for (i = 0; i < lg - 1; i++) { c->ed_r[i] = fac_rng_next(state, c->q); }
            lr = fp_trim(c->ed_r, lg - 1);
        } while (lr <= 1);
        lh = fp_polypow_big(c, c->ed_h, c->ed_r, lr, exp, c->ed_g, lg);
        c->ed_mn[0] = 1u % c->q;
        lh = fp_sub(c->ed_h, c->ed_h, lh, c->ed_mn, 1, c->q);
        lgg = fp_gcd(c->ed_gg, c->ed_h, lh, c->ed_g, lg, c->q,
                     c->g0, c->g1, c->g2, c->g3);
        if ((lgg == 1 && c->ed_gg[0] == 1u) || fp_equal(c->ed_gg, lgg, c->ed_g, lg)) {
            fp_st_push(c, c->ed_g, lg);
            continue;
        }
        lgg = fp_make_monic(c->ed_gg, c->ed_gg, lgg, c->q);
        fp_divmod(c->ed_qt, &ql, c->dd_t2, &rl, c->ed_g, lg, c->ed_gg, lgg, c->q);
        lot = fp_make_monic(c->ed_ot, c->ed_qt, ql, c->q);
        fp_st_push(c, c->ed_gg, lgg);
        fp_st_push(c, c->ed_ot, lot);
    }
    return SRMECH_OK;
}

/* Full 𝔽_p factorization of a SQUARE-FREE monic f into monic irreducibles. */
static srmech_status_t fp_factor_mod_p(fac_ctx_t *c, const uint64_t *f, int lf,
                                       uint64_t *state)
{
    int b, lgd;
    const uint64_t *gd;
    srmech_status_t st;
    assert(c != NULL);
    assert(f != NULL);
    fp_distinct_degree(c, f, lf);
    c->mp_n = 0;
    for (b = 0; b < c->db_n; b++) {
        gd = c->db_flat + (size_t)b * (size_t)c->cw;
        lgd = c->db_len[b];
        if (lgd - 1 == c->db_deg[b]) {
            fp_mp_append(c, gd, lgd);
        } else {
            st = fp_equal_degree(c, gd, lgd, c->db_deg[b], state);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* ================================================================== *
 *  bignum poly arithmetic mod m (the Hensel + recombination substrate)
 * ================================================================== */

/* Drop high-degree zero coeffs (len stays >= 1). */
static int bp_trim(const srmech_bigint_t *p, int len)
{
    assert(p != NULL);
    assert(len >= 1);
    while (len > 1 && srmech_bigint_is_zero(&p[len - 1])) { len--; }
    return len;
}

/* dst[0..len) = src[0..len) (deep copy). */
static srmech_status_t bp_copy(srmech_bigint_t *dst, const srmech_bigint_t *src,
                               int len)
{
    int i;
    srmech_status_t st;
    assert(dst != NULL);
    assert(src != NULL && len >= 0);
    for (i = 0; i < len; i++) {
        st = fbi_copy(&dst[i], &src[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* p[0..len) <- p[0..len) mod m (each coeff floor-reduced into [0, m)). */
static srmech_status_t bp_reduce(fac_ctx_t *c, srmech_bigint_t *p, int len,
                                 const srmech_bigint_t *m)
{
    int i;
    srmech_status_t st;
    assert(c != NULL);
    assert(p != NULL);
    for (i = 0; i < len; i++) {
        st = fbi_mod(c, &c->bt[6], &p[i], m);
        if (st != SRMECH_OK) { return st; }
        st = fbi_copy(&p[i], &c->bt[6]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out = a + b mod m, trimmed. out distinct from a, b. */
static srmech_status_t bp_addmod(fac_ctx_t *c, srmech_bigint_t *out, int *ol,
                                 const srmech_bigint_t *a, int la,
                                 const srmech_bigint_t *b, int lb,
                                 const srmech_bigint_t *m)
{
    int n = (la > lb) ? la : lb, i;
    srmech_status_t st;
    assert(c != NULL);
    assert(out != NULL && ol != NULL);
    for (i = 0; i < n; i++) {
        if (i < la && i < lb) {
            st = fbi_add(&c->bt[7], &a[i], &b[i]); if (st != SRMECH_OK) { return st; }
            st = fbi_mod(c, &out[i], &c->bt[7], m);
        } else if (i < la) {
            st = fbi_mod(c, &out[i], &a[i], m);
        } else {
            st = fbi_mod(c, &out[i], &b[i], m);
        }
        if (st != SRMECH_OK) { return st; }
    }
    *ol = bp_trim(out, n);
    return SRMECH_OK;
}

/* out = a - b mod m, trimmed. out distinct from a, b. */
static srmech_status_t bp_submod(fac_ctx_t *c, srmech_bigint_t *out, int *ol,
                                 const srmech_bigint_t *a, int la,
                                 const srmech_bigint_t *b, int lb,
                                 const srmech_bigint_t *m)
{
    int n = (la > lb) ? la : lb, i;
    srmech_status_t st;
    assert(c != NULL);
    assert(out != NULL && ol != NULL);
    for (i = 0; i < n; i++) {
        if (i < la && i < lb) {
            st = fbi_sub(&c->bt[7], &a[i], &b[i]); if (st != SRMECH_OK) { return st; }
            st = fbi_mod(c, &out[i], &c->bt[7], m);
        } else if (i < la) {
            st = fbi_mod(c, &out[i], &a[i], m);
        } else {
            st = fbi_seti(&c->bt[6], 0);      if (st != SRMECH_OK) { return st; }
            st = fbi_sub(&c->bt[7], &c->bt[6], &b[i]); if (st != SRMECH_OK) { return st; }
            st = fbi_mod(c, &out[i], &c->bt[7], m);
        }
        if (st != SRMECH_OK) { return st; }
    }
    *ol = bp_trim(out, n);
    return SRMECH_OK;
}

/* out = a * b mod m (convolution), trimmed. out distinct from a, b. */
static srmech_status_t bp_mulmod(fac_ctx_t *c, srmech_bigint_t *out, int *ol,
                                 const srmech_bigint_t *a, int la,
                                 const srmech_bigint_t *b, int lb,
                                 const srmech_bigint_t *m)
{
    int n = la + lb - 1, k, i, lo, hi;
    srmech_status_t st;
    assert(c != NULL);
    assert(out != NULL && ol != NULL && n >= 1);
    for (k = 0; k < n; k++) {
        st = fbi_seti(&c->bt[0], 0);       if (st != SRMECH_OK) { return st; }
        lo = (k - (lb - 1) > 0) ? k - (lb - 1) : 0;
        hi = (k < la - 1) ? k : la - 1;
        for (i = lo; i <= hi; i++) {
            st = fbi_mul(&c->bt[1], &a[i], &b[k - i]); if (st != SRMECH_OK) { return st; }
            st = fbi_add(&c->bt[2], &c->bt[0], &c->bt[1]); if (st != SRMECH_OK) { return st; }
            st = fbi_copy(&c->bt[0], &c->bt[2]); if (st != SRMECH_OK) { return st; }
        }
        st = fbi_mod(c, &out[k], &c->bt[0], m); if (st != SRMECH_OK) { return st; }
    }
    *ol = bp_trim(out, n);
    return SRMECH_OK;
}

/* (quo, rem) of a / b mod m, b MONIC mod m (b[lb-1] == 1 so no inverse needed).
 * quo/rem distinct from a, b. */
static srmech_status_t bp_divmod_monic(fac_ctx_t *c, srmech_bigint_t *quo,
                                       int *ql, srmech_bigint_t *rem, int *rl,
                                       const srmech_bigint_t *a, int la,
                                       const srmech_bigint_t *b, int lb,
                                       const srmech_bigint_t *m)
{
    int qn = (la - lb + 1 > 1) ? la - lb + 1 : 1, i, d, r = la;
    srmech_status_t st;
    assert(c != NULL);
    assert(quo != NULL && rem != NULL && lb >= 1);
    for (i = 0; i < qn; i++) { st = fbi_seti(&quo[i], 0); if (st != SRMECH_OK) { return st; } }
    st = bp_copy(rem, a, la); if (st != SRMECH_OK) { return st; }
    r = bp_trim(rem, r);
    while (r >= lb && !(r == 1 && srmech_bigint_is_zero(&rem[0]))) {
        d = r - lb;
        st = fbi_copy(&c->bt[3], &rem[r - 1]); if (st != SRMECH_OK) { return st; }
        st = fbi_copy(&quo[d], &c->bt[3]);     if (st != SRMECH_OK) { return st; }
        for (i = 0; i < lb; i++) {
            st = fbi_mul(&c->bt[4], &c->bt[3], &b[i]); if (st != SRMECH_OK) { return st; }
            st = fbi_sub(&c->bt[5], &rem[d + i], &c->bt[4]); if (st != SRMECH_OK) { return st; }
            st = fbi_mod(c, &rem[d + i], &c->bt[5], m); if (st != SRMECH_OK) { return st; }
        }
        r = bp_trim(rem, r);
    }
    *ql = bp_trim(quo, qn);
    *rl = r;
    return SRMECH_OK;
}

/* out[0..la) = the 𝔽_p poly a as srmech_bigint coeffs (each in [0, p)). */
static srmech_status_t u64_to_bp(srmech_bigint_t *out, const uint64_t *a, int la)
{
    int i;
    srmech_status_t st;
    assert(out != NULL);
    assert(a != NULL && la >= 1);
    for (i = 0; i < la; i++) {
        st = fbi_seti(&out[i], (int64_t)a[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* a mod d for a small odd prime d (Horner over the limbs, sign-magnitude). */
static uint64_t bignum_mod_u64(const srmech_bigint_t *a, uint64_t d)
{
    uint64_t r = 0u;
    uint32_t k = a->n;
    assert(a != NULL);
    assert(d > 0u);
    while (k > 0u) {
        k--;
        r = ((r << 32) | (uint64_t)a->limbs[k]) % d;
    }
    if (a->sign < 0 && r != 0u) { r = d - r; }   /* Python-mod: nonneg residue */
    return r;
}

/* out_u64[0..lf) = f reduced mod p (Python-mod, in [0, p)); returns out length. */
static int fac_reduce_mod_p(uint64_t *out, const srmech_bigint_t *f, int lf,
                            uint64_t p)
{
    int i;
    assert(out != NULL);
    assert(f != NULL && lf >= 1);
    for (i = 0; i < lf; i++) {
        out[i] = bignum_mod_u64(&f[i], p);
    }
    return fp_trim(out, lf);
}

/* True iff n (< 2^32) is prime (trial division; matches srmech.amsc.primes). */
static int fac_is_prime(uint64_t n)
{
    uint64_t d;
    assert(n < UINT64_C(4294967296));
    if (n < 2u) { return 0; }
    if (n % 2u == 0u) { return n == 2u; }
    for (d = 3u; d * d <= n; d += 2u) {
        if (n % d == 0u) { return 0; }
    }
    return 1;
}

/* m = the smallest p^k >= 2*B+1, B = 2^deg * ‖f‖₁ * |lead| + 1 (Mignotte).
 * Fills c->mod + c->modhalf. Uses scalar temps bt[0..7]. */
static srmech_status_t fac_build_modulus(fac_ctx_t *c, const srmech_bigint_t *f,
                                         int lf)
{
    srmech_bigint_t *n1 = &c->bt[0], *ab = &c->bt[1], *ac = &c->bt[3];
    srmech_bigint_t *ld = &c->bt[4], *pw = &c->bt[5], *t0 = &c->bt[6], *t1 = &c->bt[7];
    int deg = lf - 1, i;
    srmech_status_t st;
    assert(c != NULL);
    assert(f != NULL && lf >= 1);
    st = fbi_seti(n1, 0); if (st != SRMECH_OK) { return st; }
    for (i = 0; i < lf; i++) {                     /* ‖f‖₁ = Σ |f[i]| */
        st = fbi_seti(&c->bt[2], 0);   if (st != SRMECH_OK) { return st; }
        st = (f[i].sign < 0) ? fbi_sub(ab, &c->bt[2], &f[i]) : fbi_copy(ab, &f[i]);
        if (st != SRMECH_OK) { return st; }
        st = fbi_add(ac, n1, ab); if (st != SRMECH_OK) { return st; }
        st = fbi_copy(n1, ac);    if (st != SRMECH_OK) { return st; }
    }
    st = fbi_seti(&c->bt[2], 0); if (st != SRMECH_OK) { return st; }
    st = (f[deg].sign < 0) ? fbi_sub(ld, &c->bt[2], &f[deg]) : fbi_copy(ld, &f[deg]);
    if (st != SRMECH_OK) { return st; }
    st = fbi_seti(t0, 1);                          if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shl_bits(pw, t0, (uint32_t)deg); if (st != SRMECH_OK) { return st; }
    st = fbi_mul(t0, pw, n1);   if (st != SRMECH_OK) { return st; }  /* 2^deg·‖f‖₁ */
    st = fbi_mul(t1, t0, ld);   if (st != SRMECH_OK) { return st; }  /* ·|lead|    */
    st = fbi_seti(t0, 1);       if (st != SRMECH_OK) { return st; }
    st = fbi_add(pw, t1, t0);   if (st != SRMECH_OK) { return st; }  /* B          */
    st = fbi_add(t1, pw, pw);   if (st != SRMECH_OK) { return st; }  /* 2B         */
    st = fbi_add(pw, t1, t0);   if (st != SRMECH_OK) { return st; }  /* target=2B+1*/
    st = fbi_seti(c->mod, (int64_t)c->q); if (st != SRMECH_OK) { return st; }
    st = fbi_seti(t0, (int64_t)c->q);     if (st != SRMECH_OK) { return st; }
    while (srmech_bigint_cmp(c->mod, pw) < 0) {
        st = fbi_mul(t1, c->mod, t0); if (st != SRMECH_OK) { return st; }
        st = fbi_copy(c->mod, t1);    if (st != SRMECH_OK) { return st; }
    }
    return srmech_bigint_shr_bits(c->modhalf, c->mod, 1u);
}

/* ================================================================== *
 *  Hensel lift (𝔽_p bezout/product + the linear multi-factor fold)
 * ================================================================== */

/* out = Π mp_factors[start..end) over 𝔽_p. Returns out length. Scratch hp0/hp1.*/
static int fp_product(fac_ctx_t *c, uint64_t *out, int start, int end)
{
    uint64_t *acc = hp_buf(c, 0);
    int lacc = 1, j, i, lt;
    assert(c != NULL);
    assert(out != NULL);
    acc[0] = 1u % c->q;
    for (j = start; j < end; j++) {
        const uint64_t *gj = c->mp_flat + (size_t)j * (size_t)c->cw;
        lt = fp_mul(hp_buf(c, 1), acc, lacc, gj, c->mp_len[j], c->q);
        for (i = 0; i < lt; i++) { acc[i] = hp_buf(c, 1)[i]; }
        lacc = lt;
    }
    for (i = 0; i < lacc; i++) { out[i] = acc[i]; }
    return lacc;
}

/* Bézout cofactors s·g + t·h == 1 (mod p) via extended Euclid in 𝔽_p[x].
 * Writes sout/tout (u64), returns their lengths via sl and tl. hp2..hp11 scratch. */
static void fp_bezout(fac_ctx_t *c, uint64_t *sout, int *sl, uint64_t *tout,
                      int *tl, const uint64_t *g, int lg, const uint64_t *h,
                      int lh)
{
    uint64_t *or_ = hp_buf(c, 2), *r = hp_buf(c, 3), *os = hp_buf(c, 4);
    uint64_t *s = hp_buf(c, 5), *ot = hp_buf(c, 6), *t = hp_buf(c, 7);
    uint64_t *qo = hp_buf(c, 8), *pr = hp_buf(c, 9), *nx = hp_buf(c, 10);
    uint64_t *rm = hp_buf(c, 11);
    int lor = lg, lr = lh, los = 1, ls = 1, lot = 1, lt = 1, i, lq, lp, ln, lrm;
    uint64_t inv;
    assert(c != NULL);
    assert(sout != NULL && tout != NULL);
    for (i = 0; i < lg; i++) { or_[i] = g[i] % c->q; }
    for (i = 0; i < lh; i++) { r[i] = h[i] % c->q; }
    os[0] = 1u % c->q; s[0] = 0u; ot[0] = 0u; t[0] = 1u % c->q;
    while (!(lr == 1 && r[0] == 0u)) {
        fp_divmod(qo, &lq, rm, &lrm, or_, lor, r, lr, c->q);
        lp = fp_mul(pr, qo, lq, r, lr, c->q);
        ln = fp_sub(nx, or_, lor, pr, lp, c->q);
        for (i = 0; i < lr; i++) { or_[i] = r[i]; } lor = lr;
        for (i = 0; i < ln; i++) { r[i] = nx[i]; } lr = ln;
        lp = fp_mul(pr, qo, lq, s, ls, c->q);
        ln = fp_sub(nx, os, los, pr, lp, c->q);
        for (i = 0; i < ls; i++) { os[i] = s[i]; } los = ls;
        for (i = 0; i < ln; i++) { s[i] = nx[i]; } ls = ln;
        lp = fp_mul(pr, qo, lq, t, lt, c->q);
        ln = fp_sub(nx, ot, lot, pr, lp, c->q);
        for (i = 0; i < lt; i++) { ot[i] = t[i]; } lot = lt;
        for (i = 0; i < ln; i++) { t[i] = nx[i]; } lt = ln;
    }
    inv = fp_powmod_s(or_[0] % c->q, c->q - 2u, c->q);
    for (i = 0; i < los; i++) { sout[i] = fp_mulmod_s(os[i], inv, c->q); }
    for (i = 0; i < lot; i++) { tout[i] = fp_mulmod_s(ot[i], inv, c->q); }
    *sl = fp_trim(sout, los); *tl = fp_trim(tout, lot);
}

/* Compute gstar (buf10) + hstar (buf11) of the quadratic Hensel step (mod m2).*/
static srmech_status_t hs_ghstar(fac_ctx_t *c, int lF, int lg, int lh, int ls,
                                 int lt, int *lgs, int *lhs)
{
    srmech_bigint_t *m2 = c->m2, *F = bp_buf(c, 0), *G = bp_buf(c, 1);
    srmech_bigint_t *H = bp_buf(c, 2), *S = bp_buf(c, 3), *T = bp_buf(c, 4);
    srmech_bigint_t *E = bp_buf(c, 5), *t1 = bp_buf(c, 6), *t2 = bp_buf(c, 7);
    srmech_bigint_t *qq = bp_buf(c, 8), *rr = bp_buf(c, 9), *GS = bp_buf(c, 10);
    int le, l1, l2, lq, lr;
    srmech_status_t st;
    assert(c != NULL);
    assert(lF >= 1);
    st = bp_mulmod(c, t1, &l1, G, lg, H, lh, m2);        if (st) { return st; }
    st = bp_submod(c, E, &le, F, lF, t1, l1, m2);        if (st) { return st; }
    st = bp_mulmod(c, t1, &l1, S, ls, E, le, m2);        if (st) { return st; }
    st = bp_divmod_monic(c, qq, &lq, rr, &lr, t1, l1, H, lh, m2); if (st) { return st; }
    st = bp_mulmod(c, t1, &l1, T, lt, E, le, m2);        if (st) { return st; }
    st = bp_addmod(c, t2, &l2, G, lg, t1, l1, m2);       if (st) { return st; }
    st = bp_mulmod(c, t1, &l1, qq, lq, G, lg, m2);       if (st) { return st; }
    st = bp_addmod(c, GS, lgs, t2, l2, t1, l1, m2);      if (st) { return st; }
    st = bp_addmod(c, bp_buf(c, 11), lhs, H, lh, rr, lr, m2);
    return st;
}

/* Compute sstar (buf13) + tstar (buf14) of the quadratic Hensel step (mod m2).*/
static srmech_status_t hs_ststar(fac_ctx_t *c, int lg, int lh, int ls, int lt,
                                 int lgs, int lhs, int *lss, int *lts)
{
    srmech_bigint_t *m2 = c->m2, *S = bp_buf(c, 3), *T = bp_buf(c, 4);
    srmech_bigint_t *GS = bp_buf(c, 10), *HS = bp_buf(c, 11), *t1 = bp_buf(c, 6);
    srmech_bigint_t *t2 = bp_buf(c, 7), *t1b = bp_buf(c, 15), *ONE = bp_buf(c, 16);
    srmech_bigint_t *BP = bp_buf(c, 12), *CC = bp_buf(c, 17), *DD = bp_buf(c, 18);
    srmech_bigint_t *SS = bp_buf(c, 13), *TT = bp_buf(c, 14);
    int l1, l2, ln, lb_, lc, ld;
    srmech_status_t st;
    (void)lg; (void)lh;
    assert(c != NULL);
    assert(lgs >= 1 && lhs >= 1);
    st = bp_mulmod(c, t1, &l1, S, ls, GS, lgs, m2);      if (st) { return st; }
    st = bp_mulmod(c, t2, &l2, T, lt, HS, lhs, m2);      if (st) { return st; }
    st = bp_addmod(c, t1b, &ln, t1, l1, t2, l2, m2);     if (st) { return st; }
    st = fbi_seti(&ONE[0], 1);                           if (st) { return st; }
    st = bp_submod(c, BP, &lb_, t1b, ln, ONE, 1, m2);    if (st) { return st; }
    st = bp_mulmod(c, t1, &l1, S, ls, BP, lb_, m2);      if (st) { return st; }
    st = bp_divmod_monic(c, CC, &lc, DD, &ld, t1, l1, HS, lhs, m2); if (st) { return st; }
    st = bp_submod(c, SS, lss, S, ls, DD, ld, m2);       if (st) { return st; }
    st = bp_mulmod(c, t1, &l1, T, lt, BP, lb_, m2);      if (st) { return st; }
    st = bp_submod(c, t2, &l2, T, lt, t1, l1, m2);       if (st) { return st; }
    st = bp_mulmod(c, t1, &l1, CC, lc, GS, lgs, m2);     if (st) { return st; }
    st = bp_submod(c, TT, lts, t2, l2, t1, l1, m2);
    return st;
}

/* One quadratic Hensel step (mod modn -> mod modn^2). g/h/s/t (buf1..4) updated
 * in place; F (buf0) the target monic-associate of length lF. */
static srmech_status_t hensel_step(fac_ctx_t *c, const srmech_bigint_t *modn,
                                   int lF, int *lg, int *lh, int *ls, int *lt)
{
    int lgs, lhs, lss, lts;
    srmech_status_t st;
    assert(c != NULL);
    assert(modn != NULL);
    st = fbi_mul(c->m2, modn, modn);                              if (st) { return st; }
    st = hs_ghstar(c, lF, *lg, *lh, *ls, *lt, &lgs, &lhs);        if (st) { return st; }
    st = hs_ststar(c, *lg, *lh, *ls, *lt, lgs, lhs, &lss, &lts);  if (st) { return st; }
    st = bp_copy(bp_buf(c, 1), bp_buf(c, 10), lgs); if (st) { return st; } *lg = lgs;
    st = bp_copy(bp_buf(c, 2), bp_buf(c, 11), lhs); if (st) { return st; } *lh = lhs;
    st = bp_copy(bp_buf(c, 3), bp_buf(c, 13), lss); if (st) { return st; } *ls = lss;
    st = bp_copy(bp_buf(c, 4), bp_buf(c, 14), lts); if (st) { return st; } *lt = lts;
    return SRMECH_OK;
}

/* Lift one factor: g0 = mp[i], h0 = Π mp[i+1..]; lift the pair against F up to
 * m; store the lifted g in lifted[i], set F := lifted h (buf0), lF := *lFio. */
static srmech_status_t multi_lift_one(fac_ctx_t *c, int i, int *lFio)
{
    srmech_bigint_t *G = bp_buf(c, 1), *H = bp_buf(c, 2);
    int lg, lh, ls, lt, lh0, ls0, lt0;
    srmech_status_t st;
    assert(c != NULL);
    assert(i >= 0 && i < c->mp_n - 1);
    lg = c->mp_len[i];
    lh0 = fp_product(c, hp_buf(c, 12), i + 1, c->mp_n);
    fp_bezout(c, hp_buf(c, 0), &ls0, hp_buf(c, 1), &lt0,
              c->mp_flat + (size_t)i * (size_t)c->cw, lg, hp_buf(c, 12), lh0);
    st = u64_to_bp(G, c->mp_flat + (size_t)i * (size_t)c->cw, lg); if (st) { return st; }
    st = u64_to_bp(H, hp_buf(c, 12), lh0);            if (st) { return st; } lh = lh0;
    st = u64_to_bp(bp_buf(c, 3), hp_buf(c, 0), ls0);  if (st) { return st; } ls = ls0;
    st = u64_to_bp(bp_buf(c, 4), hp_buf(c, 1), lt0);  if (st) { return st; } lt = lt0;
    st = fbi_seti(c->modn, (int64_t)c->q);            if (st) { return st; }
    while (srmech_bigint_cmp(c->modn, c->mod) < 0) {
        st = hensel_step(c, c->modn, *lFio, &lg, &lh, &ls, &lt);
        if (st) { return st; }
        st = fbi_copy(c->modn, c->m2);                if (st) { return st; }
        if (srmech_bigint_cmp(c->modn, c->mod) > 0) {
            st = bp_reduce(c, G, lg, c->mod); if (st) { return st; } lg = bp_trim(G, lg);
            st = bp_reduce(c, H, lh, c->mod); if (st) { return st; } lh = bp_trim(H, lh);
            st = fbi_copy(c->modn, c->mod);   if (st) { return st; }
        }
    }
    st = bp_reduce(c, G, lg, c->mod); if (st) { return st; } lg = bp_trim(G, lg);
    st = bp_reduce(c, H, lh, c->mod); if (st) { return st; } lh = bp_trim(H, lh);
    st = bp_copy(c->lifted + (size_t)i * (size_t)c->cw, G, lg); if (st) { return st; }
    c->lif_len[i] = lg;
    st = bp_copy(bp_buf(c, 0), H, lh); if (st) { return st; } *lFio = lh;
    return SRMECH_OK;
}

/* Lift ALL mod-p factors to mod-m monic factors (the linear Zassenhaus fold). */
static srmech_status_t multi_lift(fac_ctx_t *c)
{
    srmech_bigint_t *F = bp_buf(c, 0), *invl = &c->bt[15];
    int deg = c->deg, i, lF;
    srmech_status_t st;
    assert(c != NULL);
    assert(c->mp_n >= 1);
    st = fbi_mod(c, &c->bt[6], &c->ip[deg], c->mod);  if (st) { return st; }
    st = fbi_modinv(c, invl, &c->bt[6], c->mod);
    if (st) { return st; }
    for (i = 0; i <= deg; i++) {
        st = fbi_mul(&c->bt[0], &c->ip[i], invl);     if (st) { return st; }
        st = fbi_mod(c, &F[i], &c->bt[0], c->mod);
        if (st) { return st; }
    }
    lF = bp_trim(F, deg + 1);
    for (i = 0; i < c->mp_n; i++) {
        if (i == c->mp_n - 1) {
            st = bp_copy(c->lifted + (size_t)i * (size_t)c->cw, F, lF);
            if (st) { return st; }
            c->lif_len[i] = lF;
            break;
        }
        st = multi_lift_one(c, i, &lF);
        if (st) { return st; }
    }
    return SRMECH_OK;
}

/* ================================================================== *
 *  Recombination (symmetric rep + primitive part + exact ℤ trial-div)
 * ================================================================== */

/* poly[0..len) <- its symmetric representatives mod m (centred in (−m/2, m/2]).*/
static srmech_status_t fac_symmetric_rep(fac_ctx_t *c, srmech_bigint_t *poly,
                                         int len)
{
    int i;
    srmech_status_t st;
    assert(c != NULL);
    assert(poly != NULL);
    for (i = 0; i < len; i++) {
        if (srmech_bigint_cmp(&poly[i], c->modhalf) > 0) {
            st = fbi_sub(&c->bt[0], &poly[i], c->mod); if (st) { return st; }
            st = fbi_copy(&poly[i], &c->bt[0]);        if (st) { return st; }
        }
    }
    return SRMECH_OK;
}

/* out_prim = the primitive part of poly (content 1, POSITIVE leading coeff);
 * *plen <- length. Content = gcd of the magnitudes (Class-I), sign the Class-K
 * pin-slot. poly must be nonzero. */
static srmech_status_t fac_primitive(fac_ctx_t *c, const srmech_bigint_t *poly,
                                     int len, srmech_bigint_t *out_prim,
                                     int *plen)
{
    int i, neg;
    srmech_status_t st;
    assert(c != NULL);
    assert(poly != NULL && out_prim != NULL && len >= 1);
    st = fbi_seti(&c->bt[0], 0); if (st) { return st; }        /* content */
    for (i = 0; i < len; i++) {
        st = srmech_bigint_gcd(&c->bt[1], &c->bt[0], &poly[i], c->bws, c->bws_len);
        if (st) { return st; }
        st = fbi_copy(&c->bt[0], &c->bt[1]); if (st) { return st; }
    }
    neg = (poly[len - 1].sign < 0);
    for (i = 0; i < len; i++) {
        st = srmech_bigint_divmod(&c->bt[2], NULL, &poly[i], &c->bt[0],
                                  c->bws, c->bws_len);
        if (st) { return st; }
        if (neg) {
            st = fbi_seti(&c->bt[3], 0);                  if (st) { return st; }
            st = fbi_sub(&out_prim[i], &c->bt[3], &c->bt[2]);
        } else {
            st = fbi_copy(&out_prim[i], &c->bt[2]);
        }
        if (st) { return st; }
    }
    *plen = bp_trim(out_prim, len);
    return SRMECH_OK;
}

/* (quo, ?) of the EXACT ℤ division a / b (b positive lead). *divides <- 1 iff
 * a == quo·b exactly. rem scratch = buf21. */
static srmech_status_t fac_exact_divmod(fac_ctx_t *c, const srmech_bigint_t *a,
                                        int la, const srmech_bigint_t *b, int lb,
                                        srmech_bigint_t *quo, int *ql,
                                        int *divides)
{
    srmech_bigint_t *rem = bp_buf(c, 21);
    int qn = (la - lb + 1 > 1) ? la - lb + 1 : 1, i, d, r = la;
    srmech_status_t st;
    assert(c != NULL);
    assert(a != NULL && b != NULL && lb >= 1);
    for (i = 0; i < qn; i++) { st = fbi_seti(&quo[i], 0); if (st) { return st; } }
    st = bp_copy(rem, a, la); if (st) { return st; }
    r = bp_trim(rem, r);
    while (r >= lb && !(r == 1 && srmech_bigint_is_zero(&rem[0]))) {
        st = srmech_bigint_divmod(&c->bt[0], &c->bt[1], &rem[r - 1], &b[lb - 1],
                                  c->bws, c->bws_len);
        if (st) { return st; }
        if (!srmech_bigint_is_zero(&c->bt[1])) { *divides = 0; return SRMECH_OK; }
        d = r - lb;
        st = fbi_copy(&quo[d], &c->bt[0]); if (st) { return st; }
        for (i = 0; i < lb; i++) {
            st = fbi_mul(&c->bt[2], &c->bt[0], &b[i]);       if (st) { return st; }
            st = fbi_sub(&c->bt[3], &rem[d + i], &c->bt[2]); if (st) { return st; }
            st = fbi_copy(&rem[d + i], &c->bt[3]);           if (st) { return st; }
        }
        r = bp_trim(rem, r);
    }
    *ql = bp_trim(quo, qn);
    *divides = (r == 1 && srmech_bigint_is_zero(&rem[0])) ? 1 : 0;
    return SRMECH_OK;
}

/* Advance pos[0..size) to the next combination of positions in [0, n).
 * Returns 1 if advanced, 0 if the enumeration is exhausted. */
static int next_combo(int *pos, int size, int n)
{
    int i = size - 1, j;
    assert(pos != NULL);
    assert(size >= 1);
    while (i >= 0 && pos[i] == n - size + i) { i--; }
    if (i < 0) { return 0; }
    pos[i]++;
    for (j = i + 1; j < size; j++) { pos[j] = pos[j - 1] + 1; }
    return 1;
}

/* Build the candidate lead·Π lifted[combo] mod m -> symmetric rep -> primitive
 * part, then EXACT ℤ trial-divide f_work by it. *divides <- clean division. */
static srmech_status_t fac_candidate(fac_ctx_t *c, int size, int lfw,
                                     srmech_bigint_t *quo, int *lquo,
                                     srmech_bigint_t *prim, int *lprim,
                                     int *divides)
{
    srmech_bigint_t *prod = bp_buf(c, 22), *tmp = bp_buf(c, 25);
    srmech_bigint_t *cand = bp_buf(c, 23), *fwork = bp_buf(c, 19);
    int lprod, l, j, idx, lcand;
    srmech_status_t st;
    assert(c != NULL);
    assert(size >= 1);
    st = fbi_mod(c, &prod[0], &fwork[lfw - 1], c->mod); if (st) { return st; }
    lprod = 1;
    for (j = 0; j < size; j++) {
        idx = c->rem_idx[c->combo[j]];
        st = bp_mulmod(c, tmp, &l, prod, lprod,
                       c->lifted + (size_t)idx * (size_t)c->cw, c->lif_len[idx],
                       c->mod);
        if (st) { return st; }
        st = bp_copy(prod, tmp, l); if (st) { return st; }
        lprod = l;
    }
    st = bp_copy(cand, prod, lprod); if (st) { return st; }
    lcand = lprod;
    st = fac_symmetric_rep(c, cand, lcand); if (st) { return st; }
    lcand = bp_trim(cand, lcand);
    st = fac_primitive(c, cand, lcand, prim, lprim); if (st) { return st; }
    if (*lprim <= 1) { *divides = 0; return SRMECH_OK; }
    return fac_exact_divmod(c, fwork, lfw, prim, *lprim, quo, lquo, divides);
}

/* Peel a found factor: append prim to the irreducible list, drop the combo's
 * positions from rem_idx, and set f_work := quo (length *lfw). */
static srmech_status_t fac_peel(fac_ctx_t *c, int size,
                                const srmech_bigint_t *prim, int lprim,
                                const srmech_bigint_t *quo, int lquo, int *lfw)
{
    int p, cj = 0, nn = 0;
    srmech_status_t st;
    assert(c != NULL);
    assert(prim != NULL);
    st = bp_copy(c->irr + (size_t)c->irr_n * (size_t)c->cw, prim, lprim);
    if (st) { return st; }
    c->irr_len[c->irr_n] = lprim; c->irr_n++;
    for (p = 0; p < c->rem_n; p++) {
        if (cj < size && p == c->combo[cj]) { cj++; continue; }
        c->rem_idx[nn] = c->rem_idx[p]; nn++;
    }
    c->rem_n = nn;
    st = bp_copy(bp_buf(c, 19), quo, lquo); if (st) { return st; }
    *lfw = lquo;
    return SRMECH_OK;
}

/* The recombination driver: increasing subset sizes, exact ℤ trial-division,
 * subset-cap guard. Fills c->irr / c->irr_len / c->irr_n + *hit_cap.
 * Only subsets with 2*size <= #remaining are enumerated (von zur Gathen &
 * Gerhard, Modern Computer Algebra, ch. 15, the Zassenhaus factor-combination
 * step): a true factor spanning MORE than half the modular factors has a
 * cofactor spanning LESS than half that would already have been peeled at its
 * own smaller size, so once the half bound is exhausted the leftover is
 * irreducible — this halves the classic exponential enumeration (the pure
 * Python path applies the same cutoff, so both paths stay byte-identical).
 * HONEST LIMIT: the enumeration stays WORST-CASE EXPONENTIAL in the number of
 * modular factors even with the cutoff (Swinnerton-Dyer inputs split into
 * deg <= 2 factors mod every prime yet are irreducible over ℤ — measured SD5,
 * deg 32: 39207 candidates post-cutoff vs 65539 pre). van Hoeij's LLL
 * knapsack recombination (J. Number Theory 95(2), 2002) is the known real
 * fix, deferred as a research arc. */
static srmech_status_t fac_recombine(fac_ctx_t *c, int *hit_cap)
{
    int lfw = c->deg + 1, size = 1, i, j, found, lquo, lprim, divides, lp;
    srmech_status_t st;
    assert(c != NULL);
    assert(hit_cap != NULL);
    st = bp_copy(bp_buf(c, 19), c->ip, c->deg + 1); if (st) { return st; }
    for (i = 0; i < c->mp_n; i++) { c->rem_idx[i] = i; }
    c->rem_n = c->mp_n; c->irr_n = 0; *hit_cap = 0;
    while (c->rem_n > 0 && 2 * size <= c->rem_n) {
        if (size > FAC_SUBSET_CAP) { *hit_cap = 1; break; }
        for (j = 0; j < size; j++) { c->combo[j] = j; }
        found = 0;
        while (1) {
            st = fac_candidate(c, size, lfw, bp_buf(c, 20), &lquo,
                               bp_buf(c, 24), &lprim, &divides);
            if (st) { return st; }
            if (divides) { found = 1; break; }
            if (!next_combo(c->combo, size, c->rem_n)) { break; }
        }
        if (!found) { size++; continue; }
        st = fac_peel(c, size, bp_buf(c, 24), lprim, bp_buf(c, 20), lquo, &lfw);
        if (st) { return st; }
        if (lfw <= 1) { break; }
        size = 1;
    }
    if (lfw > 1) {
        st = fac_primitive(c, bp_buf(c, 19), lfw,
                           c->irr + (size_t)c->irr_n * (size_t)c->cw, &lp);
        if (st) { return st; }
        c->irr_len[c->irr_n] = lp; c->irr_n++;
    }
    return SRMECH_OK;
}

/* ================================================================== *
 *  The square-free primitive Zassenhaus core + arena carve
 * ================================================================== */

/* Set c->irr = [c->ip] (the input itself is irreducible). */
static srmech_status_t fac_irr_is_input(fac_ctx_t *c, int *hit_cap)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(hit_cap != NULL);
    st = bp_copy(c->irr, c->ip, c->deg + 1);
    if (st) { return st; }
    c->irr_len[0] = c->deg + 1;
    c->irr_n = 1;
    *hit_cap = 0;
    return SRMECH_OK;
}

/* Choose a prime p ∤ lead with c->ip square-free mod p (< 100000). Returns the
 * prime, or 0 if none found. hp0/hp1/hp2 + g0..g3 scratch. */
static uint64_t fac_choose_prime(fac_ctx_t *c)
{
    uint64_t cand = 3u;
    int lfp, lfd, lg;
    assert(c != NULL);
    assert(c->ip != NULL && c->deg >= 1);
    while (cand < 100000u) {
        if (fac_is_prime(cand) && bignum_mod_u64(&c->ip[c->deg], cand) != 0u) {
            lfp = fac_reduce_mod_p(hp_buf(c, 0), c->ip, c->deg + 1, cand);
            lfd = fp_deriv(hp_buf(c, 1), hp_buf(c, 0), lfp, cand);
            lg = fp_gcd(hp_buf(c, 2), hp_buf(c, 0), lfp, hp_buf(c, 1), lfd, cand,
                        c->g0, c->g1, c->g2, c->g3);
            if (lg == 1 && hp_buf(c, 2)[0] == 1u) { return cand; }
        }
        cand += 2u;
    }
    return 0u;
}

/* Factor the square-free primitive c->ip (positive lead, deg >= 1) into its
 * irreducible ℤ factors (Zassenhaus). Fills c->irr / c->irr_len / c->irr_n. */
static srmech_status_t fac_squarefree_primitive(fac_ctx_t *c, int *hit_cap)
{
    uint64_t prime, state;
    int lfp, lfm;
    srmech_status_t st;
    assert(c != NULL);
    assert(hit_cap != NULL);
    if (c->deg <= 1) { return fac_irr_is_input(c, hit_cap); }
    prime = fac_choose_prime(c);
    if (prime == 0u) { return SRMECH_ERR_BAD_INPUT; }
    c->q = prime;
    state = FAC_RNG_SEED ^ (prime * (uint64_t)(c->deg + 1));
    lfp = fac_reduce_mod_p(hp_buf(c, 0), c->ip, c->deg + 1, prime);
    lfm = fp_make_monic(hp_buf(c, 13), hp_buf(c, 0), lfp, prime);
    st = fp_factor_mod_p(c, hp_buf(c, 13), lfm, &state);
    if (st) { return st; }
    if (c->mp_n == 1) { return fac_irr_is_input(c, hit_cap); }
    st = fac_build_modulus(c, c->ip, c->deg + 1);
    if (st) { return st; }
    st = multi_lift(c);
    if (st) { return st; }
    st = fac_recombine(c, hit_cap);
    return st;
}

/* Per-coefficient limb capacity (generous headroom past the modn^2 products). */
static size_t fac_cap_for(size_t coeff_limbs, int deg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap;
    assert(deg >= 0);
    cap = 10u * cl + (size_t)deg / 2u + 64u;
    assert(cap >= 64u);
    return cap;
}

/* Carve the 𝔽_p (u64) working buffers + Hensel-phase pool. Returns 0 on OOM. */
static int fac_carve_fp(fac_ctx_t *c)
{
    size_t w;
    assert(c != NULL);
    w = (size_t)c->fw;
    c->g0 = fac_carve_u64(&c->ar, w); c->g1 = fac_carve_u64(&c->ar, w);
    c->g2 = fac_carve_u64(&c->ar, w); c->g3 = fac_carve_u64(&c->ar, w);
    c->mr0 = fac_carve_u64(&c->ar, w); c->mr1 = fac_carve_u64(&c->ar, w);
    c->mr2 = fac_carve_u64(&c->ar, w); c->pm_r = fac_carve_u64(&c->ar, w);
    c->pm_b = fac_carve_u64(&c->ar, w); c->pm_t = fac_carve_u64(&c->ar, w);
    c->dd_fs = fac_carve_u64(&c->ar, w); c->dd_xq = fac_carve_u64(&c->ar, w);
    c->dd_x = fac_carve_u64(&c->ar, w); c->dd_sb = fac_carve_u64(&c->ar, w);
    c->dd_g = fac_carve_u64(&c->ar, w); c->dd_qt = fac_carve_u64(&c->ar, w);
    c->dd_t2 = fac_carve_u64(&c->ar, w); c->ed_g = fac_carve_u64(&c->ar, w);
    c->ed_r = fac_carve_u64(&c->ar, w); c->ed_h = fac_carve_u64(&c->ar, w);
    c->ed_gg = fac_carve_u64(&c->ar, w); c->ed_ot = fac_carve_u64(&c->ar, w);
    c->ed_qt = fac_carve_u64(&c->ar, w); c->ed_mn = fac_carve_u64(&c->ar, w);
    c->hp = fac_carve_u64(&c->ar, (size_t)FAC_HP_N * w);
    assert(c->g0 != NULL || c->ar.off <= c->ar.cap);
    return (c->hp != NULL && c->ed_mn != NULL);
}

/* Carve the flats (u64) + index arrays (int). Returns 0 on OOM. */
static int fac_carve_lists(fac_ctx_t *c)
{
    size_t nl, flat;
    assert(c != NULL);
    nl = (size_t)c->deg + 1u; flat = nl * (size_t)c->cw;
    c->st_flat = fac_carve_u64(&c->ar, flat);
    c->db_flat = fac_carve_u64(&c->ar, flat);
    c->mp_flat = fac_carve_u64(&c->ar, flat);
    c->st_len = fac_carve_int(&c->ar, nl); c->db_deg = fac_carve_int(&c->ar, nl);
    c->db_len = fac_carve_int(&c->ar, nl); c->mp_len = fac_carve_int(&c->ar, nl);
    c->rem_idx = fac_carve_int(&c->ar, nl); c->combo = fac_carve_int(&c->ar, nl);
    c->lif_len = fac_carve_int(&c->ar, nl); c->irr_len = fac_carve_int(&c->ar, nl);
    assert(c->st_flat != NULL || c->ar.off <= c->ar.cap);
    return (c->irr_len != NULL && c->combo != NULL);
}

/* Carve the srmech_bigint scalars + poly pool + ip/lifted/irr. Returns 0 OOM. */
static int fac_carve_big(fac_ctx_t *c)
{
    size_t nl, cw;
    assert(c != NULL);
    nl = (size_t)c->deg + 1u; cw = (size_t)c->cw;
    c->bt = fac_carve_bigints(&c->ar, 16u, c->cap);
    c->mod = fac_carve_bigints(&c->ar, 1u, c->cap);
    c->modhalf = fac_carve_bigints(&c->ar, 1u, c->cap);
    c->m2 = fac_carve_bigints(&c->ar, 1u, c->cap);
    c->modn = fac_carve_bigints(&c->ar, 1u, c->cap);
    c->pool = fac_carve_bigints(&c->ar, (size_t)FAC_BP_N * cw, c->cap);
    c->ip = fac_carve_bigints(&c->ar, cw, c->cap);
    c->lifted = fac_carve_bigints(&c->ar, nl * cw, c->cap);
    c->irr = fac_carve_bigints(&c->ar, nl * cw, c->cap);
    assert(c->bt != NULL || c->ar.off <= c->ar.cap);
    return (c->irr != NULL && c->pool != NULL && c->bt != NULL);
}

/* Initialise the context + carve every buffer from ws. Returns 0 on OOM. */
static int fac_carve(fac_ctx_t *c, void *ws, size_t ws_len, size_t coeff_limbs,
                     int deg)
{
    size_t rem;
    assert(c != NULL);
    assert(ws != NULL);
    c->deg = deg; c->cw = deg + 1; c->fw = 2 * deg + 2;
    c->cap = (uint32_t)fac_cap_for(coeff_limbs, deg);
    c->ar.base = (unsigned char *)ws; c->ar.off = 0u; c->ar.cap = ws_len;
    if (!fac_carve_big(c)) { return 0; }
    if (!fac_carve_fp(c)) { return 0; }
    if (!fac_carve_lists(c)) { return 0; }
    c->ar.off = (c->ar.off + 7u) & ~(size_t)7u;
    if (c->ar.off >= ws_len) { return 0; }
    rem = ws_len - c->ar.off;
    c->bws = c->ar.base + c->ar.off;
    c->bws_len = rem;
    return (rem >= 4096u);
}

/* Minimum out_coeffs cap (limbs) for each factor coefficient. */
size_t srmech_factor_squarefree_primitive_out_cap(size_t coeff_limbs, int deg)
{
    assert(deg >= 0);
    assert((size_t)deg < (SIZE_MAX >> 8u));
    return fac_cap_for(coeff_limbs, deg);
}

/* Minimum ws_len BYTES for srmech_factor_squarefree_primitive. */
size_t srmech_factor_squarefree_primitive_ws_bound(size_t coeff_limbs, int deg)
{
    size_t cw, nl, fw, cap;
    assert(deg >= 0);
    assert((size_t)deg < (SIZE_MAX >> 8u));
    cw = (size_t)deg + 1u; nl = (size_t)deg + 1u; fw = 2u * (size_t)deg + 2u;
    cap = fac_cap_for(coeff_limbs, deg);
    size_t hdrw = (sizeof(srmech_bigint_t) + 3u) / 4u;
    size_t big_cells = 16u + 5u + (size_t)FAC_BP_N * cw + cw + 2u * nl * cw;
    size_t big_words = big_cells * (hdrw + cap + 2u);
    size_t fp_words = (24u + (size_t)FAC_HP_N) * fw * 2u + 3u * nl * cw * 2u;
    size_t int_words = 12u * nl + 16u;
    size_t bws_words = 96u * cap + 8192u;
    size_t total = big_words + fp_words + int_words + bws_words + 8192u;
    return total * 4u;
}

/* Public: factor a SQUARE-FREE PRIMITIVE integer polynomial (coeffs low->high,
 * positive lead, content 1, deg >= 1) into irreducible ℤ factors (Zassenhaus).
 * Writes the factors' coefficients CONCATENATED low->high into out_coeffs, each
 * factor's degree into out_degs, the count into *out_nfac, and the recombination
 * subset-cap flag into *out_hit_cap. Returns SRMECH_OK, SRMECH_ERR_OVERFLOW on
 * arena exhaustion (caller falls to pure), or SRMECH_ERR_BAD_INPUT on the zero
 * polynomial / no-good-prime / deg > FAC_MAX_DEG. */
srmech_status_t srmech_factor_squarefree_primitive(
    const srmech_bigint_t *coeffs, int ncoeff, srmech_bigint_t *out_coeffs,
    int *out_degs, int *out_nfac, int *out_hit_cap, void *ws, size_t ws_len)
{
    fac_ctx_t c;
    int deg, i, j, off = 0;
    size_t cl = 1u;
    srmech_status_t st;
    assert(coeffs != NULL && out_coeffs != NULL && out_nfac != NULL);
    assert(out_degs != NULL && out_hit_cap != NULL && ws != NULL);
    if (ncoeff < 1) { return SRMECH_ERR_BAD_INPUT; }
    deg = bp_trim(coeffs, ncoeff) - 1;
    if (deg < 0) { return SRMECH_ERR_BAD_INPUT; }
    if (deg > FAC_MAX_DEG) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0; i <= deg; i++) { if (coeffs[i].n > cl) { cl = coeffs[i].n; } }
    if (!fac_carve(&c, ws, ws_len, cl, deg)) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0; i <= deg; i++) {
        st = fbi_copy(&c.ip[i], &coeffs[i]);
        if (st != SRMECH_OK) { return st; }
    }
    st = fac_squarefree_primitive(&c, out_hit_cap);
    if (st != SRMECH_OK) { return st; }
    for (j = 0; j < c.irr_n; j++) {
        out_degs[j] = c.irr_len[j] - 1;
        for (i = 0; i < c.irr_len[j]; i++) {
            st = fbi_copy(&out_coeffs[off], &c.irr[(size_t)j * (size_t)c.cw + i]);
            if (st != SRMECH_OK) { return st; }
            off++;
        }
    }
    *out_nfac = c.irr_n;
    return SRMECH_OK;
}

/* ================================================================== *
 *  srmech_factor_integer_poly — the FULL factor_integer_poly composite
 *  (rc165 deferral 2, everything-mirrors): content + primitive part,
 *  Yun square-free decomposition over exact ℚ (composing the
 *  srmech_poly_gcd / srmech_poly_divmod / srmech_poly_sub kernels +
 *  an exact-ℚ derivative), per square-free part the Zassenhaus core
 *  srmech_factor_squarefree_primitive above, merge-identical factors,
 *  and the (len, coeffs) sort — so a bare-C host factors an integer
 *  polynomial into its irreducible (factor, multiplicity) list with
 *  ONE call, byte-identical to the Python factor_integer_poly.
 * ================================================================== */

/* Q-poly slots (parallel num/den arrays, each cw coefficients wide). */
#define FIQ_P  0   /* the primitive input over ℚ (dens 1)  */
#define FIQ_DV 1   /* p'                                    */
#define FIQ_A  2   /* Yun a = gcd(p, p')                    */
#define FIQ_B  3   /* Yun b                                 */
#define FIQ_C  4   /* Yun c                                 */
#define FIQ_D  5   /* Yun d                                 */
#define FIQ_G  6   /* Yun g = gcd(b, d)                     */
#define FIQ_Q1 7   /* divmod quotient out                   */
#define FIQ_R1 8   /* divmod remainder out                  */
#define FIQ_T3 9   /* b' scratch                            */
#define FIQ_NQ 10

typedef struct fiq_ctx {
    fac_arena_t ar;
    int cw;                        /* deg + 1 coefficient slots            */
    int deg;
    uint32_t ccap;                 /* carrier limb cap (ℚ + ℤ coefficients) */
    uint32_t scap;                 /* self-check accumulator limb cap       */
    srmech_bigint_t *qn[FIQ_NQ];   /* Q-poly numerators                     */
    srmech_bigint_t *qd[FIQ_NQ];   /* Q-poly denominators (> 0, reduced)    */
    srmech_bigint_t *prim;         /* primitive part of the input (cw)      */
    srmech_bigint_t *gint;         /* den-cleared Yun part (cw)             */
    srmech_bigint_t *gprim;        /* its primitive part (cw)               */
    srmech_bigint_t *stage;        /* factor-core out staging (2*cw + 2)    */
    srmech_bigint_t *store;        /* merged factors (deg rows x cw)        */
    srmech_bigint_t *sc0, *sc1;    /* self-check accumulators (cw, scap)    */
    srmech_bigint_t *bt;           /* scalar temps bt[0..7]                 */
    int *stage_degs, *flen, *fmult, *order;
    int fcount, capped;
    void *tail; size_t tail_len;   /* sub-arena: poly kernels + factor core */
} fiq_ctx_t;

/* Carrier limb cap: covers the Yun rational growth envelope AND the
 * Zassenhaus-core factor-coefficient bound (fac_cap_for on a grown input). */
static size_t fiq_cap_for(size_t cl, int deg)
{
    size_t c = (cl == 0u) ? 1u : cl;
    size_t nt = (size_t)deg + 1u;
    size_t q = 4u * c * nt + 64u;                     /* Yun rational envelope */
    size_t o = fac_cap_for(4u * c + 8u, deg);         /* core-out envelope     */
    size_t cap = ((q > o) ? q : o) + 32u;
    assert(cap > q || cap > o);
    assert(cap >= 96u);
    return cap;
}

/* Trim a Q-poly numerator array to its canonical length (0 = the zero poly). */
static int fiq_qtrim(const srmech_bigint_t *n, int len)
{
    assert(n != NULL || len == 0);
    assert(len >= 0);
    while (len > 0 && srmech_bigint_is_zero(&n[len - 1])) { len--; }
    return len;
}

/* Reduce num/den to canonical lowest terms (den > 0; 0 -> 0/1). */
static srmech_status_t fiq_reduce(fiq_ctx_t *c, srmech_bigint_t *num,
                                  srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL);
    assert(den != NULL && den->sign > 0);
    if (srmech_bigint_is_zero(num)) { return srmech_bigint_set_i64(den, 1); }
    st = srmech_bigint_gcd(&c->bt[1], num, den, c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->bt[2], NULL, num, &c->bt[1],
                              c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->bt[2]);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->bt[2], NULL, den, &c->bt[1],
                              c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->bt[2]);
}

/* dst <- d/dx src over exact ℚ: dst[i] = src[i+1]*(i+1), reduced. */
static srmech_status_t fiq_deriv(fiq_ctx_t *c, int src, int dst, size_t slen,
                                 size_t *dlen)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && dlen != NULL);
    assert(src >= 0 && src < FIQ_NQ && dst >= 0 && dst < FIQ_NQ && src != dst);
    if (slen <= 1u) { *dlen = 0u; return SRMECH_OK; }
    for (i = 1u; i < slen; i++) {
        st = srmech_bigint_set_i64(&c->bt[0], (int64_t)i);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c->qn[dst][i - 1u], &c->qn[src][i], &c->bt[0]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->qd[dst][i - 1u], &c->qd[src][i]);
        if (st != SRMECH_OK) { return st; }
        st = fiq_reduce(c, &c->qn[dst][i - 1u], &c->qd[dst][i - 1u]);
        if (st != SRMECH_OK) { return st; }
    }
    *dlen = (size_t)fiq_qtrim(c->qn[dst], (int)slen - 1);
    return SRMECH_OK;
}

/* dst <- src (Q-poly deep copy of len coefficients). */
static srmech_status_t fiq_qcopy(fiq_ctx_t *c, int dst, int src, size_t len)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL);
    assert(src >= 0 && src < FIQ_NQ && dst >= 0 && dst < FIQ_NQ && src != dst);
    for (i = 0u; i < len; i++) {
        st = srmech_bigint_copy(&c->qn[dst][i], &c->qn[src][i]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->qd[dst][i], &c->qd[src][i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out <- the primitive part of the nonzero integer poly p (content 1,
 * POSITIVE lead — the Class-K sign pin-slot; mirrors _ipoly_primitive). */
static srmech_status_t fiq_prim_int(fiq_ctx_t *c, const srmech_bigint_t *p,
                                    int len, srmech_bigint_t *out, int *olen)
{
    int i, neg;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(out != NULL && olen != NULL && len >= 1);
    st = fbi_seti(&c->bt[5], 0);                       /* content accumulator */
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < len; i++) {
        st = srmech_bigint_gcd(&c->bt[6], &c->bt[5], &p[i],
                               c->tail, c->tail_len);
        if (st != SRMECH_OK) { return st; }
        st = fbi_copy(&c->bt[5], &c->bt[6]);
        if (st != SRMECH_OK) { return st; }
    }
    neg = (p[len - 1].sign < 0);
    for (i = 0; i < len; i++) {
        st = srmech_bigint_divmod(&c->bt[6], NULL, &p[i], &c->bt[5],
                                  c->tail, c->tail_len);
        if (st != SRMECH_OK) { return st; }
        if (neg) {
            st = fbi_seti(&c->bt[7], 0);               if (st != SRMECH_OK) { return st; }
            st = fbi_sub(&out[i], &c->bt[7], &c->bt[6]);
        } else {
            st = fbi_copy(&out[i], &c->bt[6]);
        }
        if (st != SRMECH_OK) { return st; }
    }
    *olen = bp_trim(out, len);
    return SRMECH_OK;
}

/* gint <- the Yun part FIQ_G with denominators cleared (times den-lcm),
 * trimmed; mirrors the den_lcm clearing in the Python wrapper. */
static srmech_status_t fiq_clear_dens(fiq_ctx_t *c, size_t lg, int *lint)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && lint != NULL);
    assert(lg >= 1u);
    st = fbi_seti(&c->bt[3], 1);                       /* den_lcm = 1 */
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < lg; i++) {                        /* lcm(den_lcm, den_i) */
        st = srmech_bigint_gcd(&c->bt[1], &c->bt[3], &c->qd[FIQ_G][i],
                               c->tail, c->tail_len);
        if (st != SRMECH_OK) { return st; }
        st = fbi_mul(&c->bt[4], &c->bt[3], &c->qd[FIQ_G][i]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_divmod(&c->bt[3], NULL, &c->bt[4], &c->bt[1],
                                  c->tail, c->tail_len);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0u; i < lg; i++) {          /* gint_i = num_i * (den_lcm/den_i) */
        st = srmech_bigint_divmod(&c->bt[4], NULL, &c->bt[3], &c->qd[FIQ_G][i],
                                  c->tail, c->tail_len);
        if (st != SRMECH_OK) { return st; }
        st = fbi_mul(&c->gint[i], &c->qn[FIQ_G][i], &c->bt[4]);
        if (st != SRMECH_OK) { return st; }
    }
    *lint = bp_trim(c->gint, (int)lg);
    return SRMECH_OK;
}

/* (len, coeffs) order: shorter first, then coefficientwise low->high. */
static int fiq_cmp_fac(const srmech_bigint_t *a, int la,
                       const srmech_bigint_t *b, int lb)
{
    int i, cv;
    assert(a != NULL);
    assert(b != NULL);
    if (la != lb) { return (la < lb) ? -1 : 1; }
    for (i = 0; i < la; i++) {
        cv = srmech_bigint_cmp(&a[i], &b[i]);
        if (cv != 0) { return cv; }
    }
    return 0;
}

/* Merge a primitive positive-lead factor into the store (sum mults). */
static srmech_status_t fiq_merge_add(fiq_ctx_t *c, const srmech_bigint_t *f,
                                     int len, int mult)
{
    int j, i;
    srmech_status_t st;
    assert(c != NULL && f != NULL);
    assert(len >= 1 && mult >= 1);
    for (j = 0; j < c->fcount; j++) {
        if (fiq_cmp_fac(c->store + (size_t)j * (size_t)c->cw, c->flen[j],
                        f, len) == 0) {
            c->fmult[j] += mult;
            return SRMECH_OK;
        }
    }
    if (c->fcount >= c->deg) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0; i < len; i++) {
        st = fbi_copy(&c->store[(size_t)c->fcount * (size_t)c->cw + (size_t)i],
                      &f[i]);
        if (st != SRMECH_OK) { return st; }
    }
    c->flen[c->fcount] = len;
    c->fmult[c->fcount] = mult;
    c->fcount++;
    return SRMECH_OK;
}

/* One Yun part (FIQ_G at multiplicity mult): clear dens -> primitive part ->
 * Zassenhaus core -> merge each irreducible at mult. */
static srmech_status_t fiq_process_part(fiq_ctx_t *c, size_t lg, int mult)
{
    int lint = 0, lprim = 0, nf = 0, hc = 0, j, off = 0;
    srmech_status_t st;
    assert(c != NULL);
    assert(lg >= 2u && mult >= 1);
    st = fiq_clear_dens(c, lg, &lint);                if (st != SRMECH_OK) { return st; }
    st = fiq_prim_int(c, c->gint, lint, c->gprim, &lprim);
    if (st != SRMECH_OK) { return st; }
    if (lprim <= 1) { return SRMECH_OK; }              /* defensive: unit part */
    st = srmech_factor_squarefree_primitive(c->gprim, lprim, c->stage,
                                            c->stage_degs, &nf, &hc,
                                            c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    if (hc) { c->capped = 1; }
    for (j = 0; j < nf; j++) {
        st = fiq_merge_add(c, c->stage + off, c->stage_degs[j] + 1, mult);
        if (st != SRMECH_OK) { return st; }
        off += c->stage_degs[j] + 1;
    }
    return SRMECH_OK;
}

/* Yun setup: a = gcd(p, p'); b = p/a; c = p'/a; d = c - b'. */
static srmech_status_t fiq_yun_setup(fiq_ctx_t *c, size_t lp, size_t *lb,
                                     size_t *lc, size_t *ld)
{
    size_t la = 0u, lq = 0u, lr = 0u, dl = 0u;
    srmech_status_t st;
    assert(c != NULL);
    assert(lp >= 2u && lb != NULL && lc != NULL && ld != NULL);
    st = fiq_deriv(c, FIQ_P, FIQ_DV, lp, &dl);        if (st != SRMECH_OK) { return st; }
    st = srmech_poly_gcd(c->qn[FIQ_P], c->qd[FIQ_P], lp,
                         c->qn[FIQ_DV], c->qd[FIQ_DV], dl,
                         c->qn[FIQ_A], c->qd[FIQ_A], &la,
                         c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_poly_divmod(c->qn[FIQ_P], c->qd[FIQ_P], lp,
                            c->qn[FIQ_A], c->qd[FIQ_A], la,
                            c->qn[FIQ_Q1], c->qd[FIQ_Q1], &lq,
                            c->qn[FIQ_R1], c->qd[FIQ_R1], &lr,
                            c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = fiq_qcopy(c, FIQ_B, FIQ_Q1, lq);             if (st != SRMECH_OK) { return st; }
    *lb = lq;
    st = srmech_poly_divmod(c->qn[FIQ_DV], c->qd[FIQ_DV], dl,
                            c->qn[FIQ_A], c->qd[FIQ_A], la,
                            c->qn[FIQ_Q1], c->qd[FIQ_Q1], &lq,
                            c->qn[FIQ_R1], c->qd[FIQ_R1], &lr,
                            c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = fiq_qcopy(c, FIQ_C, FIQ_Q1, lq);             if (st != SRMECH_OK) { return st; }
    *lc = lq;
    st = fiq_deriv(c, FIQ_B, FIQ_T3, *lb, &dl);       if (st != SRMECH_OK) { return st; }
    return srmech_poly_sub(c->qn[FIQ_C], c->qd[FIQ_C], *lc,
                           c->qn[FIQ_T3], c->qd[FIQ_T3], dl,
                           c->qn[FIQ_D], c->qd[FIQ_D], ld,
                           c->tail, c->tail_len);
}

/* One Yun loop step at multiplicity k: g = gcd(b, d); process g (deg >= 1);
 * b <- b/g; c <- d/g; d <- c - b'. */
static srmech_status_t fiq_yun_step(fiq_ctx_t *c, size_t *lb, size_t *lc,
                                    size_t *ld, int k)
{
    size_t lg = 0u, lq = 0u, lr = 0u, dl = 0u;
    srmech_status_t st;
    assert(c != NULL);
    assert(lb != NULL && *lb > 1u && k >= 1);
    st = srmech_poly_gcd(c->qn[FIQ_B], c->qd[FIQ_B], *lb,
                         c->qn[FIQ_D], c->qd[FIQ_D], *ld,
                         c->qn[FIQ_G], c->qd[FIQ_G], &lg,
                         c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    if (lg > 1u) {
        st = fiq_process_part(c, lg, k);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_poly_divmod(c->qn[FIQ_B], c->qd[FIQ_B], *lb,
                            c->qn[FIQ_G], c->qd[FIQ_G], lg,
                            c->qn[FIQ_Q1], c->qd[FIQ_Q1], &lq,
                            c->qn[FIQ_R1], c->qd[FIQ_R1], &lr,
                            c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = fiq_qcopy(c, FIQ_B, FIQ_Q1, lq);             if (st != SRMECH_OK) { return st; }
    *lb = lq;
    st = srmech_poly_divmod(c->qn[FIQ_D], c->qd[FIQ_D], *ld,
                            c->qn[FIQ_G], c->qd[FIQ_G], lg,
                            c->qn[FIQ_Q1], c->qd[FIQ_Q1], &lq,
                            c->qn[FIQ_R1], c->qd[FIQ_R1], &lr,
                            c->tail, c->tail_len);
    if (st != SRMECH_OK) { return st; }
    st = fiq_qcopy(c, FIQ_C, FIQ_Q1, lq);             if (st != SRMECH_OK) { return st; }
    *lc = lq;
    st = fiq_deriv(c, FIQ_B, FIQ_T3, *lb, &dl);       if (st != SRMECH_OK) { return st; }
    return srmech_poly_sub(c->qn[FIQ_C], c->qd[FIQ_C], *lc,
                           c->qn[FIQ_T3], c->qd[FIQ_T3], dl,
                           c->qn[FIQ_D], c->qd[FIQ_D], ld,
                           c->tail, c->tail_len);
}

/* Sort the merged factors by (len, coeffs) — the Python sorted() order. */
static void fiq_sort(fiq_ctx_t *c)
{
    int i, j, tmp;
    assert(c != NULL);
    assert(c->fcount >= 0);
    for (i = 0; i < c->fcount; i++) { c->order[i] = i; }
    for (i = 1; i < c->fcount; i++) {
        tmp = c->order[i];
        j = i - 1;
        while (j >= 0 &&
               fiq_cmp_fac(c->store + (size_t)c->order[j] * (size_t)c->cw,
                           c->flen[c->order[j]],
                           c->store + (size_t)tmp * (size_t)c->cw,
                           c->flen[tmp]) > 0) {
            c->order[j + 1] = c->order[j];
            j--;
        }
        c->order[j + 1] = tmp;
    }
}

/* out <- acc * f (exact-ℤ convolution); *lo <- trimmed length. */
static srmech_status_t fiq_imul_into(fiq_ctx_t *c, const srmech_bigint_t *acc,
                                     int la, const srmech_bigint_t *f, int lf,
                                     srmech_bigint_t *out, int *lo)
{
    int n = la + lf - 1, i, j;
    srmech_status_t st;
    assert(c != NULL && acc != NULL && f != NULL);
    assert(out != NULL && lo != NULL && n >= 1 && n <= c->cw);
    for (i = 0; i < n; i++) {
        st = fbi_seti(&out[i], 0);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < la; i++) {
        if (srmech_bigint_is_zero(&acc[i])) { continue; }
        for (j = 0; j < lf; j++) {
            st = fbi_mul(&c->bt[0], &acc[i], &f[j]);   if (st != SRMECH_OK) { return st; }
            st = fbi_add(&c->bt[1], &out[i + j], &c->bt[0]);
            if (st != SRMECH_OK) { return st; }
            st = fbi_copy(&out[i + j], &c->bt[1]);     if (st != SRMECH_OK) { return st; }
        }
    }
    *lo = bp_trim(out, n);
    return SRMECH_OK;
}

/* Π factor^mult must reconstruct the primitive input EXACTLY (both sides are
 * primitive with positive lead). A mismatch is an internal inconsistency ->
 * SRMECH_ERR_OVERFLOW so the Python wrapper falls back to the pure oracle
 * (never a silently wrong answer). Skipped when the subset cap was hit. */
static srmech_status_t fiq_selfcheck(fiq_ctx_t *c, int lp)
{
    srmech_bigint_t *acc = c->sc0, *nxt = c->sc1, *swp;
    int la = 1, lo = 0, idx, m, i;
    srmech_status_t st;
    assert(c != NULL);
    assert(lp >= 1 && c->fcount >= 0);
    st = fbi_seti(&acc[0], 1);
    if (st != SRMECH_OK) { return st; }
    for (idx = 0; idx < c->fcount; idx++) {
        const srmech_bigint_t *f =
            c->store + (size_t)c->order[idx] * (size_t)c->cw;
        int lf = c->flen[c->order[idx]];
        for (m = 0; m < c->fmult[c->order[idx]]; m++) {
            st = fiq_imul_into(c, acc, la, f, lf, nxt, &lo);
            if (st != SRMECH_OK) { return st; }
            swp = acc; acc = nxt; nxt = swp;
            la = lo;
        }
    }
    if (la != lp) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0; i < lp; i++) {
        if (srmech_bigint_cmp(&acc[i], &c->prim[i]) != 0) {
            return SRMECH_ERR_OVERFLOW;
        }
    }
    return SRMECH_OK;
}

/* Carve the composite's carriers from ws. Returns 0 on exhaustion. */
static int fiq_carve(fiq_ctx_t *c, void *ws, size_t ws_len, size_t cl, int deg)
{
    size_t cw, k;
    assert(c != NULL);
    assert(ws != NULL && deg >= 1);
    c->deg = deg; c->cw = deg + 1; c->fcount = 0; c->capped = 0;
    c->ccap = (uint32_t)fiq_cap_for(cl, deg);
    c->scap = 2u * c->ccap + 16u;
    c->ar.base = (unsigned char *)ws; c->ar.off = 0u; c->ar.cap = ws_len;
    cw = (size_t)c->cw;
    for (k = 0u; k < (size_t)FIQ_NQ; k++) {
        c->qn[k] = fac_carve_bigints(&c->ar, cw, c->ccap);
        c->qd[k] = fac_carve_bigints(&c->ar, cw, c->ccap);
        if (c->qn[k] == NULL || c->qd[k] == NULL) { return 0; }
    }
    c->prim = fac_carve_bigints(&c->ar, cw, c->ccap);
    c->gint = fac_carve_bigints(&c->ar, cw, c->ccap);
    c->gprim = fac_carve_bigints(&c->ar, cw, c->ccap);
    c->stage = fac_carve_bigints(&c->ar, 2u * cw + 2u, c->ccap);
    c->store = fac_carve_bigints(&c->ar, (size_t)deg * cw, c->ccap);
    c->sc0 = fac_carve_bigints(&c->ar, cw, c->scap);
    c->sc1 = fac_carve_bigints(&c->ar, cw, c->scap);
    c->bt = fac_carve_bigints(&c->ar, 8u, 2u * c->scap);
    c->stage_degs = fac_carve_int(&c->ar, cw + 2u);
    c->flen = fac_carve_int(&c->ar, (size_t)deg);
    c->fmult = fac_carve_int(&c->ar, (size_t)deg);
    c->order = fac_carve_int(&c->ar, (size_t)deg);
    if (c->bt == NULL || c->store == NULL || c->order == NULL) { return 0; }
    c->ar.off = (c->ar.off + 7u) & ~(size_t)7u;
    if (c->ar.off >= ws_len) { return 0; }
    c->tail = c->ar.base + c->ar.off;
    c->tail_len = ws_len - c->ar.off;
    return (c->tail_len >= 16384u);
}

/* Minimum out_coeffs cap (limbs) for each factor coefficient. */
size_t srmech_factor_integer_poly_out_cap(size_t coeff_limbs, int deg)
{
    assert(deg >= 0);
    assert((size_t)deg < (SIZE_MAX >> 8u));
    return fiq_cap_for(coeff_limbs, deg);
}

/* Minimum ws_len BYTES for srmech_factor_integer_poly: the composite's own
 * carriers + the deepest sub-call tail (the ℚ poly-gcd chain arena + the
 * Zassenhaus-core arena + bigint scalar scratch). */
size_t srmech_factor_integer_poly_ws_bound(size_t coeff_limbs, int deg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cw = (size_t)deg + 1u;
    size_t ccap = fiq_cap_for(cl, deg);
    size_t scap = 2u * ccap + 16u;
    size_t hdrw = (sizeof(srmech_bigint_t) + 3u) / 4u;
    size_t cells_c = 20u * cw + 3u * cw + (2u * cw + 2u) + (size_t)deg * cw;
    size_t big_words = cells_c * (hdrw + ccap + 2u)
                     + 2u * cw * (hdrw + scap + 2u)
                     + 8u * (hdrw + 2u * scap + 2u);
    size_t int_words = 3u * (size_t)deg + cw + 32u;
    size_t tail = srmech_poly_gcd_ws_bound(4u * cl + 8u, cw)
                + srmech_factor_squarefree_primitive_ws_bound(4u * cl + 8u, deg)
                + (64u * ccap + 8192u) * 4u;
    assert(deg >= 0);
    assert(big_words >= cells_c);
    return (big_words + int_words) * 4u + tail + 8192u;
}

/* Emit the sorted (factor, multiplicity) list into the caller's out arrays. */
static srmech_status_t fiq_emit(fiq_ctx_t *c, srmech_bigint_t *out_coeffs,
                                int *out_degs, int *out_mults, int *out_nfac)
{
    int j, i, off = 0;
    srmech_status_t st;
    assert(c != NULL && out_coeffs != NULL);
    assert(out_degs != NULL && out_mults != NULL && out_nfac != NULL);
    for (j = 0; j < c->fcount; j++) {
        int row = c->order[j], len = c->flen[row];
        out_degs[j] = len - 1;
        out_mults[j] = c->fmult[row];
        for (i = 0; i < len; i++) {
            st = fbi_copy(&out_coeffs[off],
                          &c->store[(size_t)row * (size_t)c->cw + (size_t)i]);
            if (st != SRMECH_OK) { return st; }
            off++;
        }
    }
    *out_nfac = c->fcount;
    return SRMECH_OK;
}

/* Public: factor an integer polynomial (coeffs low->high) into its IRREDUCIBLE
 * (factor, multiplicity) list over ℚ — the FULL factor_integer_poly composite
 * as ONE C call. out_coeffs holds the factors' coefficients CONCATENATED
 * low->high in the sorted (len, coeffs) order (>= 2*deg + 2 slots, each cap >=
 * srmech_factor_integer_poly_out_cap); out_degs/out_mults are per-factor
 * (>= deg slots). A nonzero CONSTANT input yields *out_nfac == 0. Returns
 * SRMECH_ERR_BAD_INPUT on the zero polynomial, SRMECH_ERR_OVERFLOW on arena /
 * degree overflow or an internal self-check mismatch (the Python wrapper then
 * falls back to the byte-identical pure path). */
srmech_status_t srmech_factor_integer_poly(
    const srmech_bigint_t *coeffs, int ncoeff, srmech_bigint_t *out_coeffs,
    int *out_degs, int *out_mults, int *out_nfac, int *out_capped,
    void *ws, size_t ws_len)
{
    fiq_ctx_t c;
    int deg, i, lp = 0, k;
    size_t cl = 1u, lb = 0u, lc = 0u, ld = 0u;
    srmech_status_t st;
    assert(coeffs != NULL && out_coeffs != NULL && out_nfac != NULL);
    assert(out_degs != NULL && out_mults != NULL && out_capped != NULL);
    if (ncoeff < 1) { return SRMECH_ERR_BAD_INPUT; }
    deg = bp_trim(coeffs, ncoeff) - 1;
    if (deg == 0 && srmech_bigint_is_zero(&coeffs[0])) {
        return SRMECH_ERR_BAD_INPUT;                   /* the zero polynomial */
    }
    *out_capped = 0;
    if (deg == 0) { *out_nfac = 0; return SRMECH_OK; } /* nonzero constant */
    if (deg > FAC_MAX_DEG) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0; i <= deg; i++) { if (coeffs[i].n > cl) { cl = coeffs[i].n; } }
    if (!fiq_carve(&c, ws, ws_len, cl, deg)) { return SRMECH_ERR_OVERFLOW; }
    st = fiq_prim_int(&c, coeffs, deg + 1, c.prim, &lp);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < lp; i++) {                         /* prim -> FIQ_P (dens 1) */
        st = fbi_copy(&c.qn[FIQ_P][i], &c.prim[i]);    if (st != SRMECH_OK) { return st; }
        st = fbi_seti(&c.qd[FIQ_P][i], 1);             if (st != SRMECH_OK) { return st; }
    }
    st = fiq_yun_setup(&c, (size_t)lp, &lb, &lc, &ld);
    if (st != SRMECH_OK) { return st; }
    k = 1;
    while (lb > 1u) {
        st = fiq_yun_step(&c, &lb, &lc, &ld, k);
        if (st != SRMECH_OK) { return st; }
        k++;
    }
    fiq_sort(&c);
    if (!c.capped) {
        st = fiq_selfcheck(&c, lp);
        if (st != SRMECH_OK) { return st; }
    }
    *out_capped = c.capped;
    return fiq_emit(&c, out_coeffs, out_degs, out_mults, out_nfac);
}
