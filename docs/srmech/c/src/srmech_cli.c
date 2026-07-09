/*
 * srmech_cli.c — the C CLI arg-GRAMMAR + dispatch (0.9.0rc193; the HOST-GLUE
 * console-script parser). The C peer of srmech.cli.main.{build_parser, main}
 * + the five subcommand srmech.cli.{status,bus,dsl,mcp,klass}.add_arguments.
 *
 * A bare-C host (no Python) parses the `srmech` console-script grammar for all
 * five subcommands (status / bus / dsl / mcp / class), each with its
 * flags / positionals / choices / defaults, emits the parsed argparse namespace
 * as canonical JSON (dest keys + defaults filled), and routes the command to its
 * run body. See the srmech.h srmech_cli_parse / srmech_cli_dispatch block for the
 * full grammar + the behavior-parity contract (RUN vs HELP/VERSION/ERROR vs the
 * NOT_IMPL "defer to pure argparse" signal).
 *
 * JPL-clean: no malloc (the canonical JSON is written straight to the caller's
 * `out`; argv is parsed in place — no arena), no goto, no recursion (a flat
 * subcommand switch + a bounded token loop), no libm, no abs. Bounded: a fixed
 * subcommand table + a fixed per-subcommand option table (Rule 2). ABI-additive
 * (SRMECH_ABI_VERSION stays 4). License: MIT.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

#define CLI_INT64_MIN (-9223372036854775807LL - 1)
#define CLI_MAX_OPTS  6   /* largest per-subcommand option table (send/serve/run) */
#define CLI_MAX_POS   2   /* largest positional count (pipe SRC DST; send NAME EV) */

/* ------------------------------------------------------------------
 * Canonical-JSON emitter — writes straight into the caller `out`, counting
 * `used` even past `cap` (so *out_len returns the needed length on overflow);
 * a byte is only stored when it fits. No arena, no malloc.
 * ------------------------------------------------------------------ */

typedef struct {
    char  *buf;
    size_t cap;
    size_t used;
} cli_emit_t;

static void cli_raw(cli_emit_t *e, const char *s, size_t n)
{
    size_t i;
    assert(e != NULL);
    assert(s != NULL || n == 0u);
    for (i = 0u; i < n; i++) {
        if (e->used < e->cap) {
            e->buf[e->used] = s[i];
        }
        e->used++;
    }
}

static void cli_cstr(cli_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    cli_raw(e, s, strlen(s));
}

/* Emit s[0..len) as a JSON string (surrounding quotes; escape ", \, and the
 * control bytes < 0x20; UTF-8 bytes >= 0x20 pass through — valid JSON that
 * json.loads round-trips to the identical Python str). */
static void cli_json_str_n(cli_emit_t *e, const char *s, size_t len)
{
    static const char hexd[] = "0123456789abcdef";
    const unsigned char *p = (const unsigned char *)s;
    size_t i;
    assert(e != NULL);
    assert(s != NULL || len == 0u);
    cli_raw(e, "\"", 1u);
    for (i = 0u; i < len; i++) {
        unsigned char c = p[i];
        if (c == '"') { cli_raw(e, "\\\"", 2u); }
        else if (c == '\\') { cli_raw(e, "\\\\", 2u); }
        else if (c == '\b') { cli_raw(e, "\\b", 2u); }
        else if (c == '\t') { cli_raw(e, "\\t", 2u); }
        else if (c == '\n') { cli_raw(e, "\\n", 2u); }
        else if (c == '\f') { cli_raw(e, "\\f", 2u); }
        else if (c == '\r') { cli_raw(e, "\\r", 2u); }
        else if (c < 0x20u) {
            char b[6];
            b[0] = '\\'; b[1] = 'u'; b[2] = '0'; b[3] = '0';
            b[4] = hexd[(c >> 4) & 0xFu]; b[5] = hexd[c & 0xFu];
            cli_raw(e, b, 6u);
        } else {
            char ch = (char)c;
            cli_raw(e, &ch, 1u);
        }
    }
    cli_raw(e, "\"", 1u);
}

