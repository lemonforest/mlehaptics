# F1305 — **the session ledger is hardened by a finding-ref ratchet.** A finding's cross-reference to another finding (`F735`, `Composes F1301`) is the internal analogue of a citation — under MPM it must **resolve**, not be recalled. `check_finding_refs.py` verifies every cited F-number resolves to a lodged finding (a file **or** a git commit subject), and reports the ghosts: **1196 findings, 3 unresolved refs.** That is the ledger's own no-bare-recall gate — the discipline the F1303 verification wished for when it (over-)flagged F735 as "appears nowhere."

**User (2026-07-22):** *"harden session-ledger only records."*

## Why this hardens the session ledger
The **session ledger** = the research-tree findings under `docs/srmech/rbs_lm_research/` — NOT the durable srmech package or auto-memory. Its findings cite each other by F-number. The F1303 verification named the risk exactly: *"an internal finding-tag is the internal analogue of a bare recalled citation."* A cited F-number that resolves to a lodged finding is **hardened**; one that doesn't is a **recalled ghost** — a typo, a hallucinated number, or a forward-link never written. The ratchet makes that distinction mechanical.

## What "resolves" means, honestly
A finding is **lodged** if it exists as a `R-RBS-LM-FINDING_<N>` file **or** as a git commit subject containing `F<N>` — the two ways this project records a finding. Both count. The checker converged as the resolution definition widened, which is itself the useful trace:
- files only → **31** apparent ghosts;
- + commit subjects (`F<N>:`) → **8** (the rest were commit-lodged);
- + parenthesized/any `F<N>` in subjects → **3** (the rest were `(F1242):`-style or arc references like F856).

**The 3 residuals — F134, F187, F750 — are all early findings**, each cited only by its immediate successors (F135/F175; F188–F190; F754/F755). They resolve to neither a file nor a commit F-number, so they were almost certainly lodged in the **research notebook** (a different record) or bundled — not standalone. They are flagged, not fixed: fixing means either locating the notebook entry or dropping the cross-reference, a per-item call.

## The meta-point (composes F1303)
The F1303 verification agent claimed F735 "appears nowhere" — a false ghost-flag, caught by a main-loop grep. **This checker is that grep, mechanized and run over the whole ledger** — so the next such over-flag (or genuine ghost) is caught by a ratchet, not by luck. It does NOT touch the *durable* record (srmech package / auto-memory); it hardens the *session ledger's internal consistency*, which is the specific thing the user asked to harden.

## Usage
`python3 check_finding_refs.py` (report) / `--strict` (nonzero exit on any dangling ref, for a commit gate). A dangling ref is a **typo/hallucinated number → fix it**, or a **planned finding not yet lodged → write it or drop the cite**.

Composes **F1303** (the verification's F735 over-flag, now mechanically preventable), the breadcrumb-web discipline (CLAUDE.md §0 — this is its verification arm), `[[feedback_pdf_extraction_citation_discipline]]` (a finding-tag is a citation), `[[feedback_computational_provenance_discipline]]`.
