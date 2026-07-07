/*
 * srmech_pi_archimedes.c — the projects-EVERY-step Pfaff-Archimedes two-mean
 * chiral-pair pi cascade on srmech_bigint (0.9.0rc157; the C-host peer of
 * pi_cascade_digits in srmech/amsc/rational.py).
 *
 * The COMPLEMENT of srmech_pi.c (the rotation-last Chudnovsky). Where
 * Chudnovsky keeps a bit-exact body and rotates ONCE, terminally, the
 * Archimedes chiral pair PROJECTS AT EVERY STEP: one integer square root per
 * iteration (the geometric mean). Pfaff's 1800 reformulation of Archimedes'
 * c.250 BCE polygon method is a pair of recurrent means that bracket pi over a
 * fixed-point unit `M = 1 << precision_bits` (every quantity divided by M):
 *
 *   b0 = 3*M                      inscribed  half-perimeter   (lower bound, up)
 *   a0 = isqrt(12*M*M) = 2*sqrt3*M  circumscribed perimeter   (upper bound, dn)
 *   a' = (2*a*b) // (a + b)       harmonic  mean (circumscribed, falls to pi)
 *   b' = isqrt(a' * b)            geometric mean (inscribed,    rises to pi)  <- the sqrt
 *   pi ~ (a + b) // 2            midpoint of the bracket [b, a]
 *
 * read out as "3." + D digits from  pi_int = (pi_scaled * 10^D) // M. The WHOLE
 * loop runs in C (NO per-step decimal round-trip), so a bare C host computes pi
 * with no Python and no O(digits^2) marshal churn. Byte-identical to the pure-
 * Python pi_cascade_digits oracle: the same fixed-point integers, the same
 * Python-FLOOR divmod/shr semantics, the same depth/precision.
 *
 * Early-exit: once a == b the pair is an EXACT fixed point — a' = (2*a^2)//(2a)
 * = a with zero remainder, and b' = isqrt(a^2) = a exactly — so every remaining
 * iteration Python would run is a no-op. Breaking there is a pure speedup, NOT
 * a result change (the chiral pair converges quadratically, so ~log2(bits)
 * iterations reach the fixed point far inside the linear depth bound).
 *
 * All limb buffers + the divmod/isqrt scratch are CARVED FROM THE CALLER ARENA
 * `ws` (no malloc, JPL Rule 3). Carrier-internal, like srmech_pi.c: NOT a
 * Rosetta ledger op (no ToolEntry, no count-test). Additive symbol -> ABI
 * unchanged.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative loop, helpers flat
 *   - Rule 2 (bounded loops)    : OK — depth bound + D + the isqrt/divmod guards
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror in
 *                                  BOTH asserts-live and -DNDEBUG (no assert-
 *                                  only locals; uint64 intermediates only)
 * No libm, no abs, no <complex.h>.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* A fixed roster of working bigints, all carved from the caller arena. */
typedef struct arch_ctx {
    srmech_bigint_t unit;    /* fixed-point unit M = 2^precision_bits         */
    srmech_bigint_t a;       /* circumscribed bound (falls to pi)             */
    srmech_bigint_t b;       /* inscribed bound     (rises to pi)             */
    srmech_bigint_t a_next;  /* harmonic mean this step                       */
    srmech_bigint_t tenpow;  /* 10^num_digits (the read-out scale)            */
    srmech_bigint_t t1;      /* big product scratch (~2*unit limbs)           */
    srmech_bigint_t t2;      /* big scratch / pi_scaled / pi_int              */
    srmech_bigint_t t0;      /* small-constant scratch                        */
    srmech_bigint_t rem;     /* divmod remainder sink                         */
    void  *scratch;          /* divmod/isqrt arena tail                       */
    size_t scratch_len;      /* its length in BYTES                           */
} arch_ctx_t;

/* ---- context init: carve every carrier from `ws` ------------------ */

/* Bump `count` uint32 limbs out of (*base + *cur); advance cur; NULL on
 * exhaustion. Mirrors bi_ws_take's contract (srmech_bigint.c). */