static void cli_json_str(cli_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    cli_json_str_n(e, s, strlen(s));
}

/* Emit an int64 in decimal (a JSON number). */
static void cli_emit_i64(cli_emit_t *e, int64_t v)
{
    char tmp[24];
    int pos = 0;
    uint64_t u;
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    if (v < 0) {
        cli_raw(e, "-", 1u);
        u = (uint64_t)(-(v + 1)) + 1u;   /* INT64_MIN-safe */
    } else {
        u = (uint64_t)v;
    }
    if (u == 0u) { tmp[pos++] = '0'; }
    while (u > 0u) { tmp[pos++] = (char)('0' + (int)(u % 10u)); u /= 10u; }
    while (pos > 0) { pos--; cli_raw(e, &tmp[pos], 1u); }
}

/* ------------------------------------------------------------------
 * Token lexers — bounded int64 / float-token recognisers.
 * ------------------------------------------------------------------ */

static int cli_lex_i64(const char *s, int64_t *out)
{
    size_t i = 0u;
    int neg = 0, digits = 0;
    uint64_t v = 0u;
    assert(s != NULL);
    assert(out != NULL);
    if (s[i] == '+') { i++; }
    else if (s[i] == '-') { neg = 1; i++; }
    while (s[i] >= '0' && s[i] <= '9') {
        uint64_t d = (uint64_t)(s[i] - '0');
        if (v > 922337203685477580u) { return 0; }        /* MAX/10 guard */
        v = v * 10u + d;
        i++;
        digits++;
    }
    if (digits == 0 || s[i] != '\0') { return 0; }
    if (neg) {
        if (v > 9223372036854775808u) { return 0; }
        *out = (v == 9223372036854775808u) ? CLI_INT64_MIN : -(int64_t)v;
    } else {
        if (v > 9223372036854775807u) { return 0; }
        *out = (int64_t)v;
    }
    return 1;
}

/* Accept the common float grammar [+-]?(D+.?D*|.D+)([eE][+-]?D+)? in full.
 * A token this rejects (inf / nan / underscores) defers to pure argparse. */
static int cli_lex_float_ok(const char *s)
{
    size_t i = 0u;
    int digits = 0;
    assert(s != NULL);
    assert(s[0] != '\0');
    if (s[i] == '+' || s[i] == '-') { i++; }
    while (s[i] >= '0' && s[i] <= '9') { i++; digits++; }
    if (s[i] == '.') {
        i++;
        while (s[i] >= '0' && s[i] <= '9') { i++; digits++; }
    }
    if (digits == 0) { return 0; }
    if (s[i] == 'e' || s[i] == 'E') {
        i++;
        if (s[i] == '+' || s[i] == '-') { i++; }
        if (!(s[i] >= '0' && s[i] <= '9')) { return 0; }
        while (s[i] >= '0' && s[i] <= '9') { i++; }
    }
    return s[i] == '\0';
}

/* ------------------------------------------------------------------
 * Option table — the fixed per-subcommand grammar.
 * ------------------------------------------------------------------ */

typedef enum {
    OPT_FLAG, OPT_STR, OPT_INT, OPT_FLOAT, OPT_CHOICE
} cli_opt_kind_t;

typedef struct {
    const char    *lng;      /* "--seed"                                   */
    const char    *shrt;     /* "-f" or NULL                               */
    cli_opt_kind_t kind;
    const char    *dest;     /* JSON key                                   */
    const char    *choices;  /* space-separated for OPT_CHOICE, else NULL  */
    const char    *def;      /* default: NULL -> json null (STR/INT); a    */
                             /* string for STR/CHOICE/FLOAT (emitted as-is)*/
} cli_opt_spec_t;

