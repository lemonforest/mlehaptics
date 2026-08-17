/* _1653_adv3_keyset_attack.c — ADVERSARIAL round-3 extension driver.
 *
 * Includes the prototype under test verbatim (its own main renamed away via
 * -Dmain=ks_proto_main) and hits ks_check_stage with probes the prototype's own
 * three sections do NOT contain, hunting for a FALSE ACCEPT or a FALSE REJECT.
 *
 * Every expected column here is a verdict I measured separately on the PURE
 * python projection in notes/_1653_adv3_pure_verdicts.py / an ad-hoc pure run,
 * not copied from the prototype's table.
 *
 * BUILD:
 *   cc -std=c11 -Wall -Wextra -O2 -Dmain=ks_proto_main -I<c/include> \
 *      _1653_adv3_keyset_attack.c <c/build/libsrmech.a> -o /tmp/ADV_attack
 */

#define main ks_proto_main
#include "_1653_proto_keyset_validator.c"
#undef main

typedef struct {
    const char  *json;
    uint32_t     form;
    ks_verdict_t want;
    const char  *why;
} atk_t;

#define ATK_N 18u

static const atk_t ATK[ATK_N] = {
    /* naming the FIRST positional of a leaf — never probed by the prototype */
    { "{\"op\":\"reorient\",\"value\":9,\"orientation\":-1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'value'" },
    { "{\"op\":\"chiral_flip\",\"seq\":1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'seq'" },
    { "{\"op\":\"net_chirality\",\"orientations\":1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'orientations'" },
    { "{\"op\":\"autocorrelation\",\"x\":1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'x'" },
    { "{\"op\":\"pin_slot_at_zero\",\"x\":1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'x'" },
    { "{\"op\":\"pin_slot_at_zero\",\"bogus\":1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: unexpected keyword 'bogus'" },
    { "{\"op\":\"best_rational_signed\",\"x\":1}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'x'" },
    { "{\"op\":\"cyclic_gcd\",\"a\":1,\"b\":18}", KS_FORM_LEAF,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'a'" },
    /* the DECLARED-but-second-positional case: b IS legal on a leaf */
    { "{\"op\":\"cyclic_gcd\",\"b\":18}", KS_FORM_LEAF, KS_ACCEPT,
      "pure: .then('cyclic_gcd', b=18).run(12) -> 6" },
    /* fold: naming a body's SECOND positional */
    { "{\"fold_init\":1,\"fold_op\":\"srmech.cascade.leaves.seq_get\"}",
      KS_FORM_FOLD, KS_UNKNOWN_OP, "seq_get is linked BODY-only for map; fold role" },
    /* map: a bogus key on the dotted body */
    { "{\"map_op\":\"srmech.cascade.leaves.seq_get\",\"bogus\":1}", KS_FORM_MAP,
      KS_REJECT_UNDECLARED_KEY, "pure: unexpected keyword 'bogus'" },
    { "{\"map_op\":\"srmech.cascade.leaves.seq_get\",\"seq\":1}", KS_FORM_MAP,
      KS_REJECT_UNDECLARED_KEY, "pure: multiple values for 'seq'" },
    /* reduce on a LEAF-only linked name */
    { "{\"reduce_op\":\"magnitude\"}", KS_FORM_REDUCE, KS_UNKNOWN_OP,
      "magnitude is leaf-role only; body role must not resolve" },
    /* leaf on a BODY-only linked name (dotted seq_get) */
    { "{\"op\":\"srmech.cascade.leaves.seq_get\",\"i\":2}", KS_FORM_LEAF,
      KS_UNKNOWN_OP, "dotted seq_get is body-role only" },
    /* structural key present but op key MISSING */
    { "{\"fold_init\":1}", KS_FORM_FOLD, KS_UNKNOWN_OP, "no fold_op" },
    /* op key of the WRONG json type */
    { "{\"op\":7}", KS_FORM_LEAF, KS_UNKNOWN_OP, "op is not a string" },
    /* empty object */
    { "{}", KS_FORM_LEAF, KS_UNKNOWN_OP, "no op key at all" },
    /* VALUE-DOMAIN hole the design note ACKNOWLEDGES: key declared, value illegal.
     * Pure raises ValueError (max_denominator must be >= 1); the gate has no
     * parameter-domain field, so it ACCEPTS.  Documented, not a surprise. */
    { "{\"op\":\"best_rational_signed\",\"max_denominator\":0}", KS_FORM_LEAF,
      KS_ACCEPT, "KNOWN HOLE: pure raises ValueError; gate is name-only" }
};

int main(void)
{
    uint32_t i; int fails = 0;
    assert(ATK_N == 18u);
    assert(sizeof(g_arena) == KS_ARENA);
    printf("ADVERSARIAL attack probes vs the keyset gate (srmech %s ABI %d)\n\n",
           srmech_version(), (int)srmech_abi_version());
    for (i = 0u; i < ATK_N; i++) {
        const char *bad = ""; srmech_status_t pst;
        ks_verdict_t v = ks_drive(ATK[i].json, ATK[i].form, &bad, &pst);
        assert(i < ATK_N);
        assert(ATK[i].json != NULL);
        if (pst != SRMECH_OK || v != ATK[i].want) { fails++; }
        printf("  [%02u] %-58s\n       got %-28s want %-28s %s\n       %s\n",
               i, ATK[i].json, ks_verdict_name(v), ks_verdict_name(ATK[i].want),
               (v == ATK[i].want) ? "OK" : "*** MISMATCH", ATK[i].why);
    }
    printf("\nattack mismatches: %d\n", fails);
    return (fails == 0) ? 0 : 1;
}
