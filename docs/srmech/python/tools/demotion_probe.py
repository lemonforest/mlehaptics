r"""rc465 (`#T1188`) — the SILENT-CARRIER-DEMOTION probe: a DELIBERATE TOOL RUN.

``tests/test_silent_carrier_demotion_rc463.py`` is the ratchet; :func:`merge_cell`
writes ``tests/demotion_census.ndjson``, ONE committed manifest carrying BOTH CI
cells' columns. The gate READS that manifest; it does not re-derive it.

⚠️ **A CENSUS IS NOT A GATE, AND rc465 SPENT THREE COMMITS LEARNING IT**
------------------------------------------------------------------------
Through ``08d80a037`` the gate called :func:`census` — the whole
registry-wide derivation — on every CI run, in every cell, and then diffed it
against a host-specific pin. Deriving the population is expensive; checking the
invariant is not. Three consecutive commits fought the same symptom without
asking whether the derivation belonged where it was:

  * ``8be4a95ce`` — red in every PURE shard, "the artefact did not know which
    cell it came from" -> a SECOND per-cell pinned artefact.
  * ``83aa9b74f`` — ``mlse`` allocated **7.1 GiB** inside the census and killed
    the runner -> a skip.
  * ``08d80a037`` — ``windows-latest`` has no ``SIGALRM``, so its calls were
    unbounded and the job timed out at 99% -> two more skips.

Each of those is a MITIGATION: green bought by teaching a census which ops to
avoid. Worse, the expected value was per-cell, so the pin measured the HOST
rather than the code — the same defect class this project keeps finding in its
own instruments. The resolution is placement. The census is now a tool run a
human starts on purpose; the gate reads a committed file and checks a predicate
in milliseconds, identically in every cell. **MEASURED: the gate cost
66.18 s (native) / 153.80 s (pure) per CI job and now costs 8.02 s / 7.21 s, of
which every test call is <= 0.04 s and the rest is ``import srmech``. In the
``--forked`` asserts-live cell it was paid ONCE PER TEST — ``pytest-forked``
gives each test a fresh child, so the module cache never survived and 15
census-consuming tests each re-derived it: ~15 minutes of census, observed as
+12 m of wall clock on ``asserts-live shard 4/4`` against the ``main``
baseline.**

The two per-cell artefacts consolidate to one. The native-vs-pure disagreement
does NOT disappear by being merged: it becomes a **named finding with its op
list** (``divergent`` rows, and ``meta.divergent`` naming every one), pinned in
the gate. An op whose answer depends on whether ``libsrmech`` loaded is the
``fir`` / ``matched_filter`` class rc463 already rated WORSE than a plain
demotion. Surfacing it is the resolution; absorbing it into two pins was the
mitigation.

WHY THIS EXISTS
---------------
rc463 shipped the demotion class as **six hand-written rows in one test file**,
all six in ``srmech.math.laplacian``, with ``CEIL_SILENT_DEMOTION = 6`` pinned
to ``len(_DEMOTION_MANIFEST)``. Its own module docstring named the hole
(blind spot 1): *"A missing MANIFEST row is invisible. The gate asserts over the
rows it HAS. It has no oracle telling it a row is absent."* A gate over a
hand-written roster measures the roster.

Worse, the rc463 predicate's ADMISSION conjunct is decided **by the signature**,
so an op annotated ``Sequence[float]`` was excluded BY CONSTRUCTION however
exact the operand it was handed. That is R2 shielding: rc463's own honesty
ladder rates a float parameter ANNOTATION at rung **R2 — WEAK, "nothing
enforces it"** — and then let exactly that rung decide membership. A type
annotation stood in for an accuracy contract. Admission here is decided by
MEASUREMENT, and the parameter roster is read from the REGISTRY.

THE ORACLE IS DIFFERENTIAL, SO IT NEEDS NO PER-OP EXACT VALUE
--------------------------------------------------------------
That is what makes the manifest auto-populating. Three calls, one witness
triple, substituted at one numeric leaf of one sequence-shaped parameter — or,
since rc472 (`#T1188`), AT the value of one scalar-numeric parameter (the
second lane; disclosure 8):

    P = 2**53 + 1   the smallest positive integer float64 cannot represent
    F = 2**53       the value float64 collapses P to
    G = 2**53 + 2   the next representable neighbour above F

    out(P) == out(F)  and  out(G) != out(F)   ->  DEMOTED
    out(P) != out(F)                          ->  EXACT
    all three equal                           ->  a NULL, split THREE ways

THE THREE NULLS ARE THREE DIFFERENT QUESTIONS AND ARE NEVER MERGED
-------------------------------------------------------------------
``all three equal`` says only that the witness did not move the output. WHY it
did not is a separate question, and it has three answers. The rule beside
:data:`H` — *classify every null; do not merge two of them* — is why each gets
its own name rather than sharing one:

  * ``UNRESOLVED_AT_WITNESS`` is about the **witness scale**. The leaf DOES
    reach the output, but the op's own resolution is coarser than one float64
    step at ``2**53``, so this triple cannot decide its carrier. Split by the
    coarse fourth witness :data:`H` (rc465).
  * ``VACUOUS`` is about the **binding** (rc469, `#T1188`). The HARVESTED values
    of the OTHER parameters hold the op in a degenerate regime in which this
    leaf cannot reach the output at all — while at another binding of those
    same siblings it reaches it perfectly well. Split by a bounded round-robin
    sweep, :data:`MAX_ALT_BINDINGS`.
  * ``INSENSITIVE`` is about the **op**, and is only what remains once the
    other two have been subtracted.

**``INSENSITIVE`` carried all three through rc468, and the conflation is the
kind this instrument exists to find.** ``INSENSITIVE`` is a claim about the OP;
a single harvested binding can only support a claim about the MEASUREMENT.
MEASURED at rc469: ``srmech.cascade.qdft_summand::mu_hat`` read ``INSENSITIVE``
in BOTH cells over a live silent-wrong-answer, because its harvested ``n = 2``
makes the exact turn's sine exactly zero, which annihilates the axis the row was
probing — two different axes return byte-identical output there. The null was
true of that binding and false of the op, and the row was green over the defect.

Each null is retried at further leaves before it is recorded, because the
verdict is position-specific.

``out(G) != out(F)`` is the vacuity guard and it is not decoration. Without it
an op that returns a constant, or that ignores the parameter, reads DEMOTED —
"an instrument that cannot return otherwise is not a measurement".

THE BASE MUST BE EXACT OR THE VERDICT IS NOT ABOUT THE CARRIER
---------------------------------------------------------------
If ANOTHER operand is a float, a float result is what the caller asked for and
"exact in, rounded out" was never tested. So every numeric leaf of the base is
exactified first (an integral ``1.0`` becomes ``1``); a base still carrying a
NON-integral float is recorded as ``INEXACT_BASE`` and is never called DEMOTED.

WHAT THIS PROBE CANNOT SEE — required disclosure
-------------------------------------------------
 1. **Coverage is bounded by argument reach.** An op the probe cannot build a
    binding for is emitted as ``NO_SHAPE`` and counted, never skipped silently.
    That count is the honest statement of the instrument's reach and it is what
    ``CEIL_DEMOTION_UNREACHED`` ratchets down —
    ``tests/test_silent_carrier_demotion_rc463.py``, where that constant is
    DEFINED and ASSERTED, over BOTH cells' columns in every cell. It was not,
    through rc465: this sentence named a ratchet that existed nowhere else in
    the repo, so the instrument's own reach was the one number in this file
    with no gate under it (`#T1188`). The larger unreached class is ``RAISED``
    — a real refusal by a real op against a synthesised binding — and it is
    deliberately left unratcheted, because driving it down is a question about
    :func:`synthesize`, not about the library.
 2. **One parameter at a time.** A demotion that needs two exact operands
    simultaneously is out of reach.
 3. **Bounded leaf positions** (:data:`MAX_LEAVES`), and bounded sibling
    bindings (:data:`MAX_ALT_BINDINGS`). A demotion visible only at leaf 40 of a
    long vector is out of reach; so is one visible only under a sibling value
    outside :data:`ALT_SIBLING_VALUES`, which stays ``INSENSITIVE`` rather than
    being named ``VACUOUS``. Both bounds fail SAFE in the same direction — they
    can leave a null under-split, never over-split, because ``VACUOUS`` is only
    ever awarded on a POSITIVE observation that the leaf reached the output.
 4. **It measures through PYTHON only** (rc463 blind spot 4, unchanged). A
    demotion in the C projection the Python path does not share is invisible.
 5. **Layer-3 vocabulary is a STEM REGEX WITH A NEGATION PREDICATE** (rc463
    blind spot 5; the KEYWORD LIST it describes was REPLACED at rc470,
    `#T1188`). Through rc469 it was a closed literal-substring list, and it
    erred in BOTH directions at once. Its FALSE POSITIVES — a real declaration
    read as undeclared — were morphological and lexical: it held "approximate"
    and so could not spell rc467's own APPROXIMATION, held "round-off" and so
    could not spell "rounding", and matched without word boundaries, so a
    citation URL containing ``FULp`` declared an op. Its FALSE NEGATIVES — a
    keyword in an unrelated or NEGATING sentence read as declared — are
    disclosure 9. :data:`R3_PATTERNS` replaced the list with bounded STEMS
    matched PER OCCURRENCE under a clause-local negation refusal. MEASURED over
    the 732-op registry: DECLARED 202 -> 206 (a DATED pair, taken on
    CPython <= 3.11 over the then-unfolded delegate walk; see disclosure
    10 on why that baseline is now quoted as 204), which is 15
    declarations already
    written that the old reader could not spell, against 11 readings that were
    never declarations. The delegate follow is generalised here to
    ``fn.__globals__`` — rc463's read
    ``getattr(_la, name)`` and so could not address an op outside
    ``srmech.math.laplacian`` at all, which is why its Layer 3 was structurally
    confined to the module its six hand-rows came from.
 6. **THE MANIFEST GOES STALE SILENTLY, and only one HALF of that is guarded.**
    The gate no longer re-derives the census, so nothing re-measures the tree
    on its own. :func:`registry_signature` is the cheap half: hashing
    ``(op name, parameter types, return type)`` over the whole registry costs
    milliseconds and moves whenever an op is ADDED, REMOVED or RE-SIGNATURED,
    which is what decides demotion-CANDIDACY. **It does NOT move when an
    implementation changes carrier behaviour behind an unchanged signature** —
    the very class this probe exists to find. That is stated here and again in
    the gate, because the tree has already paid for the identical blind spot
    once: the worked-example ledger's freshness key, ``src_sha256``, is the
    snippet-TEXT hash, which does not move when the implementation moves, "and
    that blind spot is exactly how the ℚ-flip defect shipped" — rc469 removed
    the scoping flag that was built on it, for that reason. A guard whose limit
    is unwritten is a guard people believe.

    **There is a SECOND staleness blind spot, and rc470 (`#T1188`) is the rc
    whose own change IS it: the READER can move behind an unchanged registry.**
    :func:`registry_signature` hashes ``(name, parameter types, return type)``,
    and NONE of those moves when :func:`declares_inexactness` changes — so a
    census regenerated by an OLD reader stays green under a NEW one while its
    ``declares`` column is jointly false, and the merge refusal does not fire
    either, because the registry signature it compares is IDENTICAL in both
    trees. rc470 closes that half with :func:`reader_signature`, written PER
    CELL into the manifest, refused on merge exactly as the registry signature
    is, and asserted by the gate.

    The IMPLEMENTATION half above stays OPEN, and that is a DECISION rather than
    an oversight. Asserting ``meta.measured_at.<cell>.srmech_version`` is the
    only guard that would catch it — the field has always been written, and both
    sibling artefacts assert theirs — but it forces a full two-cell re-measure
    on EVERY rc, of which the pure cell alone costs 17-20 minutes. rc470 buys
    the reader half at zero recurring cost and leaves this one named. Whoever
    disagrees should reopen it as a decision, not discover it as a gap.
 7. **Byte / bit carriers admit no witness.** They surface as ``NO_SHAPE`` with
    the reason stated, which is a DOMAIN fact recorded as data. rc463 asserted
    this of the whole ``hdc`` family; rc465 measured it false — ``loop_conj``,
    ``loop_bind``, ``loop_inv``, ``loop_left_op`` and ``loop_right_op`` take
    float sequences and round P.
 8. ~~**SCALAR parameters are never probed**~~ (rc466, `#T1188`) — **CLOSED at
    rc472 (`#T1188`) by the SCALAR LANE.** Through rc471 :func:`probe_op`
    enumerated SEQUENCE-shaped registry parameters only, so an op that rounds
    an exact SCALAR operand was outside the census by construction; the
    measured instance was ``srmech.math.rational.sin(Q(2**53+1, 1)) ==
    rational.sin(2**53)`` — the Q61 cascade reads its argument as float64 by
    its own contract — with NO row emitted for it. rc472 admits a second,
    DISJOINT population, :func:`scalar_numeric` — a registry type naming
    ``float`` / ``number`` / ``complex`` and not sequence-shaped — and puts
    the witness triple AT THE VALUE (:data:`SCALAR_SLOT`): the witness is a
    value, not a leaf position, exactly as this bullet said a scalar probe's
    would be. The rc466 sentence *"a scalar-parameter probe is a different
    instrument"* was half right: it is the SAME instrument with a second lane
    and two :data:`PROBE_SPEC` members, and no other change — measured at
    rc472, the lane moves ZERO of the 1410 sequence verdict cells and adds its
    own rows beside them. **The lane commit then said, of what it could not
    reach, one true thing and one false one, and C3 (`#T1188`) corrects both
    in the same change that closes the true one.** True: a REQUIRED
    scalar-numeric sibling was still filled by :func:`synthesize` with an
    int-filled vector — closed by :data:`REQUIRED_SCALAR_FILL`, which holds
    such a sibling at the slot; 13 rows that read RAISED at the sibling now
    bind and are asked. False: *"the rows whose required sibling is itself a
    scalar read NO_SHAPE … the gate's scalar NO_SHAPE ceiling is exactly
    those rows."* They read RAISED, not NO_SHAPE (an 8-vector binds, then the
    op refuses it), and the five scalar NO_SHAPE rows are the ones whose
    required sibling is OPAQUE (``fold``, ``text``, ``handle``, ``observed`` /
    ``predicted``) — a different residue, unchanged by C3, still the ceiling.
    What C3 leaves named is the ``int``-typed required sibling: it is still
    handed a vector, because ``int`` is not a member of the lane — an int
    lane admits every integer parameter of every op and the twiddle
    strict-zero gate goes red on it — and the fill follows the lane's ident
    set rather than minting a second one. The seven rows that residue holds
    are listed at :data:`REQUIRED_SCALAR_FILL`.
 9. **The reader REFUSES negation, and does so LOOK-BEHIND ONLY** (rc466
    found it, `#T1188`; rc470 fixed it). ``odft_summand`` counted as DECLARED
    through rc465 on the phrase *"(the byte-exact parity contract, not a
    tolerance)"* — the token ``tolerance`` inside a sentence DENYING it, on a
    row that was in substance undeclared. rc466 rewrote that ONE op's words and
    left the reader alone, so the CLASS stayed open and was never swept for.
    rc470 closed it: a cue in :data:`NEGATION_CUES` within :data:`NEG_REACH`
    words BEFORE an occurrence, with no intervening punctuation, denies THAT
    OCCURRENCE. MEASURED, and it is not one synthetic case — the refusal removes
    **11 op-level readings** across the 732-op registry and, inside the census
    itself, exactly **one** DEMOTED op (``cascade.phase_coherent_peak``, whose
    entire declaration was a delegate sentence denying a tolerance; rc470 gave
    it a true accuracy paragraph in the same change).

    ACROSS THE 732 OWN DOCSTRINGS THE READER REFUSES **46 OCCURRENCES**, and
    the rule that produces that number is stated here because the number does
    not survive without it: ONE count per ``(op, label, sentence, match)``,
    over each registered op's own ``inspect.getdoc``, splitting on the shipped
    :data:`SENTENCE_SPLIT`. The same population gives **43** distinct
    ``(op, label)`` pairs and **39** ops carrying at least one refusal, and 46
    again with no sentence split at all. rc470's fourth commit wrote **45**
    here and in its CHANGELOG entry, and 45 reproduces under none of those
    four enumerations — it was carried from memory rather than printed, which
    is the whole case for the rule that no figure enters shipped prose unless
    the run that writes it printed the figure with its regenerating command.

    THREE RESIDUALS SURVIVE, each disclosed with its MEASURED live count rather
    than engineered against. Each states its DETECTOR, for the same reason:

    * **LOOK-BEHIND ONLY.** A denial placed AFTER the token — *"a tolerance is
      never consulted"* — is invisible. DETECTOR: a surviving occurrence with
      ``(is|are|was|were)\s+(never|not)`` or ``never\s+(consulted|used|
      applied|taken)`` inside the 60 characters FOLLOWING it. The shape
      OCCURS **6 times on 5 ops** (``matrix_cascades.einsum``,
      ``laplacian.propagate_sparse``, ``rational.sqrt``, and both twiddles).
      On NONE is it the sole reason for the reading — EXECUTED by deleting
      every sentence carrying the shape and re-reading, all five stay
      declared. **0 live instances.** One-directional by construction.
      *(rc470's fourth commit reported 6 on 4, naming ``recover_check``
      instead of ``einsum`` and ``sqrt``, under a detector it did not state.
      The occurrence count and the live count agree; the op SET does not, and
      an unstated detector is why.)*
    * **BOUNDING QUANTIFIER.** *"no more than 2 ULP"* is refused as if it were
      a denial. DETECTOR, stated because two earlier counts differed only by
      leaving it unstated: ``no (more|worse|greater|larger) than``, case
      insensitive, counted PER OCCURRENCE.

      POPULATION 1 — the 732 registry docstrings, the reader's actual
      population and the only one the refusal can act on: **0 occurrences**,
      **0 live instances**.

      POPULATION 2 — ``srmech/`` + ``tests/`` + ``tools/`` **EXCLUDING THE
      TWO FILES WHOSE SUBJECT IS THIS RESIDUAL** (this one, and
      ``tools/rc470_figures.py``, which re-prints the figure): **8
      occurrences on 6 LINES in 4 FILES**, NONE before an R3
      token. Six are in two GENERATED tool-doc tables
      (``_tool_docs.py:577`` ×2 and ``:731``; ``_tool_docs_curated.py:4292``
      ×2 and ``:8429`` — curated prose for ``music.bessel_zero_fixed`` and
      ``signal_processing.multitaper``, *"keep n_tapers no larger than
      2*nw - 1"*); two are test prose (``test_carrier_ceiling_rc343.py:61``,
      ``test_mat_eigvals_balancing_rc29.py:265``). The bare ``no more than``
      spelling gives **1** on the same population. **0 live instances.**

      ⚠️ **THE EXCLUSION IS THE POINT, not a convenience.** This paragraph
      QUOTES the shape it is counting, so it is inside its own population and
      every edit to it moves the figure: rc470's fourth commit reported **2**
      (the two TEST files only), the repair commit reported **7**
      (under-counting the tool-doc tables, because two of those four lines
      carry the phrase TWICE, and its own prose by one), and the first draft
      of THIS correction reported **10 on 8 lines** and then became 11 on 9 by
      being written. It happened a SECOND time, one level out: the figure
      script that re-prints this number carried the phrase inside its own
      prose-diff needle and took the count 8 → 9 on its first run. A
      self-referential population cannot be quoted stably, so it is quoted
      with those files removed and the removal named — and the script PRINTS
      the exclusion list, so a third such file is visible rather than
      absorbed.

    * **CONTRASTIVE CLAUSE.** An unrelated earlier cue inside the reach of a
      later true declaration — *"not exact but accurate to round-off"* refuses
      on ``not`` at two intervening words. Of the 46 refused occurrences, **0**
      carry a contrastive conjunction
      (``but|yet|though|although|except|whereas|however``) anywhere in the 70
      characters before the token. **0 live instances.** The 70-character rule
      is part of the claim: under a SENTENCE-level rule instead, the count is
      **1** — ``signal_processing.spectrogram``, where an unrelated ``not``
      earlier in the sentence sits before a true ``rounded``; that op is
      declared by five other labels, so the op-level effect is still zero.

    Do NOT "simplify" the word class that bounds the cue's reach; see the
    comment on :data:`NEG_WORD_CLASS`. Widening it is how the delegate follow's
    blind spot came to be invisible in rc463.
10. **The reader cannot read TOPIC, and no lexical rule closes that class**
    (rc470, `#T1188`). It matches a STEM in a sentence; it has no way to ask
    whether the sentence is ABOUT this op's own numeric accuracy. MEASURED by
    hand-reading all **223** DECLARED ops against the honesty-ladder criterion
    (``tests/test_silent_carrier_demotion_rc463.py``: *given ONLY the signature
    and the docstring, can the caller predict the returned value is not the
    exact one?*): **41 are TOPICAL MISREADS**, leaving **182 substantive**.
    rc472 (`#T1188`) moves the pair to **232 / 41 / 191**: the +9 is exactly
    the nine ops that received the scalar lane's ten ACCURACY paragraphs,
    each hand-read against the eight classes and each reading on its OWN
    docstring; no other op's reading moved (measured: zero DECLARED ops
    credited through one of the nine by the delegate arm).
    ⚠️ **QUOTE THE PAIR, NEVER THE 191 ALONE.** 232 is LEXICAL and
    regenerable from this tree by anyone; 191 is 232 minus a HAND-MAINTAINED
    by-name ledger, so it is exactly as fresh as the last hand-read and no
    fresher. A single "191 substantive declarations" implies a measurement
    this instrument cannot make.
    They are pinned BY NAME with a reason and a class in
    ``tests/test_r3_reader_rc470.py``'s ``_RESIDUAL_TOPIC_MISREADS``, and the
    classes are OTHER-CARRIER 16 (``QMat``/``Poly``: *"the bigint exact peer of
    the float64 Mat"*, *"collapses to float64 ONLY via to_floats"*),
    OTHER-OP 7, DISPATCH-TYPE 6 (a native-ABI type list — *"seq is a
    homogeneous int64 / float64 list"*), EXACTNESS-CLAIM 5, SERIALISATION 2,
    OTHER-DOMAIN 2 (erasure tolerance, clock-skew tolerance),
    LOGICAL-SOUNDNESS 2, REGEX 1.

    ⚠️ **THE PAIR MOVED 219/180 -> 222/181 IN rc470'S LAST COMMIT, AND THE
    READER IS WHY — no op became less honest.** That commit folded
    comprehension-nested ``co_names`` into the delegate walk
    (:func:`_delegate_names`), which is what let the reader see three ops it
    had been blind to on CPython <= 3.11. Two of the three are FALSE readings
    and are now pinned (``zeilberger`` and ``apagodu_zeilberger``, both
    OTHER-CARRIER via ``Poly`` — which is the +2 on that class); the third,
    ``signal_processing.heat_kernel``, is a TRUE declaration and stands as the
    +1 on substantive. **The 219 was never a property of the tree — it was a
    property of the interpreter**, and the pair is quotable now in a way it
    was not before, because the fold makes it the same on every interpreter.

    **An EARLIER rc470 commit REMOVED two rows, and 41/178 became 39/180.**
    ``matrix_cascades.eig_exact`` (which was the whole HISTORY class, now
    gone) and ``matrix_cascades.singular_values_exact`` fail half (2) of the
    pinning criterion: each one WARNS the caller in prose the caller can read
    before calling — ``"value": complex,  # the terminal float/complex
    projection`` and *"``value`` / ``vector`` are the single TERMINAL
    projections (rotation-last)"* on the first, ``"value": float}  # the
    single terminal projection (project=True only)`` on the second — and both
    carry ``project: bool = True`` in the signature. DECLARED is therefore the
    substantively RIGHT verdict on both, and only the sentence that MATCHED is
    off-topic, which is the LABEL-MISATTRIBUTION class below. Pinning them had
    asserted they should read UNDECLARED, and they should not.
    ``jordan_form_exact`` was re-read the same way and needs no change: its
    ``~1e-`` fires on *"``A·P ≈ P·J`` to ~1e-9 in the projected float/complex
    read-out"*, an on-topic statement about its own accuracy.

    **35 of the 41 read DECLARED under the rc469 reader too**, so this is
    mostly a pre-existing property of the instrument that rc470 MEASURED
    rather than introduced. *(It read 33 of 39 until rc470's last commit,
    which added two rows AND made this comparison version-stable; both
    new rows land in the overlap.)* The SIX the widening added are exactly the six
    topical misreads among the fifteen lexical gains — ``lll_reduce`` (three
    occurrences of "rounding", every one of them EXACT nearest-integer
    rounding), ``continued_fraction_convergents`` (Hardy & Wright Thm 154, a
    theorem about the convergents), ``lossy_projection_record``, both
    ``modulator_constraint*`` and ``encode_aboutness`` — the same set reached
    from the other direction, which is a cross-check on both. MEASURED by
    re-implementing the rc469 substring reader from ``git show
    main:tools/demotion_probe.py``. ⚠️ Its VOCABULARY is re-used over the
    SHIPPED, FOLDED delegate walk: main's own walk carries the PEP 709
    defect this file's last commit fixed, and MEASURED it reads **202 on
    CPython 3.10.21 / 3.11.16 and 204 on 3.12.3 / 3.14.7** — so the
    published **202** was an interpreter artifact of the same defect, not
    a property of the tree. Held constant, the figure is **204** on every
    interpreter. rc470's fourth commit
    disclosed FOUR, having read only the fifteen ops its own change moved.

    A SEPARATE and SMALLER class is the LABEL MISATTRIBUTION: the verdict is
    substantively right and only the evidence pointer is wrong, because some
    OTHER sentence warns the caller while the sentence that MATCHED does not.
    **NINE** (EIGHT through rc470; rc471 added ``cascade.spectral_cascades.dft``
    — it reads DECLARED only through the ``cexp`` delegate's new ``float64``
    sentence, while its OWN warning, *"one FPU lift — don't use floats for
    bit-exact math"*, carries no R3 stem; its census row is EXACT in both
    cells), each MEASURED by a per-occurrence dump on this tree, named so a
    later rc does not read a ``declares`` label as if it located the
    declaration: ``rational.relative_writhe`` (fires on an aside about the
    float spike; its real declaration, *"a CERTIFIED TRUNCATION, not the exact
    writhe"*, carries no R3 stem), ``coupling.fold_spectrum`` (fires inside
    the discipline NAME *"honestly-inexact"*), ``rational.hypot``
    (``rounding`` survives out of the DENIAL *"no float ``a*a`` rounding"* —
    the cue's reach dies at the backticks — while ``approximation`` is the
    genuine one), ``triality.lean_isa_seventh_primitive``,
    ``octonion.octonion_exp_series_truncate``,
    ``quaternion.quaternion_exp_series_truncate``, and the two rc470's last
    commit moved here from the pinned ledger,
    ``matrix_cascades.eig_exact`` and
    ``matrix_cascades.singular_values_exact``. These are NOT pinned: pinning
    them would assert they should read undeclared, and they should not.

    ⚠️ This paragraph said **"Five"** and then listed **six** through
    rc470's repair commit, and the copy of it in
    ``tests/test_r3_reader_rc470.py`` listed five by DROPPING ``hypot``. Both
    are corrected, and the pair ``*_exp_series_truncate`` is now spelled out,
    because ``rational.exp_series_truncate`` — the third op with that name —
    reads ``[]`` and is NOT a member (EXECUTED).

    THE CONSEQUENCE, said plainly. The instrument is the reader PLUS a
    hand-maintained by-name ledger, and the ledger DRIFTS: the pin test fires
    only when a PINNED op stops reading DECLARED, never when NEW prose creates
    a new misread of the same shape. Any rc that touches docstrings should
    re-run the per-occurrence dump over the DECLARED set and diff it against
    the ledger. The structurally better instrument — read ONLY an
    ``**ACCURACY (rcNNN, `#T1188`).**``-headed paragraph, which is topical by
    construction — would move DECLARED far DOWN and demand roughly a hundred
    prose rewrites under rule D1, so it is a DESIGN DECISION for a later rc,
    named here with this 41/222 rate as its motivation rather than left to be
    discovered.

numpy-free. No ``abs()`` — a sign is a Class-K pin-slot branch composed with
Class C. No stdlib ``fractions``.
"""

