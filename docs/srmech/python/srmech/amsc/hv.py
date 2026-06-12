"""srmech.amsc.hv — the framework-native hypervector carrier (numpy-free).

The §22 / §22b boundary-type lever (UPSTREAM_NOTES, RBS-LM research subtree):
the core A-N primitive vocabulary returns an :class:`HV` handle over a stdlib
``array('B')`` buffer, **NOT** a raw ``numpy.ndarray``. A numpy-typed return
invites ``np.dot`` / ``np.linalg`` on the value; a framework-native handle
**forces the srmech op** — the value stays inside the framework until you
convert out *on purpose*.

Convert out explicitly:

* ``hv.tolist()`` / ``hv.tobytes()`` — stdlib, always available;
* ``hv.to_numpy()`` — the opt-in numpy bridge (lazy import; raises a clear
  message if numpy is absent — the numpy-free path is ``.tolist()``).

This module imports **no numpy at load time** — it is part of the numpy-free
core (the "runs embedded without numpy/LAPACK" identity). The underlying
``array('B')`` is contiguous + buffer-protocol, so the native C ops can read
and write it in place via ctypes (HAS_NATIVE keeps ``HV`` fast; the pure-
Python path is only the no-native worst case).

Distinct from ``srmech.spectral.SpectralHandle`` (that carries spectral
signatures; ``HV`` carries a raw hypervector) and intentionally lightweight.
"""
from __future__ import annotations

from array import array
from typing import Iterable, Iterator, List, Union

__all__ = ["HV"]

#: Accepted input shapes for :meth:`HV.from_sequence`.
HVLike = Union["HV", bytes, bytearray, "array", Iterable[int]]


class HV:
    """A numpy-free hypervector: an ``array('B')`` buffer + a ``sectors`` count.

    ``sectors`` is the carrier alphabet size (4 for the Klein-4 carrier — the
    order-2 (F₂)² states ``{0, 1, 2, 3}``). The buffer holds one sector index
    per position.
    """

    __slots__ = ("_buf", "sectors")

    def __init__(self, buf: "array", *, sectors: int = 4) -> None:
        assert isinstance(buf, array), "HV buffer must be an array.array"
        assert buf.typecode == "B", "HV buffer must be array('B') (uint8)"
        assert isinstance(sectors, int) and not isinstance(sectors, bool), (
            "HV sectors must be a plain int"
        )
        assert sectors >= 2, "HV sectors must be >= 2"
        self._buf = buf
        self.sectors = sectors

    # ── construction ──────────────────────────────────────────────────────
    @classmethod
    def from_sequence(cls, seq: HVLike, *, sectors: int = 4) -> "HV":
        """Build an ``HV`` from an HV / bytes / ``array`` / ``np.ndarray`` /
        iterable-of-ints. Copies the data (the new HV owns its buffer)."""
        if isinstance(seq, HV):
            return cls(array("B", seq._buf), sectors=seq.sectors)
        if isinstance(seq, (bytes, bytearray)):
            return cls(array("B", seq), sectors=sectors)
        if isinstance(seq, array) and seq.typecode == "B":
            return cls(array("B", seq), sectors=sectors)
        buf = array("B")
        for x in seq:  # list / tuple / np.ndarray (1-D) / generator
            xi = int(x)
            if xi < 0 or xi > 255:
                raise ValueError(f"HV element out of byte range [0, 255]: {x!r}")
            buf.append(xi)
        return cls(buf, sectors=sectors)

    # ── numpy-free access ─────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self._buf)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return HV(self._buf[idx], sectors=self.sectors)
        return int(self._buf[idx])  # PLAIN int — never a numpy scalar (§22b (b))

    def __iter__(self) -> Iterator[int]:
        return (int(x) for x in self._buf)

    def __eq__(self, other) -> bool:
        """Value-equality → a scalar ``bool`` (never an elementwise array).

        Accepts another ``HV``, a list/tuple, ``bytes``, or a 1-D
        ``numpy.ndarray`` — so the research-side ``np.array_equal(rec, v)``
        migration is just ``rec == v`` (§22b (b))."""
        if other is self:
            return True
        if isinstance(other, HV):
            return list(self._buf) == list(other._buf)
        if hasattr(other, "tolist"):  # numpy.ndarray and friends
            other_seq = other.tolist()
        else:
            try:
                other_seq = list(other)
            except TypeError:
                return NotImplemented
        try:
            return list(self._buf) == [int(x) for x in other_seq]
        except (TypeError, ValueError):
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    __hash__ = None  # mutable buffer → unhashable (like list)

    def __repr__(self) -> str:
        n = len(self._buf)
        head = ", ".join(str(int(x)) for x in self._buf[:8])
        ellipsis = ", …" if n > 8 else ""
        return f"HV(len={n}, sectors={self.sectors}, [{head}{ellipsis}])"

    # ── explicit conversions out ──────────────────────────────────────────
    def tolist(self) -> List[int]:
        """Stdlib ``list[int]`` copy (numpy-free)."""
        return [int(x) for x in self._buf]

    def tobytes(self) -> bytes:
        """Raw ``bytes`` copy (numpy-free; one byte per position)."""
        return self._buf.tobytes()

    @property
    def buffer(self) -> "array":
        """The underlying ``array('B')`` (contiguous, buffer-protocol — the
        handle the native C ops read/write in place). Mutating it mutates the
        HV; use :meth:`tolist` / :meth:`tobytes` for a copy."""
        return self._buf

