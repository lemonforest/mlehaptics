/*
 * srmech_pi.c — the ROTATION-LAST Chudnovsky π operator on srmech_bigint
 * (0.9.0rc19; the C-host peer of pi_chudnovsky_digits in
 * srmech/amsc/rational.py).
 *
 * The canonical srmech cascade shape: keep the body BIT-EXACT (integer
 * add / sub / mul / floor-divmod on the exact srmech_bigint substrate) and
 * perform the SINGLE continuous/frame projection ONCE, terminally. The
 * body is the Chudnovsky 1989 linear series accumulated as exact bigints:
 *
 *   L_0 = 13591409,  L_{k+1} = L_k + 545140134
 *   X_0 = 1,         X_{k+1} = X_k * (-262537412640768000)   (= 640320^3)
 *   M_0 = 1,         M_{k+1} = M_k * (12k+2)(12k+6)(12k+10) / (k+1)^3
 *   S   = Σ_{k=0}^{N-1}  (M_k * L_k) * one  //  X_k        (Python floor //)
 *
 * The ONE terminal "rotation" (the only continuous projection) is:
 *
 *   sqrt10005 = isqrt(10005 * one * one)        (= floor(√10005 · one))
 *   pi_scaled = (426880 * sqrt10005 * one) // S  (= floor(π · one))
 *
 * read out as "3." + D digits after dropping G = 16 guard digits. NO
 * float, NO libm, NO per-term square root — the opposite of the
 * Archimedes srmech polygon cascade, which projects EVERY step.
 *
 * Byte-identical to the Python oracle: every divmod/shr uses the
 * srmech_bigint PYTHON-FLOOR semantics, so a C-only host reproduces the
 * exact same decimal string. Linear term accumulation (NO binary
 * splitting) — JPL Rule 1 no-recursion clean. All limb buffers + the
 * divmod/isqrt scratch are CARVED FROM THE CALLER ARENA `ws` (no malloc),
 * sized via srmech_pi_chudnovsky_ws_bound.
 *
 * Carrier-internal, like srmech_qi.c: NOT a Rosetta ledger op (no
 * ToolEntry, no count-test). Additive symbols → ABI unchanged.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative series, helpers flat
 *   - Rule 2 (bounded loops)    : OK — loop bound is the term count N
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *                                  (no __int128, no VLA, uint64 intermediates)
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

#define PI_GUARD_DIGITS 16u
#define PI_X_STEP (-262537412640768000)   /* X_{k+1} = X_k * this (= -640320^3) */
#define PI_L0     13591409                 /* L_0                                */
#define PI_L_STEP 545140134                /* L_{k+1} = L_k + this               */
#define PI_C_LIN  426880                   /* 426880 · √10005 prefactor          */
#define PI_RADICAND 10005                  /* the lone irrational (one isqrt)    */

/* A fixed roster of working bigints, all carved from the caller arena. */
typedef struct pi_ctx {
    srmech_bigint_t one;   /* the fixed-point unit 10^P                     */
    srmech_bigint_t L;     /* L_k                                           */
    srmech_bigint_t X;     /* X_k (signed)                                  */
    srmech_bigint_t M;     /* M_k                                           */
    srmech_bigint_t S;     /* running sum (scaled by one)                   */
    srmech_bigint_t t0;    /* scratch carriers t0..t3                       */
    srmech_bigint_t t1;
    srmech_bigint_t t2;
    srmech_bigint_t t3;
    srmech_bigint_t rem;   /* divmod remainder sink (the bigint divmod needs *
                            * a real carrier even when the caller discards) */
    uint32_t limb_cap;     /* per-carrier limb capacity                     */
    void  *scratch;        /* divmod/isqrt arena tail                       */
    size_t scratch_len;    /* its length in BYTES                           */
} pi_ctx_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t pi_term_count(uint32_t num_digits);
static uint32_t pi_one_limbs(uint32_t p_digits);
static srmech_status_t pi_ctx_init(pi_ctx_t *c, uint32_t num_digits,
                                   void *ws, size_t ws_len);
static srmech_status_t pi_set_one(pi_ctx_t *c, uint32_t p_digits);
static srmech_status_t pi_mul3(pi_ctx_t *c, srmech_bigint_t *out,
                               const srmech_bigint_t *a,
                               const srmech_bigint_t *b);