from __future__ import annotations

import inspect
import json
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import example_args as ea  # noqa: E402

PY_ROOT = _TOOLS.parent


def is_native() -> bool:
    """Is a `libsrmech` actually dispatching in THIS process?

    rc465-fix (`#T1188`). The verdicts below are read off VALUES the ops
    return, so a census taken with the C peers dispatching is a different
    measurement from one taken without them — not a stale copy of it.
    """
    try:
        from srmech import _native
        return bool(getattr(_native, "HAS_NATIVE", False))
    except Exception:                        # noqa: BLE001 — absent is "pure"
        return False


def cell() -> str:
    """``"native"`` or ``"pure"`` — which CI cell this process is."""
    return "native" if is_native() else "pure"


#: The two column names the manifest carries, in report order.
CELLS = ("native", "pure")

#: **THE** manifest. One file, both columns, host-independent to read.
#:
#: ⚠️ There were TWO through ``08d80a037`` — ``demotion_census_rc465.ndjson``
#: and ``..._pure.ndjson`` — because the gate re-derived the census live and
#: had to compare it against something taken in the same cell. That is the
#: mitigation this rc removes: with the derivation out of CI there is nothing
#: to compare per-cell, so the disagreement between the cells becomes DATA in
#: one file instead of a second pin.
CENSUS = PY_ROOT / "tests" / "demotion_census.ndjson"

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent.
#: Significand 54 bits. The SAME value rc344 pinned for ``kron`` and rc463 for
#: the whole class.
P = 2 ** 53 + 1
#: What float64 collapses :data:`P` to.
F = 2 ** 53
#: The next representable neighbour above :data:`F`. Its role is the vacuity
#: guard: an op that ignores the parameter answers the same for F and G.
G = 2 ** 53 + 2
#: A COARSE fourth value, three ULP-decades away, used only to split the null.
#: ``F`` and ``G`` differ by one float64 step, so an op whose OWN output
#: resolution is coarser than that answers identically for all three — and a
#: two-way verdict would file it under "the leaf never reached the output",
#: which is a different and false statement. Measured: ``octonion_norm`` reduces
#: through a truncated Class-N rational ``sqrt`` and returns the same float for
#: P, F and G while ``H`` moves it, so it is ``UNRESOLVED_AT_WITNESS``, not
#: ``INSENSITIVE``. Classify every null; do not merge two of them — there
#: are now THREE (``VACUOUS`` is the third; see the module docstring), and
#: :data:`H` is the split for THIS one only. It asks about the witness
#: SCALE. It cannot ask whether the leaf was reachable under some other
#: binding of the siblings, which is a question about the BINDING.
H = 3 * 2 ** 53

