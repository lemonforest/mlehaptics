"""SPIKE `#T1114` rung 4 — PROTOTYPE: a general INDEXED MAP for the
declarative cascade surfaces.  EXTERNAL instrument — nothing here ships;
nothing here modifies a shipped op or surface.

WHAT THE PROTOTYPE IS
---------------------
An extension of the ADR-0008 SS2 compose surface (srmech.cascade.compose)
with THREE additional step forms, evaluated by this module's own runner:

  map step     {"map_over": <ref>, "index": <name>, "bind": {..}, "body": [steps]}
               n = len(resolve(map_over)) is FIXED AT ENTRY (a sized
               sequence is required; an unsized iterable is rejected).
               The body runs once per k in 0..n-1 with the NEW reference
               form ``@idx.<name>`` bound to k, and ``@bind.<name>`` bound
               to the entry-resolved bind values.  Output = the list of
               per-iteration body-final outputs.  Maps NEST; inner bodies
               see outer indices and binds (layered envs).
  fold step    {"fold_class": L, "fold_op": name, "fold_init": lit, "over": <ref>}
               the DSL surface's existing catamorphism-with-seed, ported
               to this surface (BLK-ITER-COMPOSE see-past, not new).
  std step     {"class": L, "op": name, "args": {...}} — the shipped SS2
               step form, resolved through the same letter->module registry.

NEW REFERENCE FORMS (the rung-4 design decision):
  ``@idx.<name>``   the current index of the named enclosing map — REQUIRED;
                    measured below: the shipped grammar (compose.py:107
                    ``_REFERENCE_PATTERN``) rejects any new namespace, and the
                    shipped ``[N]`` indexer is literal-only, so a computed
                    index can never be spelled in the shipped grammar.
  ``@bind.<name>``  a map-entry-resolved closure value.  A convenience — the
                    same values could be re-derived per iteration — but body
                    step outputs are BODY-LOCAL (``@step[N]`` inside a body
                    indexes the body's own steps), so without ``@bind`` a body
                    could not see outer prelude steps at all.  The scoping
                    fork (body-local vs chain-global step outputs) is a real
                    design decision the shipped grammar has never had to answer.

EXTERNAL STUBS (labelled; NEVER counted as shipped surface)
-----------------------------------------------------------
The census discipline (rung 1/3): anything run under an override registry or
with external stubs is LABELLED and never counted as a pass of the shipped
inventory.  Two stub kinds here, deliberately separated:

  (a) MISSING FRAMING/ACCESS LEAVES — seq_len / seq_get / f64_add / vec_add /
      vec_scale.  Genuinely absent from the registered inventory (measured by
      the harness's reachability probe).  Pointwise/total; no iteration inside
      except the fixed carrier dimension.
  (b) SHIPPED-LEAF WRAPPERS — qdft_summand / odft_summand / kuramoto_* /
      ac_term / as_quat4 / as_oct8 / resolve_mu4 / resolve_mu8 / dft_sigma /
      dft_scale / neumaier_sum.  Thin wrappers around the SHIPPED private
      helpers (qm.quaternion._twiddle_resolved, qm.octonion._resolve_mu8,
      cascade.composites._compensated_sum, ...) reproducing the shipped
      float-op order EXACTLY, so the bit-identity measurement isolates the
      ITERATION SCHEME as the only variable.  The iteration itself (over k,
      m, i, j) is NEVER inside a stub — it lives in the map/fold combinator
      layer, which is the thing under test.  ``neumaier_sum`` is the one
      whole-list delegation: the shipped compensated summation IS a fold with
      a (sum, compensation) pair accumulator + a final combine; expressing it
      as a declarative fold needs the pair/framing inventory (BLK-FRAMING),
      so it is delegated as a leaf and reported as such.

CLASS-HONESTY CAVEAT: the harness's override registry assigns these stubs to
letters (E/M/N/K) purely as see-past plumbing for the fixed letter->module
resolver (BLK-REGMAP, already catalogued at rung 3) — the letter assignments
are NOT class-identity claims.

No ``abs()`` anywhere.  No numpy / math / fractions / decimal.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import importlib

from srmech.cascade import compose as _compose

# ── the extended reference resolver ──────────────────────────────────────

_EXT_NAMESPACES = ("@idx.", "@bind.")


def _resolve_ref_ext(ref, *, row, inputs, step_outputs, idx_env, bind_env):
    if ref.startswith("@idx."):
        name = ref[len("@idx."):]
        if name not in idx_env:
            raise KeyError(f"@idx.{name}: no enclosing map binds index {name!r}")
        return idx_env[name]
    if ref.startswith("@bind."):
        name = ref[len("@bind."):]
        if name not in bind_env:
            raise KeyError(f"@bind.{name}: no enclosing map binds {name!r}")
        return bind_env[name]
    return _compose._resolve_reference(
        ref, row=row, inputs=inputs, step_outputs=step_outputs)


def _resolve_args_ext(args, *, row, inputs, step_outputs, idx_env, bind_env):
    if isinstance(args, str):
        if args.startswith("@"):
            return _resolve_ref_ext(
                args, row=row, inputs=inputs, step_outputs=step_outputs,
                idx_env=idx_env, bind_env=bind_env)
        return args
    if isinstance(args, dict):
        return {k: _resolve_args_ext(v, row=row, inputs=inputs,
                                     step_outputs=step_outputs,
                                     idx_env=idx_env, bind_env=bind_env)
                for k, v in args.items()}
    if isinstance(args, (list, tuple)):
        seq = [_resolve_args_ext(v, row=row, inputs=inputs,
                                 step_outputs=step_outputs,
                                 idx_env=idx_env, bind_env=bind_env)
               for v in args]
        return tuple(seq) if isinstance(args, tuple) else seq
    return args


# ── op resolution (same letter->module registry contract as shipped) ─────

def _resolve_op(class_id: str, op: str, registry: Optional[Dict[str, str]]):
    reg = registry or _compose.DEFAULT_CLASS_REGISTRY
    module_name = reg.get(class_id)
    if module_name is None:
        raise _compose.ChainSpecError(
            f"class {class_id!r} has no registered module")
    module = importlib.import_module(module_name)
    fn = getattr(module, op, None)
    if fn is None or not callable(fn):
        raise _compose.ChainSpecError(
            f"op {op!r} not found on {module_name!r}")
    return fn


# ── the extended runner ──────────────────────────────────────────────────

def run_ext_steps(steps: List[dict], registry, *, row=None, inputs=None,
                  idx_env=None, bind_env=None) -> Any:
    """Run an extended step list; returns the final step's output.

    TOTALITY (the rung-4 (c) argument, stated where it is enforced):
    a map step resolves ``map_over`` to a SIZED sequence and fixes
    ``n = len(seq)`` BEFORE the first body run; the body is a finite,
    descriptor-static step list; nesting depth is descriptor-static.
    So a chain of these steps performs exactly a descriptor-static
    number of op calls per input element product — total iff every leaf
    op is total, which is the SAME contract the shipped fold/reduce
    already run under (make_fold_stage iterates ``for elem in input_seq``
    over a runtime-length input).  No predicate decides continuation
    anywhere in this runner.
    """
    inputs = inputs or {}
    idx_env = idx_env or {}
    bind_env = bind_env or {}
    outs: List[Any] = []
    for st in steps:
        if "map_over" in st:
            outs.append(_run_map(st, registry, row, inputs, outs,
                                 idx_env, bind_env))
        elif "fold_op" in st:
            outs.append(_run_fold(st, registry, row, inputs, outs,
                                  idx_env, bind_env))
        else:
            args = _resolve_args_ext(
                st.get("args", {}), row=row, inputs=inputs,
                step_outputs=outs, idx_env=idx_env, bind_env=bind_env)
            fn = _resolve_op(st["class"], st["op"], registry)
            outs.append(fn(**args))
    return outs[-1] if outs else None


def _run_map(st, registry, row, inputs, outer_outs, idx_env, bind_env):
    seq = _resolve_ref_ext(st["map_over"], row=row, inputs=inputs,
                           step_outputs=outer_outs, idx_env=idx_env,
                           bind_env=bind_env)
    try:
        n = len(seq)                      # n FIXED AT ENTRY — the totality pin
    except TypeError:
        raise _compose.ChainSpecError(
            "map_over must resolve to a SIZED sequence (len()-able); an "
            "unsized iterable would make n data-dependent at run time")
    index_name = st.get("index", "k")
    binds = {}
    for name, ref in (st.get("bind") or {}).items():
        binds[name] = _resolve_args_ext(
            ref, row=row, inputs=inputs, step_outputs=outer_outs,
            idx_env=idx_env, bind_env=bind_env)
    bind2 = {**bind_env, **binds}
    idx2 = dict(idx_env)
    body = st["body"]
    out = []
    for k in range(n):                    # exactly n body runs, no predicate
        idx2[index_name] = k
        out.append(run_ext_steps(body, registry, row=row, inputs=inputs,
                                 idx_env=dict(idx2), bind_env=bind2))
    return out


def _run_fold(st, registry, row, inputs, outer_outs, idx_env, bind_env):
    seq = _resolve_ref_ext(st["over"], row=row, inputs=inputs,
                           step_outputs=outer_outs, idx_env=idx_env,
                           bind_env=bind_env)
    acc = _resolve_args_ext(st["fold_init"], row=row, inputs=inputs,
                            step_outputs=outer_outs, idx_env=idx_env,
                            bind_env=bind_env)
    fn = _resolve_op(st["fold_class"], st["fold_op"], registry)
    for elem in seq:                      # the DSL make_fold_stage contract
        acc = fn(acc, elem)
    return acc


def load_ext_chains(toml_path: str) -> Dict[str, dict]:
    from srmech import _toml as _srmech_toml
    with open(toml_path, "rb") as fh:
        data = _srmech_toml.loads(fh.read().decode("utf-8"))
    return {c["name"]: c for c in data["chain"]}


# ═════════════════════════════════════════════════════════════════════════
# EXTERNAL STUBS — kind (a): missing framing/access leaves
# ═════════════════════════════════════════════════════════════════════════

def seq_len(seq) -> int:
    """LENGTH — no registered op surfaces it (measured by the harness probe)."""
    return len(seq)


def seq_get(seq, i):
    """DYNAMIC element access seq[i] — the shipped reference grammar's ``[N]``
    indexer is literal-only (compose.py:108: ``\\[\\d+\\]``), so a computed
    index can only enter through an op.  No registered op does this."""
    return seq[i]


def f64_add(a, b):
    """Scalar accumulate a+b (the fold body for Σ).  No registered float add."""
    return a + b


def vec_add(a, b):
    """Elementwise vector accumulate — the Σ_m fold body for the DFT chains.
    Left-fold from a zero seed reproduces ``acc[i] += term[i]`` bit-exactly
    (0.0 + t == t; then the identical add order)."""
    return [a[i] + b[i] for i in range(len(a))]


def vec_scale(v, s):
    """Elementwise scale — mirrors ``[acc[i] * scale for i in range(dim)]``."""
    return [v[i] * s for i in range(len(v))]


# ═════════════════════════════════════════════════════════════════════════
# EXTERNAL STUBS — kind (b): shipped-leaf wrappers (float order preserved)
# ═════════════════════════════════════════════════════════════════════════

def neumaier_sum(values):
    """The shipped Kahan-Babuska-Neumaier compensated Σ (composites.
    _compensated_sum) as one leaf.  IS a fold with a (sum, compensation)
    pair accumulator + final combine — declaratively expressible only with
    the pair/framing inventory (BLK-FRAMING); delegated and LABELLED."""
    from srmech.cascade.composites import _compensated_sum
    return _compensated_sum(values)


def as_quat4(v):
    """Shipped QDFT sample coercion (hypercomplex_dft._as_quat4)."""
    from srmech.cascade.hypercomplex_dft import _as_quat4
    return _as_quat4(v)


def as_oct8(v):
    """Shipped ODFT sample coercion (hypercomplex_dft._as8)."""
    from srmech.cascade.hypercomplex_dft import _as8
    return _as8(v)


def resolve_mu4(mu_axis):
    """Shipped one-resolution mu-hat contract (hypercomplex_dft._resolve_mu4_qdft)."""
    from srmech.cascade.hypercomplex_dft import _resolve_mu4_qdft
    return _resolve_mu4_qdft(mu_axis)


def resolve_mu8(mu_axis):
    """Shipped ODFT axis resolution (physics.qm.octonion._resolve_mu8)."""
    from srmech.physics.qm import octonion as _oct
    return _oct._resolve_mu8(mu_axis, "octonion_dft")


def dft_sigma(inverse):
    """``sigma = 1 if inverse else -1`` — the shipped composed-path line."""
    return 1 if inverse else -1


def dft_scale(inverse, n):
    """``scale = (1.0 / float(n)) if inverse else 1.0`` — the shipped line;
    the ``n > 0`` guard mirrors the public wrapper's ``if not xs: return []``
    early-return (wrapper-layer, not iteration-layer)."""
    return (1.0 / float(n)) if (inverse and n > 0) else 1.0


def qdft_summand(xs, k, m, n, left, sigma, mu_hat):
    """ONE (k, m) summand of the QDFT — twiddle -> 4x4 operator -> row-dot
    left-to-right, the exact float order of _qdft_composed's inner loop.
    Pointwise and total; the k/m iteration stays in the combinator layer."""
    from srmech.physics.qm.quaternion import (
        _twiddle_resolved, quaternion_left_mult, quaternion_right_mult)
    w = _twiddle_resolved(k, m, n, sigma, mu_hat)
    op = quaternion_left_mult(w) if left else quaternion_right_mult(w)
    rows = op.tolist()
    xm = xs[m]
    out = []
    for i in range(4):
        t = 0.0
        for c in range(4):
            t += rows[i][c] * xm[c]
        out.append(t)
    return out


def odft_summand(xs, k, m, n, form, bracketing, sigma, mu_hat, mu_r_hat):
    """ONE (k, m) summand of the ODFT — the exact float order of
    _odft_composed's inner loop, including the DECLARED two-sided
    bracketing order (F378)."""
    from srmech.physics.qm.octonion import (
        _twiddle_resolved, octonion_left_mult, octonion_right_mult)
    from srmech.cascade.hypercomplex_dft import _odft_matvec8
    w = _twiddle_resolved(k, m, n, sigma, mu_hat)
    two_sided = form == "two_sided"
    left = form == "left"
    left_assoc = bracketing == "left_associated"
    if two_sided:
        w_r = _twiddle_resolved(k, m, n, sigma, mu_r_hat)
        if left_assoc:                     # (W_l . x) . W_r
            inner = _odft_matvec8(octonion_left_mult(w).tolist(), xs[m])
            return _odft_matvec8(octonion_right_mult(w_r).tolist(), inner)
        inner = _odft_matvec8(octonion_right_mult(w_r).tolist(), xs[m])
        return _odft_matvec8(octonion_left_mult(w).tolist(), inner)
    if left:                               # W . x
        return _odft_matvec8(octonion_left_mult(w).tolist(), xs[m])
    return _odft_matvec8(octonion_right_mult(w).tolist(), xs[m])


def kuramoto_inv_n(coupling, n):
    """``inv_n = (float(coupling) / n) if n > 0 else 0.0`` — the shipped line."""
    return (float(coupling) / n) if n > 0 else 0.0


def kuramoto_sin_term(theta, i, j):
    """ONE (i, j) coupling term of the SIMPLE path: ``sin(theta_j - theta_i)``
    via the shipped Class-N rational sin (composites' _rsin).  The simple
    path weights the SUM (inv_n * S), not the terms — order preserved."""
    from srmech.math.rational import sin as _rsin
    return _rsin(float(theta[j]) - float(theta[i]))


def kuramoto_out_simple(theta, omega, i, s, inv_n, dt):
    """``theta_i + h*(omega_i + inv_n*S)`` — the shipped simple-path line."""
    h = float(dt)
    theta_i = float(theta[i])
    return float(theta_i + h * (float(omega[i]) + inv_n * s))


def kuramoto_gen_term(theta, adjacency, coupling, inv_n, alpha, i, j):
    """ONE (i, j) term of the GENERAL path: ``w * sin(theta_j - theta_i - a)``
    with ``w = K*A[i][j]`` (rc15 SS32 fix) or ``inv_n`` — weight per TERM,
    matching the shipped general-path float order."""
    from srmech.math.rational import sin as _rsin
    a = float(alpha)
    kc = float(coupling)
    w = (kc * float(adjacency[i][j])) if adjacency is not None else inv_n
    return w * _rsin(float(theta[j]) - float(theta[i]) - a)


def kuramoto_gen_out(theta, omega, i, s, psi, ps, dt):
    """General-path combine: ``f = omega_i + S``; ``+ p_i*sin(psi_i - theta_i)``
    when pinned; ``theta_i + h*f``.  The psi-None branch mirrors the shipped
    leaf-internal branch (the exile-to-op-instance pattern, not iteration)."""
    from srmech.math.rational import sin as _rsin
    theta_i = float(theta[i])
    f = float(omega[i]) + s
    if psi is not None:
        p_i = float(ps[i]) if hasattr(ps, "__len__") else float(ps)
        f += p_i * _rsin(float(psi[i]) - theta_i)
    return float(theta_i + float(dt) * f)


def ac_term(x, i, j):
    """ONE (i, j) product of the circular autocorrelation:
    ``float(x[i]) * float(x[j])`` (the shipped per-element float coercion is
    idempotent on floats; j = (i+k) mod n arrives from the REGISTERED
    Class-I mod_add step — the index arithmetic needs NO stub)."""
    return float(x[i]) * float(x[j])


# ═════════════════════════════════════════════════════════════════════════
# The DSL-surface variant — for the closure-test measurement ONLY
# ═════════════════════════════════════════════════════════════════════════

def make_map_indexed_stage(body_fn):
    """The sixth-builder shape at the DSL layer: input -> [body(k, input)
    for k in range(len(input))].  n fixed at entry; body total => stage
    total — the same totality class as make_fold_stage."""
    def map_fn(input_seq):
        n = len(input_seq)                # fixed BEFORE the first body call
        return [body_fn(k, input_seq) for k in range(n)]
    return map_fn


def widened_chain_class():
    """A Chain SUBCLASS carrying ``map_indexed`` — built only so the harness
    can measure, against the SHIPPED closure test's own sets, that a sixth
    builder is caught (the letter break).  Never registered anywhere."""
    from srmech.dsl import Chain

    class MapChain(Chain):
        __slots__ = ()

        def map_indexed(self, body):      # the hypothetical sixth builder
            self._guard_not_terminal()
            stage_fn = make_map_indexed_stage(body)
            self._stages.append(("map_indexed(<body>)", stage_fn, {}))
            self._native_ir.append(None)
            return self

    return MapChain
