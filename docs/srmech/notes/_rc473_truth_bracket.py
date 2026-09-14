"""rc473 truth round (`#T1188`): the round(e * 2^61) bracket against e.

Reproduces, from a stated generator, the counts the rc473 CHANGELOG quotes for
``kepler_solve``'s Q61 bracket, in BOTH streams: the one the close-out's script
actually drew (one discarded ``random()`` between ``randint`` and
``getrandbits``) and the one the CHANGELOG described until the truth round
(no discarded draw). The instrument is the shipped helper
``srmech.math.kepler._kq_emul`` with ``srmech.math.rational._Q61_ONE``; the
excess is decided in exact integers.

Usage (from docs/srmech):  python3 notes/_rc473_truth_bracket.py python
"""
import random
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "python")
import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech.math.kepler import _kq_emul  # noqa: E402
from srmech.math.rational import _Q61_ONE  # noqa: E402

print("python", sys.version.split()[0], "srmech", srmech.__version__,
      "HAS_NATIVE", _native.HAS_NATIVE)


def excess(e):
    """(round(e * 2^61) * 2^-61 - e) scaled by 2^61 * den(e), exactly."""
    e_n, e_d = float(e).as_integer_ratio()
    e_sh = e_d.bit_length() - 1
    return _kq_emul(e_n, e_sh, _Q61_ONE) * e_d - e_n * _Q61_ONE, e_d


def run(discard_a_draw):
    rng = random.Random(473)
    n = over = under = ties = above = 0
    for _ in range(200000):
        k = rng.randint(10, 1021)
        if discard_a_draw:
            rng.random()
        mant = rng.getrandbits(52)
        e = ((1 << 52) | mant) / (2.0 ** 52) / (2.0 ** k)   # exact: (2^52 + mant) 2^(-52-k)
        if not 0.0 < e < 1.0:
            continue
        n += 1
        num, e_d = excess(e)
        if num > 0:
            over += 1
            if 2 * num < e_d:
                under += 1
            elif 2 * num == e_d:
                ties += 1
            else:
                above += 1
    return n, over, under, ties, above


for label, discard in (("one discarded random() per sample", True),
                       ("no discarded draw", False)):
    n, over, under, ties, above = run(discard)
    print(f"seed 473, {label}: n {n}, bracket > e on {over}, by < 2^-62 on {under}, "
          f"by == 2^-62 on {ties}, by > 2^-62 on {above}")
for e in (0.0549, 0.1, 0.3, 0.5, 0.9, 0.9999999999999999):
    print(f"e = {e!r}: bracket > e -> {excess(e)[0] > 0}")