typedef struct {
    int      set;
    const char *sval;        /* value token (STR/CHOICE/FLOAT)             */
    int64_t  ival;           /* lexed int (OPT_INT)                        */
} cli_opt_res_t;

/* Match `tok` against `name` as --name or --name=VALUE (sets *inl to the value
 * after '=' or NULL for the bare form). Returns 1 on a long-option match. */
static int cli_long(const char *tok, const char *name, const char **inl)
{
    size_t n;
    assert(tok != NULL);
    assert(name != NULL);
    n = strlen(name);
    if (strncmp(tok, name, n) != 0) { return 0; }
    if (tok[n] == '\0') { *inl = NULL; return 1; }
    if (tok[n] == '=') { *inl = &tok[n + 1]; return 1; }
    return 0;
}

/* Membership test for an OPT_CHOICE token against space-separated `choices`. */
static int cli_choice_ok(const char *choices, const char *val)
{
    size_t vl, i = 0u;
    assert(choices != NULL);
    assert(val != NULL);
    vl = strlen(val);
    while (choices[i] != '\0') {
        size_t j = i;
        while (choices[j] != '\0' && choices[j] != ' ') { j++; }
        if (j - i == vl && strncmp(&choices[i], val, vl) == 0) { return 1; }
        i = (choices[j] == ' ') ? j + 1u : j;
    }
    return 0;
}

/* Find the spec `tok` names; set *idx + *inl. Returns 1 on a match. */
static int cli_find_spec(const cli_opt_spec_t *specs, int nspec,
                         const char *tok, int *idx, const char **inl)
{
    int k;
    assert(specs != NULL || nspec == 0);
    assert(tok != NULL);
    for (k = 0; k < nspec; k++) {
        if (cli_long(tok, specs[k].lng, inl)) { *idx = k; return 1; }
        if (specs[k].shrt != NULL && strcmp(tok, specs[k].shrt) == 0) {
            *inl = NULL; *idx = k; return 1;
        }
    }
    return 0;
}

/* Apply one matched option: consume its value (inline or next token), validate
 * per kind, fill `res`. *extra = #following tokens consumed (0 or 1). */
static srmech_status_t cli_opt_apply(const cli_opt_spec_t *sp, const char *inl,
                                     const char *const *argv, int argc,
                                     int oi, cli_opt_res_t *res, int *extra)
{
    const char *val;
    assert(sp != NULL);
    assert(res != NULL);
    *extra = 0;
    if (sp->kind == OPT_FLAG) {
        if (inl != NULL) { return SRMECH_ERR_NOT_IMPL; }  /* --flag=x -> defer */
        res->set = 1;
        return SRMECH_OK;
    }
    if (inl != NULL) {
        val = inl;
    } else {
        if (oi + 1 >= argc) { return SRMECH_ERR_BAD_INPUT; }  /* missing value */
        val = argv[oi + 1];
        if (val[0] == '-' && val[1] != '\0') {
            /* argparse consumes a NEGATIVE-NUMBER token as the value (no srmech
             * option looks like a negative number); any other option-like token
             * ("--json", "-{...}") -> defer to pure argparse. */
            int64_t neg;
            if (!cli_lex_i64(val, &neg) && !cli_lex_float_ok(val)) {
                return SRMECH_ERR_NOT_IMPL;
            }
        }
        *extra = 1;
    }
    if (sp->kind == OPT_INT) {
        if (!cli_lex_i64(val, &res->ival)) { return SRMECH_ERR_NOT_IMPL; }
    } else if (sp->kind == OPT_FLOAT) {
        if (val[0] == '\0' || !cli_lex_float_ok(val)) { return SRMECH_ERR_NOT_IMPL; }
    } else if (sp->kind == OPT_CHOICE) {
        if (!cli_choice_ok(sp->choices, val)) { return SRMECH_ERR_BAD_INPUT; }
    }
    res->set = 1;
    res->sval = val;
    return SRMECH_OK;
}

