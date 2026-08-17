/* #T1145 ADVERSARIAL RE-DERIVATION — API-strength C tool-registry check.
 *
 * The census under review cross-checked the C tool registry by GREPPING quoted
 * string literals in c/src/srmech_tool_registry.c, and recorded a caveat that
 * "srmech.h exports no tool-registry enumerator, only the five chain/DSL entry
 * points". That caveat is FALSE: srmech.h:5802-5809 export
 *   size_t                     srmech_tool_registry_count(void);
 *   const srmech_tool_entry_t *srmech_tool_registry_get(size_t index);
 *   const srmech_tool_entry_t *srmech_tool_registry_find(const char *name);
 * This driver uses them, so the cross-check becomes API-strength: a name is
 * "present" only when srmech_tool_registry_find() returns a real entry from the
 * const registration table, which a doc-string occurrence can never do.
 *
 * JPL Power-of-Ten: no recursion, no malloc, no goto, functions <= 60 lines,
 * >= 2 asserts per function, all storage caller-arena / const-static.
 * Build: cc -std=c99 -Wall -Wextra -I../c/include this.c ../c/build/libsrmech.a
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "srmech.h"

#include "names.inc"

#define N_FLAT   (sizeof(FLAT_NAMES)  / sizeof(FLAT_NAMES[0]))
#define N_DOTTED (sizeof(DOTTED_FAIL) / sizeof(DOTTED_FAIL[0]))
#define N_REG    (sizeof(REG_CLASS)   / sizeof(REG_CLASS[0]))

/* Count how many of `names[0..n)` are REGISTERED entries, via the public API.
 * Returns the present-count; writes the first absent name index to *first_absent
 * (or (size_t)-1 when none are absent). */
static size_t count_registered(const char *const *names, size_t n,
                               size_t *first_absent)
{
    size_t present = 0u;
    size_t i = 0u;

    assert(names != NULL);
    assert(first_absent != NULL);
    assert(n < 4096u);

    *first_absent = (size_t)-1;
    for (i = 0u; i < n; i++) {
        const srmech_tool_entry_t *e = NULL;
        assert(names[i] != NULL);
        e = srmech_tool_registry_find(names[i]);
        if (e != NULL) {
            /* API-strength: the entry's own name must echo the query. */
            assert(e->name != NULL);
            if (strcmp(e->name, names[i]) == 0) {
                present++;
            }
        } else if (*first_absent == (size_t)-1) {
            *first_absent = i;
        }
    }
    return present;
}

/* Does any registered entry name END WITH ".leaf" of `q`? This re-derives the
 * shipped Python resolve_all() rule (t.name == q || t.name.endswith("." + q))
 * against the C table, independently of the Python harness. */
static size_t count_suffix_matches(const char *q)
{
    size_t total = 0u;
    size_t hits = 0u;
    size_t i = 0u;
    size_t qlen = 0u;

    assert(q != NULL);
    qlen = strlen(q);
    assert(qlen > 0u && qlen < 512u);

    total = srmech_tool_registry_count();
    for (i = 0u; i < total; i++) {
        const srmech_tool_entry_t *e = srmech_tool_registry_get(i);
        size_t nlen = 0u;
        assert(e != NULL);
        assert(e->name != NULL);
        nlen = strlen(e->name);
        if (nlen == qlen && strcmp(e->name, q) == 0) {
            hits++;
        } else if (nlen > qlen + 1u &&
                   e->name[nlen - qlen - 1u] == '.' &&
                   strcmp(e->name + (nlen - qlen), q) == 0) {
            hits++;
        }
    }
    return hits;
}

int main(void)
{
    size_t total = 0u;
    size_t absent_at = 0u;
    size_t flat_present = 0u;
    size_t dotted_present = 0u;
    size_t reg_present = 0u;
    size_t i = 0u;

    total = srmech_tool_registry_count();
    assert(total > 0u);
    assert(total < 100000u);
    printf("C_registry_count=%zu\n", total);

    flat_present = count_registered(FLAT_NAMES, N_FLAT, &absent_at);
    printf("flat_names_total=%zu flat_names_registered=%zu\n",
           N_FLAT, flat_present);
    if (absent_at != (size_t)-1) {
        printf("first_absent_flat=%s\n", FLAT_NAMES[absent_at]);
    }

    dotted_present = count_registered(DOTTED_FAIL, N_DOTTED, &absent_at);
    printf("dotted_failing_total=%zu dotted_failing_registered_in_C=%zu\n",
           N_DOTTED, dotted_present);

    reg_present = count_registered(REG_CLASS, N_REG, &absent_at);
    printf("registry_class_total=%zu registry_class_registered_in_C=%zu\n",
           N_REG, reg_present);

    /* Per-spelling suffix re-derivation for the registry-class three: a
     * genuinely unregistered leaf must have ZERO suffix matches in C too. */
    for (i = 0u; i < N_REG; i++) {
        const char *leaf = strrchr(REG_CLASS[i], '.');
        assert(leaf != NULL);
        printf("regclass_leaf=%s c_suffix_matches=%zu\n",
               leaf + 1, count_suffix_matches(leaf + 1));
    }
    /* And a data-class control: its leaf MUST have exactly one C suffix match. */
    for (i = 0u; i < N_FLAT && i < 4u; i++) {
        const char *leaf = strrchr(FLAT_NAMES[i], '.');
        assert(leaf != NULL);
        printf("dataclass_leaf=%s c_suffix_matches=%zu\n",
               leaf + 1, count_suffix_matches(leaf + 1));
    }
    return 0;
}
