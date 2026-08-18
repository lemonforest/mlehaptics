/* _t1158_planted_red_rc449.c — the PLANTED-RED transcript for `#T1158`
 * (gh #1653 residual), captured against the UNFIXED rc448 tree.
 *
 * Per [[feedback_computational_provenance_discipline]] this is the generating
 * code for every "rc448 returns X" number in the rc449 PR body and in
 * docs/srmech/notes/_t1158_planted_red_rc449.txt.
 *
 * NO PYTHON. NO ctypes — the same host class as c/test/test_srmech_chain_run.c,
 * because the whole point of the finding is that the rc447 Python-side fix does
 * not exist here.
 *
 * Build (WSL2):
 *   cc -std=c17 -Iinclude -O2 notes/_t1158_planted_red_rc449.c \
 *      c/build/libsrmech.a -o /tmp/t1158_red && /tmp/t1158_red
 *
 * Reports the LITERAL status value for every row, never `!= SRMECH_OK` — a
 * status-blind probe cannot tell a refusal from a deferral, which is the exact
 * blindness `#T1158` exists to remove (rc449 spec §6.3).
 */
#include "srmech.h"

#include <stdio.h>
#include <string.h>

static unsigned char ws[8u << 20];

static const char *st_name(srmech_status_t s)
{
    switch (s) {
    case SRMECH_OK:             return "OK";
    case SRMECH_ERR_NULL_ARG:   return "NULL_ARG";
    case SRMECH_ERR_BAD_INPUT:  return "BAD_INPUT";
    case SRMECH_ERR_IO:         return "IO";
    case SRMECH_ERR_OVERFLOW:   return "OVERFLOW";
    case SRMECH_ERR_NOT_IMPL:   return "NOT_IMPL";
    default:                    return "OTHER";
    }
}

static void probe_dsl(const char *label, const char *chain, const char *input)
{
    char out[4096];
    size_t clen = strlen(chain), ilen = strlen(input), olen = 0u;
    size_t need = srmech_dsl_chain_run_arena_bytes(clen, ilen);
    srmech_status_t st;

    if (need > sizeof(ws)) { printf("  %-52s ARENA-TOO-SMALL\n", label); return; }
    st = srmech_dsl_chain_run(chain, clen, input, ilen, ws, need,
                              out, sizeof(out) - 1u, &olen);
    if (st == SRMECH_OK) { out[olen] = '\0'; printf("  %-52s %-9s %s\n", label, st_name(st), out); }
    else { printf("  %-52s %-9s -\n", label, st_name(st)); }
}

static void probe_chain(const char *label, const char *chain, const char *ctx)
{
    char out[4096];
    size_t clen = strlen(chain), xlen = strlen(ctx), olen = 0u;
    size_t need = srmech_chain_run_arena_bytes(clen, xlen);
    srmech_status_t st;

    if (need > sizeof(ws)) { printf("  %-52s ARENA-TOO-SMALL\n", label); return; }
    st = srmech_chain_run(chain, clen, ctx, xlen, ws, need,
                          out, sizeof(out) - 1u, &olen);
    if (st == SRMECH_OK) { out[olen] = '\0'; printf("  %-52s %-9s %s\n", label, st_name(st), out); }
    else { printf("  %-52s %-9s -\n", label, st_name(st)); }
}

#define SEED3 "{\"k\":\"f\",\"v\":0.3333333333333333}"
#define SEEDM "{\"k\":\"f\",\"v\":-3.5}"