#: How many numeric leaves of one parameter are tried before the row is
#: recorded ``INSENSITIVE``. Bounded so the census terminates; blind spot 3.
MAX_LEAVES = 6

#: Values substituted into ONE sibling parameter when a null needs splitting
#: into ``VACUOUS`` vs ``INSENSITIVE``. Small ints, because the degeneracies
#: this is built to escape are structural rather than numeric: a period, a
#: dimension, a term count sitting at the value that collapses the op.
#: MEASURED on the ``qdft_summand`` binding — ``n = 2`` gives the exact turn a
#: sine of exactly zero, and ``3`` is the first value that un-degenerates it.
ALT_SIBLING_VALUES = (3, 4, 5)

#: How many alternate sibling bindings are tried before the null is recorded
#: ``INSENSITIVE``. Bounded so the census terminates, like :data:`MAX_LEAVES`.
#:
#: ⚠️ **ENUMERATION ORDER IS LOAD-BEARING AND A DEPTH-FIRST ORDER MAKES THIS
#: INSTRUMENT BLIND.** :func:`_alt_bindings` goes ROUND-ROBIN — one value across
#: EVERY sibling before any sibling's second value. MEASURED on the harvested
#: ``qdft_summand::mu_hat`` binding (siblings ``k``, ``left``, ``m``, ``n``,
#: ``sigma``): ``k`` = 3/4/5 does not un-degenerate it, ``left`` = 3/4/5 does
#: not, ``m`` = 3/4/5 RAISES ``IndexError``, and ``n`` = 3/4/5 DOES. In
#: sibling-major (depth-first) order the only sibling that answers arrives at
#: candidate **10 of 15**; round-robin reaches it at candidate **4**.
#:
#: **Stated exactly, because the weaker claim is the true one:** at the budget
#: shipped here, 12, that particular row is found under EITHER order — 10 <= 12.
#: The orders separate as soon as a row has five or more scalar siblings, which
#: is why the planted control that pins this (``gated_deep``, five
#: co-parameters, only the last of which un-degenerates) has five rather than
#: the three a smaller reading of the same point would need: round-robin reaches
#: its answer at candidate 5, sibling-major would need candidate 13, and 13 > 12.
#: MEASURED both ways in
#: ``tests/test_silent_carrier_demotion_rc463.py``. A depth-first "simplification"
#: of :func:`_alt_bindings` therefore does not fail loudly — it returns
#: ``INSENSITIVE`` for the wide-signature rows and the census diff shows nothing
#: moving, whose natural misreading is "the fix had no effect" rather than "the
#: instrument is blind".
#:
#: WHAT IT CAN HIDE, stated because a bounded instrument that does not say so
#: is a guard people believe: an op whose degeneracy is escaped ONLY by a
#: sibling value outside :data:`ALT_SIBLING_VALUES`, or only by moving TWO
#: siblings at once, or by a sibling that is neither ``int`` nor ``bool`` (the
#: sweep does not move strings or sequences — ``odft_summand``'s ``bracketing``
#: and ``form`` are outside it), still reads ``INSENSITIVE``. That is the same
#: shape as blind spot 2 and is bounded by the same argument: one at a time.
MAX_ALT_BINDINGS = 12

#: How many of the null-reaching (shape, leaf) POSITIONS the sweep re-asks at.
#:
#: ⚠️ **ONE IS NOT ENOUGH, AND THIS WAS MEASURED BY A PLANTED CONTROL
#: RATHER THAN REASONED.** The first cut of this split remembered a single
#: position — the LAST one to reach the null — and planted control
#: ``gated(v, n)`` read ``INSENSITIVE`` where it must read ``VACUOUS``. The
#: cause is that :func:`synthesize` ends its candidate list with SQUARE shapes,
#: so the last position reached was the 1x1 matrix ``[[1]]``: at the harvested
#: ``n = 2`` the op short-circuits and never looks at ``v``, so that shape binds
#: and records a null — and at ``n = 3`` it evaluates ``sum([[x]])`` and
#: RAISES. The sweep then saw nothing but failures and reported no finding.
#: **A position that binds under the HARVESTED sibling values need not bind
#: under the alternate ones**, so the sweep re-asks at the first few positions
#: in DISCOVERY order (the harvested shape first whenever it is int-clean)
#: rather than at whichever one happened to be walked last. Bounds the sweep at
#: ``MAX_NULL_CONTEXTS * MAX_ALT_BINDINGS * 2`` calls per row, paid ONLY by rows
#: that would otherwise have been recorded ``INSENSITIVE``.
MAX_NULL_CONTEXTS = 3

#: Shapes synthesised for a sequence-shaped parameter with no harvested value.
#: The Cayley-Dickson ladder, because that is what this package's vector ops are
#: dimensioned by; ``3`` is included because the graph / geometry family is not.
FLAT_DIMS = (8, 4, 3, 2, 16, 1)
#: Square shapes for a matrix-shaped parameter.
SQUARE_DIMS = (2, 3, 4, 8, 1)

#: Per-call wall-clock cutoff, seconds — a HANG GUARD for the instrument, not
#: a verdict-shaping cutoff. A call that exceeds it is recorded
#: ``CALL_TIMED_OUT`` with the number, never silently dropped.
#:
#: ⚠️ **20 through ``08d80a037``, and at 20 it DECIDED verdicts.** Two rows
#: measured 20.0-22.2 s straddling it and flipped between consecutive censuses
#: on an unchanged tree — a verdict that is a function of the MACHINE. The
#: repair shipped then was to skip both ops (see :data:`CONTRACT_SKIP`, where
#: they now sit for a reason about the OP), and to skip four more in the pure
#: cell whose only fault was costing 53-526 s there against 0.15 s in native.
#: All of that existed because the census ran inside CI, where a slow row is a
#: job that dies and ``windows-latest`` cannot enforce a ``SIGALRM`` cutoff at
#: all.
#:
#: With the census OUT of CI that argument dissolves. A deliberate tool run may
#: take as long as the tree takes, so the cutoff is set clear of every call that
#: can still reach it instead of through the middle of two. MEASURED, slowest
#: rows now that the two label-operand ops are contract-skipped (a row is 3-4
#: calls):
#:
#:     pure    ``recover_check_spectral::edges``        526.5 s
#:             ``recover_check_spectral::weights``       59.1 s
#:             ``recover_check::weights``                53.1 s
#:     native  the same three                        0.15-6.7 s
#:
#: Those four rows are now MEASURED rather than skipped, in both cells, and the
#: ~13 extra minutes are paid by whoever chose to run the instrument. 900 s
#: against a 592 s worst row bounds a HANG and adjudicates nothing.
#:
#: REPRODUCIBILITY, measured rather than argued: a second independent pure pass
#: over exactly those five rows differed from the committed column in **0**
#: verdicts, while their wall clocks moved by up to 27% (157.6 -> 200.0 s on
#: ``recover_check_spectral::weights``). At 20 s the cutoff sat INSIDE that
#: spread and adjudicated; at 900 s it does not.
#:
#: It is still needed: ``tensor_product_multiplicities`` hung indefinitely in
#: the first census run, and a probe that can hang has no honest verdict to
#: publish. ``signal.SIGALRM`` fires between BYTECODES and does not exist on
#: Windows — neither fact bounds anything the tree depends on any more, because
#: this is a tool a human runs and can interrupt, not a job with a timeout.
CALL_TIMEOUT = 900

TIMEOUT_MARKER = "TIMEOUT>"

#: Ops skipped by NAME with the reason attached — the same discipline as
#: ``frame_probe.CONTRACT_SKIP``: a probe must not violate a contract the op
#: states plainly. ``gf_*`` document "p must be PRIME" and the native peer
#: ``assert()``s it, which took SIGABRT under the asserts-live CI job at rc430.
CONTRACT_SKIP: Dict[str, str] = {
    "srmech.math.modular_linalg.gf_rref":
        "p must be PRIME (2 <= p < 2**31); the native peer asserts",
    "srmech.math.modular_linalg.gf_solve": "same prime contract as gf_rref",
    "srmech.math.modular_linalg.gf_nullspace": "same prime contract as gf_rref",
    # The witness is a LABEL, not a value carrier. A Dynkin / weight coordinate
    # of 2**53 asks these ops to enumerate a Weyl orbit of that size, so the
    # substitution is not "the same question at a bigger magnitude" — it is a
    # different question the op cannot be asked. MEASURED: the first census run
    # hung indefinitely inside `tensor_product_multiplicities` (no verdict after
    # 20 min; SIGALRM cannot pre-empt a long pure loop that never yields, and
    # the per-shape budget is only checked BETWEEN shapes). `frame_probe`
    # already names two of these three in its own SLOW_SKIP for the same
    # structural reason (|P_k| is quartic in level).
    "srmech.math.weight_lattice.tensor_product_multiplicities":
        "a weight LABEL, not a value carrier: a 2**53 Dynkin coordinate makes "
        "the Weyl-orbit sum unbounded (census hang, measured)",
    "srmech.math.weight_lattice.affine_fusion_multiplicities":
        "same weight-label contract as tensor_product_multiplicities",
    "srmech.math.weight_lattice.verlinde_fusion_multiplicities":
        "same weight-label contract; frame_probe.SLOW_SKIP names it too",
    # ⚠️ rc465-fix (`#T1188`) — TWO ROWS THAT ``08d80a037`` PUT IN ``SLOW_SKIP``
    # FOR A WINDOWS-TIMEOUT REASON, AND THAT BELONG HERE FOR THE OP'S OWN.
    #
    # That commit skipped them because a 20 s cutoff `windows-latest` cannot
    # enforce is not a cutoff — true, and about the MACHINE. The question this
    # rc asks of every skip is whether the reason survives the census leaving
    # CI. MEASURED (WSL2 py3.10, native), scanning the operand rather than
    # asserting about it:
    #
    #   alcove_fold("A1", [w], level=1)          w = 1 .. 4096   0.00 s
    #                                            w = 2**20       1.06 s
    #                                            w = 2**30       NO ANSWER >30 s
    #                                            w = 2**53+1     NO ANSWER >60 s
    #   equal_temperament_partials(degrees=[d])  d = 1 .. 4096   0.00 s
    #                                            d = 2**20       ValueError:
    #                                              "Exceeds the limit (4300) for
    #                                               integer string conversion"
    #                                            d = 2**53+1     NO ANSWER >60 s
    #
    # Both costs are LINEAR IN THE OPERAND'S VALUE, because in both ops the
    # operand is an INDEX and not a value carrier. `weight` is documented "a
    # rank-length DYNKIN LABEL", and the affine Weyl fold takes one reflection
    # step per unit of the label, so a 2**53 coordinate asks for ~2**53 steps —
    # the identical unbounded-orbit fact the three weight-lattice rows below
    # already record, and those predate the CI panic entirely. `degrees` is
    # documented "which SCALE DEGREES to return", and the exact ratio is
    # `octave**(degree/divisions)`, so degree 2**20 already exceeds CPython's
    # 4300-digit integer conversion limit; at 2**53 the number has ~10**15 bits.
    #
    # Neither is "the same question at a bigger magnitude", which is the test
    # the mlse note below states. That reason holds on any machine, so these
    # stay skipped and the WINDOWS reason is retired as the wrong one.
    "srmech.math.weight_lattice.alcove_fold":
        "a Dynkin LABEL, not a value carrier: the affine Weyl fold takes one "
        "reflection step per unit of the coordinate, so cost is LINEAR IN THE "
        "OPERAND VALUE. MEASURED 0.00s at 4096, 1.06s at 2**20, no answer in "
        "30s at 2**30. frame_probe.SLOW_SKIP names this family too",
    "srmech.music.equal_temperament_partials":
        "a scale-degree INDEX, not a value carrier: the exact ratio is "
        "octave**(degree/divisions), so the operand sizes the NUMBER rather "
        "than the question. MEASURED, degree 2**20 already raises \"Exceeds "
        "the limit (4300) for integer string conversion\"; at 2**53 the value "
        "has ~10**15 bits",
    # ⚠️ **THE ONE SKIP THAT SURVIVED THE rc465 CENSUS-PLACEMENT FIX, and it
    # survives on its own merits rather than on CI's** (`#T1188`).
    #
    # It ARRIVED as a mitigation — `83aa9b74f`, "one op allocated 7.1 GiB
    # inside the census and killed the CI runner" — and every other skip added
    # in that panic is deleted, because "the census is expensive in CI" stopped
    # being a reason the moment the census left CI. This one is kept, and the
    # test is whether the reason is about the OP or about the MACHINE:
    #
    #   `mlse`'s `n_states` means `A**L` (the rc425 v14 ABI bump), so the
    #   Viterbi trellis is EXPONENTIAL in the operand. Substituting `2**53`
    #   into `alphabet` / `channel_taps` / `initial_state` / `observations`
    #   does not ask the same question at a bigger magnitude — it asks for a
    #   trellis the op cannot build, exactly as a `2**53` Dynkin coordinate
    #   asks for an unbounded Weyl orbit in the three weight-lattice rows
    #   above, which predate the CI panic entirely. The witness is not a value
    #   carrier here.
    #
    # That reason holds on a workstation with 128 GiB as squarely as on a
    # 7 GiB runner, so it stays. It is recorded AS DATA — a `CONTRACT_SKIP`
    # verdict with this reason attached in every manifest row — not as a
    # silence. MEASURED per-op peak-RSS profile over the whole census (WSL2
    # py3.10): +7256.8 MiB for `mlse` against +17.4 MiB for the next largest
    # op, `singular_values_exact`.
    "srmech.signal_processing.mlse":
        "n_states is A**L, so the trellis is EXPONENTIAL in the operand: a "
        "2**53 witness asks for a state space the op cannot build, not the "
        "same question at a bigger magnitude. MEASURED +7.1 GiB peak RSS, "
        "against +17.4 MiB for the next largest op in the census",
}

