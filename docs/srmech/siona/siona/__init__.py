"""siona — a grounded RBS-HDC instrument: storage + retrieval (k=3 chiral addressing) and the grounded
inference loop, on srmech.

NOT an alias for srmech (that was the ≤0.0.4 metapackage; srmech removed the in-wheel `import siona` alias).
Siona is the inference layer — a srmech PROFILE (`srmech.profiles` entry-point "siona") exposing:
  - the de Bruijn recall path (siona.bridge: walk/recall) over lean srmech's math core;
  - the grounded inference loop (siona.infer: Session — route/ground/drive/self-host/session, F1008–F1012);
  - the language-BOARD layer (siona.boards: per-language declared operator profiles on the byte/glyph
    substrate — English is board #1, not the architecture; F649 Rosetta lineage, dignity-first).
`srmech.profile("siona")` discovers + smoke-tests + activates it.
"""
from .bridge import walk, recall            # noqa: F401
from .boards import Board, ENGLISH, load_board, merge_boards  # noqa: F401
from .infer import Session, Grounding       # noqa: F401

__version__ = "0.1.0rc1"
__all__ = ["walk", "recall", "Session", "Grounding", "Board", "ENGLISH", "load_board", "merge_boards"]