static uint32_t *arch_take(uint32_t *base, size_t words, size_t *cur,
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
static srmech_status_t arch_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = arch_take(base, words, cur, cap);
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

/* Per-carrier limb cap: the largest magnitude is 12*M*M (~2*M limbs); the
 * read-out product pi_scaled*10^D adds the decimal limbs, so 2*m + d + slack
 * covers every intermediate (m = M limbs, d = 10^D limbs). */
static uint32_t arch_carrier_limbs(uint32_t num_digits, uint32_t precision_bits)
{
    uint32_t m_limbs = precision_bits / 32u + 2u;
    uint32_t d_limbs = num_digits / 9u + 2u;
    uint32_t cap = 2u * m_limbs + d_limbs + 32u;
    assert(m_limbs >= 2u);
    assert(cap > 2u * m_limbs);              /* no uint32 wrap on sane inputs */
    return cap;
}

static srmech_status_t arch_ctx_init(arch_ctx_t *c, uint32_t num_digits,
                                     uint32_t precision_bits, void *ws,
                                     size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    uint32_t cap = arch_carrier_limbs(num_digits, precision_bits);
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    st |= arch_bind(&c->unit, base, words, &cur, cap);
    st |= arch_bind(&c->a, base, words, &cur, cap);
    st |= arch_bind(&c->b, base, words, &cur, cap);
    st |= arch_bind(&c->a_next, base, words, &cur, cap);
    st |= arch_bind(&c->tenpow, base, words, &cur, cap);
    st |= arch_bind(&c->t1, base, words, &cur, cap);
    st |= arch_bind(&c->t2, base, words, &cur, cap);
    st |= arch_bind(&c->t0, base, words, &cur, cap);
    st |= arch_bind(&c->rem, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + cur);          /* the arena tail */
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ---- exact-integer body: the two-mean chiral-pair bracket --------- */

/* unit = 1<<precision_bits, b0 = 3*unit, a0 = isqrt(12*unit^2) = 2*sqrt3*unit. */
static srmech_status_t arch_init_bounds(arch_ctx_t *c, uint32_t precision_bits)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(precision_bits > 0u);
    st = srmech_bigint_set_i64(&c->t0, 1);                 /* t0 = 1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shl_bits(&c->unit, &c->t0, precision_bits);  /* M = 1<<p */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t0, 3);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->b, &c->t0, &c->unit);       /* b0 = 3*M */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t0, 12);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t1, &c->t0, &c->unit);      /* t1 = 12*M */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t2, &c->t1, &c->unit);      /* t2 = 12*M^2 */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_isqrt(&c->a, &c->t2,              /* a0 = isqrt(12*M^2) */
                              c->scratch, c->scratch_len);
}

/* One chiral-pair step: a' = (2ab)//(a+b); b = isqrt(a'*b); a = a'. */
static srmech_status_t arch_step(arch_ctx_t *c)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(c->a.sign != 0 && c->b.sign != 0);       /* both bounds positive */
    st = srmech_bigint_mul(&c->t1, &c->a, &c->b);         /* t1 = a*b */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shl_bits(&c->t1, &c->t1, 1u);      /* t1 = 2*a*b */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&c->t2, &c->a, &c->b);         /* t2 = a + b */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->a_next, &c->rem, &c->t1, &c->t2,
                              c->scratch, c->scratch_len);  /* a' = 2ab//(a+b) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t1, &c->a_next, &c->b);    /* t1 = a'*b */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_isqrt(&c->b, &c->t1,               /* b = isqrt(a'*b) */
                             c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&c->a, &c->a_next);         /* a = a' */
}

/* The bit-exact body: iterate the pair to the fixed point (or depth bound). */
static srmech_status_t arch_converge(arch_ctx_t *c, uint32_t max_depth)
{
    uint32_t i;
    srmech_status_t st;
    assert(c != NULL);
    assert(max_depth >= 1u);
    for (i = 0u; i < max_depth; i++) {
        st = arch_step(c);
        if (st != SRMECH_OK) { return st; }
        if (srmech_bigint_cmp(&c->a, &c->b) == 0) {  /* exact fixed point: */
            break;                                    /* remaining iters no-op */
        }
    }
    return SRMECH_OK;
}

/* ---- read-out scale + projection to pi_int ------------------------ */

