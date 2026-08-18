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
/* Static arena: a bare-C host has no allocator, which is the point. ONE arena,
 * shared by both runner helpers — rc449 added run_dsl beside run_chain and the
 * two are never live at the same time, so a second 8 MiB block would be waste,
 * not safety. */
/* ⚠️ 8 MiB, and the size is a FINDING, not a guess. 1 MiB was the first
 * try and the 3-step chiral_dual chain returned SRMECH_ERR_OVERFLOW: the
 * arena formula is dominated by 4096 * chain_len, so a ~400-byte descriptor
 * already wants ~2.6 MiB. A firmware host must call
 * srmech_chain_run_arena_bytes and honour it — it cannot assume a chain is
 * small because its JSON is. Only a bare-C host surfaces this; the ctypes
 * tests allocate exactly what the formula asks for and never notice. */
static unsigned char ws[8u << 20];

static srmech_status_t run_chain(const char *chain, const char *ctx,
                                 char *out, size_t out_cap)
{
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

/* One DSL chain run into the same caller-owned arena (rc449, `#T1158`).
 *
 * ⚠️ WHY THIS HELPER EXISTS. Through rc448 this file drove srmech_chain_run ONLY
 * and touched srmech_dsl_chain_run — the surface the gh #1653 D1 finding was
 * actually filed against — exactly ZERO times. So the release that shipped the
 * ADR-0003 bare-C proof demonstrated that consumers can reach a host where the
 * Python-side rc447 fix does not exist, without ever running that host against
 * the defect. This puts the shipped proof on its own subject.
 *
 * `input` is an F1 value descriptor ({"k":"f","v":..}), the same seed shape
 * Chain._run_native marshals. */
static srmech_status_t run_dsl(const char *chain, const char *input,
                               char *out, size_t out_cap)
{
    size_t clen = strlen(chain);
    size_t ilen = strlen(input);
    size_t need = srmech_dsl_chain_run_arena_bytes(clen, ilen);
    size_t olen = 0u;
    srmech_status_t st;

    if (need > sizeof(ws)) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_dsl_chain_run(chain, clen, input, ilen, ws, need,
                              out, out_cap - 1u, &olen);
    if (st == SRMECH_OK) { out[olen] = '\0'; }
    return st;
}

/* The two seeds the stage rows below thread. best_rational_signed is the PRIMARY
 * witness rather than magnitude because magnitude on an INT seed returns NOT_IMPL
 * for unrelated carrier reasons — a dirty row whose clean twin does not run OK is
 * vacuous, so the twin is checked first everywhere. */
#define DSL_SEED_THIRD "{\"k\":\"f\",\"v\":0.3333333333333333}"
#define DSL_SEED_NEG   "{\"k\":\"f\",\"v\":-3.5}"

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

    /* ── rc449 (`#T1158`): STAGE KEY-SET REFUSAL on srmech_dsl_chain_run ──
     *
     * The gh #1653 D1 class: "an unknown op kwarg on a C-backed DSL leaf is
     * silently ignored". rc447 closed it at the PYTHON IR BUILDER, which is a
     * host that does not exist here — so through rc448 every dirty row below
     * returned SRMECH_OK and computed. The rc448 transcript is committed at
     * notes/_t1158_planted_red_rc449.txt, generated by the .c beside it.
     *
     * ⚠️ EVERY ROW ASSERTS A LITERAL STATUS VALUE, never `!= SRMECH_OK`. An
     * op-table miss and a missing REQUIRED key both return NOT_IMPL, and arena
     * exhaustion returns OVERFLOW; a gate that only asked "did it decline?"
     * would pass when any of those fired instead of the new validator — the
     * same blindness that let a divergence-only fix look complete. */

    /* B1/B2 — the clean twins, checked FIRST and by VALUE. B2 additionally
     * proves a LEGAL extra key is not merely tolerated but USED: the answer
     * MOVES (1,3) -> (0,1). Without that, "refuses unknown keys" is
     * indistinguishable from "refuses keys". */
    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"best_rational_signed\"}]}",
                 DSL_SEED_THIRD, out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": 1}") != NULL
          && strstr(out, "\"v\": 3}") != NULL,
          "DSL best_rational_signed(1/3) == (1, 3) — the seed reaches the leaf");

    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"best_rational_signed\",\"max_denominator\":2}]}",
                 DSL_SEED_THIRD, out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": 0}") != NULL
          && strstr(out, "\"v\": 1}") != NULL,
          "a LEGAL stage kwarg is accepted AND USED — (1,3) becomes (0,1)");

    /* B3 — the witness. One dropped letter from B2's key. rc448: OK and (1,3),
     * i.e. the constraint silently dropped and a DIFFERENT NUMBER returned. */
    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"best_rational_signed\",\"max_denominatr\":2}]}",
                 DSL_SEED_THIRD, out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a MISSPELT stage kwarg is BAD_INPUT (rc448 returned OK and (1,3))");

    /* B4 — a zero-kwarg leaf. leaf_magnitude never RECEIVES `stage`, so the
     * check cannot live inside the leaves; this row is what proves it lives at
     * dispatch. Clean twin first, or the dirty row proves nothing. */
    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"magnitude\"}]}",
                 DSL_SEED_NEG, out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "3.5") != NULL,
          "DSL magnitude(-3.5) == 3.5 — the zero-kwarg clean twin runs");

    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"magnitude\",\"bogus\":1}]}",
                 DSL_SEED_NEG, out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "an unknown kwarg on a leaf that never receives `stage` is BAD_INPUT");

    /* B5 — params[0] is the DATA CARRIER and is NOT a legal stage kwarg. A
     * params[*] rule passes every other row in this file and still ships the
     * measured 7/7 residual, so this row is the one that pins the index. */
    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"magnitude\",\"x\":5}]}",
                 DSL_SEED_NEG, out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "the DATA-carrier param name (params[0]) is refused as a stage kwarg");

    /* B6 — key sets are PER-OP, not one global vocabulary: `orientation` is a
     * real key one leaf over (reorient), and meaningless here. */
    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"pin_slot_at_zero\",\"orientation\":-1}]}",
                 DSL_SEED_NEG, out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a key legal on ANOTHER leaf is still BAD_INPUT here — per-op sets");

    /* B7/B8 — the DEFER channel, pinned BY VALUE. If either of these became
     * BAD_INPUT the fix would have been built by reclassifying a neighbour, and
     * if the refusal above returned NOT_IMPL it would be rc447's divergence-only
     * shape rebuilt inside C with only the constants moved. */
    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":"
                 "[{\"op\":\"definitely_not_an_op\"}]}",
                 DSL_SEED_THIRD, out, sizeof(out));
    check(st == SRMECH_ERR_NOT_IMPL,
          "an op outside the leaf table still DEFERS (NOT_IMPL), never refuses");

    st = run_dsl("{\"chain\":{\"name\":\"t\"},\"stage\":[{\"op\":\"reorient\"}]}",
                 DSL_SEED_NEG, out, sizeof(out));
    check(st == SRMECH_ERR_NOT_IMPL,
          "a MISSING REQUIRED kwarg still DEFERS — a disjoint defect class");

    /* ── DECLINES: a bare-C host must refuse, never guess ───────────────── */
    /* rc449: tightened from `!= SRMECH_OK` to the literal value. The loose form
     * is the §6.3 failure mode in miniature — it cannot tell this DEFER from the
     * BAD_INPUT the rows above earn, which is the whole distinction of this rc. */
    st = run_chain(
        "{\"name\":\"u\",\"steps\":[{\"class\":\"X\",\"op\":\"no_such_op\","
        "\"args\":{}}]}", "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_NOT_IMPL, "an op outside the table DECLINES (NOT_IMPL)");

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

    /* ── rc449 (`#T1158`): `args` KEY-SET REFUSAL on srmech_chain_run ─────
     *
     * The Surface-A twin. ⚠️ The legal set here is params[*], NOT the DSL
     * surface's params[1..]: operands arrive BY NAME inside `args` rather than
     * implicitly as a threaded value, so gcd{a,b} must run. A1/A3 are what stop
     * anyone "unifying" the two rules — under params[1..] they go red. */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"6\"") != NULL,
          "gcd(12,18) == 6 — every DECLARED param is a legal `args` key");

    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"bogus\":99}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "an unknown `args` key is BAD_INPUT (rc448 returned OK and 6)");

    /* A3/A4 — the SAME-ARITY CROSS-OP pair. Both are 3-key declarations naming
     * `n`; `n` is real and legal on mod_add and meaningless on gcd. Nothing that
     * keyed off arity, or off a global key vocabulary, could tell them apart. */
    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"mod_add\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"n\":5}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_OK,
          "mod_add{a,b,n} runs — a 3-key declaration where all three are legal");

    st = run_chain(
        "{\"name\":\"g\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"n\":5}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "the SAME key on gcd is BAD_INPUT — per-op sets, not arity");

    /* rc449: the rc318 rename that never reached C. cr_op_pi read the pre-rc318
     * spelling `precision_bits` for 131 rcs, so C honoured a key Python REFUSES
     * (TypeError) and ignored `precision`, the one Python accepts — a divergence
     * in BOTH directions on an op whose entire output is a number. */
    st = run_chain(
        "{\"name\":\"p\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\","
        "\"args\":{\"num_digits\":10,\"precision\":600}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "3.1415926535") != NULL,
          "pi_cascade_digits accepts `precision` — the name rc318 gave it");

    st = run_chain(
        "{\"name\":\"p\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\","
        "\"args\":{\"num_digits\":10,\"precision_bits\":600}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "`precision_bits` is BAD_INPUT — Python raises TypeError on it");

    printf("== bare-C chain-run: %d passed, %d failed ==\n", g_pass, g_fail);
    return (g_fail == 0) ? 0 : 1;
}
