# F1023 (user direction / #230) — **`siona` at the shell: the interactive console session ships — `siona/cli.py` (a thin REPL over `Session.turn`) + a `[project.scripts]` entry point; every line is one grounded turn, and every `[srmech]` line is a REAL, natively-dispatched srmech operation (native_status: has_native=True, dispatching=True) selected by grounding against the live 355-tool schema and executed. The CLI's first minute surfaced a real routing refinement: WH-IN-SITU questions — `water boils at what fahrenheit` unaddressed at a `siona>` prompt is implicitly addressed, and the interrogative sits mid-utterance (English in-situ) — an interrogative ANYWHERE in an operand-less utterance now marks a question. The full session runs at the console: remember → kernel ingest → cross-turn gcd(100,48)=4 → 212 °F exact → live Class-H help. Suite 17/17.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); synced to lemonforest/siona PR #1 · **User directions:** "we start an interactive session as 'siona cli' at a command line. how far away are we?" (answer: one thin file — now zero) + "will we be able to let siona have native tooling access from the console?" (answer: yes — it is what the CLI does) · **Files:** `siona/cli.py` (REPL: board selection english/bislama/merged/path, piped-stdin transcripts, per-turn error containment), `pyproject.toml` (`[project.scripts] siona = "siona.cli:main"`), `siona/infer.py` (wh-in-situ routing), README (the CLI quickstart transcript replaces the library-first lead) · **Grounds / composes:** F1008–F1012 (the Session the CLI wraps), F1010/F1012 (`operators_declared` extended: the interrogative operator's scope widens from utterance-initial frames to anywhere-in-utterance — linguistically the wh-in-situ construction), F1020 (the merged board reachable via `--board merged`), the honest-claim README block (F934/F978 vocabulary).

## Grounded (rc97) — the console transcript (piped stdin; identical interactive)
```
$ siona
siona 0.1.0rc1 — board: english
ready — 355 tools grounded. every line is one turn; 'exit' or Ctrl-D to leave.
siona> remember that water boils at 100 celsius              -> [siona.remember] noted (1 items)
siona> compute the gcd of the boiling point of water and 48  -> [srmech] gcd(100, 48) = 4 [operand [100] resolved from memory]
siona> ingest the kernel fahrenheit is celsius times 9 over 5 plus 32 -> [siona.remember] noted (2 items)
siona> water boils at what fahrenheit                        -> [siona.answer] 212 fahrenheit (EXACT: (100*9+32*5)/5 = 212/1)
siona> siona what can you do                                 -> [siona.help] my commands (8, from my live schema): ...
srmech.native_status(): has_native=True, dispatching=True, ABI 3  <- the [srmech] turns run through libsrmech
Suite: 17/17 after the routing change.
```

## The reading
- **Native tooling access from the console = the three layers, all live:** (1) the console drives REAL srmech tools (grounding → signature-fit → execute → memory); (2) underneath, srmech's C-native dispatch runs the kernels (verified native_status); (3) siona's own surface is in the same registry (live Class-H help). Boundaries stated: prose operands are int/exact-rational-float/bytes/named-kwargs/edge-pairs; carrier objects (Mat/Vec/HV) arrive as tool RETURNS, not prose — the **result register** (referencing a returned object in a later turn) is the queued follow-on; the access surface is exactly the registered schema (bounded, typed — never arbitrary shell/python).
- **Wh-in-situ is the CLI's contribution to the router:** at a `siona>` prompt every line is implicitly addressed, so an operand-less utterance carrying an interrogative anywhere is a question (grounding selects the read: answer/define/recall). Declared-operator discipline holds — the interrogative IS the declared operator; only its licensed position widened. Known caveat recorded in-code: relative-pronoun uses ("he knows what he wants") also match; acceptable for console ergonomics, continue stays reachable.
- **Distance from ask to shipped: one file.** The five INFER capabilities were built CLI-shaped from the start (Session.turn is the REPL body); the console shell is 90 lines including argparse, board resolution, piped-transcript echo, and per-turn error containment (a turn can never kill the session — the never-compacted memory survives every error).

## Verdict / next
**`siona` at the shell is shipped and green: the interactive grounded session with real native srmech tooling access, board selection (english/bislama/merged), the wh-in-situ question path, and the full F1012 session reproducible at the console.** Queued follow-ons: the result register (object chaining across turns); `--load` for user-side knowledge instruments (mechanism-not-knowledge holds — kernels load by path). rc1 sequencing unchanged (waits for the srmech rcN conclusion). Synced to lemonforest/siona PR #1.