static srmech_status_t pi_add_term(pi_ctx_t *c);
static srmech_status_t pi_advance(pi_ctx_t *c, uint32_t k);
static srmech_status_t pi_series(pi_ctx_t *c, uint32_t n_terms);
static srmech_status_t pi_rotation(pi_ctx_t *c, srmech_bigint_t *pi_scaled);
static srmech_status_t pi_render(pi_ctx_t *c, srmech_bigint_t *pi_scaled,
                                 uint32_t num_digits, char *out, size_t out_cap,
                                 size_t *out_len);

/* ---- bounds ------------------------------------------------------- */

/* ~14.18 digits per Chudnovsky term: N = D/14 + 2 (matches the oracle). */
static uint32_t pi_term_count(uint32_t num_digits)
{
    uint32_t n = num_digits / 14u + 2u;
    assert(n >= 2u);
    assert(n >= num_digits / 14u);
    return n;
}

/* Limbs to hold 10^p_digits: ceil(p_digits * log2(10) / 32) + 1. We use
 * the safe over-estimate p_digits/9 + 2 (a decimal '9-digits-per-limb'
 * bound, same shape as srmech_bigint_from_dec_bound). */
static uint32_t pi_one_limbs(uint32_t p_digits)
{
    uint32_t limbs = p_digits / 9u + 2u;
    assert(limbs >= 2u);
    assert(limbs > p_digits / 9u);
    return limbs;
}

size_t srmech_pi_chudnovsky_ws_bound(uint32_t num_digits)
{
    uint32_t p = num_digits + PI_GUARD_DIGITS;
    uint32_t one_limbs = pi_one_limbs(p);
    /* Per-carrier cap covers the largest magnitude (426880·√10005·one ~ 2P
     * digits): 2·one_limbs + 16 slack. */
    size_t cap = (size_t)one_limbs * 2u + 16u;
    size_t carriers = cap * 10u;          /* 10 carriers in pi_ctx */
    /* Scratch for the heaviest isqrt (radicand ~2·one_limbs): isqrt holds
     * 3·(a->n+2) carriers + an inner divmod arena; 16·one_limbs + 256 is a
     * safe envelope. Words → bytes. */
    size_t scratch = (size_t)one_limbs * 16u + 256u;
    size_t words = carriers + scratch;
    assert(one_limbs >= 2u);                 /* pi_one_limbs floor */
    assert(words >= carriers);               /* no size_t wrap */
    return words * sizeof(uint32_t);
}

/* ---- context init: carve every carrier from `ws` ------------------ */

/* Bump `count` uint32 limbs out of (*base + *cur); advance cur; NULL on
 * exhaustion. Mirrors bi_ws_take's contract (srmech_bigint.c). */
static uint32_t *pi_take(uint32_t *base, size_t words, size_t *cur,
                         size_t count)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (count > words || *cur > words - count) {
        return NULL;
    }
    p = base + *cur;
    *cur += count;
    return p;
}

/* Bind one carrier `b` to a fresh `cap`-limb slice of the arena. */
static srmech_status_t pi_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap)
{
    uint32_t *limbs = pi_take(base, words, cur, cap);
    assert(b != NULL);
    assert(cap > 0u);                        /* every carrier needs storage */
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t pi_ctx_init(pi_ctx_t *c, uint32_t num_digits,
                                   void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    uint32_t p = num_digits + PI_GUARD_DIGITS;
    uint32_t one_limbs = pi_one_limbs(p);
    uint32_t cap = one_limbs * 2u + 16u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    st |= pi_bind(&c->one, base, words, &cur, cap);
    st |= pi_bind(&c->L, base, words, &cur, cap);
    st |= pi_bind(&c->X, base, words, &cur, cap);
    st |= pi_bind(&c->M, base, words, &cur, cap);
    st |= pi_bind(&c->S, base, words, &cur, cap);
    st |= pi_bind(&c->t0, base, words, &cur, cap);
    st |= pi_bind(&c->t1, base, words, &cur, cap);
    st |= pi_bind(&c->t2, base, words, &cur, cap);
    st |= pi_bind(&c->t3, base, words, &cur, cap);
    st |= pi_bind(&c->rem, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + cur);          /* the arena tail */
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ---- exact-integer body helpers ----------------------------------- */

/* one = 10^p_digits, via repeated *10 from set_i64(1). */
static srmech_status_t pi_set_one(pi_ctx_t *c, uint32_t p_digits)
{
    srmech_bigint_t ten;
    uint32_t tl = 10u, i;
    srmech_status_t st;
    assert(c != NULL);
    assert(p_digits > 0u);
    ten.sign = 1; ten.n = 1u; ten.cap = 1u; ten.limbs = &tl;
    st = srmech_bigint_set_i64(&c->one, 1);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < p_digits; i++) {           /* one *= 10, p_digits times */
        st = pi_mul3(c, &c->one, &c->one, &ten); /* one = one * 10 via t0 */
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out = a * b, routed through scratch carrier t0 so out may alias a/b. */
static srmech_status_t pi_mul3(pi_ctx_t *c, srmech_bigint_t *out,
                               const srmech_bigint_t *a,
                               const srmech_bigint_t *b)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out != &c->t0);                       /* t0 is the mul scratch */
    st = srmech_bigint_mul(&c->t0, a, b);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out, &c->t0);
}

