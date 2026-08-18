/* test_srmech_chain_run.c — gh #1653: the ADR-0003 BARE-C HOST PROOF for
 * config-driven cascade execution.
 *
 * The issue's requirement is that "config-driven cascade execution must work in
 * C, not only Python". Every other gate for it is a pytest that reaches the
 * library through ctypes — which proves the library computes, but NOT that a
 * host without Python can drive a cascade from a descriptor. Those are different
 * claims, and only this file makes the second one.
 *
 * NO PYTHON. NO ctypes. NO malloc (JPL Rule 3 — every buffer is static or
 * caller-arena). The chain descriptors below are the same JSON a TOML cascade
 * descriptor compiles to, written as string literals exactly as a firmware host
 * would embed them.
 *
 * Standalone — build with the rest of test/. License: MIT.
 */
#include "srmech.h"

#include <stdio.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *desc)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", desc); }
    else      { g_fail++; printf("  FAIL  %s\n", desc); }
}

/* One chain run into a caller-owned arena. Returns the status; `out` receives
 * the NUL-terminated value descriptor. */
static srmech_status_t run_chain(const char *chain, const char *ctx,
                                 char *out, size_t out_cap)
{
    /* Static arena: a bare-C host has no allocator, which is the point. */
    /* ⚠️ 8 MiB, and the size is a FINDING, not a guess. 1 MiB was the first
     * try and the 3-step chiral_dual chain returned SRMECH_ERR_OVERFLOW: the
     * arena formula is dominated by 4096 * chain_len, so a ~400-byte descriptor
     * already wants ~2.6 MiB. A firmware host must call
     * srmech_chain_run_arena_bytes and honour it — it cannot assume a chain is
     * small because its JSON is. Only a bare-C host surfaces this; the ctypes
     * tests allocate exactly what the formula asks for and never notice. */
    static unsigned char ws[8u << 20];
    size_t clen = strlen(chain);
    size_t xlen = strlen(ctx);
    size_t need = srmech_chain_run_arena_bytes(clen, xlen);
    size_t olen = 0u;
    srmech_status_t st;

    if (need > sizeof(ws)) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_chain_run(chain, clen, ctx, xlen, ws, need,
                          out, out_cap - 1u, &olen);
    if (st == SRMECH_OK) { out[olen] = '\0'; }
    return st;
}