# ⚠️ **THERE IS NO ``SLOW_SKIP`` HERE, AND ITS DELETION IS THE POINT**
# (`#T1188`). ``08d80a037`` shipped one — a per-cell roster of ops the census
# was told to avoid — holding ``alcove_fold`` and ``equal_temperament_partials``
# in BOTH cells (20.0-22.2 s rows against a 20 s cutoff that ``windows-latest``
# cannot enforce at all) and ``recover_check`` / ``recover_check_spectral`` in
# the pure cell (53-526 s rows whose verdicts were measured FLIPPING between
# consecutive censuses). Both rosters existed for one reason: the census was
# being re-derived inside CI, where a slow row is a job that dies.
#
# A deliberate tool run has no such constraint, so each of the six was re-asked
# the only question that matters — is the reason about the OP or about the
# MACHINE? The four ``recover_check`` rows are about the machine: they ANSWER,
# they just cost 53-526 s on the pure path against 0.15 s in native, so they are
# MEASURED now in both cells, ``CALL_TIMEOUT`` is set clear of them, and the
# ~11 extra minutes are paid by whoever chose to run the instrument. The other
# two are about the op — ``alcove_fold`` and ``equal_temperament_partials`` take
# an INDEX where the probe substitutes a VALUE, measured linear in the operand
# — so they move to :data:`CONTRACT_SKIP` and are recorded there with the scan
# that shows it. That is where a genuinely unadjudicable row belongs, next to
# ``mlse`` and the three weight-lattice rows. A roster keyed by how fast the
# machine is measures the machine.

#: THE SHAPE LEVER (rc471, `#T1188`) — ``op -> {harvested parameter: value}``,
#: overriding the harvest for ONE op, with its invariance MEASURED and its
#: COUNTER-CONTROL pinned in the same test.
#:
#: ⚠️ **READ THE PARAGRAPH ABOVE FIRST: this is NOT ``SLOW_SKIP`` returning.**
#: A skip DELETES a measurement and reports the deletion as a saving — rc465
#: measured that cost at four rows of real signal (pure DEMOTED 117 -> 121,
#: undeclared 67 -> 71, decided 219 -> 223). This changes the SHAPE the same
#: measurement is taken at, keeps the row, and is legitimate for exactly one
#: reason, which is a property of the OP and not of the machine:
#: :func:`srmech.math.laplacian.recover_check_spectral` takes ``max_dim`` as a
#: CALLER BOUND on a principal submatrix — *"the first ``min(vocab_size,
#: max_dim)`` nodes + the edges within that block"* — so a smaller
#: ``vocab_size`` asks the SAME question of a smaller block rather than a
#: different question. An op that refuses out-of-block indices instead of
#: bounding them is destroyed by the identical shrink, which is what the
#: counter-control below demonstrates rather than asserts.
#:
#: MEASURED (WSL2 py3.12.3, PURE cell, native absent), the full probe records
#: — verdict, ``leaf``, ``shape``, ``reason``, ``declares``, ``base_source`` —
#: at every value against the committed 64-shape column:
#:
#:   ``recover_check_spectral``  {charges DEMOTED, edges INSENSITIVE,
#:                                weights DEMOTED}
#:       vocab_size  8   2.96 s     16 edges over  8 nodes in the block
#:       vocab_size 16   8.49 s     48 edges over 16 nodes   <- SHIPPED
#:       vocab_size 24  27.16 s     72 edges over 24 nodes
#:       vocab_size 32  71.66 s    112 edges over 32 nodes
#:       vocab_size 64 504.98 s    288 edges over 64 nodes   (the harvest)
#:
#: All five reproduce the committed triple, and at 8 and 16 the whole record is
#: BYTE-IDENTICAL to the committed row, ``leaf [0]`` / ``shape`` ``synth[0]``,
#: ``harvested`` and the INSENSITIVE ``reason`` string included. **16 is
#: shipped rather than 8** because the choice is not free: the bounded block at
#: 8 holds 16 edges over 8 nodes and at 16 holds 48 over 16, so 16 buys three
#: times the graph for 5.5 s, and BOTH are asserted by the pinned test so the
#: shipped value is never the only one exercised.
#:
#: ⚠️ **THE COUNTER-CONTROL IS WHAT MAKES THIS PER-OP RATHER THAN POLICY**, and
#: it is pinned in ``tests/test_shape_lever_rc471.py`` beside the invariance:
#: :func:`srmech.math.laplacian.recover_check` is DESTROYED by the same shrink
#: — all three of its params collapse to ``RAISED`` at 8 / 16 / 32 (0.02 s,
#: because nothing is computed), where the harvested 64 reproduces
#: ``{charges DEMOTED, edges RAISED, weights DEMOTED}`` in 44.78 s. It is
#: therefore NOT levered, and its committed column stays the 64-shape
#: measurement. Any further op needs its own measured invariance proof:
#: ``propagate_sparse::weights`` (60.8 s), ``relational_structure::weights``
#: (59.2 s) and ``ground_state_flux_response::fluxes`` (51.2 s) are UNMEASURED
#: on this axis and are deliberately not levered — two of the eight slow rows
#: were tested and came out OPPOSITE ways.
#:
#: It is a member of :data:`PROBE_SPEC`, so :func:`probe_signature` moves when
#: it moves and a census measured under a different lever cannot be carried
#: forward as if it were this one.
SHAPE_LEVER: Dict[str, Dict[str, Any]] = {
    "srmech.math.laplacian.recover_check_spectral": {"vocab_size": 16},
}

#: The values of :data:`SHAPE_LEVER` proven verdict-preserving by measurement,
#: asserted by ``tests/test_shape_lever_rc471.py``. A lever value outside this
#: set is a value nobody measured.
SHAPE_LEVER_MEASURED_INVARIANT: Dict[str, Dict[str, Tuple[int, ...]]] = {
    "srmech.math.laplacian.recover_check_spectral": {"vocab_size": (8, 16, 24, 32)},
}


_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")

#: Type identifiers that denote a sequence-shaped parameter — one that CAN carry
#: a numeric leaf. Read from the REGISTRY, never from the signature: the
#: signature is what shielded this class in rc463.
_SEQ_IDENTS = frozenset({
    "HV", "Vec", "Mat", "QMat", "list", "sequence", "Sequence",
    "tuple", "array", "iterable", "Iterable",
})

#: Identifiers that make a shape UNSYNTHESISABLE by this probe (no numeric leaf
#: is constructible). Recorded, not skipped.
_OPAQUE_IDENTS = frozenset({
    "bytes", "str", "dict", "Mapping", "SpectralHandle", "host_callable",
    "host_rng", "Path", "pathlib", "object", "ChainSpec", "One",
    "RecoverableFold", "MockQSeries", "operator_name", "CDRegister",
})


def type_idents(ty: str) -> Tuple[str, ...]:
    """The identifier tokens of a registry type string."""
    return tuple(_IDENT.findall(ty or ""))


def sequence_shaped(ty: str) -> bool:
    """Does the REGISTRY declare this parameter as sequence-shaped?"""
    return any(i in _SEQ_IDENTS for i in type_idents(ty))


#: THE SCALAR LANE (rc472, `#T1188`): type identifiers that denote a scalar
#: NUMERIC parameter — one whose VALUE is the witness slot. Through rc471 the
#: census enumerated sequence-shaped registry parameters only (disclosure 8
#: above), so an op that rounds an exact SCALAR operand — ``rational.sin``,
#: ``kuramoto_inv_n``, every ``float`` coefficient in ``signal_processing`` —
#: was outside the instrument by construction. The lane predicate is exactly
#: ``type_idents(ty) ∩ _SCALAR_IDENTS ≠ ∅ and not sequence_shaped(ty)``; the
#: second clause keeps the two lanes DISJOINT (``list[float]`` is a sequence).
#: ``int`` is deliberately NOT a member: an int lane admits every integer
#: parameter of every op — a period, a dimension, a term count — and the
#: twiddle strict-zero gate goes red on it (measured in the rc472 scoping).
#: Private, like its two peers above, and exposed in :data:`PROBE_SPEC` under
#: a public key, exactly as they are.
_SCALAR_IDENTS = frozenset({"float", "number", "complex"})

#: Where the scalar lane puts its witness: the parameter's VALUE. An ``int``
#: ``1``, for the same reason :func:`synthesize` is int-filled — a ``1.0``
#: would force every op onto a float route and the whole lane would read
#: DEMOTED. ``leaf_paths(1)`` is the empty path and ``set_leaf(1, (), w)`` is
#: ``w``, so the witness triple REPLACES the slot wholesale and the rest of
#: :func:`probe_param` is the same walk for both lanes. A harvested scalar
#: float is never used as a shape: a non-integral one could only ever answer
#: ``INEXACT_BASE`` (through the OTHER parameters, which is what ``clean``
#: reads), and the question is about the carrier, not the harvest.
SCALAR_SLOT = 1

#: THE REQUIRED-SCALAR FILL (rc472 C3, `#T1188`): what :func:`_fill_required`
#: binds to a REQUIRED scalar-numeric sibling the harvest left unbound. The
#: same value as :data:`SCALAR_SLOT`, bound under its own name because it is a
#: different KNOB — the lane decides where the WITNESS goes; this decides what
#: the other scalar parameters are held at while it is asked — and a member of
#: :data:`PROBE_SPEC` in its own right for the same reason.
#:
#: Through the rc472 lane commit ``_fill_required`` asked :func:`synthesize`
#: for EVERY missing required parameter, and ``synthesize`` refuses only the
#: :data:`_OPAQUE_IDENTS`, so a missing ``float`` / ``complex`` / ``float | Q``
#: sibling was bound to ``[1] * 8`` — an 8-vector handed to a parameter the
#: registry declares scalar — and the op RAISED at that sibling before the
#: probed parameter was ever asked. Those rows read RAISED with a reason that
#: was the instrument's, wearing the op's name.
#:
#: What this does NOT reach is named rather than absorbed: a required ``int``
#: sibling (``dim``, ``sigma``, ``k``, ``n_sources``, …) is still bound to a
#: synthesised vector, because :func:`scalar_numeric` excludes ``int`` by
#: design (see :data:`_SCALAR_IDENTS`) and the fill follows the lane's own
#: ident set rather than minting a second one. MEASURED in the rc472 build
#: (native cell, in process, CPython 3.12.3, numpy absent, the shipped
#: :func:`probe_param` walk): this fill moves **13** rows over 8 ops, every one
#: OUT of RAISED and none INTO it; the same walk with ``int`` admitted to the
#: FILL ONLY moves **20**, and the seven it adds — ``cd_promote::x``,
#: ``the_one::w``, ``top_k_by_score::scores``, ``music_doa::R`` /
#: ``::steering_vectors``, ``modular_forms_ring_represent::q_series``,
#: ``quasimodular_represent::q_series`` — are the int-fill residue, handed to
#: the next rc as a design question the lane's exclusion has already ruled on
#: once, not as a knob to widen quietly.
REQUIRED_SCALAR_FILL = SCALAR_SLOT


def scalar_numeric(ty: str) -> bool:
    """Does the REGISTRY declare this parameter as scalar-numeric — the rc472
    lane? Disjoint from :func:`sequence_shaped` by construction."""
    return bool(set(type_idents(ty)) & _SCALAR_IDENTS) and not sequence_shaped(ty)


def lane_of(ty: str) -> str:
    """``"sequence"`` or ``"scalar"`` — the census lane a registry type is
    probed in.

    DERIVED from the type, never stored on a row: the gate keys its NO_SHAPE
    ceiling by ``(lane, cell)`` and reads the lane through this function, so
    a row cannot be filed under a lane by a stale field. Raises on a type in
    neither lane, because such a type has no census row to be asked about.
    """
    if sequence_shaped(ty):
        return "sequence"
    if scalar_numeric(ty):
        return "scalar"
    raise ValueError(f"registry type {ty!r} is in neither census lane")


# ── exactness plumbing ────────────────────────────────────────────────────────
def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def exactify(v: Any) -> Tuple[Any, bool]:
    """Replace every INTEGRAL float leaf with the ``int`` it equals.

    Returns ``(value, clean)``; ``clean`` is False when a NON-integral float
    survives, which disqualifies the binding from a DEMOTED verdict.
    """
    if isinstance(v, bool) or v is None:
        return v, True
    if isinstance(v, float):
        if v == int(v):
            return int(v), True
        return v, False
    if isinstance(v, list):
        out: List[Any] = []
        ok = True
        for x in v:
            y, k = exactify(x)
            out.append(y)
            ok = ok and k
        return out, ok
    if isinstance(v, tuple):
        acc: List[Any] = []
        ok = True
        for x in v:
            y, k = exactify(x)
            acc.append(y)
            ok = ok and k
        return tuple(acc), ok
    if isinstance(v, dict):
        dd: Dict[Any, Any] = {}
        ok = True
        for k2, x in v.items():
            y, k = exactify(x)
            dd[k2] = y
            ok = ok and k
        return dd, ok
    return v, True


def leaf_paths(v: Any, prefix: Tuple[int, ...] = ()) -> Iterator[Tuple[int, ...]]:
    """Paths to every numeric leaf of a nested list/tuple, depth-first."""
    if isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            yield from leaf_paths(x, prefix + (i,))
    elif _is_int(v) or isinstance(v, float):
        yield prefix


def set_leaf(v: Any, path: Tuple[int, ...], value: Any) -> Any:
    """A COPY of ``v`` with the leaf at ``path`` replaced. No mutation."""
    if not path:
        return value
    i, rest = path[0], path[1:]
    seq = list(v)
    seq[i] = set_leaf(seq[i], rest, value)
    return tuple(seq) if isinstance(v, tuple) else seq


def synthesize(ty: str, extra_dims: Sequence[int] = ()) -> List[Any]:
    """Candidate INT-filled shapes for a sequence-shaped type, best first.

    Int-filled is load-bearing: a synthesised ``1.0`` would force every op —
    exact ones included — onto a float route, and the probe would then report
    the whole population DEMOTED.

    ``extra_dims`` carries the lengths of the OTHER list-valued parameters in
    the same binding, tried first. Measured: without it ``dense_adjacency`` and
    ``dense_laplacian`` reported ``RAISED`` on ``weights``, because a weight
    vector must be as long as the harvested ``edges`` list and no dimension in
    :data:`FLAT_DIMS` happened to match. That is an instrument artefact wearing
    the name of an op fact — the exact confusion this rc's D2 half is about.
    """
    idents = set(type_idents(ty))
    if idents & _OPAQUE_IDENTS and not (idents & {"list", "Sequence", "sequence"}):
        return []
    matrixish = bool(idents & {"Mat", "QMat"}) or "list[list" in ty \
        or "Sequence[Sequence" in ty
    dims: List[int] = []
    for n in tuple(extra_dims) + FLAT_DIMS:
        if n > 0 and n not in dims:
            dims.append(n)
    # A UNIT-FIRST vector isolates the witness: every other leaf is 0, so a
    # derived quantity carries the witness alone. ``octonion_norm`` needs it —
    # sqrt(P^2 + junk) can round P, F and G together and read INSENSITIVE.
    flats = [[1] * n for n in dims] + [[1] + [0] * (n - 1) for n in dims if n > 1]
    squares = [[[1 if r == c else 0 for c in range(n)] for r in range(n)]
               for n in SQUARE_DIMS]
    return (squares + flats) if matrixish else (flats + squares)


# ── exact structural comparison ───────────────────────────────────────────────
_ADDR = re.compile(r" at 0x[0-9a-fA-F]+")