/* S += (M * L) * one // X (Python floor). t1=M*L, t1=t1*one, t2=t1//X. */
static srmech_status_t pi_add_term(pi_ctx_t *c)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(c->X.sign != 0);                      /* divisor X never zero */
    st = pi_mul3(c, &c->t1, &c->M, &c->L);       /* t1 = M * L */
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->t1, &c->t1, &c->one);    /* t1 = (M*L) * one */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t2, &c->rem, &c->t1, &c->X,
                              c->scratch, c->scratch_len);  /* t2 = t1 // X */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_add(&c->S, &c->S, &c->t2);         /* S += t2 */
}

/* Advance M, L, X for the next k: M = M*(12k+2)(12k+6)(12k+10)/(k+1)^3,
 * L += 545140134, X *= -262537412640768000. Exact divisions (assert r==0). */
static srmech_status_t pi_advance(pi_ctx_t *c, uint32_t k)
{
    srmech_bigint_t f; uint32_t fl[2];
    int64_t num = (int64_t)(12u * k + 2u) * (int64_t)(12u * k + 6u);
    int64_t den64;
    srmech_status_t st;
    assert(c != NULL);
    assert(12u * k + 10u >= 10u);                /* no uint wrap for sane k */
    f.sign = 1; f.n = 0u; f.cap = 2u; f.limbs = fl;
    st = srmech_bigint_set_i64(&c->t3, num);     /* t3 = (12k+2)(12k+6) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&f, (int64_t)(12u * k + 10u));
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->t3, &c->t3, &f);         /* t3 = ·(12k+10) */
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->M, &c->M, &c->t3);       /* M *= (12k+2)(12k+6)(12k+10) */
    if (st != SRMECH_OK) { return st; }
    den64 = (int64_t)(k + 1u) * (int64_t)(k + 1u) * (int64_t)(k + 1u);
    st = srmech_bigint_set_i64(&c->t3, den64);   /* t3 = (k+1)^3 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->M, &c->t2, &c->M, &c->t3,
                              c->scratch, c->scratch_len);  /* M //= (k+1)^3 */
    if (st != SRMECH_OK) { return st; }
    assert(srmech_bigint_is_zero(&c->t2));       /* exact: remainder 0 */
    st = srmech_bigint_set_i64(&f, PI_L_STEP);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&c->L, &c->L, &f);    /* L += 545140134 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&f, PI_X_STEP);
    if (st != SRMECH_OK) { return st; }
    return pi_mul3(c, &c->X, &c->X, &f);         /* X *= -262537412640768000 */
}

/* The bit-exact body: accumulate the N-term Chudnovsky series in S. */
static srmech_status_t pi_series(pi_ctx_t *c, uint32_t n_terms)
{
    uint32_t k;
    srmech_status_t st;
    assert(c != NULL);
    assert(n_terms >= 1u);
    st = srmech_bigint_set_i64(&c->L, PI_L0);    /* L_0 = 13591409 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->X, 1);        /* X_0 = 1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->M, 1);        /* M_0 = 1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->S, 0);        /* S = 0 */
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < n_terms; k++) {
        st = pi_add_term(c);                     /* S += term_k */
        if (st != SRMECH_OK) { return st; }
        st = pi_advance(c, k);                   /* M,L,X -> k+1 */
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- the ONE terminal rotation / projection ----------------------- */

/* pi_scaled = (426880 * isqrt(10005·one²) * one) // S = floor(π·one). */
static srmech_status_t pi_rotation(pi_ctx_t *c, srmech_bigint_t *pi_scaled)
{
    srmech_bigint_t k; uint32_t kl[2];
    srmech_status_t st;
    assert(c != NULL && pi_scaled != NULL);
    assert(c->S.sign != 0);                      /* divisor S never zero */
    st = srmech_bigint_set_i64(&c->t3, PI_RADICAND);  /* t3 = 10005 */
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->t3, &c->t3, &c->one);    /* t3 = 10005 · one */
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->t3, &c->t3, &c->one);    /* t3 = 10005 · one² */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_isqrt(&c->t1, &c->t3,
                             c->scratch, c->scratch_len);   /* t1 = √(…) */
    if (st != SRMECH_OK) { return st; }
    k.sign = 1; k.n = 0u; k.cap = 2u; k.limbs = kl;
    st = srmech_bigint_set_i64(&k, PI_C_LIN);    /* k = 426880 */
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->t1, &c->t1, &k);         /* t1 = 426880 · √ */
    if (st != SRMECH_OK) { return st; }
    st = pi_mul3(c, &c->t1, &c->t1, &c->one);    /* t1 = · one */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_divmod(pi_scaled, &c->rem, &c->t1, &c->S,
                               c->scratch, c->scratch_len); /* // S */
}

