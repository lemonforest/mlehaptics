"""siona — a grounded RBS-HDC instrument: storage + retrieval (k=3 chiral addressing) on srmech.

NOT an alias for srmech (that was the ≤0.0.4 metapackage; srmech removed the in-wheel `import siona` alias).
Siona is the inference layer — a srmech PROFILE (`srmech.profiles` entry-point "siona") exposing the de Bruijn
recall path over lean srmech's math core. `srmech.profile("siona")` discovers + smoke-tests + activates it.
"""
from .bridge import walk, recall  # noqa: F401

__version__ = "0.1.0rc1"
__all__ = ["walk", "recall"]