def canon(x: Any) -> Any:
    """A hashable EXACT canonical form. Type-tagged, so ``1`` and ``1.0`` differ.

    That distinction is the point: an op that returns the ``int`` it was given
    is exact; one that returns ``1.0`` has passed the value through a float
    carrier even where the magnitude happened to survive.
    """
    if x is None or isinstance(x, bool):
        return ("b", x)
    if _is_int(x):
        return ("i", x)
    if isinstance(x, float):
        return ("f", x.hex() if x == x else "nan")
    if isinstance(x, complex):
        return ("c", canon(x.real), canon(x.imag))
    if isinstance(x, (bytes, bytearray)):
        return ("y", bytes(x))
    if isinstance(x, str):
        return ("s", x)
    if hasattr(x, "to_lists"):
        return ("Q", canon(x.to_lists()))
    if hasattr(x, "tolist"):
        return ("M", canon(x.tolist()))
    if hasattr(x, "numerator") and hasattr(x, "denominator"):
        return ("q", canon(x.numerator), canon(x.denominator))
    if isinstance(x, dict):
        return ("d", tuple(sorted((canon(k), canon(v)) for k, v in x.items())))
    if isinstance(x, (list, tuple, set, frozenset)):
        return ("l", tuple(canon(v) for v in x))
    r = repr(x)
    if _ADDR.search(r):
        return ("?", type(x).__name__)          # unstable identity: uncomparable
    return ("r", r)


def _uncomparable(c: Any) -> bool:
    """Does this canonical form contain the unstable-identity marker?

    Walks EVERY element, and guards the empty tuple. The first draft read
    ``c[0] == "?" or any(... for v in c[1:])``, which assumed every nested
    tuple was a tagged node — but a container node's payload is a tuple OF
    nodes, so the recursion reached a bare child tuple, then an empty one, and
    the whole census died on ``IndexError`` after ~200 ops. A scanner must not
    assume the shape it is scanning.
    """
    if isinstance(c, tuple):
        if c and c[0] == "?":
            return True
        return any(_uncomparable(v) for v in c)
    return False


class _Timeout(Exception):
    pass


def _alarm(_sig, _frm):                                # pragma: no cover
    raise _Timeout()


def call_bounded(fn, kwargs: Dict[str, Any]):
    """``(ok, value_or_exception_string)`` with the per-call cutoff applied."""
    has = hasattr(signal, "SIGALRM")
    old = None
    if has:
        old = signal.signal(signal.SIGALRM, _alarm)
        signal.setitimer(signal.ITIMER_REAL, CALL_TIMEOUT)
    try:
        return True, fn(**kwargs)
    except _Timeout:
        return False, f"TIMEOUT>{CALL_TIMEOUT}s"
    except BaseException as exc:
        return False, f"{type(exc).__name__}: {exc}"[:160]
    finally:
        if has:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)


# ── the honesty read (rc463 Layer 3, generalised off srmech.math.laplacian) ───
#: R3 patterns — a bounded-STEM regex vocabulary with WORD BOUNDARIES and a
#: clause-local NEGATION refusal, matched PER OCCURRENCE.
#:
#: Through rc469 this was a closed literal-substring list (``R3_VOCABULARY``),
#: and it could not read its own tree. It could not spell "approximation" (it
#: held only "approximate", so rc467's own APPROXIMATION went unread); it could
#: not spell "rounding" (only "round-off"); it matched INSIDE unrelated words,
#: so a citation URL containing ``FULp`` declared an op and a JSON tag key
#: spelled ``__float64__`` declared another; and it could not read NEGATION, so
#: a sentence DENYING a tolerance counted as declaring one. rc470 (`#T1188`)
#: replaced it. See disclosures 5 and 9.
#:
#: EVERY KNOB THAT DECIDES A READ MUST APPEAR IN :data:`R3_READER_SPEC` BELOW.
#: That is the contract that makes :func:`reader_signature` meaningful, and it
#: is enforced by REVIEW alone: a knob left outside the tuple moves the reader
#: without moving the digest — precisely the blind spot that signature exists
#: to close, so reproducing it there would be the worst of both.
#: :data:`CASE_POLICY` is a member for exactly that reason; it was the knob an
#: earlier draft of this change left implicit.
CASE_POLICY = "lower"            # the ONLY fold; patterns are lowercase-only

#: The CLOSED fold table :data:`CASE_POLICY` names, and the reason
#: :data:`CASE_POLICY` is now WIRED rather than merely declared.
#:
#: ⚠️ Through rc470's repair commit ``CASE_POLICY`` was a member of
#: :data:`R3_READER_SPEC` that **no code read**: :func:`declares_inexactness`
#: called ``.lower()`` under a comment saying ``# CASE_POLICY == "lower"``, so
#: the constant and the fold agreed only by review. That is the INVERSE of the
#: hole the spec was minted to close — a knob outside the tuple moves the
#: reader without moving the digest; a tuple member nothing reads moves the
#: DIGEST without moving the reader, and no mutation of it can move a read.
#: A gate can then only prove the digest moved (which
#: ``tests/test_silent_carrier_demotion_rc463.py`` did) and never that the
#: READER moved. Removing the member instead would have put the fold back
#: OUTSIDE the spec, which is the worse of the two.
#:
#: The table is CLOSED and checked at import: an unknown policy is a
#: mis-spelling, and a mis-spelling that fell through to a default fold would
#: be the same silent-wrong-answer the whole rc is about. ``"none"`` is a real
#: member, not a placeholder — it is what the can-fail row in
#: ``tests/test_r3_reader_rc470.py`` selects to prove the wire carries current.
#:
#: A real ``raise``, not an ``assert`` (rc433 shape, `#T1188`): this table's
#: own closedness check was ITSELF a bare ``assert`` until the gate in
#: ``tests/test_assert_contract_gate_rc433.py`` caught it — an import-time
#: guard that ``python -O`` strips is no guard at all, the identical defect
#: class rc433 exists to drain. ``ValueError`` follows the stdlib idiom for
#: "argument value outside a closed set of choices" (e.g. ``str.encode``'s
#: ``errors=``), which is what ``CASE_POLICY`` is.
_FOLDS = {"lower": str.lower, "none": lambda s: s}

if CASE_POLICY not in _FOLDS:
    raise ValueError(
        f"CASE_POLICY is {CASE_POLICY!r}, which names no fold in _FOLDS "
        f"({sorted(_FOLDS)}). The table is closed on purpose: a policy that fell "
        f"through to a default would read the tree with a fold its own freshness "
        f"key claims it is not using.")

#: ``(label, pattern)``. The LABEL is what reaches the census, never the matched
#: TEXT — ``tests/test_declared_inexactness_rc466.py`` tells an OWN hit from a
#: DELEGATE hit by whether the string ends in ``)``, so a label must never.
R3_PATTERNS = (
    ("ulp",                 r"\bulps?\b"),
    # ABSORBS AND REMOVES the old "to round-off", which was a strict substring
    # subset of "round-off" and so could never have fired alone.
    ("round-off",           r"\bround-?off\b"),
    ("rounding",            r"\bround(?:ing|s|ed)\b"),
    ("tolerance",           r"\btoleranc\w*"),
    ("float64",             r"\bfloat64\b"),
    ("approximation",       r"\bapproximat\w*"),
    ("terminal float lift", r"\bterminal float lift"),
    ("accurate to",         r"\baccurate to\b"),
    # NO leading ``\b``. ``\b`` before ``~`` asserts a PRECEDING WORD CHARACTER,
    # so ``\b~1e-\d`` never matches at all: EXECUTED, ``re.search(r"\b~1e-\d",
    # "accurate to ~1e-9 here")`` is None while the look-behind below matches.
    # A builder "regularising" this pattern to look like its neighbours would
    # silently drop every ~1e- declaration in the tree.
    ("~1e-",                r"(?<![\w~])~1e-\d"),
    ("inexact",             r"\binexact\w*"),
    # THE STATED-BOUND stem. A fixed-precision Class-N series that names
    # its own error in words was invisible to every earlier vocabulary:
    # ``rational.cos`` says "until the truncation remainder is <
    # ``2**-P``" and read [] through rc470's fourth commit. The ``\s+`` is
    # load-bearing — the docstrings are hard-wrapped and the phrase spans
    # the break.
    #
    # MEASURED on the 732-op registry, everything else held; the two wider
    # forms are REFUSED, and NEITHER SUBSUMES THIS ONE (both miss
    # ``rational.exp``, whose bound is worded "absolute error"):
    #   this pattern         DECLARED 207 -> 215, +8 / -0: rational.cos,
    #                        rational.exp and music.bessel_j_fixed on their
    #                        OWN prose; kepler.pin_slot, rational.cexp,
    #                        rational.complex_exp, rational.tan and
    #                        music.bessel_zero_fixed through one delegate.
    #                        All eight hand-read; none is exact.
    #   ``\btruncation\b``  DECLARED 207 -> 229, +22 / -0. Fifteen of
    #                        the 22 are outside this set and every one
    #                        truncates a LIST, a BASIS or a FILE rather
    #                        than a value — ``huffman``, ``hdc_truncation``,
    #                        ``cooccurrence_topk``, ``the_one``,
    #                        ``harmonic_oscillator_hamiltonian``.
    #   ``\btruncat\w*``    DECLARED 207 -> 278, +71 / -0, of which 33
    #                        ride ONE sentence: ``sha256_bytes``'s "(a
    #                        truncated 32-bit tag)", which is a SLICE of a
    #                        digest — 24 through it and 9 through the
    #                        private ``_sha256_bytes`` that repeats it.
    # The label must not end in ")" — tests/test_declared_inexactness_rc466
    # tells an OWN hit from a DELEGATE hit by exactly that.
    ("truncation",          r"\btruncation\s+(?:remainder|error)\b"
                            r"|\babsolute\s+error\b"),
)

#: Cues that DENY the token following them. ``0|zero`` is a member because the
#: tree writes honest zero-counts ("6135 divisions, 0 inexact") that are the
#: OPPOSITE of a declaration; removing it alone moves DECLARED
#: **222 -> 224** on this tree, letting in exactly
#: ``weight_lattice.weight_multiplicities`` and
#: ``weight_lattice.tensor_product_multiplicities``. The DELTA is the
#: invariant; the baseline moves with every reader change, which is why
#: ``tests/test_r3_reader_rc470.py`` asserts the delta and the NAMED SET
#: rather than a remembered pair. This line read "206 -> 208" until
#: rc470's repair commit: the reader-only baseline copied into a comment
#: while the same build printed 207 -> 209 into the test beside it.
NEGATION_CUES = (r"not|never|no|none|nothing|nor|without|neither|rather\s+than|"
                 r"instead\s+of|free\s+(?:of|from)|cannot|can't|isn't|doesn't|"
                 r"don't|avoids?|refuses?|0|zero")

#: Words a cue may reach across. MEASURED: 3 is too short for
#: ``hypercomplex_exp``'s "rather than falling back to a rounded angle".
NEG_REACH = 4

#: ⚠️ THE INTERVENING WORD CLASS IS THE STOP SET, and it is a
#: READ-DECIDING KNOB — which is why it is a member of
#: :data:`R3_READER_SPEC`. Through the first four rc470 commits it was a
#: LITERAL interpolated into :data:`_R3_NEG`, and therefore OUTSIDE the
#: spec: MEASURED over the 732 own docstrings, dropping the hyphen moves
#: 2 ops' label lists (``math.dispatch.infer`` gains
#: ``tolerance (via _try_spectral)``; ``signal_processing.spectrogram``
#: gains ``rounding``) and widening to ``\S+`` moves 6, with
#: :func:`reader_signature` UNMOVED in both cases — exactly the blind
#: spot that signature was minted to close.
#:
#: ``[-\w'’]+`` cannot match a comma, semicolon, colon, bracket,
#: dash, backtick, quote or asterisk, so a cue's reach DIES at the first
#: punctuation. That is what keeps ``cascade.autocorrelation``'s
#: "JPL-clean: no recursion, no transcendentals), parity to FFT roundoff
#: (~1e-12)" a DECLARATION — ``no`` cannot reach ``roundoff`` across the
#: ``)`` and the ``,``. Widening the class to ``\w+`` or ``\S+``
#: destroys that, and adding a separate explicit stop-set merely
#: duplicates it. The HYPHEN must stay INSIDE the class, or
#: ``dispatch._try_spectral``'s denial "never a float-magnitude tolerance"
#: survives as a declaration.
NEG_WORD_CLASS = r"[-\w'’]+"

SENTENCE_SPLIT = r"(?<=[.!?])\s+|\n\s*\n"

_R3_COMPILED = tuple((lab, re.compile(pat)) for lab, pat in R3_PATTERNS)
_R3_NEG = re.compile(r"\b(?:" + NEGATION_CUES + r")\b(?:\s+" + NEG_WORD_CLASS
                     + r"){0,%d}\s*$" % NEG_REACH)
_R3_SPLIT = re.compile(SENTENCE_SPLIT)


def declares_inexactness(text) -> List[str]:
    """The R3 labels ``text`` DECLARES, in canonical :data:`R3_PATTERNS` order.

    PER OCCURRENCE, not per docstring: a label survives if ANY occurrence of its
    pattern survives negation, in any sentence. ``hypercomplex_exp`` is why — it
    carries a denial ("hold exactly, with ``==``, not to a tolerance") AND a true
    declaration ("the Q61 cosine of the ROUNDED angle") in ONE docstring, so a
    per-docstring rule would have to read one of them wrongly.

    Canonical order, never occurrence order: these labels are written into the
    committed census, and occurrence order would churn cell-columns for no
    information.
    """
    low = _FOLDS[CASE_POLICY](text or "")   # WIRED, not asserted in a comment
    found = set()
    for sent in _R3_SPLIT.split(low):
        if not sent:
            continue
        for lab, rx in _R3_COMPILED:
            if lab in found:
                continue
            for m in rx.finditer(sent):
                if _R3_NEG.search(sent[:m.start()]):
                    continue            # this OCCURRENCE is denied
                found.add(lab)
                break                   # ANY surviving occurrence keeps the label
    return [lab for lab, _ in R3_PATTERNS if lab in found]


#: EVERY KNOB THAT DECIDES A READ LIVES HERE. A knob outside this tuple moves
#: the reader without moving the digest — the blind spot this constant closes,
#: which is why reproducing it here would be self-defeating.
#:
#: ⚠️ The digest is over DATA, not CODE. It is blind to a change in
#: :func:`declares_inexactness`'s BODY that leaves this tuple untouched —
#: re-ordering the three arms of :func:`declaration_hits`, say, or dropping
#: the ``break`` that stops at the first surviving occurrence. (An earlier
#: draft of this warning offered "dropping the sentence split" as its
#: example. That example was FALSE: :data:`SENTENCE_SPLIT` IS a member, and
#: neutering it DOES move the digest — EXECUTED. The genuinely invisible
#: change is one no member can see.) That limit is enforced by review, and
#: is written here rather than left for a reader to discover.
R3_READER_SPEC = (R3_PATTERNS, NEGATION_CUES, NEG_REACH, NEG_WORD_CLASS,
                  SENTENCE_SPLIT, CASE_POLICY)


def reader_signature() -> str:
    """sha256 over :data:`R3_READER_SPEC` — the census's READER freshness key.

    :func:`registry_signature` hashes ``(op name, parameter types, return
    type)``, none of which moves when the READER moves, so a census regenerated
    by an OLDER reader stays GREEN under a newer one. rc470 (`#T1188`) is the
    first rc whose own change is exactly that blind spot, so it ships the key
    that can see it.

    Routed through ``srmech.amsc.format.sha256_bytes`` — never a direct
    ``hashlib`` call — so native dispatch picks it up transparently.
    """
    from srmech.amsc.format import sha256_bytes
    body = json.dumps(R3_READER_SPEC, sort_keys=True) + "\n"
    return sha256_bytes(body.encode("utf-8"))


