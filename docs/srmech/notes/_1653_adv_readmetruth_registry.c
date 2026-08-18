/* ADVERSARIAL VERIFICATION of gh #1653 round-2 "readme-truth" FINDING 3.
 *
 * The claim under test: the stale "17 executable" catalog count is COMPILED
 * into libsrmech's const tool registry, so a host with no Python in the
 * process hands its clients the wrong number.
 *
 * This host links libsrmech.a ONLY. No libpython, no Python interpreter. It
 * asks the const registry for srmech.dsl.run_cascade_chain and prints the two
 * fields an MCP tools/list response is built from (example_json, explanation),
 * then reports whether each carries "17 executable" or "18 executable".
 *
 * The live value measured through the Python projection is 18. If the C table
 * says 17 and never 18, the finding reproduces from a bare-C host.
 *
 * JPL Power-of-Ten: no recursion, no dynamic allocation, no branch-out jumps,
 * every function under 60 lines with at least two assertions.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

/* Count non-overlapping occurrences of `needle` in `hay`. */
static int count_occurrences(const char *hay, const char *needle)
{
    int n = 0;
    const char *p = hay;
    size_t nlen = 0;

    assert(hay != NULL);
    assert(needle != NULL);

    nlen = strlen(needle);
    assert(nlen > 0u);

    while (*p != '\0') {
        const char *hit = strstr(p, needle);
        if (hit == NULL) {
            break;
        }
        n += 1;
        p = hit + nlen;
    }
    return n;
}

/* Report one registry field: how many times it says 17 vs 18. */
static int report_field(const char *label, const char *text)
{
    int got17 = 0;
    int got18 = 0;

    assert(label != NULL);
    assert(text != NULL);

    got17 = count_occurrences(text, "17 executable");
    got18 = count_occurrences(text, "18 executable");
    printf("  %-14s : '17 executable' x%d   '18 executable' x%d   %s\n",
           label, got17, got18,
           (got17 > 0 && got18 == 0) ? "<== STALE (finding reproduces)"
                                     : "ok");
    return got17;
}

int main(void)
{
    const srmech_tool_entry_t *e = NULL;
    size_t total = 0u;
    int stale = 0;

    total = srmech_tool_registry_count();
    assert(total > 0u);
    printf("bare-C host, libsrmech.a only (no libpython in this process)\n");
    printf("srmech_version ............ %s\n", srmech_version());
    printf("srmech_abi_version ........ %d\n", (int)srmech_abi_version());
    printf("srmech_tool_registry_count  %lu\n", (unsigned long)total);

    e = srmech_tool_registry_find("srmech.dsl.run_cascade_chain");
    assert(e != NULL);
    assert(e->name != NULL);
    printf("\nentry: %s\n", e->name);

    if (e->example_json != NULL) {
        stale += report_field("example_json", e->example_json);
    }
    if (e->explanation != NULL) {
        stale += report_field("explanation", e->explanation);
    }

    printf("\nstale '17 executable' occurrences served by the C registry: %d\n",
           stale);
    printf("VERDICT: %s\n", (stale > 0)
           ? "CONFIRMED — the wrong count ships inside the compiled table"
           : "REFUTED — the compiled table does not carry the stale count");
    return 0;
}
