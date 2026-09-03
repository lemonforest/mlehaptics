"""rc464 (`#T1188`) — RECORD the shipped SedenionRegister as a golden fixture.

Provenance generator, committed as provenance and NEVER run as a test. It
imports the class rc464 removes, so it can only ever run against a tree where
that class still exists; the fixture it writes is what survives.

WHY THIS EXISTS. Three shipped tests used the LIVE ``SedenionRegister`` as the
oracle ``CDRegister(16, namespace="SEDENION")`` is measured against, and one of
them (``tests/test_cd_register_rc297.py::test_sedenion_register_is_still_an_
independent_class_not_an_alias``) asserted through ``inspect.getsource`` that
the oracle does not mention the subject — the guarantee was CODE INDEPENDENCE:
two implementations that cannot share a failure mode because they do not share
a line.

Removing the oracle class does not weaken that guarantee if the guarantee MOVES
rather than being deleted. Recorded output cannot acquire the subject's failure
modes for a reason stronger than "different lines": it is not running. So the
guarantee becomes DATA PROVENANCE — these bytes were produced by the shipped
class, at a named commit, from a source file whose SHA-256 is in the header, and
every later comparison is against the bytes, never against a peer that could
drift with the subject.

WHAT IT RECORDS (one NDJSON record per line; ``kind`` names the record):

  header    provenance + the LAWS the shipped register rides on, so a reader can
            reconstruct why a probe has the value it has without the class
  probe     the rc297 faithfulness gate VERBATIM: 9 D values x 15 directions x 8
            keys = 1080 probes, each with the navmap-predicted destination and
            the (key, sign) actually read back there
  probe_hits the per-D hit count (pins 116/120 at D=256, 120/120 at D>=1024)
  navmap    navmap(j) for every j in [0,16) — the 16-slot signed permutation
  navigate  the slot routing of a fixed 4-slot occupancy at every j
  couple    the rc301 reversible-working-word records, as float.hex() strings
            (bit-exact; a decimal repr is not)
  carry     the Hamming EC codewords at n in {3,4}
  correct   every single-bit error position of each codeword, and its decode
  reads     the rc330 record: D=512, 5 signed slots, read() on all 16 + slots()
  storage   materialize() / unbind / clean at BYTE level (SHA-256 digests) for
            the rc140 and rc200 register fixtures at three D

Usage (from docs/srmech/python):
    python3 ../notes/_golden_sedenion_register_rc464.py [commit]

It writes tests/sedenion_register_golden_rc464.ndjson with LF newlines — the
pinned digest is over those exact bytes — and prints the digest to stderr.

numpy-free; no ``abs()``; every digest routes through
``srmech.amsc.format.sha256_bytes`` (no new ``hashlib.sha256`` call).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from srmech.amsc.format import sha256_bytes
from srmech.cascade.sedenion_register import SedenionRegister, sedenion_register
from srmech.math.hdc import bind
from srmech import _native

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, "..", "python"))
SRC = os.path.join(PKG, "srmech", "cascade", "sedenion_register.py")
OUT = os.path.join(PKG, "tests", "sedenion_register_golden_rc464.ndjson")

NAMES = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
D_VALUES = [256, 288, 320, 352, 384, 448, 512, 1024, 4096]


def _commit() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=PKG,
                          capture_output=True, text=True, check=True).stdout.strip()


def _rec(out, **kw):
    out.append(json.dumps(kw, sort_keys=True, separators=(",", ":")))


def _header(out) -> None:
    with open(SRC, "rb") as fh:
        src = fh.read()
    import srmech
    _rec(
        out,
        kind="header",
        recorded_by="docs/srmech/notes/_golden_sedenion_register_rc464.py",
        oracle="srmech.cascade.sedenion_register.SedenionRegister",
        oracle_source="srmech/cascade/sedenion_register.py",
        oracle_source_sha256=sha256_bytes(src),
        oracle_source_bytes=len(src),
        srmech_version=srmech.__version__,
        source_commit=_commit(),
        has_native=bool(_native.HAS_NATIVE),
        native_abi_version=_native.NATIVE_ABI_VERSION,
        laws={
            "address_mint_name": "SEDENION:e{slot}",
            "value_mint_name": "VAL:{key}",
            "pad_name": "__pad__, appended when the part count is EVEN (bundle needs odd N)",
            "mint": "SHA-256(name || u64_be(counter)) chained to D/8 bytes",
            "sign": "Class-C chiral_flip on the value vector; never abs()",
            "clean_tie_rule": "positive polarity takes >=, negative takes > (a tie keeps +1)",
            "navmap": "e_i * e_j = sign * e_k over the 16-slot cd_basis_product cocycle",
            "num_slots": 16,
            "default_D": 8192,
            "working_word_cap": 7,
        },
        subsuming_form=("CDRegister(16, namespace=\"SEDENION\", coupling=True, "
                        "error_correction=True)"),
        note=("The 16-slot register's coupling and EC layers are UNGATED; "
              "CDRegister gates them, so the subsuming form must opt into both "
              "or it raises where the recorded class returned."),
    )


def _probes(out) -> None:
    """The rc297 gate verbatim: a fresh register per direction, 8 keys written,
    each read back at its navmap-predicted destination."""
    dirs = list(range(1, 16))
    for D in D_VALUES:
        hits = 0
        for j in dirs:
            r = sedenion_register(D=D)
            for i, k in enumerate(NAMES):
                r.write(i, k)
            nav = r.navmap(j)
            moved = r.navigate(j)
            for i, k in enumerate(NAMES):
                dest, sign = nav[i]
                got_key, got_sign = moved.read(dest)
                hit = bool(got_key == k and got_sign == sign)
                hits += 1 if hit else 0
                _rec(out, kind="probe", D=D, j=j, i=i, key=k, dest=dest,
                     sign_expected=sign, got_key=got_key, got_sign=got_sign,
                     hit=hit)
        _rec(out, kind="probe_hits", D=D, hits=hits, of=len(dirs) * len(NAMES))


def _navmaps(out) -> None:
    r = SedenionRegister()
    for j in range(16):
        m = r.navmap(j)
        _rec(out, kind="navmap", dim=16, j=j,
             map={str(i): list(m[i]) for i in range(16)})


def _navigate(out) -> None:
    occ = [(0, "a", 1), (3, "b", -1), (10, "c", 1), (7, "d", -1)]
    for j in range(16):
        r = SedenionRegister(D=512)
        for slot, key, sign in occ:
            r.write(slot, key, sign=sign)
        routed = r.navigate(j).slots()
        _rec(out, kind="navigate", j=j,
             occupancy=[[s, k, g] for s, k, g in occ],
             routed={str(s): [k, g] for s, (k, g) in sorted(routed.items())})


def _couple(out) -> None:
    r = SedenionRegister()
    for vals in ([1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0],
                 [0.3, -0.7, 0.1],
                 [0.5],
                 [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]):
        word = r.couple_working(vals)
        back = r.uncouple_working(word)
        _rec(out, kind="couple",
             vals=[float(v).hex() for v in vals],
             word=[float(v).hex() for v in word],
             uncoupled=[float(v).hex() for v in back])


def _ec(out) -> None:
    r = SedenionRegister()
    for n in (3, 4):
        big = (1 << n) - 1
        data = [(i * 3) & 1 for i in range(big - n)]
        enc = r.carry(data, n=n)
        _rec(out, kind="carry", n=n, data=data, codeword=list(enc))
        for pos in range(big):
            bad = list(enc)
            bad[pos] ^= 1
            _rec(out, kind="correct", n=n, pos=pos, codeword=bad,
                 result=r.correct(bad))


def _reads(out) -> None:
    """The rc330 record."""
    occ = {0: 1, 1: -1, 5: 1, 9: 1, 12: -1}
    r = SedenionRegister(D=512)
    for s, sign in occ.items():
        r.write(s, "v%d" % s, sign=sign)
    _rec(out, kind="reads", D=512,
         occupancy={str(s): g for s, g in occ.items()},
         reads={str(s): list(r.read(s)) for s in range(16)},
         slots={str(s): [k, g] for s, (k, g) in sorted(r.slots().items())})


def _storage(out) -> None:
    """Byte-level storage records: the materialised bundle, the per-slot unbound
    ("noisy") vector, and what the nearest-codebook clean makes of it."""
    fixtures = [
        ("rc200", [(0, "alpha", 1), (3, "beta", -1), (10, "gamma", 1), (7, "delta", -1)]),
        ("rc140", [(0, "alpha", 1), (3, "beta", -1), (9, "gamma", 1)]),
    ]
    for label, writes in fixtures:
        for D in (256, 512, 8192):
            r = SedenionRegister(D=D)
            for slot, key, sign in writes:
                r.write(slot, key, sign=sign)
            bundle = r.materialize()
            _rec(out, kind="storage", label=label, D=D,
                 writes=[[s, k, g] for s, k, g in writes],
                 materialize_sha256=sha256_bytes(bundle),
                 materialize_bytes=len(bundle),
                 codebook_sha256={k: sha256_bytes(v)
                                  for k, v in sorted(r.codebook.items())},
                 unbind_sha256={str(s): sha256_bytes(bind(r._addr(s), bundle))
                                for s in range(16)},
                 reads={str(s): list(r.read(s)) for s in range(16)},
                 slots={str(s): [k, g] for s, (k, g) in sorted(r.slots().items())})


def main() -> int:
    out = []
    _header(out)
    _probes(out)
    _navmaps(out)
    _navigate(out)
    _couple(out)
    _ec(out)
    _reads(out)
    _storage(out)
    body = "".join(line + "\n" for line in out)
    raw = body.encode("utf-8")
    with open(OUT, "wb") as fh:                 # LF, byte-exact; never text mode
        fh.write(raw)
    sys.stderr.write("records: %d\nbytes: %d\nsha256: %s\n"
                     % (len(out), len(raw), sha256_bytes(raw)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