#: The code-object names CPython gives to the three comprehension forms PEP 709
#: (3.12) INLINED. ``<genexpr>`` is deliberately ABSENT: PEP 709 never inlined
#: generator expressions, so they stay nested on every interpreter and folding
#: them could not repair a version split. MEASURED and INERT rather than
#: assumed — on the real 732-op registry, folding ``<genexpr>`` too (335 nested
#: objects), or folding EVERY nested code object regardless of name (a further
#: 26 ``<lambda>`` and ~35 named inner functions), yields a label map
#: BYTE-IDENTICAL to this tuple's on all five of 3.10.21 / 3.11.16 / 3.12.3 /
#: 3.13.15 / 3.14.7. Scoping the fold to exactly the PEP 709 class is what
#: makes the convergence argument a proof rather than an observation; the null
#: above is recorded because it says the arm could be widened later at a
#: measured cost of zero today.
_COMP_CODE_NAMES = ("<listcomp>", "<setcomp>", "<dictcomp>")


def _delegate_names(code) -> Tuple[str, ...]:
    """``code.co_names`` PLUS every name reachable through a nested
    COMPREHENSION code object, recursively — order-preserving, de-duplicated.

    ⚠️ **THIS EXISTS BECAUSE ``co_names`` ANSWERS A QUESTION ABOUT A COMPILED
    ARTIFACT, AND THE READER IS ASKING ONE ABOUT SOURCE.** Through CPython 3.11
    a comprehension compiles to its OWN nested code object, so a callee named
    only inside one lives in ``<listcomp>.co_names`` and is INVISIBLE to
    ``fn.__code__.co_names``. PEP 709 (3.12) inlined comprehensions and those
    names JOIN the function's. Same source, two readings — MEASURED on this
    registry: **DECLARED 219 on 3.10.21 and 3.11.16, 222 on 3.12.3, 3.13.15 and
    3.14.7**, a cutover at 3.12 with a measured point on each side and no
    unmeasured interior.

    Folding UNCONDITIONALLY makes that split IMPOSSIBLE rather than merely
    named. On >= 3.12 this returns ``()`` for every op in the registry — a
    STRUCTURAL no-op, not a coincidence, because PEP 709 leaves no nested
    comprehension code object to find (MEASURED: 0 of 732 there, against 839
    ``<listcomp>`` + 51 ``<dictcomp>`` + 9 ``<setcomp>`` on 3.10/3.11). On
    <= 3.11 it recovers exactly the three names 3.12 could already see.

    The recursion is EXERCISED, not defensive: ``apokatastasis.zeilberger``
    itself nests a listcomp inside a listcomp
    (``[Poly.from_coeffs([Q(a, b) for a, b in cp]) for cp in coeff_pairs]``,
    :file:`srmech/apokatastasis/zeilberger.py`:306-307), and **48 of 732 ops**
    need depth > 1 to reach their full comprehension-name set.
    """
    seen: set = set()
    out: List[str] = []

    def _push(names) -> None:
        for n in names:
            if n not in seen:
                seen.add(n)
                out.append(n)

    def _walk(c, guard: set) -> None:
        if id(c) in guard:
            return
        guard.add(id(c))
        for const in getattr(c, "co_consts", ()) or ():
            if hasattr(const, "co_names") and const.co_name in _COMP_CODE_NAMES:
                _push(const.co_names)
                _walk(const, guard)

    _push(code.co_names)
    _walk(code, set())
    return tuple(out)


def declaration_hits(fn) -> List[str]:
    """Every R3 marker reachable from ``fn``'s own contract surface.

    THREE ARMS, unchanged in STRUCTURE by rc470: the op's OWN docstring; then
    ``exact=`` in the signature; then, ONLY if still empty, one level of
    delegate through ``fn.__globals__`` over :func:`_delegate_names`, breaking
    at the first delegate with a hit. What rc470 changed is the PREDICATE each
    arm applies — :func:`declares_inexactness` rather than a substring sweep.

    ⚠️ **THE DELEGATE CANDIDATE LIST IS ``_delegate_names(code)``, NOT
    ``code.co_names``** (rc470's last commit, `#T1188`). Reading ``co_names``
    alone asked a COMPILED artifact a question about SOURCE, and PEP 709 made
    the two answers differ: DECLARED read **219** on CPython <= 3.11 and
    **222** on >= 3.12, from one unchanged tree. The fold is unconditional and
    the convergence is MEASURED over the WHOLE population, not inferred from
    three counts — on 3.10.21 / 3.11.16 / 3.12.3 / 3.13.15 / 3.14.7 the folded
    label MAP is byte-identical, all 223 rows, sha256
    ``b43563f9e417da49…`` (222 rows / ``06f93439fe15b27f…`` at rc470; rc471's
    W6 prose added one, hand-read at ``_DECLARED_LABEL_MAP_DIGEST``). That is the LABEL map and not merely the count,
    which matters because of the residue in the next paragraph.

    ⚠️ **WHAT THE FOLD DOES NOT FIX, named so it is not rediscovered as a
    surprise.** The loop ``break``s at the first hit-bearing delegate, so
    ORDER decides the LABEL while the fold only makes MEMBERSHIP convergent by
    construction. **13 of the 573 ops that reach this arm have two or more
    hit-bearing delegates** (an identical list on 3.10 and 3.12), and their
    labels agree across interpreters only because the names that changed
    position are non-hit-bearing and jumped AROUND the hit-bearing pair. The
    label-map digest pinned in ``tests/test_r3_reader_rc470.py`` is what turns
    that accident into something a matrix cell can SEE: without it DECLARED
    would stay 222 everywhere while the credited delegate silently differed.
    The principled repair — making label selection a function of the SET,
    which IS convergent, by iterating sorted names or collecting all hits
    instead of breaking at the first — moves labels on those 13 ops on EVERY
    interpreter and therefore owes its own adjudication and its own rc.

    ⚠️ The delegation follow is rc463's, with ONE change that is the whole point
    of this file: rc463 resolved a delegate as ``getattr(_la, name)``, hard-wired
    to ``srmech.math.laplacian``, so Layer 3 could not read the contract of any
    op outside the module its six hand-rows came from. Here the delegate is
    resolved in ``fn.__globals__``, which is the module the body actually names
    its callees in. Its dependence on ``code.co_names`` ORDER is a PRE-EXISTING
    property, named here so a reviewer does not spend a slot rediscovering it;
    rc470 does not touch it.
    """
    hits = declares_inexactness(inspect.getdoc(fn) or "")
    try:
        if "exact" in inspect.signature(fn).parameters:
            hits.append("exact= opt-in")
    except (TypeError, ValueError):
        pass
    if not hits:
        code = getattr(fn, "__code__", None)
        glb = getattr(fn, "__globals__", {}) or {}
        for name in (_delegate_names(code) if code is not None else ()):
            delegate = glb.get(name)
            if delegate is None or delegate is fn or not callable(delegate):
                continue
            ddoc = inspect.getdoc(delegate) or ""
            hits += [f"{d} (via {name})" for d in declares_inexactness(ddoc)]
            if hits:
                break
    return hits


# ── the probe ─────────────────────────────────────────────────────────────────
def _base_for(entry, rows: Dict[str, Any], *,
              lever: Optional[Dict[str, Dict[str, Any]]] = None
              ) -> Tuple[Dict[str, Any], bool, str]:
    """``(base, exact_clean, source)`` — the harvested binding, exactified.

    ``lever`` defaults to :data:`SHAPE_LEVER` and is applied AFTER the harvest
    and BEFORE :func:`exactify`, so a levered value is exactified on the same
    path a harvested one is. Pass ``{}`` to measure the raw harvest — that is
    how ``tests/test_shape_lever_rc471.py`` takes the shape ladder and the
    counter-control.
    """
    raw = dict((rows.get(entry.name) or {}).get("args") or {})
    src = "ledger" if raw else "none"
    if not raw:
        hint = getattr(entry, "smoke_test_hint", None)
        if isinstance(hint, dict) and isinstance(hint.get("args"), dict):
            raw = dict(hint["args"])
            src = "smoke_test_hint"
    lv = SHAPE_LEVER if lever is None else lever
    over = lv.get(entry.name)
    if over and raw:
        # Only OVERRIDE what the harvest already bound. Introducing a NEW
        # parameter here would be synthesis wearing a lever's name, and the
        # `base_source` would then say `ledger` about a value no ledger holds.
        for k, v in over.items():
            if k in raw:
                raw[k] = v
    base, clean = exactify(raw)
    return base, clean, src


def _fill_required(fn, base: Dict[str, Any], entry
                   ) -> Tuple[Dict[str, Any], List[str]]:
    """Bind the required parameters the harvest left unbound.

    A required sibling whose registry type is scalar-numeric
    (:func:`scalar_numeric`) is held at :data:`REQUIRED_SCALAR_FILL`; every
    other required sibling is asked of :func:`synthesize`, exactly as before
    rc472 C3 (`#T1188`). The scalar arm exists because ``synthesize`` refuses
    only the opaque identifiers, so it answered ``[1] * 8`` for a ``float`` —
    a vector handed to a scalar — and the op raised at the sibling before the
    probed parameter was ever reached. See :data:`REQUIRED_SCALAR_FILL` for
    what the repair moves and for the ``int``-typed residue it leaves named.
    """
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return base, ["<no signature>"]
    types = {p.name: (p.type or "") for p in (entry.parameters or ())}
    missing: List[str] = []
    out = dict(base)
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is not inspect.Parameter.empty or p.name in out:
            continue
        ty = types.get(p.name, "")
        cands = [REQUIRED_SCALAR_FILL] if scalar_numeric(ty) else synthesize(ty)
        if not cands:
            missing.append(p.name)
            continue
        out[p.name] = cands[0]
    for k in list(out):
        if k not in sig.parameters:
            del out[k]
    return out, missing


def _verdict(cP: Any, cF: Any, cG: Any) -> str:
    if _uncomparable(cP) or _uncomparable(cF) or _uncomparable(cG):
        return "UNCOMPARABLE"
    if cP != cF:
        return "EXACT"
    if cG == cF:
        return "INSENSITIVE"
    return "DEMOTED"


def _scalar_siblings(base: Dict[str, Any], pname: str) -> List[str]:
    """The OTHER parameters a witness sweep can move: bare ``int`` / ``bool``.

    Sequence and string siblings are deliberately outside it — substituting a
    small int for a vector or for a mode name asks a DIFFERENT question of the
    op, and would answer this one with an artefact.
    """
    return sorted(k for k, v in base.items()
                  if k != pname and (_is_int(v) or isinstance(v, bool)))


def _alt_bindings(base: Dict[str, Any], pname: str
                  ) -> Iterator[Tuple[str, int, Dict[str, Any]]]:
    """``(sibling, value, binding)`` — ROUND-ROBIN, not sibling-major.

    One value across EVERY sibling before any sibling's second value. See
    :data:`MAX_ALT_BINDINGS` for the measurement that decides this, and for what
    a depth-first walk costs.
    """
    sibs = _scalar_siblings(base, pname)
    spent = 0
    for val in ALT_SIBLING_VALUES:
        for k in sibs:
            if base[k] == val:
                continue
            if spent >= MAX_ALT_BINDINGS:
                return
            spent += 1
            yield k, val, {**base, k: val}


def _vacuous_by(fn, base: Dict[str, Any], pname: str, shape: Any,
                path: Tuple[int, ...]) -> Optional[Tuple[str, int]]:
    """Does this leaf reach the output under some OTHER sibling binding?

    Returns the ``(sibling, value)`` that shows it does, or ``None``.

    ⚠️ **THE COMPARISON IS WITHIN ONE ALTERNATE BINDING.** ``out(H at B')``
    against ``out(F at B')`` — never ``out at B'`` against ``out at B``. Under
    the latter an op that merely RETURNS one of its other parameters moves the
    moment a sibling moves, and every such op would be misfiled ``VACUOUS``
    while the probed leaf still reaches nothing. Both calls here differ in the
    probed leaf and in nothing else, so what they measure is the leaf.
    """
    for k, val, alt in _alt_bindings(base, pname):
        okF, vF = call_bounded(fn, {**alt, pname: set_leaf(shape, path, F)})
        if not okF:
            continue                     # this sibling value does not bind
        okH, vH = call_bounded(fn, {**alt, pname: set_leaf(shape, path, H)})
        if not okH:
            continue
        cF, cH = canon(vF), canon(vH)
        if _uncomparable(cF) or _uncomparable(cH):
            continue
        if cH != cF:
            return k, val
    return None


