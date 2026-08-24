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

    /* ── the REQUIRED CHAIN HEADER (rc452, gh #1653 finding (b)) ──────────
     * srmech_chain_run's declared input is "the FULL chain object
     * {name,summary,returns,on_error?,steps}", and Python's parse_chain_spec
     * refuses a dict missing any of the three header keys — yet through
     * rc452 Phase 3 this runner ACCEPTED and RAN such chains (every literal
     * in this file carried name+steps only, which is how the divergence
     * stayed invisible). Co-equal projections agree on what they REFUSE. */
    st = run_chain(
        "{\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\","
        "\"op\":\"gcd\",\"args\":{\"a\":12,\"b\":18}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a chain missing `name` is BAD_INPUT — parse_chain_spec's "
          "required-key rule, now enforced by the runner too");
    st = run_chain(
        "{\"name\":\"g\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\","
        "\"op\":\"gcd\",\"args\":{\"a\":12,\"b\":18}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a chain missing `summary` is BAD_INPUT (this exact shape RAN "
          "through rc452 Phase 3)");
    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"steps\":[{\"class\":\"I\","
        "\"op\":\"gcd\",\"args\":{\"a\":12,\"b\":18}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a chain missing `returns` is BAD_INPUT — the full parse-layer "
          "key set, not a two-of-three compromise");

    /* ── Class I: a cyclic chain, exact integer arithmetic ──────────────── */
    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
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
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
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
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":\"1180591620717411303424\",\"b\":\"18\"}}",
        out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"2\"") != NULL,
          "gcd(2^70,18) == 2 via the decimal-STRING transport — the carrier is "
          "bigint, not a machine word");

    /* A result WIDER than int64: proves the whole path is arbitrary-precision,
     * not just the operands. gcd(2^200, 2^100) == 2^100. */
    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":\"1606938044258990275541962092341162602522202993782792835301376\","
        "\"b\":\"1267650600228229401496703205376\"}}", out, sizeof(out));
    check(st == SRMECH_OK &&
          strstr(out, "1267650600228229401496703205376") != NULL,
          "gcd(2^200,2^100) == 2^100 — a RESULT wider than int64 marshals back");

    /* The control: a genuine string must NOT be retyped as a number. */
    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":\"notanumber\",\"b\":\"18\"}}", out, sizeof(out));
    check(st != SRMECH_OK,
          "a non-numeric string is NOT coerced — the widening is at the point "
          "of USE, so `combine=\"4\"` stays a mode name");

    /* ── the FOLD step form (rc446) ─────────────────────────────────────── */
    st = run_chain(
        "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"fold_class\":\"C\","
        "\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
        "\"fold_init\":1,\"over\":\"@input.orientations\"}]}",
        "{\"inputs\":{\"orientations\":[1,-1,1]}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"-1\"") != NULL,
          "net_chirality fold == -1 (the Surface-A fold form, in C)");

    /* The ABSORBING zero — Class-K pin-slot, not a sign multiply. */
    st = run_chain(
        "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"fold_class\":\"C\","
        "\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
        "\"fold_init\":1,\"over\":\"@input.orientations\"}]}",
        "{\"inputs\":{\"orientations\":[0,-1]}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"0\"") != NULL,
          "the zero ABSORBS — a reorient fold would give -1 here");

    /* ── CR_DBL + the list descriptor (rc447) ───────────────────────────── */
    st = run_chain(
        "{\"name\":\"c\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":["
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
        "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":["
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
        "{\"name\":\"u\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"X\",\"op\":\"no_such_op\","
        "\"args\":{}}]}", "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_NOT_IMPL, "an op outside the table DECLINES (NOT_IMPL)");

    /* ⚠️ THIS CHECK INVERTED AT rc452 (`#T1166`). It asserted the MAP form was
     * NOT_IMPL — "recognised but unimplemented" — which was true from rc446
     * until this rc and is now false: `cr_drive` implements it. The assertion
     * FIRED when the map landed, which is the gate doing its job (a stale
     * "still unimplemented" claim that kept passing would be the worse
     * outcome), so the premise moves rather than the check being deleted.
     * It now pins the VALUE: [i mod 2 for i in 0..2] over a 3-element sequence
     * is [0, 1, 0]. */
    st = run_chain(
        "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"i\","
        "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
        "\"args\":{\"a\":\"@idx.i\",\"b\":0,\"n\":2}}]}]}",
        "{\"inputs\":{\"xs\":[1,2,3]}}", out, sizeof(out));
    check(st == SRMECH_OK &&
          strcmp(out,
                 "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"0\"}, "
                 "{\"k\": \"i\", \"v\": \"1\"}, "
                 "{\"k\": \"i\", \"v\": \"0\"}]}") == 0,
          "the MAP form RUNS and returns [i mod 2 for i in 0..2] = [0, 1, 0]");

    st = run_chain(
        "{\"name\":\"x\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"fold_op\":\"orientation_compose\","
        "\"fold_init\":1,\"over\":\"@input.xs\",\"op\":\"gcd\",\"args\":{}}]}",
        "{\"inputs\":{\"xs\":[1]}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "a MIXED step is BAD_INPUT — malformed, distinct from unimplemented");

    st = run_chain(
        "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"K\","
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
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\"}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"6\"") != NULL,
          "gcd(12,18) == 6 — every DECLARED param is a legal `args` key");

    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"bogus\":99}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "an unknown `args` key is BAD_INPUT (rc448 returned OK and 6)");

    /* A3/A4 — the SAME-ARITY CROSS-OP pair. Both are 3-key declarations naming
     * `n`; `n` is real and legal on mod_add and meaningless on gcd. Nothing that
     * keyed off arity, or off a global key vocabulary, could tell them apart. */
    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"mod_add\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"n\":5}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_OK,
          "mod_add{a,b,n} runs — a 3-key declaration where all three are legal");

    st = run_chain(
        "{\"name\":\"g\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"I\",\"op\":\"gcd\","
        "\"args\":{\"a\":\"@input.a\",\"b\":\"@input.b\",\"n\":5}}]}",
        "{\"inputs\":{\"a\":12,\"b\":18}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "the SAME key on gcd is BAD_INPUT — per-op sets, not arity");

    /* rc449: the rc318 rename that never reached C. cr_op_pi read the pre-rc318
     * spelling `precision_bits` for 131 rcs, so C honoured a key Python REFUSES
     * (TypeError) and ignored `precision`, the one Python accepts — a divergence
     * in BOTH directions on an op whose entire output is a number. */
    st = run_chain(
        "{\"name\":\"p\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\","
        "\"args\":{\"num_digits\":10,\"precision\":600}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "3.1415926535") != NULL,
          "pi_cascade_digits accepts `precision` — the name rc318 gave it");

    st = run_chain(
        "{\"name\":\"p\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"N\",\"op\":\"pi_cascade_digits\","
        "\"args\":{\"num_digits\":10,\"precision_bits\":600}}]}",
        "{\"inputs\":{}}", out, sizeof(out));
    check(st == SRMECH_ERR_BAD_INPUT,
          "`precision_bits` is BAD_INPUT — Python raises TypeError on it");

    /* ── rc451 (`#T1164`, gh #1653 item 4): THE SIX-STEP best_rational_signed
     * CHAIN, FROM ITS DESCRIPTOR, WITH NO PYTHON.
     *
     * This is the ADR-0003 claim for this rc and it is the whole point of the
     * slice: a firmware host embeds the descriptor and gets the answer by
     * EXECUTING ITS SIX DECLARED STEPS — Class K pin-slot, Class K dead-band,
     * Class N banker's scale-round, Class N best_rational, Class C reorient,
     * Class B pair. The fused srmech_cascade_best_rational_signed_f64 exists
     * and would answer identically; it is deliberately not what runs here, and
     * the interpreter TU is pinned to reference no such symbol.
     *
     * The JSON below is exactly what
     * cascade_catalog/best_rational_signed.toml's [[cascade.chain]] compiles
     * to, transcribed rather than described. */
#define BRS_CHAIN \
    "{\"name\":\"brs\",\"summary\":\"s\",\"returns\":\"r\"," \
    "\"chain_schema_version\":2,\"steps\":[" \
    "{\"class\":\"K\",\"op\":\"srmech.cascade.pin_slot_at_zero\"," \
    "\"args\":{\"x\":\"@input.x\"}}," \
    "{\"class\":\"K\",\"op\":\"srmech.cascade.dead_band\"," \
    "\"args\":{\"value\":\"@step[0].output[1]\",\"band\":1e-12}}," \
    "{\"class\":\"N\",\"op\":\"scale_round_half_even\"," \
    "\"args\":{\"value\":\"@step[1].output\",\"scale\":\"@input.fine_scale\"}}," \
    "{\"class\":\"N\",\"op\":\"best_rational\",\"args\":{" \
    "\"numerator\":\"@step[2].output\"," \
    "\"denominator\":\"@input.fine_scale\"," \
    "\"max_denominator\":\"@input.max_denominator\"}}," \
    "{\"class\":\"C\",\"op\":\"srmech.cascade.reorient\"," \
    "\"args\":{\"value\":\"@step[3].output[0]\"," \
    "\"orientation\":\"@step[0].output[0]\"}}," \
    "{\"class\":\"B\",\"op\":\"srmech.cascade.pair\"," \
    "\"args\":{\"first\":\"@step[4].output\"," \
    "\"second\":\"@step[3].output[1]\"}}]}"

    st = run_chain(BRS_CHAIN,
                   "{\"inputs\":{\"x\":3.14159265358979,"
                   "\"fine_scale\":1000000,\"max_denominator\":100}}",
                   out, sizeof(out));
    check(st == SRMECH_OK,
          "the SIX-step best_rational_signed chain runs with no Python present");
    /* THE KIND IS ASSERTED AS A STRING, not inferred from the value. A wire
     * spelling this pair as the pre-existing rational kind "q" would carry the
     * same two integers and reconstruct to the same Python tuple — so it would
     * satisfy every value-level check in the tree while leaving the tuple kind
     * unshipped. Only the letter can refuse it. */
    check(st == SRMECH_OK && strstr(out, "\"k\": \"t\"") != NULL,
          "the final value crosses as the rc451 TUPLE kind {\"k\":\"t\"}, "
          "not as a list and not as a rational");
    check(st == SRMECH_OK && strstr(out, "\"v\": \"22\"") != NULL
                          && strstr(out, "\"v\": \"7\"") != NULL,
          "pi -> (22, 7): the Class-N convergent, INTEGER-carried through the "
          "Class-C tail (a double there would print 22.0 and is the rc451 "
          "reorient type-preservation fix)");

    st = run_chain(BRS_CHAIN,
                   "{\"inputs\":{\"x\":-3.14159265358979,"
                   "\"fine_scale\":1000000,\"max_denominator\":100}}",
                   out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"v\": \"-22\"") != NULL,
          "-pi -> (-22, 7): the Class-C re-application, from the descriptor");

    /* THE LEMMA THE FUSED SYMBOL SHORT-CIRCUITS AND THE FINE PATH EXERCISES.
     * The coarse op early-returns (0,1) on a sub-dead-band magnitude, so its
     * zero NEVER flows through best_rational / reorient / pair. The declared
     * chain has no such shortcut: 0 must flow through
     * best_rational(0, d, m) == (0, 1) and out through the Class-C and Class-B
     * steps. That is a TESTED path here rather than a vacuous one. */
    st = run_chain(BRS_CHAIN,
                   "{\"inputs\":{\"x\":5e-13,"
                   "\"fine_scale\":10000000000000,"
                   "\"max_denominator\":1000000000000}}",
                   out, sizeof(out));
    check(st == SRMECH_OK && strstr(out, "\"k\": \"t\"") != NULL
                          && strstr(out, "\"v\": \"0\"") != NULL
                          && strstr(out, "\"v\": \"1\"") != NULL,
          "a sub-dead-band magnitude flows a ZERO through steps 2-5 to (0, 1) "
          "— the branch the fused symbol never walks");

    /* ── rc451: the two new OP-GRANULAR exports, called directly. A bare-C host
     * gets the STEPS, not only the whole chain. */
    {
        double db = 1.0;
        int64_t sr = 0;
        check(srmech_cascade_dead_band_f64(-1.0, 1e-12, &db) == SRMECH_OK
              && db == 0.0 && (1.0 / db) < 0.0,
              "srmech_cascade_dead_band_f64(-1.0) is NEGATIVE zero — the "
              "value's own zero, never a literal 0.0");
        check(srmech_cascade_dead_band_f64(2.5, 1e-12, &db) == SRMECH_OK
              && db == 2.5,
              "dead_band passes a magnitude at or above the band unchanged");
        check(srmech_cascade_scale_round_half_even_i64(2.5, 1, &sr)
              == SRMECH_OK && sr == 2,
              "scale_round_half_even ties to EVEN: 2.5 -> 2, not 3");
        check(srmech_cascade_scale_round_half_even_i64(-1.5, 1, &sr)
              == SRMECH_OK && sr == -2,
              "and it is sign-symmetric via Class-K pin-slot + Class-C "
              "reorient: -1.5 -> -2, with no abs() anywhere");
        check(srmech_cascade_scale_round_half_even_i64(1e30, 1000000, &sr)
              == SRMECH_ERR_BAD_INPUT,
              "a product past 2^63 DECLINES rather than clamping — Python "
              "answers there with a bignum, so C must refuse, not narrow");
    }

    /* ─────────────────────────────────────────────────────────────────
     * rc452 (`#T1166`) — THE DEPTH-BOUNDED VALUE SPINE, on a bare-C host.
     *
     * ⚠️ WHY THESE ASSERT LITERAL WIRE BYTES. Every other check of this
     * capability compares C against Python — and `resolve_chain` runs the
     * NATIVE path first and returns `_reconstruct_value`'s output, so both
     * "projections" pass through ONE reader. Measured this arc: a planted
     * reader collapse left the classifier reporting 51/51 BYTE_IDENTICAL
     * while 32 of 39 rows rebuilt as the wrong type. A C-vs-Python compare
     * cannot see a defect both sides route through, at any strictness. A
     * hand-written expected descriptor can, and there is no Python in this
     * process at all.
     *
     * Nesting rides the EXISTING `l` kind — Python's reader has always been
     * recursive — so this widens a capability, not a discriminator, and adds
     * no kind letter.
     * ───────────────────────────────────────────────────────────────── */
    {
        static const char nest_chain[] =
            "{\"name\":\"p\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"B\",\"op\":\"pair\","
            "\"args\":{\"first\":\"@input.a\",\"second\":\"@input.b\"}}]}";

        st = run_chain(nest_chain,
                       "{\"inputs\":{\"a\":[[1,2],[3]],\"b\":5}}",
                       out, sizeof(out));
        /* ⚠️ THE SEPARATORS CARRY SPACES — `", "` and `": "`. That is the
         * shipped writer's canonical form, and it is asserted here in FULL
         * rather than by strstr on a fragment, so the whole descriptor
         * (nesting, order, key set, every scalar) is pinned rather than one
         * substring of it. The compact spelling was written first and this
         * check caught it, which is the difference between a strcmp and the
         * strstr the older cases in this file use. */
        check(st == SRMECH_OK &&
              strcmp(out,
                     "{\"k\": \"t\", \"v\": [{\"k\": \"l\", \"v\": ["
                     "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"1\"}, "
                     "{\"k\": \"i\", \"v\": \"2\"}]}, "
                     "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"3\"}]}]}, "
                     "{\"k\": \"i\", \"v\": \"5\"}]}") == 0,
              "a depth-2 nested list INGESTS and MARSHALS to depth-3 wire "
              "bytes, compared against a literal descriptor with no Python "
              "reader in the loop");

        /* BOOL ingest. Through rc451 cr_json_scalar returned NULL on
         * SRMECH_JSON_BOOL, so BOTH DFT chains deferred WHOLE on their
         * `inverse: false` argument — a gap NO listed gate named, attributed
         * instead to the op table and carrier width (both also true, and
         * neither of which could have released the chain). */
        st = run_chain(nest_chain,
                       "{\"inputs\":{\"a\":true,\"b\":false}}",
                       out, sizeof(out));
        check(st == SRMECH_OK &&
              strcmp(out,
                     "{\"k\": \"t\", \"v\": [{\"k\": \"i\", \"v\": \"1\"}, "
                     "{\"k\": \"i\", \"v\": \"0\"}]}") == 0,
              "a JSON bool INGESTS as 0/1 — matching Python, where bool IS an "
              "int subclass, so this is the same coercion and not a C-side "
              "convention. No output kind is added: measured over all 21 "
              "descriptors, ZERO declare a bool return");

        /* A nested LITERAL arg, not a reference — the other ingest path
         * (cr_resolve_elem), which had its own flat-only limit. */
        st = run_chain(
            "{\"name\":\"p\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"class\":\"B\",\"op\":\"pair\","
            "\"args\":{\"first\":[[1.5,2.5],[3.5]],\"second\":0}}]}",
            "{\"inputs\":{}}", out, sizeof(out));
        check(st == SRMECH_OK &&
              strcmp(out,
                     "{\"k\": \"t\", \"v\": [{\"k\": \"l\", \"v\": ["
                     "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 1.5}, "
                     "{\"k\": \"f\", \"v\": 2.5}]}, "
                     "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 3.5}]}]}, "
                     "{\"k\": \"i\", \"v\": \"0\"}]}") == 0,
              "a nested ARRAY LITERAL in args ingests too, not only a nested "
              "@input reference");

        /* NEGATIVE CONTROL. The cap must DECLINE, never truncate — a
         * truncating walker would return a well-formed descriptor holding
         * fewer levels than the input had, which is a silent wrong answer of
         * exactly the class this arc exists to close. */
        st = run_chain(nest_chain,
                       "{\"inputs\":{\"a\":[[[[[1]]]]],\"b\":0}}",
                       out, sizeof(out));
        check(st != SRMECH_OK,
              "past the depth cap the ingest DECLINES to the pure path rather "
              "than silently truncating the nesting");
    }

    /* ─────────────────────────────────────────────────────────────────
     * rc452 (`#T1166`) — THE MAP STEP FORM on a bare-C host, the last of
     * Surface A's three forms. `cr_drive` is an explicit-frame-stack
     * trampoline: JPL Rule 1 bans the recursive body walk compose.py uses,
     * so the call stack is made explicit, arena-backed and depth-capped.
     *
     * These assert VALUES. A map arm that ran the body the wrong number of
     * times, leaked an outer scope into an inner one, or resolved `@idx` to
     * a constant returns rc 0 just as happily as a correct one.
     * ───────────────────────────────────────────────────────────────── */
    {
        /* n comes from len(map_over), NOT from element values: the elements
         * are all 9 and the output counts 0..4. That is the totality pin —
         * data-SIZED, never data-DEPENDENT. */
        st = run_chain(
            "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"map_over\":\"@input.xs\","
            "\"index\":\"i\",\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
            "\"args\":{\"a\":\"@idx.i\",\"b\":0,\"n\":100}}]}]}",
            "{\"inputs\":{\"xs\":[9,9,9,9,9]}}", out, sizeof(out));
        check(st == SRMECH_OK &&
              strcmp(out,
                     "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"0\"}, "
                     "{\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"2\"}, "
                     "{\"k\": \"i\", \"v\": \"3\"}, "
                     "{\"k\": \"i\", \"v\": \"4\"}]}") == 0,
              "MAP runs the body exactly len(map_over) times with @idx bound "
              "to the iteration — n pinned at ENTRY from the sequence LENGTH, "
              "never from its contents");

        /* The EMPTY map. A live proof case on autocorrelation (x=[]) and
         * kuramoto_step (theta=[]), and the one case that distinguishes
         * "ran zero times" from "never entered": the body must NOT run. */
        st = run_chain(
            "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"map_over\":\"@input.xs\","
            "\"index\":\"i\",\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
            "\"args\":{\"a\":\"@idx.i\",\"b\":0,\"n\":100}}]}]}",
            "{\"inputs\":{\"xs\":[]}}", out, sizeof(out));
        check(st == SRMECH_OK && strcmp(out, "{\"k\": \"l\", \"v\": []}") == 0,
              "an EMPTY map_over yields the empty list and never runs the "
              "body — compose.py's `for k in range(0)`");

        /* NESTED map: the inner body sees BOTH indices (layered environments),
         * and the inner frame's `@step[0]` is BODY-local. This is the shape
         * autocorrelation, kuramoto_step and both DFT chains are built from. */
        st = run_chain(
            "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"map_over\":\"@input.o\","
            "\"index\":\"i\",\"body\":[{\"map_over\":\"@input.n\","
            "\"index\":\"j\",\"body\":["
            "{\"class\":\"I\",\"op\":\"mod_mul\","
            "\"args\":{\"a\":\"@idx.i\",\"b\":10,\"n\":1000}},"
            "{\"class\":\"I\",\"op\":\"mod_add\","
            "\"args\":{\"a\":\"@step[0].output\",\"b\":\"@idx.j\","
            "\"n\":1000}}]}]}]}",
            "{\"inputs\":{\"o\":[0,0],\"n\":[0,0,0]}}", out, sizeof(out));
        check(st == SRMECH_OK &&
              strcmp(out,
                     "{\"k\": \"l\", \"v\": ["
                     "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"0\"}, "
                     "{\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"2\"}]}, "
                     "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"10\"}, "
                     "{\"k\": \"i\", \"v\": \"11\"}, "
                     "{\"k\": \"i\", \"v\": \"12\"}]}]}") == 0,
              "NESTED map: the inner body reads the OUTER @idx as well as its "
              "own (layered environments), and its @step[0] is body-local");

        /* @bind is resolved ONCE, in the ENCLOSING scope, and is visible
         * throughout the body. */
        st = run_chain(
            "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"map_over\":\"@input.xs\","
            "\"index\":\"i\",\"bind\":{\"row\":\"@input.ys\"},\"body\":["
            "{\"class\":\"I\",\"op\":\"mod_add\","
            "\"args\":{\"a\":\"@bind.row[1]\",\"b\":\"@idx.i\","
            "\"n\":100}}]}]}",
            "{\"inputs\":{\"xs\":[0,0,0],\"ys\":[10,20,30]}}",
            out, sizeof(out));
        check(st == SRMECH_OK &&
              strcmp(out,
                     "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"20\"}, "
                     "{\"k\": \"i\", \"v\": \"21\"}, "
                     "{\"k\": \"i\", \"v\": \"22\"}]}") == 0,
              "@bind resolves ONCE in the enclosing scope and supports a [N] "
              "tail inside the body");

        /* NEGATIVE CONTROL. An unbound @idx name must DECLINE. Resolving it to
         * 0 would be a silent wrong answer, and 0 is the value most likely to
         * look plausible in an index position. */
        st = run_chain(
            "{\"name\":\"m\",\"summary\":\"s\",\"returns\":\"r\",\"steps\":[{\"map_over\":\"@input.xs\","
            "\"index\":\"i\",\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
            "\"args\":{\"a\":\"@idx.NOPE\",\"b\":0,\"n\":100}}]}]}",
            "{\"inputs\":{\"xs\":[1]}}", out, sizeof(out));
        check(st != SRMECH_OK,
              "an UNBOUND @idx name DECLINES rather than resolving to 0");
    }

    printf("== bare-C chain-run: %d passed, %d failed ==\n", g_pass, g_fail);
    return (g_fail == 0) ? 0 : 1;
}
