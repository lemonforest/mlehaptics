"""Coupled-wave (EM quadrature) driver — the full-chirality (E, B) drive.

W17 / F577 (the "verb-flip / correct-structure" fix). A FLAT scalar driver
gates direction by ``sign(wave)``, which flips hard at every zero-crossing
(2 per cycle); when the driven element is *chiral/relational* (a verb), that
injects spurious reversals — a STRUCTURE error. A COUPLED quadrature wave
(``E = sin``, ``B = cos`` — 90 deg apart, exactly EM) rotates monotonically,
so the direction is the smooth rotation, **not** a flipping 1-bit sign.

Framework reading (F552): the flat sign is a chirality-COLLAPSED 1-bit
(Class K); the coupled ``(E, B)`` pair is the FULL-chirality 2D rotation
(gamma-5 / Klein-4 — the four ``(sign E, sign B)`` quadrants ARE the four
Klein-4 sectors used by :func:`parallel_sector_dispatch`).

**Handedness is a settable convention, never hardcoded.** Left- and
right-handed are both first-class options — the substrate privileges neither,
exactly as it privileges no byte-order (endianness is the CS precedent). The
two options are related by a Class-K phase sign-flip ``theta -> -theta`` (no
``abs``), and the chosen convention is echoed back in the result.

This is a *composition* of existing C-backed primitives
(``rational.{sin,cos}`` + Class-K ``pin_slot_at_zero``); it adds no new
irreducible kernel (``composition_of_c`` in the Rosetta ledger).
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

from srmech.amsc.rational import sin as _sin, cos as _cos
from srmech.amsc import hdc as _hdc
from srmech.amsc.format import sha256_bytes as _sha256

from .atoms import magnitude as _magnitude, pin_slot_at_zero

#: The trig component functions a coupled wave may use for its (E, B) legs.
_COMPONENTS = {"sin": _sin, "cos": _cos}


def _normalise_handedness(handedness: int) -> int:
    """Return the convention sign in ``{+1, -1}`` (Class-K, no ``abs``).

    Both handednesses are first-class; neither is privileged (endianness
    precedent). ``0`` is not a convention — it is rejected.
    """
    orient, _ = pin_slot_at_zero(float(handedness))
    assert orient in (-1, 0, 1)
    if orient == 0:
        raise ValueError(
            "handedness must be a nonzero convention (+1 or -1); "
            "the substrate privileges neither, but 0 selects no rotation sense"
        )
    return orient


def coupled_wave(
    theta: float,
    *,
    handedness: int = 1,
    components: Sequence[str] = ("sin", "cos"),
) -> Tuple[float, float, int, Tuple[int, int]]:
    """The coupled EM quadrature drive at phase ``theta`` (radians).

    Returns ``(E, B, handedness, klein4_quadrant)`` — the full-chirality
    rotation pair instead of a collapsed 1-bit sign.

    Args:
        theta: Phase angle in radians.
        handedness: The rotation-sense convention, ``+1`` or ``-1``. **Both
            are first-class; the default ``+1`` is an arbitrary convention,
            not a privileged truth** (endianness posture). ``-handedness`` is
            applied as a Class-K phase sign-flip ``theta -> -theta``.
        components: The ``(E_fn, B_fn)`` quadrature pair, each ``"sin"`` or
            ``"cos"`` and the two distinct. Default ``("sin", "cos")`` =>
            ``E = sin(theta)``, ``B = cos(theta)``.

    Returns:
        ``(E, B, handedness, klein4_quadrant)`` where ``E``/``B`` are the
        quadrature legs (float, C-dispatched, exact-rational underneath),
        ``handedness`` echoes the chosen convention (stable — it does NOT
        flip with ``theta``), and ``klein4_quadrant = (sign E, sign B)`` is
        the Klein-4 sector (each sign via Class-K ``pin_slot_at_zero``).
    """
    assert isinstance(theta, (int, float))
    assert len(components) == 2, "components must be an (E, B) pair"
    e_name, b_name = components[0], components[1]
    if e_name not in _COMPONENTS or b_name not in _COMPONENTS:
        raise ValueError(
            f"components must each be 'sin' or 'cos'; got {components!r}"
        )
    if e_name == b_name:
        raise ValueError(
            "components must be a quadrature pair (one 'sin', one 'cos'); "
            f"got {components!r}"
        )
    h = _normalise_handedness(handedness)
    # -handedness == a Class-K phase sign-flip (no abs), reversing the
    # rotation sense / mirroring the chirality.
    phase = theta if h > 0 else -theta
    e_val = _COMPONENTS[e_name](phase)
    b_val = _COMPONENTS[b_name](phase)
    sign_e, _ = pin_slot_at_zero(e_val)
    sign_b, _ = pin_slot_at_zero(b_val)
    return (e_val, b_val, h, (sign_e, sign_b))


_MULTIPLEX_MODES = ("roundrobin", "pickbest", "superpose")

#: Role-tag hypervector width (bytes) — the storage anchor for the clause-slot
#: assignment (NOT the driver waves, which are real-valued).
_ROLE_HV_BYTES = 32


def _role_hv(label: str, width_bytes: int = _ROLE_HV_BYTES) -> bytes:
    """A deterministic role/identity hypervector for ``label``.

    Class-M anchor: SHA-256 of the label, tiled / truncated to ``width_bytes``.
    Deterministic (same label -> same HV) so a bound role tag is unbindable.
    Routes through ``sha256_bytes`` (native dispatch) per hashing discipline.
    Used ONLY for the clause-role *tag storage*, never for the wave recombine.
    """
    assert isinstance(label, str)
    assert width_bytes > 0
    seed = bytes.fromhex(_sha256(label.encode("utf-8")))
    out = (seed * (width_bytes // len(seed) + 1))[:width_bytes]
    assert len(out) == width_bytes
    return out


def multiplex_streams(
    streams: Sequence[Sequence[float]],
    *,
    mode: str = "roundrobin",
    roles: Sequence[str] = None,
) -> Dict[str, object]:
    """Recombine N steering WAVES into one driver — the multiplex (W18).

    A *stream* is a per-step DRIVER WAVE — a real-valued steering signal that
    decides which content gets selected downstream, **not** the content/tokens.
    The output is a single steering *driver*; emission (the fluency-ear +
    manifold gate that turns the driver into tokens) is a SEPARATE consumer —
    W18 stops at the driver and keeps that layer boundary. Ideally each stream
    is a coupled ``(E, B)`` wave from :func:`coupled_wave`, so it carries a
    stable rotation (bearing) instead of a flipping sign (the F577 verb-flip
    fix); W17 and W18 compose.

    Per F573/F577 the multi-stream is for **correct sentence STRUCTURE**
    (clause-role assignment, S-V-O), not richness/embellishment.

    Args:
        streams: N equal-length real-valued sequences (the steering waves).
        mode:
            - ``"roundrobin"`` (default; the validated-best F573 multiplex):
              the ``t mod N`` schedule — stream ``t % N`` drives step ``t``.
            - ``"superpose"``: real-field interference — elementwise SUM across
              streams, then renormalise by the driver's max magnitude (like
              summing E-fields). The weakest combiner (averages N waves into
              one drive); shipped, but not the default for that reason.
            - ``"pickbest"``: the strongest-bearing stream wins each step (max
              Class-K magnitude). A pure-WAVE pick — distinct from a downstream
              content-fluency pick.
        roles: Optional N clause-role labels (e.g. ``("S", "V", "O")``),
            length-matched to ``streams``. Role ``k`` steers clause-slot ``k``
            sequentially; the verb stream especially should be a coupled
            ``(E, B)`` bearing (W17) so its which-way can't flip mid-clause.
            Each ``(stream, role)`` is tagged via Class-M ``hdc.bind`` purely
            as unbindable STORAGE of the role assignment.

    Returns:
        ``{"driver", "mode", "n_streams", "length", "roles", "role_bound",
        "layer"}`` — ``driver`` is the single recombined real-valued steering
        wave; ``role_bound`` is the clause-slot tagging when ``roles`` is given.

    Note:
        ``streams`` are real-valued *waves*; ``hdc.bind``/``bundle`` (bipolar
        HDC *content* vectors) are a different layer and are NOT used to
        recombine the driver — only to store the role tag. A content-vector
        multiplex would be a separate signature.
    """
    assert streams is not None
    n = len(streams)
    if n == 0:
        raise ValueError("streams must be non-empty")
    length = len(streams[0])
    for s in streams:
        if len(s) != length:
            raise ValueError("all streams must have equal length")
    if mode not in _MULTIPLEX_MODES:
        raise ValueError(f"mode must be one of {_MULTIPLEX_MODES}; got {mode!r}")
    if roles is not None and len(roles) != n:
        raise ValueError("roles must be length-matched to streams")

    driver = _recombine_waves(streams, mode, n, length)
    role_bound = _bind_roles(roles, n) if roles is not None else None
    return {
        "driver": driver,
        "mode": mode,
        "n_streams": n,
        "length": length,
        "roles": tuple(roles) if roles is not None else None,
        "role_bound": role_bound,
        "layer": "steering-driver (emission is a separate downstream consumer)",
    }


def _recombine_waves(streams, mode, n, length):
    """Recombine N real-valued steering waves into one driver wave."""
    assert n > 0
    assert length >= 0
    if mode == "roundrobin":
        # The t mod N multiplex — stream (t % N) drives step t.
        return [float(streams[t % n][t]) for t in range(length)]
    if mode == "pickbest":
        # Strongest-bearing wave wins each step (Class-K magnitude).
        out = []
        for t in range(length):
            best_i = 0
            best_m = _magnitude(float(streams[0][t]))
            for i in range(1, n):
                m = _magnitude(float(streams[i][t]))
                if m > best_m:
                    best_m, best_i = m, i
            out.append(float(streams[best_i][t]))
        return out
    # superpose — real-field interference: elementwise SUM, then renormalise
    # by the driver's peak magnitude (keeps the steering wave bounded).
    summed = [sum(float(streams[i][t]) for i in range(n)) for t in range(length)]
    peak = 0.0
    for v in summed:
        m = _magnitude(v)
        if m > peak:
            peak = m
    if peak == 0.0:
        return summed
    return [v / peak for v in summed]


def _bind_roles(roles, n):
    """Tag each stream to its clause slot (role k -> slot k), with an
    unbindable Class-M ``hdc.bind`` storage tag (NOT a driver recombine)."""
    assert roles is not None
    assert len(roles) == n
    bindings = []
    for i in range(n):
        stream_hv = _role_hv(f"stream{i}")
        role_hv = _role_hv(roles[i])
        bindings.append({
            "stream": i,
            "role": roles[i],
            "clause_slot": i,
            "tag": _hdc.bind(stream_hv, role_hv),  # unbindable role tag
        })
    return {
        "stream_roles": tuple(roles),
        "semantic": "role k steers clause-slot k sequentially; the verb stream "
                    "should be a coupled (E,B) bearing (W17) so its which-way "
                    "cannot flip mid-clause (F577)",
        "bindings": bindings,
    }


__all__ = ["coupled_wave", "multiplex_streams"]
