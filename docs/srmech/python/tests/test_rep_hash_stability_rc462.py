"""rc462 — the ℚ rep-payload HASH-STABILITY pin gate (`#T1179`, step C1).

**Why this file exists, and why it exists BEFORE the serializer is touched.**
The `#T1179` package widens the tier-4 rep payload from exact-ℚ to ℚ(ζₑ),
and the one irreversible defect that widening can ship is a silently MOVED
ℚ ``matrices_sha256``.  It would be silent (no exception, no wrong shape),
wheel-borne (the digest is emitted into the MCP tool list and
the compiled C registry) and un-catchable by the ledgers, because
``tests/example_args_ledger.ndjson`` carries those digests and is
REGENERATED — a moved hash rewrites it green.  So the pin has to live here,
in literals this file owns, written before ``_rep_matrices_bytes`` moves.

**What is pinned.**  Twenty-five fixtures — twenty-three rep PAYLOADS built
by the shipped constructors (seventeen permutation-kind, six general-kind),
plus two synthetic general-kind matrix families that exist only to exercise
the serializer's alphabet (negative numerators, multi-digit denominators,
the canonical zero ``0/1`` and one ``1/1``).  For each: its
``matrices_sha256``,
the LENGTH of its canonical serialization, and — for the fourteen bodies
short enough to read — the canonical BYTES themselves.  The pair is
deliberate: a digest pin says *that* something moved, a bytes pin says
*how*, and ``sha256_bytes(PINNED_BODIES[k]) == PINNED_DIGESTS[k]`` (which
never calls the serializer at all) separates a serializer move from a
``sha256_bytes`` native-dispatch divergence.

**The corpus is DERIVED, never inlined.**  Every payload comes out of
``cyclic_group`` / ``dihedral_group`` / ``unit_loop`` /
``semidirect_product`` / ``permutation_representation`` /
``tensor_product_representation`` / ``direct_sum_representation`` — so the
gate covers the PRODUCERS, not only the private serializer.  The two
``SYNTHETIC_*`` entries are the stated exception and are named as such.

**The instrument can return otherwise** — ``test_a_moved_serialization_``
``moves_the_digest`` executes a perturbation and requires the digest to
move, and it carries the measured vacuity trap with it: a per-element
transpose does NOT move C2's digest (its two matrices are symmetric), so
the control has to run on S3 natural, which contains 3-cycles.  Both halves
are asserted, so the choice of fixture is executed rather than remembered.

NO numpy.  NO ``hashlib``.  NO ``abs()``.  Digests go through
``srmech.amsc.format.sha256_bytes`` so the native dispatch is under test.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from srmech.amsc.format import sha256_bytes
from srmech.cascade import dihedral_group, unit_loop
from srmech.math.groups import (_check_rep_payload, _rep_matrices_bytes,
                                cyclic_group, direct_sum_representation,
                                permutation_representation,
                                semidirect_product,
                                tensor_product_representation)
from srmech.math.qmat import QMat

# ── the corpus, DERIVED from the shipped constructors ────────────────────

_C = {n: cyclic_group(n)["cayley_table"] for n in range(2, 9)}
_D4 = dihedral_group(4, "rotation_first")["cayley_table"]
_Q8 = unit_loop(4)["cayley_table"]
_S3 = semidirect_product(_C[3], _C[2], [[0, 1, 2], [0, 2, 1]])["cayley_table"]
#: F21 = C7 ⋊ C3, the mult-by-2 action (the rc458 deep-ring fixture).
_F21 = semidirect_product(
    _C[7], _C[3],
    [[(a * pow(2, h, 7)) % 7 for a in range(7)] for h in range(3)]
)["cayley_table"]
#: the natural 3-point S3 action: idx(a, h) sends x ↦ a + (−1)^h·x.
_NAT = [[(a + (x if h == 0 else -x)) % 3 for x in range(3)]
        for a in range(3) for h in range(2)]


def _build_corpus():
    """Every fixture, built by the SHIPPED ops.  Returns
    ``{name: (kind, matrices, payload_or_None)}``."""
    reps = {}
    for n in range(2, 9):
        reps[f"C{n}_REGULAR"] = permutation_representation(_C[n], _C[n])
    reps["S3_REGULAR"] = permutation_representation(_S3, _S3)
    reps["S3_NATURAL"] = permutation_representation(_S3, _NAT)
    reps["S3_TRIVIAL_DEGREE1"] = permutation_representation(_S3, [[0]] * 6)
    reps["D4_REGULAR"] = permutation_representation(_D4, _D4)
    reps["Q8_REGULAR"] = permutation_representation(_Q8, _Q8)
    reps["F21_REGULAR"] = permutation_representation(_F21, _F21)
    reps["C2_TENSOR_REG_REG"] = tensor_product_representation(
        reps["C2_REGULAR"], reps["C2_REGULAR"])
    reps["C2_DIRECT_SUM_REG_REG"] = direct_sum_representation(
        reps["C2_REGULAR"], reps["C2_REGULAR"])
    reps["S3_TENSOR_NAT_NAT"] = tensor_product_representation(
        reps["S3_NATURAL"], reps["S3_NATURAL"])
    reps["S3_DIRECT_SUM_NAT_REG"] = direct_sum_representation(
        reps["S3_NATURAL"], reps["S3_REGULAR"])

    # general kind — the sign rep spelled as canonical pairs, and the
    # rc458 conjugated rep (S = [[1/2, 1/3], [0, 1]]) whose entries carry
    # non-unit denominators, so the general branch's ``num/den`` alphabet
    # is exercised by a REAL payload and not only by the synthetics.
    sign = [[[(1, 1)]] if i % 2 == 0 else [[(-1, 1)]] for i in range(6)]
    reps["S3_SIGN_DEGREE1"] = {
        "order": 6, "degree": 1, "field": "Q", "kind": "general",
        "matrices": sign,
        "cayley_sha256": reps["S3_REGULAR"]["cayley_sha256"],
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("general", sign))}
    s_mat = QMat.from_rows([[(1, 2), (1, 3)], [0, 1]])
    s_inv = s_mat.inverse()
    conj = []
    for i in range(6):
        sgn = (1, 1) if i % 2 == 0 else (-1, 1)
        blk = QMat.from_rows([[sgn, (0, 1)], [(0, 1), (1, 1)]])
        prod = s_mat.matmul(blk).matmul(s_inv)
        conj.append([[prod[r, c].as_pair() for c in range(2)]
                     for r in range(2)])
    reps["S3_CONJUGATED_DEGREE2"] = {
        "order": 6, "degree": 2, "field": "Q", "kind": "general",
        "matrices": conj,
        "cayley_sha256": reps["S3_REGULAR"]["cayley_sha256"],
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("general", conj))}
    reps["S3_TENSOR_NAT_SIGN"] = tensor_product_representation(
        reps["S3_NATURAL"], reps["S3_SIGN_DEGREE1"])
    reps["S3_TENSOR_CONJ_SIGN"] = tensor_product_representation(
        reps["S3_CONJUGATED_DEGREE2"], reps["S3_SIGN_DEGREE1"])
    reps["S3_DIRECT_SUM_NAT_SIGN"] = direct_sum_representation(
        reps["S3_NATURAL"], reps["S3_SIGN_DEGREE1"])
    reps["S3_DIRECT_SUM_CONJ_CONJ"] = direct_sum_representation(
        reps["S3_CONJUGATED_DEGREE2"], reps["S3_CONJUGATED_DEGREE2"])

    corpus = {name: (rep["kind"], rep["matrices"], rep)
              for name, rep in reps.items()}
    # the two serializer-alphabet probes — NOT payloads, and named so
    corpus["SYNTHETIC_WIDE_ALPHABET"] = (
        "general",
        [[[(-3, 7), (12, 5)], [(0, 1), (101, 1)]],
         [[(46, 89), (-1, 1)], [(7, 12), (-99, 100)]]],
        None)
    corpus["SYNTHETIC_IDENTITY_2X2"] = (
        "general", [[[(1, 1), (0, 1)], [(0, 1), (1, 1)]]], None)
    return corpus


CORPUS = _build_corpus()

#: the two fixtures that are matrix families rather than rep payloads
SYNTHETIC = ("SYNTHETIC_WIDE_ALPHABET", "SYNTHETIC_IDENTITY_2X2")

# ── THE PINS.  Literals.  Nothing below is computed at import. ───────────

PINNED_DIGESTS = {
    "C2_REGULAR":
        "1247237b24cae0c6b3dc2e9148c1e9730abfb2379a53de915491e65b903521d7",
    "C3_REGULAR":
        "b670766efeea789186d5c365aa94ffcb31b87955ad783101b7f0b74bb2301afd",
    "C4_REGULAR":
        "1edb84f774cbba7f1834031fc396cc7004e3d78112e42d813553a942cecfa7f1",
    "C5_REGULAR":
        "10f148e0c893c424598d54d98b54ae443ba504742acc78ff8ac510c696bc00c3",
    "C6_REGULAR":
        "9c8d9f4cd9b323be09ca51fee2a4d9a4c14daefc3afad372cc1ca1a1eac58faf",
    "C7_REGULAR":
        "9f02486b03d1cc49490b5c50a6fa0dd386d62695971bae88c4de724e6e852efa",
    "C8_REGULAR":
        "1e5c55cb10f97849fbeceb6903a402efca2f5ba762864efe9bad65418676a102",
    "S3_REGULAR":
        "46a9593eb1d04c72c4fd0c4e63ad0118edc173ac24563a74d6cc2027c4bad375",
    "S3_NATURAL":
        "7e241c60a77943b87626d768ac3c8159a0bcab1dde1cac7bd6dc4189470b65f5",
    "S3_TRIVIAL_DEGREE1":
        "4ca63357f242420fbcf50189211a4ba35b24bd46568bad241c792b693dc2616e",
    "D4_REGULAR":
        "40c00c9b1999f8478c8d92afb0f95000e2bc4d5f5b92a3ca0757e42910f1a841",
    "Q8_REGULAR":
        "a82bd9e971895857b5a2ca0e97b2ff5dc5e689b58955978f8ec7794e7ad97df2",
    "F21_REGULAR":
        "78212dc08da717dea165088685ead5df453551a6505fd1f132b34ccc74ec0b0b",
    "C2_TENSOR_REG_REG":
        "2f55cdddfb638a98ed9dd5680786a1cd74d7757a9d1680b1421e1fbe66ffc025",
    "C2_DIRECT_SUM_REG_REG":
        "e5c4a6cac7cd4ebbc1fd51d49f25160cc280f12817064a8465a059b318284453",
    "S3_TENSOR_NAT_NAT":
        "70ebb6bae7d04b2bed23323ebcbc62a7e9cbcce959effd9ab65af2ae861a359d",
    "S3_DIRECT_SUM_NAT_REG":
        "c1ef1d465cd80cec6da271515b8e121bb90d28741bb9361e1fa61e8a2e1ee326",
    "S3_SIGN_DEGREE1":
        "35ab88e23617c054368b8d0774f861a1c8b3f67e706b8b580684bb9d7306efd0",
    "S3_CONJUGATED_DEGREE2":
        "7979ca8d53f101b38edc290ebd879229b6b8a1db9c28dbdecd4c6ec6b9d2b374",
    "S3_TENSOR_NAT_SIGN":
        "7a97fab1b986a1728610aaa93289111b6a8d60fad061e254aa5deddcc26e79d0",
    "S3_TENSOR_CONJ_SIGN":
        "62e9a046e14009f580d1895f34d36cd8581ee160044b3d8758c59f088faeaae2",
    "S3_DIRECT_SUM_NAT_SIGN":
        "94fb87909abb1b75eb1076404f7ad372d1c3d9f7f9be152931a8d606647d02b8",
    "S3_DIRECT_SUM_CONJ_CONJ":
        "d6a93e32827da5e1d67ad1267974bdd1b2babe0a5ef998ad11259c257c994afd",
    "SYNTHETIC_WIDE_ALPHABET":
        "07cc66acf8ab0322167ada105d1376772f77e00b6d2aec2da269c89354d899aa",
    "SYNTHETIC_IDENTITY_2X2":
        "7b73600ae2f191677f78a831c124f264451621e6d5c439465db08238430eb45e",
}

PINNED_BODY_LENGTHS = {
    "C2_REGULAR": 16,
    "C3_REGULAR": 55,
    "C4_REGULAR": 130,
    "C5_REGULAR": 253,
    "C6_REGULAR": 436,
    "C7_REGULAR": 691,
    "C8_REGULAR": 1030,
    "S3_REGULAR": 436,
    "S3_NATURAL": 112,
    "S3_TRIVIAL_DEGREE1": 16,
    "D4_REGULAR": 1030,
    "Q8_REGULAR": 1030,
    "F21_REGULAR": 18541,
    "C2_TENSOR_REG_REG": 64,
    "C2_DIRECT_SUM_REG_REG": 64,
    "S3_TENSOR_NAT_NAT": 976,
    "S3_DIRECT_SUM_NAT_REG": 976,
    "S3_SIGN_DEGREE1": 31,
    "S3_CONJUGATED_DEGREE2": 103,
    "S3_TENSOR_NAT_SIGN": 229,
    "S3_TENSOR_CONJ_SIGN": 106,
    "S3_DIRECT_SUM_NAT_SIGN": 391,
    "S3_DIRECT_SUM_CONJ_CONJ": 394,
    "SYNTHETIC_WIDE_ALPHABET": 44,
    "SYNTHETIC_IDENTITY_2X2": 15,
}

#: the canonical bytes themselves, for every body short enough to read —
#: this is the pin that says HOW a serialization moved, not merely that it
#: did.  ``\n`` separates rows, ``\n\n`` separates elements, ``,``
#: separates cells; a general-kind cell is ``num/den``.
PINNED_BODIES = {
    "C2_REGULAR": (
        b"1,0\n0,1\n\n0,1\n1,0"
    ),
    "C3_REGULAR": (
        b"1,0,0\n0,1,0\n0,0,1\n\n0,0,1\n1,0,0\n0,1,0\n\n0,1,0\n0,0"
        b",1\n1,0,0"
    ),
    "C4_REGULAR": (
        b"1,0,0,0\n0,1,0,0\n0,0,1,0\n0,0,0,1\n\n0,0,0,1\n1,0,0,0\n"
        b"0,1,0,0\n0,0,1,0\n\n0,0,1,0\n0,0,0,1\n1,0,0,0\n0,1,0,0\n"
        b"\n0,1,0,0\n0,0,1,0\n0,0,0,1\n1,0,0,0"
    ),
    "C5_REGULAR": (
        b"1,0,0,0,0\n0,1,0,0,0\n0,0,1,0,0\n0,0,0,1,0\n0,0,0,0,1\n"
        b"\n0,0,0,0,1\n1,0,0,0,0\n0,1,0,0,0\n0,0,1,0,0\n0,0,0,1,0"
        b"\n\n0,0,0,1,0\n0,0,0,0,1\n1,0,0,0,0\n0,1,0,0,0\n0,0,1,0,"
        b"0\n\n0,0,1,0,0\n0,0,0,1,0\n0,0,0,0,1\n1,0,0,0,0\n0,1,0,0"
        b",0\n\n0,1,0,0,0\n0,0,1,0,0\n0,0,0,1,0\n0,0,0,0,1\n1,0,0,"
        b"0,0"
    ),
    "S3_NATURAL": (
        b"1,0,0\n0,1,0\n0,0,1\n\n1,0,0\n0,0,1\n0,1,0\n\n0,0,1\n1,0"
        b",0\n0,1,0\n\n0,1,0\n1,0,0\n0,0,1\n\n0,1,0\n0,0,1\n1,0,0"
        b"\n\n0,0,1\n0,1,0\n1,0,0"
    ),
    "S3_TRIVIAL_DEGREE1": (
        b"1\n\n1\n\n1\n\n1\n\n1\n\n1"
    ),
    "C2_TENSOR_REG_REG": (
        b"1,0,0,0\n0,1,0,0\n0,0,1,0\n0,0,0,1\n\n0,0,0,1\n0,0,1,0\n"
        b"0,1,0,0\n1,0,0,0"
    ),
    "C2_DIRECT_SUM_REG_REG": (
        b"1,0,0,0\n0,1,0,0\n0,0,1,0\n0,0,0,1\n\n0,1,0,0\n1,0,0,0\n"
        b"0,0,0,1\n0,0,1,0"
    ),
    "S3_SIGN_DEGREE1": (
        b"1/1\n\n-1/1\n\n1/1\n\n-1/1\n\n1/1\n\n-1/1"
    ),
    "S3_CONJUGATED_DEGREE2": (
        b"1/1,0/1\n0/1,1/1\n\n-1/1,2/3\n0/1,1/1\n\n1/1,0/1\n0/1,1/"
        b"1\n\n-1/1,2/3\n0/1,1/1\n\n1/1,0/1\n0/1,1/1\n\n-1/1,2/3\n"
        b"0/1,1/1"
    ),
    "S3_TENSOR_NAT_SIGN": (
        b"1/1,0/1,0/1\n0/1,1/1,0/1\n0/1,0/1,1/1\n\n-1/1,0/1,0/1\n0"
        b"/1,0/1,-1/1\n0/1,-1/1,0/1\n\n0/1,0/1,1/1\n1/1,0/1,0/1\n0"
        b"/1,1/1,0/1\n\n0/1,-1/1,0/1\n-1/1,0/1,0/1\n0/1,0/1,-1/1\n"
        b"\n0/1,1/1,0/1\n0/1,0/1,1/1\n1/1,0/1,0/1\n\n0/1,0/1,-1/1"
        b"\n0/1,-1/1,0/1\n-1/1,0/1,0/1"
    ),
    "S3_TENSOR_CONJ_SIGN": (
        b"1/1,0/1\n0/1,1/1\n\n1/1,-2/3\n0/1,-1/1\n\n1/1,0/1\n0/1,1"
        b"/1\n\n1/1,-2/3\n0/1,-1/1\n\n1/1,0/1\n0/1,1/1\n\n1/1,-2/3"
        b"\n0/1,-1/1"
    ),
    "SYNTHETIC_WIDE_ALPHABET": (
        b"-3/7,12/5\n0/1,101/1\n\n46/89,-1/1\n7/12,-99/100"
    ),
    "SYNTHETIC_IDENTITY_2X2": (
        b"1/1,0/1\n0/1,1/1"
    ),
}

#: head and tail of the eleven bodies too long to pin whole — enough to
#: catch a prefix, separator or suffix move on the large fixtures.
PINNED_BODY_EDGES = {
    "C6_REGULAR": (
        b"1,0,0,0,0,0\n0,1,0,0,0,0\n0,0,1,0,",
        b",0,0,1,0\n0,0,0,0,0,1\n1,0,0,0,0,0"),
    "C7_REGULAR": (
        b"1,0,0,0,0,0,0\n0,1,0,0,0,0,0\n0,0,",
        b",1,0\n0,0,0,0,0,0,1\n1,0,0,0,0,0,0"),
    "C8_REGULAR": (
        b"1,0,0,0,0,0,0,0\n0,1,0,0,0,0,0,0\n",
        b"\n0,0,0,0,0,0,0,1\n1,0,0,0,0,0,0,0"),
    "S3_REGULAR": (
        b"1,0,0,0,0,0\n0,1,0,0,0,0\n0,0,1,0,",
        b",1,0,0,0\n0,1,0,0,0,0\n1,0,0,0,0,0"),
    "D4_REGULAR": (
        b"1,0,0,0,0,0,0,0\n0,1,0,0,0,0,0,0\n",
        b"\n0,1,0,0,0,0,0,0\n1,0,0,0,0,0,0,0"),
    "Q8_REGULAR": (
        b"1,0,0,0,0,0,0,0\n0,1,0,0,0,0,0,0\n",
        b"\n0,1,0,0,0,0,0,0\n1,0,0,0,0,0,0,0"),
    "F21_REGULAR": (
        b"1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,",
        b",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"),
    "S3_TENSOR_NAT_NAT": (
        b"1,0,0,0,0,0,0,0,0\n0,1,0,0,0,0,0,",
        b",0,0,0,0,0,0,0\n1,0,0,0,0,0,0,0,0"),
    "S3_DIRECT_SUM_NAT_REG": (
        b"1,0,0,0,0,0,0,0,0\n0,1,0,0,0,0,0,",
        b",0,0,1,0,0,0,0\n0,0,0,1,0,0,0,0,0"),
    "S3_DIRECT_SUM_NAT_SIGN": (
        b"1/1,0/1,0/1,0/1\n0/1,1/1,0/1,0/1\n",
        b"1/1,0/1,0/1,0/1\n0/1,0/1,0/1,-1/1"),
    "S3_DIRECT_SUM_CONJ_CONJ": (
        b"1/1,0/1,0/1,0/1\n0/1,1/1,0/1,0/1\n",
        b"0/1,0/1,-1/1,2/3\n0/1,0/1,0/1,1/1"),
}

NAMES = tuple(sorted(PINNED_DIGESTS))
PAYLOAD_NAMES = tuple(n for n in NAMES if n not in SYNTHETIC)


def _body(name: str) -> bytes:
    kind, matrices, _rep = CORPUS[name]
    return _rep_matrices_bytes(kind, matrices)


# ── the pins ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", NAMES)
def test_the_serializer_digest_equals_the_pin(name):
    """THE gate.  ``sha256_bytes(_rep_matrices_bytes(...))`` must equal the
    literal pinned above, for every ℚ fixture.  If the ζ widening moves a
    ℚ serialization, this is what goes red."""
    assert sha256_bytes(_body(name)) == PINNED_DIGESTS[name], (
        f"{name}: the ℚ canonical serialization MOVED - a widening of "
        f"_rep_matrices_bytes must leave every existing ℚ hash "
        f"byte-identical (`#T1179` hash-stability law)")


def test_every_pinned_body_hashes_to_its_pinned_digest():
    """The bytes→digest half, which never calls the serializer: it fails
    only if ``sha256_bytes`` itself answers differently (a native-dispatch
    divergence), which is why it is a separate assertion."""
    assert len(PINNED_BODIES) == 14
    for name, body in PINNED_BODIES.items():
        assert sha256_bytes(body) == PINNED_DIGESTS[name], (
            f"{name}: sha256_bytes disagrees with the pinned digest on "
            f"BYTES this file owns - the serializer is not implicated; "
            f"the Class-A content-address dispatch is")


def test_the_serializer_reproduces_every_pinned_body_byte_for_byte():
    """The bytes half that DOES call the serializer — the pin that says
    HOW a serialization moved rather than merely that it did."""
    for name, body in PINNED_BODIES.items():
        assert _body(name) == body, (
            f"{name}: the canonical bytes moved (hash-stability law)")


def test_pinned_body_lengths_and_edges_hold():
    """Length + head/tail for the eleven bodies too long to pin whole."""
    assert len(PINNED_BODY_LENGTHS) == len(NAMES) == 25
    assert len(PINNED_BODY_EDGES) == 11
    assert set(PINNED_BODIES) | set(PINNED_BODY_EDGES) == set(NAMES)
    for name in NAMES:
        body = _body(name)
        assert len(body) == PINNED_BODY_LENGTHS[name], name
    for name, (head, tail) in PINNED_BODY_EDGES.items():
        body = _body(name)
        assert body[:len(head)] == head, name
        assert body[-len(tail):] == tail, name


def test_every_payload_carries_its_pinned_matrices_sha256():
    """The PRODUCER side: the digest the shipped constructor puts in the
    payload, not only the digest the private serializer computes."""
    assert len(PAYLOAD_NAMES) == 23
    for name in PAYLOAD_NAMES:
        rep = CORPUS[name][2]
        assert rep["matrices_sha256"] == PINNED_DIGESTS[name], name
        assert rep["field"] == "Q", name


def test_every_payload_still_passes_the_shipped_validator():
    """The corpus is real rep payloads — asserted by handing each one to
    the shipped validator.  It also binds this gate to the checker: if the
    ζ widening breaks ℚ acceptance, this reds."""
    for name in PAYLOAD_NAMES:
        _check_rep_payload("hash_stability_rc462", CORPUS[name][2])


def test_distinct_fixtures_carry_distinct_digests():
    """Injectivity over the corpus — a serializer that collapsed two
    distinct matrix families onto one address would pass every pin above
    and still be broken."""
    bodies = {name: _body(name) for name in NAMES}
    assert len(set(bodies.values())) == len(NAMES)
    assert len(set(PINNED_DIGESTS.values())) == len(NAMES)


# ── the shipped surfaces: no ℚ digest may become an orphan ───────────────

_FULL = re.compile(r"matrices_sha256.{0,24}?([0-9a-f]{64})", re.S)
_TRUNC = re.compile(r"matrices_sha256.{0,24}?([0-9a-f]{16})\.\.\.", re.S)
#: tool_schema.py splits a 64-hex digest across an implicit string
#: concatenation, so a naive grep for the whole digest finds ZERO there.
#: Joining adjacent literals first is what makes the scan honest.
_JOIN = re.compile(r'"\s*\n\s*"')

#: the ``test_citation_contradiction_rc436`` path idiom, verbatim
_SR_ROOT = pathlib.Path(__file__).resolve().parents[2]
_INTROSPECT = _SR_ROOT / "python" / "srmech" / "introspect"
SHIPPED_SURFACES = {
    "srmech_tool_registry.c": _SR_ROOT / "c" / "src"
    / "srmech_tool_registry.c",
    "tool_schema.py": _INTROSPECT / "tool_schema.py",
    "_tool_docs.py": _INTROSPECT / "_tool_docs.py",
    "_tool_docs_curated.py": _INTROSPECT / "_tool_docs_curated.py",
}


def test_no_shipped_matrices_sha256_is_orphaned():
    """Every ``matrices_sha256`` value that SHIPS — in the compiled C
    registry, in the ToolEntry source that ``describe()`` and MCP emit, and
    in the two doc surfaces — must still be a digest this gate pins.

    **This is the clause that makes the REPAIR honest, and it is the half
    the digest pins above cannot cover.**  If the ζ widening moves a ℚ
    hash, the pins go red; the cheapest way to make them green again is to
    re-pin, and re-pinning is exactly the wrong move, because the OLD
    digest is already inside published artifacts.  Re-pinning orphans
    every shipped site and this test fires.  MEASURED at rc462: replacing
    one pinned literal with a moved digest reds it naming
    ``srmech_tool_registry.c``.

    Stated as membership, not as a count, deliberately: a later rc that
    registers a new op quoting one of these digests must not red this,
    while a MOVED digest orphans every site at once."""
    pinned = set(PINNED_DIGESTS.values())
    prefixes = {d[:16] for d in pinned}
    seen_full, seen_trunc = 0, 0
    for label, path in SHIPPED_SURFACES.items():
        assert path.is_file(), f"{label}: {path} is missing"
        joined = _JOIN.sub("", path.read_text(encoding="utf-8",
                                              errors="replace"))
        for digest in _FULL.findall(joined):
            seen_full += 1
            assert digest in pinned, (
                f"{label}: ships matrices_sha256 {digest} which this "
                f"gate does not pin - either the serializer moved or the "
                f"corpus is short a fixture")
        for short in _TRUNC.findall(joined):
            seen_trunc += 1
            assert short in prefixes, (
                f"{label}: ships truncated matrices_sha256 {short}... "
                f"which is not the prefix of any pinned digest")
    # measured at rc462: 18 full (all C2 regular; 9 in the C registry and
    # 9 line-split in tool_schema.py) and 12 truncated across three
    # prefixes.  Floors, so a regex that stopped matching cannot pass.
    assert seen_full >= 18, seen_full
    assert seen_trunc >= 12, seen_trunc


# ── the instrument must be able to return otherwise ──────────────────────


def test_a_moved_serialization_moves_the_digest():
    """The negative control, with its measured vacuity trap attached.

    A per-element TRANSPOSE is a real change of the matrix family, and on
    S3 natural — which contains 3-cycles — it moves the digest.  On C2
    regular it does NOT: both matrices of that rep are symmetric, so the
    transpose is the identity on the body.  Measured, and asserted in both
    directions, so nobody later "simplifies" the control onto the smaller
    fixture and leaves a gate that cannot fail."""
    def transposed(name):
        kind, mats, _rep = CORPUS[name]
        flipped = [[[m[c][r] for c in range(len(m))] for r in range(len(m))]
                   for m in mats]
        return _rep_matrices_bytes(kind, flipped)

    nat = transposed("S3_NATURAL")
    assert nat != _body("S3_NATURAL")
    assert sha256_bytes(nat) != PINNED_DIGESTS["S3_NATURAL"]

    # the trap: the same perturbation is INERT here
    assert transposed("C2_REGULAR") == _body("C2_REGULAR")
    assert sha256_bytes(transposed("C2_REGULAR")) == \
        PINNED_DIGESTS["C2_REGULAR"]

    # and a single-cell edit moves the general-kind lane too
    kind, mats, _rep = CORPUS["SYNTHETIC_WIDE_ALPHABET"]
    edited = [[list(row) for row in m] for m in mats]
    edited[0][0][0] = (-3, 8)
    assert sha256_bytes(_rep_matrices_bytes(kind, edited)) != \
        PINNED_DIGESTS["SYNTHETIC_WIDE_ALPHABET"]


def test_the_kind_argument_is_load_bearing():
    """``_rep_matrices_bytes`` dispatches on ``kind``, and the ζ widening
    lands as a THIRD branch keyed on the same argument — so the two
    existing branches must be shown to be genuinely different spellings of
    the same family, not an accident that a new branch could collide with.
    Serializing general cells under the permutation branch emits Python
    tuple repr, which is exactly the silent-repr failure a checker widened
    without a serializer branch would content-address."""
    _kind, mats, _rep = CORPUS["SYNTHETIC_IDENTITY_2X2"]
    wrong = _rep_matrices_bytes("permutation", mats)
    assert wrong != _rep_matrices_bytes("general", mats)
    assert b"(1, 1)" in wrong          # the repr leak, executed
    assert sha256_bytes(wrong) != PINNED_DIGESTS["SYNTHETIC_IDENTITY_2X2"]


# ── vacuity floors ───────────────────────────────────────────────────────


def test_the_pin_set_is_not_vacuous():
    """Floors on the corpus, and on the LITERALS in this file's own source
    — a strict-equality sweep over an empty or computed pin set would pass
    while measuring nothing."""
    assert set(PINNED_DIGESTS) == set(CORPUS) == set(PINNED_BODY_LENGTHS)
    kinds = {CORPUS[n][0] for n in NAMES}
    assert kinds == {"permutation", "general"}
    assert sum(1 for n in NAMES if CORPUS[n][0] == "permutation") >= 17
    assert sum(1 for n in NAMES if CORPUS[n][0] == "general") >= 8
    for digest in PINNED_DIGESTS.values():
        assert len(digest) == 64
        assert set(digest) <= set("0123456789abcdef")
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    literals = set(re.findall(r"[0-9a-f]{64}", src))
    assert len(literals) >= 25, len(literals)
    assert set(PINNED_DIGESTS.values()) <= literals