def probe_param(fn, base: Dict[str, Any], opname: str,
                pname: str, ptype: str) -> Dict[str, Any]:
    """One (op, parameter) row — a sequence-shaped parameter (the leaf walk)
    or, since rc472 (`#T1188`), a scalar-numeric one (the value slot)."""
    rec: Dict[str, Any] = {"op": opname, "param": pname, "type": ptype}
    # ⚠️ Cleanliness is read over the OTHER parameters ONLY. The probed one is
    # about to be REPLACED by the witness shape, so judging the binding by a
    # value that will not survive the call retires the parameter on a question
    # nobody asked: it is what made ``octonion_conjugate`` and
    # ``quaternion_conjugate`` read INEXACT_BASE while they demote.
    clean = exactify({k: v for k, v in base.items() if k != pname})[1]
    extra = [len(v) for k, v in base.items()
             if k != pname and isinstance(v, (list, tuple)) and v]
    # rc472 (`#T1188`): the SCALAR lane's one candidate is the value slot; the
    # sequence lane's shape ladder is untouched. A scalar has no leaf to walk
    # — leaf_paths(SCALAR_SLOT) is the empty path and set_leaf puts the
    # witness AT the value — so everything below is the same walk for both
    # lanes. (A required scalar-NUMERIC sibling is held at REQUIRED_SCALAR_FILL
    # by `_fill_required` since rc472 C3; a required `int` sibling still
    # arrives as an int-filled vector and the op raises at it before this walk
    # starts. That residue is disclosure 8's, not this function's.)
    synth = [SCALAR_SLOT] if scalar_numeric(ptype) else synthesize(ptype, extra)
    shapes: List[Any] = []
    # rc472 C3 (`#T1188`): each candidate's LABEL is recorded beside it, never
    # recovered afterwards by identity. The old `raw_shape is base.get(pname)`
    # read "harvested" for ANY candidate that happened to be the same OBJECT
    # as the base's value — and the scalar lane's one candidate is the small
    # int 1, which CPython interns, so every scalar row whose base value was
    # 1 (a harvested `sin(1)`, or a required sibling held at the fill) called
    # the slot "harvested" for a value no harvest supplied. The lane never
    # offers the harvested value as a candidate (`harvested` below requires a
    # list / tuple), so on a scalar row "harvested" was always the artefact.
    # MEASURED on the first C3 regeneration, both cells: 2 rows relabelled
    # THEMSELVES through the fill (feynman_photon_propagator::k_squared,
    # higgs_potential::phi) with their verdicts unmoved, and the committed C2
    # census already carried the artefact on every scalar row bound at 1.
    labels: List[Optional[str]] = []
    harvested = pname in base and isinstance(base[pname], (list, tuple))
    # ⚠️ ORDER IS A MEASUREMENT DECISION. A harvested vector carrying a
    # NON-INTEGRAL float can only ever yield ``INEXACT_BASE`` — a float result
    # is what such a caller asked for — so trying it first would retire the
    # parameter on a binding that cannot answer the question. It is used only
    # after every int-clean synthesised shape has failed to bind.
    hv_clean = harvested and exactify(base[pname])[1]
    if hv_clean:
        shapes.append(base[pname])
        labels.append("harvested")
    shapes.extend(synth)
    labels.extend([None] * len(synth))
    if harvested and not hv_clean:
        shapes.append(base[pname])
        labels.append("harvested")
    if not shapes:
        rec["verdict"] = "NO_SHAPE"
        rec["reason"] = f"no shape synthesisable for declared type {ptype!r}"
        return rec

    last_err: Optional[str] = None
    saw_leafless = False
    null_seen: Optional[str] = None
    # WHERE the INSENSITIVE null was reached — (shape, path, shape_label),
    # in DISCOVERY order, capped at MAX_NULL_CONTEXTS. The VACUOUS sweep
    # re-asks the question at those exact leaves under a different sibling
    # binding, so it needs the positions, not just the verdict. It is a LIST,
    # and first-wins, for the reason recorded at MAX_NULL_CONTEXTS: a
    # position that binds under the harvested sibling values need not bind
    # under the alternate ones.
    null_ctxs: List[Tuple[Any, Tuple[int, ...], str]] = []
    timed_out = 0
    for si, raw_shape in enumerate(shapes):
        if timed_out:
            rec["verdict"] = null_seen or "CALL_TIMED_OUT"
            rec["reason"] = (
                f"a call exceeded {CALL_TIMEOUT}s on candidate shape "
                f"{timed_out - 1}; the remaining shapes were not tried"
                if null_seen is None else
                f"a call exceeded {CALL_TIMEOUT}s; recorded the null already "
                f"reached")
            return rec
        shape, sclean = exactify(raw_shape)
        paths = list(leaf_paths(shape))[:MAX_LEAVES]
        if not paths:
            saw_leafless = True
            continue
        for path in paths:
            outs: Dict[str, Any] = {}
            failed: Optional[str] = None
            for tag, w in (("P", P), ("F", F), ("G", G)):
                kw = dict(base)
                kw[pname] = set_leaf(shape, path, w)
                ok, val = call_bounded(fn, kw)
                if not ok:
                    failed = val
                    if isinstance(val, str) and val.startswith(TIMEOUT_MARKER):
                        timed_out = si + 1
                    break
                outs[tag] = canon(val)
            if failed is not None:
                last_err = failed
                break                        # this shape does not bind; next one
            v = _verdict(outs["P"], outs["F"], outs["G"])
            if v == "INSENSITIVE":
                # SPLIT THE NULL. One coarse extra call decides whether the leaf
                # reaches the output at all, or merely not at one float64 step.
                ok, val = call_bounded(fn, {**base,
                                            pname: set_leaf(shape, path, H)})
                cH = canon(val) if ok else None
                null_seen = ("INSENSITIVE" if (not ok or cH == outs["F"])
                             else "UNRESOLVED_AT_WITNESS")
                if null_seen == "INSENSITIVE" \
                        and len(null_ctxs) < MAX_NULL_CONTEXTS:
                    null_ctxs.append(
                        (shape, path, labels[si] or f"synth[{si}]"))
                continue                     # position-specific; try next leaf
            if v == "DEMOTED" and not (clean and sclean):
                rec["verdict"] = "INEXACT_BASE"
                rec["reason"] = ("a non-integral float survives in the binding, "
                                 "so a float result is what the caller asked for")
            else:
                rec["verdict"] = v
            rec["leaf"] = list(path)
            rec["shape"] = labels[si] or f"synth[{si}]"
            return rec
        if timed_out:
            continue                     # decided at the top of the next pass
    if timed_out:
        rec["verdict"] = null_seen or "CALL_TIMED_OUT"
        rec["reason"] = (
            f"a call exceeded {CALL_TIMEOUT}s on the last candidate shape"
            if null_seen is None else
            f"a call exceeded {CALL_TIMEOUT}s; recorded the null already reached")
        return rec
    if null_seen is not None:
        # SPLIT THE NULL A SECOND TIME, on a different axis. ``H`` asked whether
        # the WITNESS was too fine. This asks whether the BINDING was degenerate
        # — the difference between a claim about the op and a claim about this
        # one measurement.
        hit = None
        ctx: Optional[Tuple[Any, Tuple[int, ...], str]] = None
        if null_seen == "INSENSITIVE":
            for ctx in null_ctxs:
                hit = _vacuous_by(fn, base, pname, ctx[0], ctx[1])
                if hit is not None:
                    break
        if hit is not None:
            sib, val = hit
            rec["verdict"] = "VACUOUS"
            rec["reason"] = (
                f"no witness reached the output in {MAX_LEAVES} leaves under "
                f"the HARVESTED binding, but it does at {sib}={val} — so the "
                f"null is a fact about this binding, not about the op")
            rec["leaf"] = list(ctx[1])          # type: ignore[index]
            rec["shape"] = ctx[2]               # type: ignore[index]
            return rec
        rec["verdict"] = null_seen
        rec["reason"] = (
            f"no witness reached the output in {MAX_LEAVES} leaves, and none "
            f"reached it under {MAX_ALT_BINDINGS} alternate sibling "
            f"bindings at any of {MAX_NULL_CONTEXTS} null positions "
            f"either"
            if null_seen == "INSENSITIVE" else
            "the leaf reaches the output, but the op's own resolution is "
            "coarser than one float64 step at 2**53 — this witness triple "
            "cannot decide the carrier")
        return rec
    if saw_leafless and last_err is None:
        rec["verdict"] = "NO_SHAPE"
        rec["reason"] = "no numeric leaf constructible (byte / string carrier)"
        return rec
    rec["verdict"] = "RAISED"
    rec["reason"] = last_err or "no shape bound"
    return rec


def probe_op(entry, rows: Dict[str, Any], *,
             lever: Optional[Dict[str, Dict[str, Any]]] = None
             ) -> List[Dict[str, Any]]:
    """Every sequence-shaped parameter of one registered op — and, since rc472
    (`#T1188`), every scalar-numeric one: the two census lanes, disjoint by
    construction (:func:`lane_of`).

    ``lever`` is forwarded to :func:`_base_for`; see :data:`SHAPE_LEVER`.
    """
    params = [p for p in (entry.parameters or ())
              if sequence_shaped(p.type or "") or scalar_numeric(p.type or "")]
    if not params:
        return []
    if entry.name in CONTRACT_SKIP:
        return [{"op": entry.name, "param": p.name, "type": p.type,
                 "verdict": "CONTRACT_SKIP", "reason": CONTRACT_SKIP[entry.name],
                 "base_source": "none", "seconds": 0.0} for p in params]
    res = ea.resolve(entry.name)
    if res is None:
        return [{"op": entry.name, "param": p.name, "type": p.type,
                 "verdict": "UNRESOLVABLE", "base_source": "none",
                 "seconds": 0.0} for p in params]
    fn = res[2]
    base, _clean, src = _base_for(entry, rows, lever=lever)
    base, missing = _fill_required(fn, base, entry)
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        sig = None
    variadic = {p.name for p in (sig.parameters.values() if sig else ())
                if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)}
    out: List[Dict[str, Any]] = []
    for p in params:
        t0 = time.time()
        rec: Dict[str, Any]
        if p.name in variadic:
            rec = {"op": entry.name, "param": p.name, "type": p.type,
                   "verdict": "NO_SHAPE",
                   "reason": "VAR_POSITIONAL / VAR_KEYWORD: cannot be bound by "
                             "keyword, so a single-parameter witness has no slot"}
        elif missing:
            rec = {"op": entry.name, "param": p.name, "type": p.type,
                   "verdict": "NO_SHAPE",
                   "reason": f"required parameter(s) unbindable: {sorted(missing)}"}
        elif sig is not None and p.name not in sig.parameters:
            rec = {"op": entry.name, "param": p.name, "type": p.type,
                   "verdict": "NO_SHAPE",
                   "reason": "declared in the registry but absent from the "
                             "signature; nothing to bind the witness to"}
        else:
            rec = probe_param(fn, base, entry.name, p.name, p.type or "")
        rec["base_source"] = src
        rec["seconds"] = round(time.time() - t0, 3)
        if rec.get("verdict") == "DEMOTED":
            rec["declares"] = declaration_hits(fn)
        out.append(rec)
    return out


def census(rows: Optional[Dict[str, Any]] = None, *,
           progress: bool = False) -> List[Dict[str, Any]]:
    """Every sequence-shaped and (rc472) every scalar-numeric parameter of
    every registered op."""
    from srmech.introspect.tool_schema import get_tool_schema
    rows = ea.load_ledger() if rows is None else rows
    recs: List[Dict[str, Any]] = []
    tools = list(get_tool_schema().tools)
    for i, entry in enumerate(tools):
        t0 = time.time()
        got = probe_op(entry, rows)
        recs.extend(got)
        if got and progress:
            dt = time.time() - t0
            print(f"[{i + 1}/{len(tools)}] {dt:7.2f}s {entry.name} "
                  + ",".join(sorted({r["verdict"] for r in got})),
                  file=sys.stderr, flush=True)
    return recs


def by_verdict(recs: Sequence[Dict[str, Any]], cel: str = "") -> Dict[str, int]:
    """Verdict histogram. ``cel`` selects a MANIFEST column; "" reads a flat
    cell census (what :func:`census` returns)."""
    out: Dict[str, int] = {}
    for r in recs:
        col = r.get(cel) if cel else r
        if col:
            out[col["verdict"]] = out.get(col["verdict"], 0) + 1
    return dict(sorted(out.items()))


def key(row: Dict[str, Any]) -> str:
    """``op::param`` — the row identity, in every consumer."""
    return f"{row['op']}::{row['param']}"


