/* siona_debruijn.c (F824) — a C-native de Bruijn WALK as a 3rd-party srmech PLUGIN.
 *
 * The de Bruijn fiber walk (F805/F813/F818): given a symbol-id sequence and a window k, build the
 * (k-1)-gram context -> successor map and WALK it from the seed to regenerate the whole sequence.
 * This is Siona's full-body recall op (F818) lifted out of pure-Python into native C, exposed via
 * srmech's `srmech.profiles` entry-point surface — NO edit to srmech core (the lean-srmech premise).
 *
 * Symbol-agnostic: it operates on int64 ids, so the SAME op serves text tokens, DNA bases (de Bruijn
 * graphs ARE the genome-assembly algorithm), or any discrete stream — hence "another process benefits".
 *
 * JPL-lean: static arrays (no malloc, Rule 3), open-addressing hash, functions <= 60 lines (Rule 4),
 * asserts (Rule 5), no goto (Rule 1). ABI v1. cc -shared -fPIC.
 */
#include <stdint.h>
#include <assert.h>

#define DB_MAXN 200000          /* max symbols in a sequence */
#define DB_HBITS 19
#define DB_HSZ (1 << DB_HBITS)  /* 524288 buckets; load < 0.4 at DB_MAXN */
#define DB_HMASK (DB_HSZ - 1)

static int64_t  g_ids[DB_MAXN];     /* the sequence being walked (set by db_load) */
static int64_t  g_n;                /* its length */
static int32_t  g_ctx_at[DB_HSZ];   /* bucket -> start index of a (k-1)-gram context, or -1 */
static int64_t  g_succ[DB_HSZ];     /* bucket -> the successor id for that context */

int siona_debruijn_abi_version(void) { return 1; }

/* FNV-1a over the (k-1) ids starting at position p (the context ids[p .. p+k-1)). */
static uint64_t db_hash(int64_t p, int64_t k) {
    uint64_t h = 1469598103934665603ULL;
    int64_t j;
    assert(k >= 2);
    for (j = 0; j < k - 1; j++) {
        uint64_t v = (uint64_t) g_ids[p + j];
        h = (h ^ v) * 1099511628211ULL;
    }
    return h;
}

/* Do the two (k-1)-grams at a and b compare equal? */
static int db_ctx_eq(int64_t a, int64_t b, int64_t k) {
    int64_t j;
    for (j = 0; j < k - 1; j++) {
        if (g_ids[a + j] != g_ids[b + j]) return 0;
    }
    return 1;
}

/* Build the context->successor map over g_ids at window k. Returns 0 ok, -1 on bad k. */
static int db_build(int64_t k) {
    int64_t i, b;
    assert(k >= 2);
    if (k < 2 || k > g_n) return -1;
    for (b = 0; b < DB_HSZ; b++) g_ctx_at[b] = -1;
    for (i = k - 1; i < g_n; i++) {
        int64_t cs = i - (k - 1);            /* context start */
        uint64_t h = db_hash(cs, k) & DB_HMASK;
        while (g_ctx_at[h] != -1) {
            if (db_ctx_eq((int64_t) g_ctx_at[h], cs, k)) break;  /* seen: keep first successor */
            h = (h + 1) & DB_HMASK;
        }
        if (g_ctx_at[h] == -1) { g_ctx_at[h] = (int32_t) cs; g_succ[h] = g_ids[i]; }
    }
    return 0;
}

/* Load a sequence (copy in). Returns 0 ok, -1 if too long. */
int siona_debruijn_load(const int64_t *ids, int64_t n) {
    int64_t i;
    if (n < 0 || n > DB_MAXN) return -1;
    for (i = 0; i < n; i++) g_ids[i] = ids[i];
    g_n = n;
    return 0;
}

/* Walk from the seed (first k-1 ids) regenerating the sequence into out[0..cap).
 * Returns the reconstructed length, or -1 on bad args / overflow. Caller compares to the original. */
int64_t siona_debruijn_walk(int64_t k, int64_t *out, int64_t cap) {
    int64_t len, steps, s;
    if (db_build(k) != 0 || cap < k - 1) return -1;
    for (len = 0; len < k - 1; len++) out[len] = g_ids[len];   /* the seed */
    for (steps = 0; steps < g_n - (k - 1); steps++) {
        uint64_t h;
        int64_t cs = len - (k - 1);
        /* hash the just-emitted context out[cs..len); reuse g_ids view via a tiny local copy */
        uint64_t hh = 1469598103934665603ULL;
        for (s = 0; s < k - 1; s++) hh = (hh ^ (uint64_t) out[cs + s]) * 1099511628211ULL;
        h = hh & DB_HMASK;
        while (g_ctx_at[h] != -1) {
            int eq = 1;
            for (s = 0; s < k - 1; s++)
                if (g_ids[g_ctx_at[h] + s] != out[cs + s]) { eq = 0; break; }
            if (eq) break;
            h = (h + 1) & DB_HMASK;
        }
        if (g_ctx_at[h] == -1) break;          /* no successor -> stop */
        if (len >= cap) return -1;
        out[len++] = g_succ[h];
    }
    return len;
}