/* The bounded token loop: split argv[start..argc) into options (matched against
 * `specs`) + positionals (into `pos`). Sets *want_help on -h/--help. Returns
 * SRMECH_OK / BAD_INPUT (structural error) / NOT_IMPL (defer to pure). */
static srmech_status_t cli_parse_opts(const char *const *argv, int argc, int start,
                                      const cli_opt_spec_t *specs, int nspec,
                                      cli_opt_res_t *res, const char **pos,
                                      int maxpos, int *npos, int *want_help)
{
    int i = start, k;
    assert(argv != NULL || argc == 0);
    assert(npos != NULL && want_help != NULL);
    *npos = 0;
    *want_help = 0;
    for (k = 0; k < nspec; k++) { res[k].set = 0; res[k].sval = NULL; res[k].ival = 0; }
    while (i < argc) {
        const char *tok = argv[i];
        const char *inl = NULL;
        int idx = 0, extra = 0;
        srmech_status_t st;
        if (strcmp(tok, "-h") == 0 || strcmp(tok, "--help") == 0) {
            *want_help = 1;
            return SRMECH_OK;
        }
        if (strcmp(tok, "--") == 0) { return SRMECH_ERR_NOT_IMPL; }
        if (tok[0] == '-' && tok[1] != '\0') {
            if (!cli_find_spec(specs, nspec, tok, &idx, &inl)) {
                return SRMECH_ERR_NOT_IMPL;               /* unknown / abbrev */
            }
            st = cli_opt_apply(&specs[idx], inl, argv, argc, i, &res[idx], &extra);
            if (st != SRMECH_OK) { return st; }
            i += 1 + extra;
        } else {
            if (*npos >= maxpos) { return SRMECH_ERR_BAD_INPUT; }  /* too many */
            pos[(*npos)++] = tok;
            i++;
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Namespace emitter — command + subcmd + positionals + option fields.
 * ------------------------------------------------------------------ */

/* Emit one option field ,"dest":<value-or-default>. */
static void cli_emit_opt(cli_emit_t *e, const cli_opt_spec_t *sp,
                         const cli_opt_res_t *r)
{
    assert(sp != NULL);
    assert(r != NULL);
    cli_raw(e, ",\"", 2u);
    cli_cstr(e, sp->dest);
    cli_raw(e, "\":", 2u);
    if (sp->kind == OPT_FLAG) {
        cli_cstr(e, r->set ? "true" : "false");
    } else if (sp->kind == OPT_INT) {
        if (r->set) { cli_emit_i64(e, r->ival); }
        else if (sp->def != NULL) { cli_cstr(e, sp->def); }
        else { cli_cstr(e, "null"); }
    } else {  /* STR / CHOICE / FLOAT — emit the token (or default) as a string */
        const char *v = r->set ? r->sval : sp->def;
        if (v == NULL) { cli_cstr(e, "null"); }
        else { cli_json_str(e, v); }
    }
}

/* Emit the whole namespace object. `subkey` is the sub-subcommand dest key
 * (e.g. "bus_subcommand") or NULL for the flat `status`; `subval` its value. */
static void cli_emit_ns(cli_emit_t *e, const char *command, const char *subkey,
                        const char *subval, const char *const *posnames,
                        int npos_names, const char **pos, int npos,
                        const cli_opt_spec_t *specs, const cli_opt_res_t *res,
                        int nspec)
{
    int j;
    assert(e != NULL);
    assert(command != NULL);
    cli_cstr(e, "{\"command\":");
    cli_json_str(e, command);
    if (subkey != NULL) {
        cli_raw(e, ",\"", 2u);
        cli_cstr(e, subkey);
        cli_raw(e, "\":", 2u);
        cli_json_str(e, subval);
    }
    for (j = 0; j < npos_names; j++) {
        cli_raw(e, ",\"", 2u);
        cli_cstr(e, posnames[j]);
        cli_raw(e, "\":", 2u);
        if (j < npos) { cli_json_str(e, pos[j]); }
        else { cli_cstr(e, "null"); }   /* an optional positional not given */
    }
    for (j = 0; j < nspec; j++) { cli_emit_opt(e, &specs[j], &res[j]); }
    cli_raw(e, "}", 1u);
}

/* ------------------------------------------------------------------
 * Per-subcommand parse: run the token loop, validate the positional count,
 * emit the namespace. `minpos` positionals are required; `npos_names` slots
 * are emitted (optional trailing slots -> null). Sets *action.
 * ------------------------------------------------------------------ */
static srmech_status_t cli_parse_and_emit(cli_emit_t *e, const char *command,
        const char *subkey, const char *subval, const char *const *argv,
        int argc, int start, const cli_opt_spec_t *specs, int nspec,
        const char *const *posnames, int npos_names, int minpos, int *action)
{
    cli_opt_res_t res[CLI_MAX_OPTS];
    const char *pos[CLI_MAX_POS];
    int npos = 0, want_help = 0;
    srmech_status_t st;
    assert(e != NULL);
    assert(action != NULL);
    st = cli_parse_opts(argv, argc, start, specs, nspec, res, pos,
                        npos_names, &npos, &want_help);
    if (st != SRMECH_OK) {
        if (st == SRMECH_ERR_BAD_INPUT) { *action = SRMECH_CLI_ACTION_ERROR; return SRMECH_OK; }
        return st;   /* NOT_IMPL -> defer */
    }
    if (want_help) { *action = SRMECH_CLI_ACTION_HELP; return SRMECH_OK; }
    if (npos < minpos) { *action = SRMECH_CLI_ACTION_ERROR; return SRMECH_OK; }
    cli_emit_ns(e, command, subkey, subval, posnames, npos_names,
                pos, npos, specs, res, nspec);
    *action = SRMECH_CLI_ACTION_RUN;
    return SRMECH_OK;
}

/* ---- status (flat: no sub-subcommand) ------------------------------------- */
static srmech_status_t cli_do_status(cli_emit_t *e, const char *const *argv,
                                     int argc, int *action)
{
    static const cli_opt_spec_t specs[] = {
        { "--pid", NULL, OPT_INT, "pid", NULL, NULL },
        { "--follow", "-f", OPT_FLAG, "follow", NULL, NULL },
        { "--json", NULL, OPT_FLAG, "json", NULL, NULL },
        { "--poll-interval", NULL, OPT_FLOAT, "poll_interval", NULL, "0.5" },
    };
    assert(e != NULL);
    assert(action != NULL);
    return cli_parse_and_emit(e, "status", NULL, NULL, argv, argc, 1,
                              specs, 4, NULL, 0, 0, action);
}

/* A sub-subcommand descriptor (the {list,tap,...} / {run,ops,...} choices). */
typedef struct {
    const char           *name;       /* token + JSON subval                 */
    const cli_opt_spec_t *specs;
    int                   nspec;
    const char *const    *posnames;
    int                   npos_names;
    int                   minpos;     /* required positional count           */
} cli_subcmd_t;

/* Generic nested-command handler: emit {command, subkey:null} on a bare
 * `srmech <command>`, HELP on -h/--help, defer on an option-like token, else
 * look the sub-subcommand up in `table` + parse its grammar. Sets *action. */
static srmech_status_t cli_nested(cli_emit_t *e, const char *command,
                                  const char *subkey, const char *const *argv,
                                  int argc, const cli_subcmd_t *table, int ntab,
                                  int *action)
{
    const char *sub;
    int k;
    assert(e != NULL);
    assert(action != NULL);
    if (argc <= 1) {
        cli_cstr(e, "{\"command\":\"");
        cli_cstr(e, command);
        cli_cstr(e, "\",\"");
        cli_cstr(e, subkey);
        cli_cstr(e, "\":null}");
        *action = SRMECH_CLI_ACTION_RUN;
        return SRMECH_OK;
    }
    sub = argv[1];
    if (strcmp(sub, "-h") == 0 || strcmp(sub, "--help") == 0) {
        *action = SRMECH_CLI_ACTION_HELP;
        return SRMECH_OK;
    }
    if (sub[0] == '-') { return SRMECH_ERR_NOT_IMPL; }
    for (k = 0; k < ntab; k++) {
        if (strcmp(sub, table[k].name) == 0) {
            return cli_parse_and_emit(e, command, subkey, table[k].name, argv,
                                      argc, 2, table[k].specs, table[k].nspec,
                                      table[k].posnames, table[k].npos_names,
                                      table[k].minpos, action);
        }
    }
    *action = SRMECH_CLI_ACTION_ERROR;   /* invalid choice */
    return SRMECH_OK;
}

/* ---- status (flat: no sub-subcommand) ------------------------------------- */
/* (defined above) */

/* ---- bus {list,tap,pipe,send,serve} --------------------------------------- */
static const cli_opt_spec_t CLI_BUS_LIST[] = {
    { "--json", NULL, OPT_FLAG, "json", NULL, NULL },
    { "--all", NULL, OPT_FLAG, "show_all", NULL, NULL },
};
static const char *const CLI_TAP_PN[] = { "name" };
static const cli_opt_spec_t CLI_BUS_TAP[] = {
    { "--seed", NULL, OPT_STR, "seed", NULL, NULL },
    { "--format", NULL, OPT_CHOICE, "output_format", "json pretty", "json" },
    { "--filter", NULL, OPT_STR, "type_filter", NULL, NULL },
    { "--limit", NULL, OPT_INT, "limit", NULL, NULL },
};
static const char *const CLI_PIPE_PN[] = { "src", "dst" };
static const cli_opt_spec_t CLI_BUS_PIPE[] = {
    { "--seed-src", NULL, OPT_STR, "seed_src", NULL, NULL },
    { "--seed-dst", NULL, OPT_STR, "seed_dst", NULL, NULL },
    { "--transform", NULL, OPT_STR, "transform", NULL, NULL },
};
static const char *const CLI_SEND_PN[] = { "name", "event_json" };
static const cli_opt_spec_t CLI_BUS_SEND[] = {
    { "--seed", NULL, OPT_STR, "seed", NULL, NULL },
    { "--timeout", NULL, OPT_FLOAT, "timeout", NULL, "5.0" },
    { "--stdin", NULL, OPT_FLAG, "stdin", NULL, NULL },
};
static const char *const CLI_SERVE_PN[] = { "name" };
static const cli_opt_spec_t CLI_BUS_SERVE[] = {
    { "--echo", NULL, OPT_FLAG, "echo", NULL, NULL },
    { "--seed", NULL, OPT_STR, "seed", NULL, NULL },
    { "--seed-mint", NULL, OPT_FLAG, "seed_mint", NULL, NULL },
    { "--handler-module", NULL, OPT_STR, "handler_module", NULL, NULL },
};
static const cli_subcmd_t CLI_BUS_TABLE[] = {
    { "list", CLI_BUS_LIST, 2, NULL, 0, 0 },
    { "tap", CLI_BUS_TAP, 4, CLI_TAP_PN, 1, 1 },
    { "pipe", CLI_BUS_PIPE, 3, CLI_PIPE_PN, 2, 2 },
    { "send", CLI_BUS_SEND, 3, CLI_SEND_PN, 2, 1 },
    { "serve", CLI_BUS_SERVE, 4, CLI_SERVE_PN, 1, 1 },
};

static srmech_status_t cli_do_bus(cli_emit_t *e, const char *const *argv,
                                  int argc, int *action)
{
    assert(e != NULL);
    assert(action != NULL);
    return cli_nested(e, "bus", "bus_subcommand", argv, argc,
                      CLI_BUS_TABLE, 5, action);
}

/* ---- dsl {run,ops,visualize} ---------------------------------------------- */
static const char *const CLI_RUN_PN[] = { "chain_toml" };
static const cli_opt_spec_t CLI_DSL_RUN[] = {
    { "--input", NULL, OPT_STR, "input", NULL, NULL },
    { "--input-file", NULL, OPT_STR, "input_file", NULL, NULL },
    { "--output-file", NULL, OPT_STR, "output_file", NULL, NULL },
    { "--ndjson-input", NULL, OPT_FLAG, "ndjson_input", NULL, NULL },
    { "--json", NULL, OPT_FLAG, "json", NULL, NULL },
};
static const cli_opt_spec_t CLI_DSL_JSON[] = {
    { "--json", NULL, OPT_FLAG, "json", NULL, NULL },
};
static const char *const CLI_VIZ_PN[] = { "chain_toml" };
static const cli_subcmd_t CLI_DSL_TABLE[] = {
    { "run", CLI_DSL_RUN, 5, CLI_RUN_PN, 1, 1 },
    { "ops", CLI_DSL_JSON, 1, NULL, 0, 0 },
    { "visualize", CLI_DSL_JSON, 1, CLI_VIZ_PN, 1, 1 },
};

static srmech_status_t cli_do_dsl(cli_emit_t *e, const char *const *argv,
                                  int argc, int *action)
{
    assert(e != NULL);
    assert(action != NULL);
    return cli_nested(e, "dsl", "dsl_command", argv, argc,
                      CLI_DSL_TABLE, 3, action);
}

/* ---- mcp {emit-mcpb} ------------------------------------------------------- */
static const cli_opt_spec_t CLI_MCP_EMIT[] = {
    { "--out", NULL, OPT_STR, "out", NULL, "." },
    { "--type", NULL, OPT_CHOICE, "server_type", "uv python", "uv" },
    { "--name", NULL, OPT_STR, "name", NULL, "srmech" },
    { "--manifest-only", NULL, OPT_FLAG, "manifest_only", NULL, NULL },
    { "--filter", NULL, OPT_STR, "name_filter", NULL, NULL },
};
static const cli_subcmd_t CLI_MCP_TABLE[] = {
    { "emit-mcpb", CLI_MCP_EMIT, 5, NULL, 0, 0 },
};

static srmech_status_t cli_do_mcp(cli_emit_t *e, const char *const *argv,
                                  int argc, int *action)
{
    assert(e != NULL);
    assert(action != NULL);
    return cli_nested(e, "mcp", "mcp_subcommand", argv, argc,
                      CLI_MCP_TABLE, 1, action);
}

/* ---- class {list,describe} ------------------------------------------------ */
static const char *const CLI_DESCRIBE_PN[] = { "name" };
static const cli_subcmd_t CLI_CLASS_TABLE[] = {
    { "list", NULL, 0, NULL, 0, 0 },
    { "describe", NULL, 0, CLI_DESCRIBE_PN, 1, 1 },
};

static srmech_status_t cli_do_class(cli_emit_t *e, const char *const *argv,
                                    int argc, int *action)
{
    assert(e != NULL);
    assert(action != NULL);
    return cli_nested(e, "class", "class_command", argv, argc,
                      CLI_CLASS_TABLE, 2, action);
}

/* ------------------------------------------------------------------
 * Public: srmech_cli_parse.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_cli_parse(int argc, const char *const *argv,
                                 char *out, size_t out_cap, size_t *out_len,
                                 int *out_action, int *out_exit)
{
    cli_emit_t e;
    const char *cmd;
    srmech_status_t st;
    if (out == NULL || out_len == NULL || out_action == NULL ||
        out_exit == NULL || (argc > 0 && argv == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(out_action != NULL);
    e.buf = out;
    e.cap = out_cap;
    e.used = 0u;
    *out_action = SRMECH_CLI_ACTION_RUN;
    *out_exit = 0;
    if (argc <= 0) {                         /* bare `srmech` -> command null */
        cli_cstr(&e, "{\"command\":null}");
        st = SRMECH_OK;
    } else {
        cmd = argv[0];
        if (strcmp(cmd, "-h") == 0 || strcmp(cmd, "--help") == 0) {
            *out_action = SRMECH_CLI_ACTION_HELP; st = SRMECH_OK;
        } else if (strcmp(cmd, "--version") == 0) {
            *out_action = SRMECH_CLI_ACTION_VERSION; st = SRMECH_OK;
        } else if (cmd[0] == '-') {
            return SRMECH_ERR_NOT_IMPL;       /* unknown top option -> defer */
        } else if (strcmp(cmd, "status") == 0) {
            st = cli_do_status(&e, argv, argc, out_action);
        } else if (strcmp(cmd, "bus") == 0) {
            st = cli_do_bus(&e, argv, argc, out_action);
        } else if (strcmp(cmd, "dsl") == 0) {
            st = cli_do_dsl(&e, argv, argc, out_action);
        } else if (strcmp(cmd, "mcp") == 0) {
            st = cli_do_mcp(&e, argv, argc, out_action);
        } else if (strcmp(cmd, "class") == 0) {
            st = cli_do_class(&e, argv, argc, out_action);
        } else {
            *out_action = SRMECH_CLI_ACTION_ERROR;   /* invalid choice */
            st = SRMECH_OK;
        }
    }
    if (st != SRMECH_OK) { return st; }
    if (*out_action == SRMECH_CLI_ACTION_ERROR) { *out_exit = 2; }
    *out_len = e.used;
    if (*out_action == SRMECH_CLI_ACTION_RUN && e.used > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Public: srmech_cli_dispatch — read "command" from the parsed JSON, route.
 * ------------------------------------------------------------------ */

/* Match the value after the FIRST `"command":` against the known commands. */
static int cli_command_route(const char *json, size_t len, int *route)
{
    const char *key = "\"command\":";
    size_t kl = 10u, i;
    assert(json != NULL || len == 0u);
    assert(route != NULL);
    for (i = 0u; i + kl <= len; i++) {
        if (strncmp(&json[i], key, kl) == 0) {
            const char *v = &json[i + kl];
            size_t rem = len - (i + kl);
            if (rem >= 4u && strncmp(v, "null", 4u) == 0) { *route = SRMECH_CLI_ROUTE_HELP; return 1; }
            if (rem >= 8u && strncmp(v, "\"status\"", 8u) == 0) { *route = SRMECH_CLI_ROUTE_STATUS; return 1; }
            if (rem >= 5u && strncmp(v, "\"bus\"", 5u) == 0) { *route = SRMECH_CLI_ROUTE_BUS; return 1; }
            if (rem >= 5u && strncmp(v, "\"dsl\"", 5u) == 0) { *route = SRMECH_CLI_ROUTE_DSL; return 1; }
            if (rem >= 5u && strncmp(v, "\"mcp\"", 5u) == 0) { *route = SRMECH_CLI_ROUTE_MCP; return 1; }
            if (rem >= 7u && strncmp(v, "\"class\"", 7u) == 0) { *route = SRMECH_CLI_ROUTE_CLASS; return 1; }
            return 0;
        }
    }
    return 0;
}

srmech_status_t srmech_cli_dispatch(const char *parsed_json, size_t len,
                                    int *out_route)
{
    int route = SRMECH_CLI_ROUTE_HELP;
    if (parsed_json == NULL || out_route == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(parsed_json != NULL);
    assert(out_route != NULL);
    if (!cli_command_route(parsed_json, len, &route)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out_route = route;
    return SRMECH_OK;
}