/* ---- read-out: "3." + D digits, dropping the G guard digits -------- */

/* Render pi_scaled (= floor(π·10^(D+G))) as "3." + D digits into out. */
static srmech_status_t pi_render(pi_ctx_t *c, srmech_bigint_t *pi_scaled,
                                 uint32_t num_digits, char *out, size_t out_cap,
                                 size_t *out_len)
{
    srmech_bigint_t g; uint32_t gl[2]; size_t dec_len = 0u, i;
    char *digits = out + 2;                       /* leave "3." prefix */
    srmech_status_t st;
    assert(c != NULL && pi_scaled != NULL && out != NULL && out_len != NULL);
    assert(out_cap >= (size_t)num_digits + 4u);
    g.sign = 1; g.n = 0u; g.cap = 2u; g.limbs = gl;
    st = srmech_bigint_set_i64(&g, 1);            /* g = 10^G */
    if (st != SRMECH_OK) { return st; }
    { uint32_t j; for (j = 0u; j < PI_GUARD_DIGITS; j++) {
        srmech_bigint_t ten; uint32_t tl = 10u;
        ten.sign = 1; ten.n = 1u; ten.cap = 1u; ten.limbs = &tl;
        st = pi_mul3(c, &g, &g, &ten); if (st != SRMECH_OK) { return st; }
    } }
    st = srmech_bigint_divmod(&c->t2, &c->rem, pi_scaled, &g,
                              c->scratch, c->scratch_len);  /* drop guard */
    if (st != SRMECH_OK) { return st; }
    /* t2 = floor(π·10^D); its decimal is "3" + the D fractional digits. */
    st = srmech_bigint_to_dec(&c->t2, digits, out_cap - 2u, &dec_len,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    if (dec_len != (size_t)num_digits + 1u || digits[0] != '3') {
        return SRMECH_ERR_BAD_INPUT;              /* integer part must be 3 */
    }
    out[0] = '3';
    out[1] = '.';
    for (i = 0u; i < (size_t)num_digits; i++) {   /* shift frac after "3." */
        out[2u + i] = digits[1u + i];
    }
    out[2u + (size_t)num_digits] = '\0';
    *out_len = 2u + (size_t)num_digits;
    return SRMECH_OK;
}

/* ---- public entry ------------------------------------------------- */

srmech_status_t srmech_pi_chudnovsky(uint32_t num_digits, char *out,
                                     size_t out_cap, size_t *out_len,
                                     void *ws, size_t ws_len)
{
    pi_ctx_t c;
    srmech_bigint_t pi_scaled; uint32_t p, n_terms;
    srmech_status_t st;
    assert(out != NULL && out_len != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (out == NULL || out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (out_cap < (size_t)num_digits + 4u) { return SRMECH_ERR_OVERFLOW; }
    if (num_digits == 0u) {                       /* "3." */
        out[0] = '3'; out[1] = '.'; out[2] = '\0'; *out_len = 2u;
        return SRMECH_OK;
    }
    st = pi_ctx_init(&c, num_digits, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    p = num_digits + PI_GUARD_DIGITS;
    n_terms = pi_term_count(num_digits);
    st = pi_set_one(&c, p);                       /* one = 10^P */
    if (st != SRMECH_OK) { return st; }
    st = pi_series(&c, n_terms);                  /* bit-exact body → S */
    if (st != SRMECH_OK) { return st; }
    pi_scaled = c.t3;                             /* reuse t3 as the result */
    st = pi_rotation(&c, &pi_scaled);             /* the ONE rotation */
    if (st != SRMECH_OK) { return st; }
    return pi_render(&c, &pi_scaled, num_digits, out, out_cap, out_len);
}
