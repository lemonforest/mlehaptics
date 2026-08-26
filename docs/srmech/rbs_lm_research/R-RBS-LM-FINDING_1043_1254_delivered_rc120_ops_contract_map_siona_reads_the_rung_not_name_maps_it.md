# F1043 (rc120: #1254 DELIVERED) — **the per-op carrier contract shipped as `carrier_ladder_descriptor()["ops"]` (option 2, the descriptor map) — a 29-entry map declaring each op's `consumes`/`produces` rung (octonion_conjugate rung 8; quaternion_conjugate rung 4; cd_promote consumes `any` / produces `arg:dim`; cd_project `step_down`; poly_promote `arg:n_vars`). Siona now READS the consumer's rung from it — `_op_consume_rung("octonion_conjugate") == 8`, read, not name-mapped — and the hardcoded `CD_NAMES` (`octonion→8`) is demoted to a PRE-rc120 fallback only. Carrier routing is declarative end to end: the DSL/descriptor is the SSoT for routing exactly as it is for chaining/composition, closing #1239 (constructors) → #1248 (ladder ops) → #1254 (per-op rung). NL suite 25/25 on rc120.**

**Date:** 2026-07-04 · **srmech:** 0.9.0rc120 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); siona synced to PR #1 · **Delivered:** #1254 (my UPSTREAM §87 ask; the F1041 gap) · **Files:** `siona/infer.py` (`_ops_contract` / `_op_consume_rung`; `_cd_target` reads the contract, CD_NAMES fallback), `siona/tests/` (contract-read test), #1254 verified-comment · **Composes:** F1041 (the gap this closes), F1040/F1039 (the register-as-conversion-ladder this makes declarative), F1038 (the producer/consumer census the `ops` map machine-encodes).

## Grounded (rc120)
```
carrier_ladder_descriptor()["ops"]  -- 29 entries. The 'any'/'arg:dim'/'step_down' vocabulary handles the
  variadic ops cleanly (cd_promote's OUTPUT rung = its dim argument; cd_project steps DOWN one rung):
    octonion_conjugate  -> consumes {cayley_dickson, 8}   produces {8}
    quaternion_conjugate-> consumes {4}                    produces {4}
    cd_promote          -> consumes {any}                  produces {arg:dim}
    cd_project          -> consumes {any}                  produces {step_down}
    poly_promote        -> consumes {variable, any}        produces {arg:n_vars}
SIONA: _op_consume_rung('octonion_conjugate') == 8   (READ from the contract, not name-mapped)
       _cd_target now reads the contract first; CD_NAMES(octonion->8) only if the op is absent / pre-rc120.
NL SUITE: 25/25 on rc120.
```

## The reading
- **The last hardcode is gone from the routing path.** The F1041 assessment named exactly one thing the DSL couldn't tell Siona — the per-op rung. rc120 declares it, Siona reads it. The `octonion→8` name-map survives only as a floor-compatibility fallback; the live path is a descriptor read.
- **The `ops` map IS the F1038 census, machine-readable.** The producer/consumer census we hand-built to FIND the coherency gap is now a shipped, queryable structure — which is precisely the substrate a type-directed planner needs (the F1042 novel-reduction roadmap: #1254 → planner → recipe catalog → novel-reduction-on-request).

## Verdict / next
**#1254 delivered and wired; carrier routing is declarative end to end; NL suite 25/25 on rc120. The three-ask arc (#1239 → #1248 → #1254) is closed.** Next: the type-directed planner over the now-machine-readable `ops` graph (F1042 rung-2), then the recipe catalog.