int main(void)
{
    char out[4096];
    srmech_status_t st;

    printf("== srmech_chain_run bare-C host proof (gh #1653) ==\n");

    /* ── the arena contract, before any chain runs ──────────────────────── */
    check(srmech_chain_run_arena_bytes(64u, 16u) > 0u,
          "arena_bytes reports a size a host can allocate up-front");

    /* ── Class I: a cyclic chain, exact integer arithmetic ──────────────── */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_OK, "Class-I cyclic chain runs with no Python present");
    check(st == SRMECH_OK && strstr(out, "\"v\": \"6\"") != NULL,
          "gcd(12,18) == 6 from a descriptor a firmware host embedded");

    /* ⚠️ THE BIGINT CARRIER IS UNREACHABLE FROM A JSON LITERAL, and this is the
     * test that establishes it. rc447 put gcd / mod_add / mod_mul / mod_pow on
     * the full bigint carrier so no operand is narrowed — but an operand larger
     * than int64 cannot ARRIVE, because srmech_json_parse returns
     * SRMECH_ERR_LIMIT for such a literal (a deliberate rc404 status, distinct
     * from OVERFLOW precisely because no arena can relieve it).
     *
     * So the bigint width is real but only reachable by a COMPUTED value — a
     * @step[N].output carrying a big result — which no shipped descriptor
     * currently produces. Asserted as a DECLINE so the boundary is recorded
     * rather than assumed, and so the day the parser widens, this fails and
     * the claim gets re-examined. */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":1180591620717411303424,\"b\":18}}",
        out, sizeof(out));
    check(st == SRMECH_ERR_LIMIT,
          "an out-of-int64 LITERAL is ERR_LIMIT at the parser (deliberate: a "
          "clamped value would be a silent wrong answer)");

    /* ...and the SAME operands DO reach the bigint carrier as decimal STRINGS —
     * the rc176 transport srmech_carrier_marshal.c has used since it shipped.
     * The chain runner was the one numeric surface not honouring it, which is
     * what made the bigint widening unreachable from a descriptor. */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":\"1180591620717411303424\",\"b\":\"18\"}}",
        out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"2\"") != NULL,
          "gcd(2^70,18) == 2 via the decimal-STRING transport — the carrier is "
          "bigint, not a machine word");

    /* A result WIDER than int64: proves the whole path is arbitrary-precision,
     * not just the operands. gcd(2^200, 2^100) == 2^100. */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":\"1606938044258990275541962092341162602522202993782792835301376\","
        "\"b\":\"1267650600228229401496703205376\"}}", out, sizeof(out));
    check(st == SRMECH_OK &&
          strstr(out, "1267650600228229401496703205376") != NULL,
          "gcd(2^200,2^100) == 2^100 — a RESULT wider than int64 marshals back");

    /* The control: a genuine string must NOT be retyped as a number. */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":\"notanumber\",\"b\":\"18\"}}", out, sizeof(out));
    check(st != SRMECH_OK,
          "a non-numeric string is NOT coerced — the widening is at the point "
          "of USE, so `combine=\"4\"` stays a mode name");

    /* ── the FOLD step form (rc446) ─────────────────────────────────────── */
    st = run_chain(
        "{\"name\":\"n\",\"steps\":[{\"fold_class\":\"C\","
        "\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
        "\"fold_init\":1,\"over\":\"@input.orientations\"}]}",
        "{\"inputs\":{\"orientations\":[1,-1,1]}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"-1\"") != NULL,
          "net_chirality fold == -1 (the Surface-A fold form, in C)");

    /* The ABSORBING zero — Class-K pin-slot, not a sign multiply. */
    st = run_chain(
        "{\"name\":\"n\",\"steps\":[{\"fold_class\":\"C\","
        "\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
        "\"fold_init\":1,\"over\":\"@input.orientations\"}]}",
        "{\"inputs\":{\"orientations\":[0,-1]}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"0\"") != NULL,
          "the zero ABSORBS — a reorient fold would give -1 here");

    /* ── CR_DBL + the list descriptor (rc447) ───────────────────────────── */
    st = run_chain(
        "{\"name\":\"c\",\"steps\":["
        "{\"class\":\"C\",\"op\":\"srmech.cascade.atoms.chiral_flip\","
        "\"args\":{\"seq\":\"@input.x\"}},"
        "{\"class\":\"L\",\"op\":\"srmech.cascade.composites.autocorrelation\","
        "\"args\":{\"x\":\"@step[0].output\"}},"
        "{\"class\":\"C\",\"op\":\"srmech.cascade.atoms.chiral_flip\","
        "\"args\":{\"seq\":\"@step[1].output\"}}]}",
        "{\"inputs\":{\"x\":[1.0,2.0,3.0]}}", out, sizeof(out));
    check(st == SRMECH_OK, "chiral_dual: a 3-step real-valued chain runs in C");
    check(st == SRMECH_OK && strstr(out, "\"k\": \"l\"") != NULL,
          "the result marshals as the LIST descriptor kind");
    check(st == SRMECH_OK && strstr(out, "14") != NULL,
          "chiral_dual([1,2,3]) carries the expected energy term");

    /* ── the INDEXED step ref + Class-K pin-slot (rc447) ────────────────── */
    st = run_chain(
        "{\"name\":\"m\",\"steps\":["
        "{\"class\":\"K\",\"op\":\"srmech.cascade.atoms.pin_slot_at_zero\","
        "\"args\":{\"x\":\"@input.x\"}},"
        "{\"class\":\"C\",\"op\":\"srmech.cascade.atoms.reorient\","
        "\"args\":{\"value\":\"@step[0].output[1]\",\"orientation\":1}}]}",
        "{\"inputs\":{\"x\":-3.5}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "3.5") != NULL,
          "magnitude(-3.5) == 3.5 via @step[0].output[1] element indexing");

    /* ── DECLINES: a bare-C host must refuse, never guess ───────────────── */
    st = run_chain(
        "{\"name\":\"u\",\"steps\":[{\"class\":\"X\",\"op\":\"no_such_op\","
        "\"args\":{}}]}", "{\"inputs\":{}}", out, sizeof(out));
    check(st != SRMECH_OK, "an op outside the table DECLINES");

    st = run_chain(
        "{\"name\":\"m\",\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"i\","
        "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
        "\"args\":{\"a\":\"@idx.i\",\"b\":0,\"n\":2}}]}]}",
        "{\"inputs\":{\"xs\":[1,2,3]}}", out, sizeof(out));
    check(st == SRMECH_ERR_NOT_IMPL,
          "the MAP form is NOT_IMPL — recognised but unimplemented");

    st = run_chain(
        "{\"name\":\"x\",\"steps\":[{\"fold_op\":\"orientation_compose\","
        "\"fold_init\":1,\"over\":\"@input.xs\",\"op\":\"gcd\",\"args\":{}}]}",
        "{\"inputs\":{\"xs\":[1]}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a MIXED step is BAD_INPUT — malformed, distinct from unimplemented");

    st = run_chain(
        "{\"name\":\"n\",\"steps\":[{\"class\":\"K\","
        "\"op\":\"srmech.cascade.atoms.pin_slot_at_zero\","
        "\"args\":{\"x\":\"@input.x\"}}]}",
        "{\"inputs\":{\"x\":NaN}}", out, sizeof(out));
    check(st != SRMECH_OK,
          "a non-finite literal is refused — RFC 8259 has no such token");

    printf("== bare-C chain-run: %d passed, %d failed ==\n", g_pass, g_fail);
    return (g_fail == 0) ? 0 : 1;
}
