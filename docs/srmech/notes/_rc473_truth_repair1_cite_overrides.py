# Citations the resolver must not judge by rule, each read by hand (r1_inspect9.py).
# (entry, token) -> (action, new_path). "skip": left to a LITERAL edit below.
# "rewrite": the cited line was read and holds neither the definition nor the code
# the sentence names; the token keeps its path and loses the line number.
_J = "srmech/apokatastasis/elliptic_jackson.py"
_JA = "srmech/apokatastasis/elliptic_jackson_an.py"
OVERRIDES = {
    # line 516 of srmech/math/carrier_spectrum.py is `def carrier_spectrum` (this op),
    # while the parenthetical sits after ``the_one`` (srmech/cascade/one.py).
    ("srmech.math.carrier_spectrum.carrier_spectrum", "srmech/amsc/carrier_spectrum.py:516"): ("skip", None),
    # elliptic_jackson.py:99 reads `raise TypeError(` (def multivariate_elliptic_jackson at 103);
    # elliptic_jackson_an.py:142 reads `w = w * u` (def multivariate_elliptic_jackson_an at 146)
    ("srmech.apokatastasis.apagodu_zeilberger.apagodu_zeilberger", _J + ":99"): ("rewrite", _J),
    ("srmech.apokatastasis.apagodu_zeilberger.apagodu_zeilberger", _JA + ":142"): ("rewrite", _JA),
    ("srmech.apokatastasis.elliptic_determinant.elliptic_cauchy_determinant", _J + ":99"): ("rewrite", _J),
    ("srmech.apokatastasis.elliptic_determinant.elliptic_cauchy_determinant", _JA + ":142"): ("rewrite", _JA),
    ("srmech.apokatastasis.elliptic_wz_certificate.elliptic_wz_certificate", _J + ":99"): ("rewrite", _J),
    ("srmech.apokatastasis.elliptic_wz_certificate.elliptic_wz_certificate", _JA + ":142"): ("rewrite", _JA),
    # zeilberger.py:256 is blank (def zeilberger at 259)
    ("srmech.apokatastasis.wz_certificate.wz_certificate", "srmech/apokatastasis/zeilberger.py:256"):
        ("rewrite", "srmech/apokatastasis/zeilberger.py"),
    # cyclic.py:234 is blank (def mod_pow at 278)
    ("srmech.math.primes.is_prime", "srmech/math/cyclic.py:234"): ("rewrite", "srmech/math/cyclic.py"),
    # _native/__init__.py:1516 is the srmech_walsh_hadamard_i64 binding; the
    # srmech_qm_minkowski_metric binding is at 1902-1904 -> literal edit (drops " region")
    ("srmech.physics.qm.relativistic.minkowski_metric", "srmech/_native/__init__.py:1516"): ("skip", None),
}
LITERAL = [
    ("WHAT — the OPERAND-side dual of ``the_one`` (``srmech/amsc/carrier_spectrum.py:516``).",
     "WHAT — the OPERAND-side dual of ``the_one`` (``srmech/cascade/one.py``); this op is defined in ``srmech/math/carrier_spectrum.py``."),
    ("(srmech/_native/__init__.py:1516 region)", "(srmech/_native/__init__.py)"),
]
