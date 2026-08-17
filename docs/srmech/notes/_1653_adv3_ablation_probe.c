/* _1653_adv3_ablation_probe.c — ADVERSARIAL independent re-probe of the
 * three shipped-runner gates claimed by the round-2 op-table-wedge
 * deliverable (gh #1653). Written from scratch; it does not include or
 * link any part of _1653_wedge_optable_rc444.c.
 *
 * It calls the SHIPPED srmech_chain_run out of c/build/libsrmech.a with
 * six minimal chains that use ONLY ops already in the shipped 10-entry
 * dispatch table, so the op table is held constant and each pair varies
 * exactly one thing:
 *
 *   P1 bare `@step[0].output`      vs  P2 `@step[0].output[0]`
 *   P3 integer 2-list `[1,3]`      vs  P4 real 2-list `[1.0,3]`
 *   P5 single-step control          (no ref, no real literal)
 *   P6 `@input.a` ref control       (the namespace the parse half accepts)
 *
 * JPL: no recursion, no goto, no malloc, caller-arena only, every
 * function <= 60 lines with >= 2 asserts.
 *
 * BUILD:
 *   gcc -std=c11 -O2 -I<WT>/docs/srmech/c/include -o /tmp/adv3probe \
 *       <WT>/docs/srmech/notes/_1653_adv3_ablation_probe.c \
 *       <WT>/docs/srmech/c/build/libsrmech.a
 */

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

#define AP_WS_BYTES (1u << 22)
#define AP_OUT_BYTES 8192u

static unsigned char ap_ws[AP_WS_BYTES];
static char ap_out[AP_OUT_BYTES];

static const char *AP_CTX = "{\"row\":null,\"inputs\":{\"a\":[1,2]}}";

typedef struct { const char *label; const char *json; } ap_case_t;

/* P1 / P2 differ ONLY in the ref spelling on step 1. */
static const char *AP_P1 =
    "{\"name\":\"p1\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],\"b\":[1,3]}},"
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":"
    "{\"a\":\"@step[0].output\",\"b\":[3,1]}}]}";

static const char *AP_P2 =
    "{\"name\":\"p2\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],\"b\":[1,3]}},"
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":"
    "{\"a\":\"@step[0].output[0]\",\"b\":[3,1]}}]}";

/* P3 / P4 differ ONLY in whether one list element is spelled 1 or 1.0. */
static const char *AP_P3 =
    "{\"name\":\"p3\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":{\"a\":[1,3],\"b\":[3,1]}}]}";

static const char *AP_P4 =
    "{\"name\":\"p4\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":{\"a\":[1.0,3],\"b\":[3,1]}}]}";

/* P5 control: one in-table op, integer args, no refs at all. */
static const char *AP_P5 =
    "{\"name\":\"p5\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],\"b\":[1,2]}}]}";

/* P6 control: an @input ref, which the shipped resolver DOES accept. */
static const char *AP_P6 =
    "{\"name\":\"p6\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":"
    "{\"a\":\"@input.a\",\"b\":[3,1]}}]}";

static int ap_run_one(const ap_case_t *c)
{
    size_t out_len = 0u;
    size_t need;
    srmech_status_t st;
    assert(c != NULL);
    assert(c->json != NULL);
    need = srmech_chain_run_arena_bytes(strlen(c->json), 32u);
    if (need > (size_t)AP_WS_BYTES) {
        printf("  %-8s ARENA_TOO_SMALL need=%lu\n", c->label,
               (unsigned long)need);
        return -1;
    }
    st = srmech_chain_run(c->json, strlen(c->json), AP_CTX, strlen(AP_CTX),
                          ap_ws, need, ap_out, (size_t)AP_OUT_BYTES,
                          &out_len);
    printf("  %-8s rc=%d out=%.*s\n", c->label, (int)st,
           (st == SRMECH_OK) ? (int)out_len : 0, ap_out);
    return (int)st;
}

int main(void)
{
    ap_case_t cases[6];
    size_t i;
    int rcs[6];
    assert(sizeof(cases) / sizeof(cases[0]) == 6u);
    assert(AP_CTX != NULL);
    cases[0].label = "P1bare";  cases[0].json = AP_P1;
    cases[1].label = "P2index"; cases[1].json = AP_P2;
    cases[2].label = "P3int";   cases[2].json = AP_P3;
    cases[3].label = "P4real";  cases[3].json = AP_P4;
    cases[4].label = "P5ctl";   cases[4].json = AP_P5;
    cases[5].label = "P6input"; cases[5].json = AP_P6;
    printf("srmech %s ABI %d — independent shipped-runner ablation\n",
           srmech_version(), srmech_abi_version());
    for (i = 0u; i < 6u; i++) { rcs[i] = ap_run_one(&cases[i]); }
    printf("VERDICT ref-index-gate  : bare=%d indexed=%d  (differ=%d)\n",
           rcs[0], rcs[1], (rcs[0] != rcs[1]) ? 1 : 0);
    printf("VERDICT real-literal-gate: int=%d real=%d  (differ=%d)\n",
           rcs[2], rcs[3], (rcs[2] != rcs[3]) ? 1 : 0);
    printf("VERDICT controls        : plain=%d input_ref=%d\n",
           rcs[4], rcs[5]);
    return 0;
}