int main(void)
{
    printf("srmech %s ABI %d\n", SRMECH_VERSION, SRMECH_ABI_VERSION);

    printf("\n== SURFACE B (srmech_dsl_chain_run) — leaf stage kwargs ==\n");
    probe_dsl("B1 best_rational_signed {}                 -> want OK (1,3)",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"best_rational_signed\"}]}", SEED3);
    probe_dsl("B2 + max_denominator:2  (LEGAL)            -> want OK (0,1)",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"best_rational_signed\",\"max_denominator\":2}]}", SEED3);
    probe_dsl("B3 + max_denominatr:2   (TYPO)             -> want BAD_INPUT",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"best_rational_signed\",\"max_denominatr\":2}]}", SEED3);
    probe_dsl("B4 magnitude {bogus:1}  (0-kwarg leaf)     -> want BAD_INPUT",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"magnitude\",\"bogus\":1}]}", SEEDM);
    probe_dsl("B4t magnitude {} (clean twin)              -> want OK 3.5",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"magnitude\"}]}", SEEDM);
    probe_dsl("B5 magnitude {x:5}      (params[0] name)   -> want BAD_INPUT",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"magnitude\",\"x\":5}]}", SEEDM);
    probe_dsl("B6 pin_slot_at_zero {orientation:-1}       -> want BAD_INPUT",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"pin_slot_at_zero\",\"orientation\":-1}]}", SEEDM);
    probe_dsl("B7 definitely_not_an_op {}  (DEFER chan.)  -> want NOT_IMPL",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"definitely_not_an_op\"}]}", SEED3);
    probe_dsl("B8 reorient {} (missing REQUIRED)          -> want NOT_IMPL",
              "{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"reorient\"}]}", SEEDM);

    printf("\n== SURFACE A (srmech_chain_run) — step `args` keys ==\n");
    probe_chain("A1 gcd{a,b} 12/18                          -> want OK 6",
                "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\",\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
                "{\"inputs\":{\"a\":12,\"b\":18}}");
    probe_chain("A2 gcd{a,b,bogus:99}                       -> want BAD_INPUT",
                "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\",\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"bogus\":99}}]}",
                "{\"inputs\":{\"a\":12,\"b\":18}}");
    probe_chain("A3 mod_add{a,b,n} (3 keys LEGAL here)      -> want OK",
                "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"mod_add\",\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"n\":5}}]}",
                "{\"inputs\":{\"a\":12,\"b\":18}}");
    probe_chain("A4 gcd{a,b,n:5}  (same key, WRONG op)      -> want BAD_INPUT",
                "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\",\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"n\":5}}]}",
                "{\"inputs\":{\"a\":12,\"b\":18}}");

    printf("\n== THE rc318 RENAME THAT NEVER REACHED C (pi_cascade_digits) ==\n");
    printf("   registry+python param is `precision`; cr_op_pi reads `precision_bits`\n");
    probe_chain("P1 pi{num_digits:10} baseline              -> OK",
                "{\"name\":\"p\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\",\"args\":{\"num_digits\":10}}]}",
                "{\"inputs\":{}}");
    /* THE WITNESS. num_digits=100, precision=64. Python HONOURS precision=64 and
     * degrades after ~19 places:
     *   3.1415926535897932370491360265507552185226813890039920806884...
     * At rc448 C never read the key at all, auto-scaled to 1024 bits, and returned
     * the CORRECT expansion. Same declaration, two co-equal projections, DIFFERENT
     * DIGITS OF PI — and nothing anywhere reported a problem.
     *
     * ⚠️ P2 IS *NOT* CLOSED BY rc449, AND MUST NOT BE READ AS CLOSED. rc449 fixes
     * the KEY NAME only (P3): cr_op_pi now reads `precision`, the name rc318 gave
     * it, so `precision_bits` is refused and `precision` is no longer discarded.
     * The VALUE semantics still diverge, because cr_op_pi clamps `prec < 512` up to
     * 512 while Python honours anything in [64, 32768]. MEASURED: the two agree
     * from ~precision 350 upward and disagree below it, so precision ∈ [64, ~350)
     * still returns different digits from the two projections. That is a
     * wrong-VALUE divergence, not a wrong-KEY one — a different defect class from
     * `#T1158`, deliberately left open rather than folded in, so this rc's refusal
     * claim is not entangled with a numeric-semantics change. FILED in
     * notes/_1653_gap_ledger.ndjson as pi_cascade_digits_precision_clamp. */
    probe_chain("P2 pi{num_digits:100,precision:64} LEGAL   -> read, but CLAMPED",
                "{\"name\":\"p\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\",\"args\":{\"num_digits\":100,\"precision\":64}}]}",
                "{\"inputs\":{}}");
    probe_chain("P3 pi{num_digits:100,precision_bits:64} C-only -> HONOURED?",
                "{\"name\":\"p\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\",\"args\":{\"num_digits\":100,\"precision_bits\":64}}]}",
                "{\"inputs\":{}}");
    return 0;
}