/* tenpow = 10^num_digits via repeated *10 (exact, == Python 10**num_digits). */
static srmech_status_t arch_make_tenpow(arch_ctx_t *c, uint32_t num_digits)
{
    srmech_bigint_t ten; uint32_t tl = 10u, j;
    srmech_status_t st;
    assert(c != NULL);
    assert(c->tenpow.cap > 0u);
    ten.sign = 1; ten.n = 1u; ten.cap = 1u; ten.limbs = &tl;
    st = srmech_bigint_set_i64(&c->tenpow, 1);           /* tenpow = 1 */
    if (st != SRMECH_OK) { return st; }
    for (j = 0u; j < num_digits; j++) {
        st = srmech_bigint_mul(&c->t1, &c->tenpow, &ten);  /* t1 = tenpow*10 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->tenpow, &c->t1);     /* tenpow = t1 */
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* pi_scaled = (a+b)//2; pi_int = (pi_scaled*10^D)//M -> left in c->t2. */
static srmech_status_t arch_project(arch_ctx_t *c, uint32_t num_digits)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(c->unit.sign != 0);                      /* divisor M never zero */
    st = srmech_bigint_add(&c->t1, &c->a, &c->b);         /* t1 = a + b */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shr_bits(&c->t2, &c->t1, 1u);      /* t2 = (a+b)//2 */
    if (st != SRMECH_OK) { return st; }
    st = arch_make_tenpow(c, num_digits);                /* tenpow = 10^D */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t1, &c->t2, &c->tenpow);  /* t1 = pi_scaled*10^D */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_divmod(&c->t2, &c->rem, &c->t1, &c->unit,
                                c->scratch, c->scratch_len);  /* t2 = pi_int */
}

/* ---- read-out: "3." + D digits (integer part must be 3) ----------- */

/* Render pi_int (= floor(pi*10^D), in c->t2) as "3." + D digits into out. */
static srmech_status_t arch_render(arch_ctx_t *c, uint32_t num_digits,
                                   char *out, size_t out_cap, size_t *out_len)
{
    size_t dec_len = 0u, i;
    char *digits = out + 2;                          /* leave "3." prefix */
    srmech_status_t st;
    assert(c != NULL && out != NULL && out_len != NULL);
    assert(out_cap >= (size_t)num_digits + 4u);
    st = srmech_bigint_to_dec(&c->t2, digits, out_cap - 2u, &dec_len,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    /* t2's decimal is "3" + the D fractional digits (integer part 3). */
    if (dec_len != (size_t)num_digits + 1u || digits[0] != '3') {
        return SRMECH_ERR_BAD_INPUT;                 /* depth/precision short */
    }
    out[0] = '3';
    out[1] = '.';
    for (i = 0u; i < (size_t)num_digits; i++) {       /* shift frac after "3." */
        out[2u + i] = digits[1u + i];
    }
    out[2u + (size_t)num_digits] = '\0';
    *out_len = 2u + (size_t)num_digits;
    return SRMECH_OK;
}

/* ---- public entry ------------------------------------------------- */

srmech_status_t srmech_pi_archimedes(uint32_t num_digits,
                                     uint32_t max_cascade_depth,
                                     uint32_t precision_bits,
                                     char *out, size_t out_cap, size_t *out_len,
                                     void *ws, size_t ws_len)
{
    arch_ctx_t c;
    srmech_status_t st;
    assert(out != NULL && out_len != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (out == NULL || out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (out_cap < (size_t)num_digits + 4u) { return SRMECH_ERR_OVERFLOW; }
    if (num_digits == 0u) {                           /* "3." */
        out[0] = '3'; out[1] = '.'; out[2] = '\0'; *out_len = 2u;
        return SRMECH_OK;
    }
    if (max_cascade_depth == 0u || precision_bits == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = arch_ctx_init(&c, num_digits, precision_bits, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = arch_init_bounds(&c, precision_bits);        /* unit, b0, a0 */
    if (st != SRMECH_OK) { return st; }
    st = arch_converge(&c, max_cascade_depth);        /* the chiral-pair loop */
    if (st != SRMECH_OK) { return st; }
    st = arch_project(&c, num_digits);                /* pi_scaled -> pi_int */
    if (st != SRMECH_OK) { return st; }
    return arch_render(&c, num_digits, out, out_cap, out_len);
}