# -- the REGISTRY SIGNATURE: the whole staleness guard -------------------------
def registry_signature_lines() -> List[str]:
    """``name|pname:ptype,...|returntype`` for every registered op, sorted.

    The triple is chosen because it is exactly what decides DEMOTION-CANDIDACY:
    :func:`probe_op` selects parameters by their REGISTRY type, builds a binding
    from the signature, and files the answer under the return carrier. An op
    added, removed or re-signatured moves this string; nothing else about the
    tree does — and that limit is the guard's declared blind spot, written out
    in ``tests/test_silent_carrier_demotion_rc463.py`` rather than left implied.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    out: List[str] = []
    for e in get_tool_schema().tools:
        params = ",".join(f"{q.name}:{q.type or ''}"
                          for q in (e.parameters or ()))
        rt = getattr(getattr(e, "returns", None), "type", "") or ""
        out.append(f"{e.name}|{params}|{rt}")
    return sorted(out)


def registry_signature() -> str:
    """sha256 over the NORMALISED signature lines.

    Normalised (newline-joined with a trailing newline, UTF-8) rather than raw
    file bytes, for the reason ``tests/test_op_name_set_witness_rc361.py`` gives
    about its own manifest: a CRLF checkout must not make the digest disagree
    between the Windows and Linux CI cells, or a platform artifact wears a
    rename's clothes.

    Routed through ``srmech.amsc.format.sha256_bytes`` — never a direct
    ``hashlib`` call — so native dispatch picks it up transparently.
    """
    from srmech.amsc.format import sha256_bytes
    body = ("\n".join(registry_signature_lines()) + "\n").encode("utf-8")
    return sha256_bytes(body)


#: EVERY KNOB THAT DECIDES A VERDICT LIVES HERE — the PROBE's freshness key
#: (rc471, `#T1188`), the third and last of the three staleness axes this file
#: names. :func:`registry_signature` moves when the POPULATION moves;
#: :func:`reader_signature` moves when the R3 READER moves; neither moves when
#: the INSTRUMENT does, and the instrument is what decides the verdict column.
#:
#: ⚠️ **THIS IS THE AXIS THAT ACTUALLY FIRED, and nothing could see it.**
#: MEASURED across the ``srmech-v0.9.0rc468`` -> ``rc469`` boundary: the
#: registry signature did NOT move and ``declares`` moved ZERO times, yet
#: **16 census verdicts moved over 7 ops**. Only **2 of the 7** had an
#: implementation change; the other **5** moved because the PROBE moved —
#: ``VACUOUS`` went 0 -> 9 mentions between those tags, arriving with
#: :data:`ALT_SIBLING_VALUES`, :data:`MAX_ALT_BINDINGS`, :func:`_alt_bindings`
#: and :func:`_vacuous_by`. A per-op IMPLEMENTATION key — the other candidate,
#: REFUSED for rc471 in the CHANGELOG with its three reasons — catches 2 of
#: those 7 ops. This one catches the other 5.
#:
#: The membership rule is the one :data:`R3_READER_SPEC` states: a knob outside
#: this tuple moves the instrument without moving the digest. So it holds MORE
#: than the four bounds a narrow reading would take — the witness values
#: themselves (:data:`P` / :data:`F` / :data:`G` and the coarse fourth
#: :data:`H`, which SPLITS a null and therefore decides a verdict string), the
#: shapes :func:`synthesize` offers (:data:`FLAT_DIMS` / :data:`SQUARE_DIMS`:
#: which shape BINDS first decides the ``shape`` and ``leaf`` a row records,
#: and can decide the verdict when an early candidate raises), the two identity
#: sets that decide which registry parameters are probed AT ALL
#: (:data:`_SEQ_IDENTS` / :data:`_OPAQUE_IDENTS` — a change to either moves the
#: ROW POPULATION with no registry signature move, which is the same blind spot
#: one level out), the hang guard :data:`CALL_TIMEOUT` (at 20 s it DECIDED two
#: rows; the comment beside it records the flip), the named refusals
#: :data:`CONTRACT_SKIP` (a member's presence IS its row's verdict), and
#: :data:`SHAPE_LEVER` (rc471's own change, which sets the SHAPE a row is
#: measured at).
#:
#: ⚠️ The digest is over DATA, not CODE, exactly as :data:`R3_READER_SPEC` is.
#: It is blind to a change in :func:`probe_param`'s BODY that leaves this tuple
#: untouched — re-ordering the candidate shapes, dropping the ``break`` that
#: retires a parameter at the first deciding leaf, or making
#: :func:`_alt_bindings` depth-first (which the comment at
#: :data:`MAX_ALT_BINDINGS` measures as SILENT). That limit is enforced by
#: review and is written here rather than left for a reader to discover.
PROBE_SPEC = (
    ("witness", (str(P), str(F), str(G), str(H))),
    ("leaves", MAX_LEAVES),
    ("alt_sibling_values", ALT_SIBLING_VALUES),
    ("alt_bindings", MAX_ALT_BINDINGS),
    ("null_contexts", MAX_NULL_CONTEXTS),
    ("call_timeout", CALL_TIMEOUT),
    ("contract_skip", CONTRACT_SKIP),
    ("shape_lever", SHAPE_LEVER),
    ("flat_dims", FLAT_DIMS),
    ("square_dims", SQUARE_DIMS),
    ("seq_idents", tuple(sorted(_SEQ_IDENTS))),
    ("opaque_idents", tuple(sorted(_OPAQUE_IDENTS))),
    # rc472 (`#T1188`): the scalar lane's two knobs, exact peers of the two
    # lines above. `scalar_idents` decides which registry parameters the lane
    # admits AT ALL — a change moves the ROW POPULATION with no registry
    # signature move, the identical blind spot `seq_idents` closes one lane
    # over — and `scalar_slot` is the value every scalar witness is put at.
    # Adding them is what makes rc472's own regeneration REFUSE a one-cell
    # merge: the committed columns carry the rc471 digest, so both cells must
    # be re-measured from an empty manifest, which is the guard doing its job.
    ("scalar_idents", tuple(sorted(_SCALAR_IDENTS))),
    ("scalar_slot", SCALAR_SLOT),
    # rc472 C3 (`#T1188`): the value a REQUIRED scalar-numeric sibling is held
    # at by `_fill_required`. It decides which rows can BIND at all — 13 rows
    # left RAISED when it landed — so it is a verdict-deciding knob and belongs
    # in the key, separately from `scalar_slot` even while the two values are
    # equal: a future change to one and not the other must move the digest.
    ("required_scalar_fill", REQUIRED_SCALAR_FILL),
)


def probe_signature() -> str:
    """sha256 over :data:`PROBE_SPEC` — the census's INSTRUMENT freshness key.

    The peer of :func:`reader_signature`, minted at rc471 (`#T1188`) for the
    third staleness axis. Written PER CELL into the manifest by
    :func:`merge_cell`, refused on merge exactly as the registry and reader
    signatures are, and asserted by
    ``tests/test_silent_carrier_demotion_rc463.py``.

    The witness values are stringified because :data:`P`, :data:`F`, :data:`G`
    and :data:`H` are 54-bit integers and a JSON number is not the right
    carrier for a value whose EXACT bits are the point.

    Routed through ``srmech.amsc.format.sha256_bytes`` — never a direct
    ``hashlib`` call — so native dispatch picks it up transparently.
    """
    from srmech.amsc.format import sha256_bytes
    body = json.dumps(PROBE_SPEC, sort_keys=True) + "\n"
    return sha256_bytes(body.encode("utf-8"))


# -- manifest readers ---------------------------------------------------------
def demoters(recs: Sequence[Dict[str, Any]], cel: str = ""
             ) -> List[Dict[str, Any]]:
    """DEMOTED rows, sorted. ``cel`` selects a MANIFEST column; "" reads flat."""
    def v(r):
        return (r.get(cel) or {}).get("verdict") if cel else r.get("verdict")
    return sorted((r for r in recs if v(r) == "DEMOTED"),
                  key=lambda r: (r["op"], r["param"]))


def undeclared(recs: Sequence[Dict[str, Any]], cel: str = ""
               ) -> List[Dict[str, Any]]:
    """DEMOTED rows publishing NO R3 accuracy declaration — the strict-zero set."""
    return [r for r in demoters(recs, cel)
            if not ((r.get(cel) or {}) if cel else r).get("declares")]


def undeclared_keys(recs: Sequence[Dict[str, Any]], cel: str) -> List[str]:
    return sorted(key(r) for r in undeclared(recs, cel))


def divergent(recs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """THE NAMED FINDING: rows whose verdict depends on whether `libsrmech` loaded.

    rc463 already rates this class WORSE than a plain demotion — an op whose
    ANSWER is decided by which projection happens to be dispatching is not
    merely inexact, it is two ops wearing one name. Through ``08d80a037`` the
    disagreement was ABSORBED into two per-cell pinned artefacts, which is
    exactly how it stopped being visible. Here it is a first-class row property
    and every member is named in ``meta.divergent``.
    """
    out = []
    for r in recs:
        n, u = r.get("native"), r.get("pure")
        if n and u and n["verdict"] != u["verdict"]:
            out.append(r)
    return sorted(out, key=lambda r: (r["op"], r["param"]))


def load_manifest(path: Optional[Path] = None
                  ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """``(meta, rows)`` from the ONE committed manifest.

    There is no cell-swap check here and nothing to stale-check against a live
    run: this file is read identically in every CI cell, which is the whole
    reason it replaced the two per-cell artefacts.
    """
    p = path or CENSUS
    meta: Dict[str, Any] = {}
    recs: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("record") == "meta":
                meta.update(obj)
            else:
                recs.append(obj)
    return meta, recs


# -- the tool run -------------------------------------------------------------
#: Row fields that belong to the (op, parameter) itself rather than to a cell.
_SHARED = ("op", "param", "type", "base_source")
#: Per-cell fields. ``seconds`` is DELIBERATELY not among them: it is a property
#: of the HOST, and a committed artefact carrying it would churn on every
#: regeneration and make any digest over the file host-dependent — the defect
#: this rc removed at the level of the whole artefact. The tool PRINTS the
#: slowest rows instead, which is where that number is actually useful.
_CELL_FIELDS = ("verdict", "reason", "leaf", "shape", "declares")


def merge_cell(path: Optional[Path] = None, *, progress: bool = True
               ) -> Dict[str, Any]:
    """Measure THIS cell and merge its column into the committed manifest.

    The other cell's column is carried forward UNTOUCHED — which is the rc460
    worked-example-ledger defect (its own CHANGELOG entry, of the scoped re-run
    rc469 has since removed: it "stamps the CURRENT cell's ``native`` flag onto
    rows merged from another cell") repaired rather than repeated: nothing here
    relabels a measurement it did not take.

    ⚠️ It REFUSES to carry forward a column measured against a DIFFERENT
    registry signature, OR against a different R3 READER, OR against a
    different PROBE. Two halves of one manifest measured on two different trees
    is a file that is internally consistent and jointly false, and the gate
    reading it could not tell.

    The READER refusal (rc470, `#T1188`) is the one that catches the shortcut
    this rc's own change invited: running only the native cell. A reader change
    moves NO registry signature, so without it the pure column is carried
    forward with its stale ``declares`` and nothing anywhere objects.

    The PROBE refusal (rc471, `#T1188`) closes the third axis, and rc471 IS a
    tree it fires on: :data:`SHAPE_LEVER` moves :func:`probe_signature`, so a
    one-cell regeneration on this tree is REFUSED BY NAME rather than silently
    producing a manifest whose two columns were measured by two instruments.
    That is the guard working; the cost is that BOTH cells must be measured in
    the rc that changes the instrument.
    """
    import srmech
    p = path or CENSUS
    me = cell()
    sig = registry_signature()
    rsig = reader_signature()
    psig = probe_signature()

    prev_meta: Dict[str, Any] = {}
    prev_rows: Dict[str, Dict[str, Any]] = {}
    if p.exists():
        prev_meta, prv = load_manifest(p)
        prev_rows = {key(r): r for r in prv}
    other = [c for c in CELLS if c != me][0]
    prev_rsigs = dict(prev_meta.get("reader_signature_sha256") or {})
    if other in prev_rsigs and prev_rsigs[other] != rsig:
        raise SystemExit(
            f"REFUSING to merge: the committed {other!r} column's `declares` "
            f"was written by R3 reader {prev_rsigs[other][:12]} and this "
            f"tree's reader is {rsig[:12]}. A reader change moves NO registry "
            f"signature, so nothing else in this file can see it. Re-measure "
            f"{other!r} on THIS tree "
            f"(`PYTHONPATH=$PWD python3 tools/demotion_probe.py` in that cell) "
            f"or delete {p.name} and measure both.")
    prev_psigs = dict(prev_meta.get("probe_signature_sha256") or {})
    if other in prev_psigs and prev_psigs[other] != psig:
        raise SystemExit(
            f"REFUSING to merge: the committed {other!r} column was measured "
            f"by PROBE {prev_psigs[other][:12]} and this tree's probe is "
            f"{psig[:12]}. A probe change moves NO registry signature and no "
            f"reader signature — MEASURED at rc468->rc469, where 16 verdicts "
            f"moved over 7 ops with both of those UNMOVED. Re-measure "
            f"{other!r} on THIS tree "
            f"(`PYTHONPATH=$PWD python3 tools/demotion_probe.py` in that cell) "
            f"or delete {p.name} and measure both.")
    prev_sigs = dict(prev_meta.get("registry_signature_sha256") or {})
    if other in prev_sigs and prev_sigs[other] != sig:
        raise SystemExit(
            f"REFUSING to merge: the committed {other!r} column was measured "
            f"against registry signature {prev_sigs[other][:12]} and this tree "
            f"is {sig[:12]}. Re-measure {other!r} on THIS tree "
            f"(`PYTHONPATH=$PWD python3 tools/demotion_probe.py` in that cell) "
            f"or delete {p.name} and measure both.")
    # rc472 W2 (`#T1188`): the FOURTH carry-forward refusal — the other
    # column's RELEASE — with the interpreter WARNING beside it.
    _refuse_cross_release(dict(prev_meta.get("measured_at") or {}), other,
                          srmech.__version__, sys.version_info, p.name)

    t0 = time.time()
    recs = census(progress=progress)
    elapsed = round(time.time() - t0, 1)

    merged: Dict[str, Dict[str, Any]] = {}
    for r in recs:
        k = key(r)
        row = dict(prev_rows.get(k) or {})
        for f in _SHARED:
            if r.get(f) is not None:
                row[f] = r[f]
        row[me] = {f: r[f] for f in _CELL_FIELDS if r.get(f) is not None}
        merged[k] = row
    # Rows the OTHER cell measured that this one no longer reaches at all are
    # KEPT with this cell's column dropped, so a shrinking reach is visible as a
    # half-populated row rather than as a silent deletion.
    for k, row in prev_rows.items():
        if k not in merged:
            keep = dict(row)
            keep.pop(me, None)
            if keep.get(other):
                merged[k] = keep

    rows = [merged[k] for k in sorted(merged)]
    for r in rows:
        n, u = r.get("native"), r.get("pure")
        if n and u and n["verdict"] != u["verdict"]:
            r["divergent"] = True
        else:
            r.pop("divergent", None)

    sigs = dict(prev_sigs)
    sigs[me] = sig
    rsigs = dict(prev_rsigs)
    rsigs[me] = rsig
    psigs = dict(prev_psigs)
    psigs[me] = psig
    measured = dict(prev_meta.get("measured_at") or {})
    # ⚠️ NO WALL CLOCK HERE. `census_seconds` was in this dict until it was
    # MEASURED: a native re-run on an unchanged tree reproduced all 703 rows
    # byte-identically and differed in exactly one field, this one (74.2 ->
    # 66.6). A committed artefact carrying the host's clock can never diff
    # empty on a no-op re-measurement, which destroys the one signal a
    # maintainer actually reads off `git diff` — and it is the same
    # host-dependence this rc removed from the ROWS, left behind in the meta.
    # The elapsed time is PRINTED below, which is where a human wanting it
    # looks; nothing reads it back.
    measured[me] = {
        "srmech_version": srmech.__version__,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    }
    cells_present = [c for c in CELLS if any(r.get(c) for r in rows)]
    meta = {
        "record": "meta",
        "cells_measured": cells_present,
        "registry_signature_sha256": sigs,
        "reader_signature_sha256": rsigs,
        "probe_signature_sha256": psigs,
        "measured_at": measured,
        "n_rows": len(rows),
        "n_ops": len({r["op"] for r in rows}),
        "by_verdict": {c: by_verdict(rows, c) for c in cells_present},
        "undeclared": {c: undeclared_keys(rows, c) for c in cells_present},
        "divergent": [f"{key(r)} native={r['native']['verdict']} "
                      f"pure={r['pure']['verdict']}" for r in divergent(rows)],
        "witness": {"P": str(P), "F": str(F), "G": str(G)},
    }
    with p.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, sort_keys=True) + "\n")
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    slow = sorted(((r.get("seconds") or 0.0), key(r)) for r in recs)[-8:]
    print(f"\n[{me}] census {elapsed}s over {len(recs)} rows; manifest now "
          f"{len(rows)} rows / {meta['n_ops']} ops; "
          f"cells {meta['cells_measured']}", file=sys.stderr)
    print("slowest rows this cell:", file=sys.stderr)
    for sec, k in reversed(slow):
        print(f"  {sec:8.1f}s  {k}", file=sys.stderr)
    if meta["divergent"]:
        print(f"NATIVE-vs-PURE DIVERGENCE ({len(meta['divergent'])} rows):",
              file=sys.stderr)
        for d in meta["divergent"]:
            print(f"  {d}", file=sys.stderr)
    return meta


def _refuse_cross_release(prev_measured: Dict[str, Any], other: str,
                          live_version: str, live_py, manifest_name: str
                          ) -> None:
    """rc472 W2 (`#T1188`): the FOURTH carry-forward refusal in
    :func:`merge_cell`, symmetric with the three ``SystemExit`` refusals on
    the reader / probe / registry signatures — on the OTHER cell's
    ``measured_at[other]["srmech_version"]``.

    Until rc472 the other column's ``measured_at`` was carried forward with
    NO comparison of either field, so a manifest whose two columns were
    measured at two RELEASES could be PRODUCED here and caught only later,
    by ``tests/test_silent_carrier_demotion_rc463.py``'s version stamp —
    after the cell's minutes had been spent on a merge the tree would
    refuse. An implementation can change carrier behaviour behind an
    unchanged signature, an unchanged reader and an unchanged probe; the
    release stamp is the one axis those three digests cannot see, which is
    why this refuses rather than warns.

    The INTERPRETER gets a printed WARNING, never a refusal: the committed
    census declares ``3.12`` in both cells, and the rc471 arc measured the
    interpreter non-causal for every figure it had been blamed for —
    asserting it here would forbid the very cross-interpreter re-measure
    that showed so. Can-fail: ``tests/test_merge_cell_cross_release_rc472.py``
    plants a manifest whose other column carries a foreign release and
    asserts the refusal fires BEFORE :func:`census` runs.
    """
    rec = dict(prev_measured.get(other) or {})
    v = rec.get("srmech_version")
    if v is not None and v != live_version:
        raise SystemExit(
            f"REFUSING to merge: the committed {other!r} column was measured "
            f"at srmech {v} and this tree is {live_version}. An "
            f"implementation can change carrier behaviour behind an unchanged "
            f"signature, reader and probe — the release stamp is the one axis "
            f"those digests cannot see. Re-measure {other!r} on THIS tree "
            f"(`PYTHONPATH=$PWD python3 tools/demotion_probe.py` in that cell) "
            f"or delete {manifest_name} and measure both.")
    py = rec.get("python")
    live = f"{live_py[0]}.{live_py[1]}"
    if py is not None and py != live:
        print(f"[merge_cell] WARNING: the committed {other!r} column was "
              f"measured on python {py}; this cell is running {live}. Not a "
              f"refusal — the interpreter is DISCLOSED in `measured_at`, and "
              f"the rc471 arc measured it non-causal — but a reader of the "
              f"merged manifest should know the two columns differ in it.",
              file=sys.stderr)


if __name__ == "__main__":                                # pragma: no cover
    m = merge_cell()
    print(json.dumps({k: v for k, v in m.items() if k != "undeclared"},
                     indent=2, sort_keys=True))
