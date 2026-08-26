/**
 * research-triality — STANDING research workflow (user direction 2026-05-31 / 2026-06-01 / 2026-06-04;
 * rationale F248 + F291). Supersedes and replaces the retired k=2 `research-twin`.
 *
 * Every research dive runs the SAME task through THREE agents — haiku + sonnet + opus (identical
 * prompt; the model TIER is the ONLY variable) — then adversarially TRIANGULATES and MERGES by
 * per-claim majority (2-of-3). We never trust one model's research.
 *   - F248 (no privileged model): the multi-model pass caught two hallucinated citations a single
 *     sonnet run would have shipped silently, and showed the F242b honesty-gradient is TASK-RELATIVE
 *     (sonnet most honest on RENDERING, opus most honest/uncentered on RESEARCH) — so NO model is the
 *     privileged "honest one".
 *   - F291 (why three not two): an opus∥sonnet PAIR is a k=2 parity check — it DETECTS disagreement
 *     but cannot error-CORRECT (a 1-vs-1 split has no majority -> a human tie-breaker). k=3 = haiku +
 *     sonnet + opus is the Hurwitz k=3 error-correction rung (ℍ/SU(2)/triality, the same 1:3:7 ladder
 *     the loop bind's k=7 sits on); majority (2-of-3) CORRECTS with no human tie-break. Live proof:
 *     the old 2-model pass missed L4's boundary-digit drift; k=3 triality caught it unanimously.
 *
 * INVOKE:
 *   Workflow({ name: "research-triality", args: { task: "<the full research prompt>" } })
 *   Workflow({ name: "research-triality", args: "<the full research prompt>" })       // string ok
 *   Workflow({ scriptPath: "docs/srmech/rbs_lm_research/research_triality_workflow.js", args: {...} })
 *
 * The CANONICAL committed copy is this file (docs/); a working copy lives in the gitignored
 * .claude/workflows/research-triality.js so the Workflow tool resolves it by name. Keep them in sync.
 */
export const meta = {
  name: 'research-triality',
  description: 'Standing k=3 triality-research: run a research task identically through haiku + sonnet + opus (the model tier is the only variable), triangulate per-claim, then merge by 2-of-3 majority — no privileged model, error-correcting (F248 + F291)',
  phases: [
    { title: 'Survey-ABC', detail: 'same prompt through 3 agents — haiku ∥ sonnet ∥ opus (tier is the only variable)' },
    { title: 'Triangulate', detail: 'per-claim 2-of-3 majority; catch hallucinated citations; centering/structural-touch per the F242b lens' },
    { title: 'Merge-verify', detail: 'majority-corrected union, spot-verify load-bearing citations, attested result + flagged minority residue' },
  ],
}

const TASK = (typeof args === 'string') ? args : (args && args.task)
if (!TASK) {
  throw new Error('research-triality requires args.task (the research prompt) or a string arg')
}

const DISC = `STANDING RESEARCH DISCIPLINE (load-bearing): (1) UNCENTERED — privilege no example/substrate/hypothesis; centering hides fiber content; hold many perspectives at once. (2) WEB-VERIFY every load-bearing citation (real authors + title + venue + year + DOI/URL); FLAG any you cannot verify; a paywalled-only DOI is rejected — use the OA/preprint copy. (3) Pre-STATE any null and report mechanically (no leaning; null findings count). (4) The biology / domain facts are the LITERATURE's to assert; any framework reading (e.g. a substrate-native settling op, an A-N cascade) is a LENS offered, never asserted as established. (5) Benign / defensive / framework-reading scope ONLY; CAD-ban (algebra/spectral/eigenbasis side, no fabrication/RTL/mesh/timing-closure). State uncertainties explicitly.`

const RESEARCH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    findings: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: {
        item: { type: 'string' },
        claim: { type: 'string' },
        support: { type: 'string' },
        citation: { type: 'string' },
        verified: { type: 'boolean' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      }, required: ['item', 'claim', 'citation', 'verified', 'confidence'] } },
    cross_cutting: { type: 'string' },
    uncentered_note: { type: 'string' },
    gaps: { type: 'array', items: { type: 'string' } },
  }, required: ['findings', 'cross_cutting', 'uncentered_note', 'gaps'],
}

const TRIANGULATE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    finding_count_by_tier: { type: 'object', additionalProperties: false,
      properties: { haiku: { type: 'integer' }, sonnet: { type: 'integer' }, opus: { type: 'integer' } },
      required: ['haiku', 'sonnet', 'opus'] },
    per_claim: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: {
        item: { type: 'string' },
        agree_count: { type: 'integer' },                                    // how many of the 3 tiers asserted it (1/2/3)
        consensus: { type: 'string', enum: ['unanimous', 'majority', 'minority', 'disputed'] },
        corrected_claim: { type: 'string' },                                 // the 2-of-3 majority-corrected claim
        dissenting_tier: { type: 'string', enum: ['haiku', 'sonnet', 'opus', 'none'] },
      }, required: ['item', 'agree_count', 'consensus', 'corrected_claim'] } },
    who_centered_less: { type: 'string', enum: ['haiku', 'sonnet', 'opus', 'tie'] },
    structural_touch_difference: { type: 'string' },
    false_attributions_caught: { type: 'array', items: { type: 'string' } },  // hallucinated citations any tier emitted
    consistent_with_F242b_gradient: { type: 'boolean' },
    verdict: { type: 'string' },
  }, required: ['finding_count_by_tier', 'per_claim', 'who_centered_less',
    'false_attributions_caught', 'consistent_with_F242b_gradient', 'verdict'],
}

const MERGE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    merged_findings: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { item: { type: 'string' }, claim: { type: 'string' }, best_citation: { type: 'string' },
        consensus: { type: 'string', enum: ['unanimous', 'majority', 'minority', 'disputed'] },
        verification_status: { type: 'string', enum: ['verified', 'flagged', 'unverifiable'] } },
      required: ['item', 'claim', 'best_citation', 'consensus', 'verification_status'] } },
    cross_cutting: { type: 'string' },
    flagged_citations: { type: 'array', items: { type: 'string' } },
    minority_residue: { type: 'array', items: { type: 'string' } },           // 1-of-3 claims kept but marked
    honest_tier: { type: 'string' },
  }, required: ['merged_findings', 'cross_cutting', 'flagged_citations', 'minority_residue', 'honest_tier'],
}

phase('Survey-ABC')
const [haikuSurvey, sonnetSurvey, opusSurvey] = await parallel([
  () => agent(`${DISC}\n\n=== RESEARCH TASK ===\n${TASK}`, { label: 'survey:haiku', phase: 'Survey-ABC', model: 'haiku', schema: RESEARCH_SCHEMA }),
  () => agent(`${DISC}\n\n=== RESEARCH TASK ===\n${TASK}`, { label: 'survey:sonnet', phase: 'Survey-ABC', model: 'sonnet', schema: RESEARCH_SCHEMA }),
  () => agent(`${DISC}\n\n=== RESEARCH TASK ===\n${TASK}`, { label: 'survey:opus', phase: 'Survey-ABC', model: 'opus', schema: RESEARCH_SCHEMA }),
])

phase('Triangulate')
const triangulation = await agent(
  `Three independent surveys produced from the IDENTICAL prompt — the only variable is the model TIER (HAIKU, SONNET, OPUS). This is a k=3 triality error-correction pass (F291): for EACH item, count how many of the three tiers assert it (agree_count 1/2/3) and set consensus = unanimous(3) / majority(2) / minority(1); the 2-of-3 MAJORITY is the corrected claim (no human tie-break). Note the dissenting tier where one disagrees. Then, WITHOUT leaning, per the F242b lens: (a) who CENTERED less / held more perspectives; (b) STRUCTURAL-TOUCH — who asserted a lens as established; (c) CATCH every hallucinated/false attribution any tier emitted (list each); (d) is it consistent with the F242b task-relative gradient. Do NOT privilege opus just because it is the largest tier — the whole point is majority over tiers, not deference to one.\n\nHAIKU: ${JSON.stringify(haikuSurvey)}\n\nSONNET: ${JSON.stringify(sonnetSurvey)}\n\nOPUS: ${JSON.stringify(opusSurvey)}`,
  { label: 'triangulate', phase: 'Triangulate', model: 'opus', schema: TRIANGULATE_SCHEMA })

phase('Merge-verify')
const merged = await agent(
  `Merge the three surveys into ONE attested result by the k=3 majority, NO model privileged. (1) Keep every item; set its claim to the 2-of-3 MAJORITY-corrected claim from the triangulation; a 1-of-3 (minority) item is KEPT but recorded in minority_residue and marked consensus='minority'. (2) best-attested citation per item. (3) SPOT-VERIFY (web) the most load-bearing citations; mark verified/flagged/unverifiable; reject paywalled-only DOIs for OA; carry every false attribution the triangulation caught into flagged_citations. (4) cross-cutting synthesis (mark any framework lens as LENS, not asserted). (5) honest_tier note (domain facts = literature's; framework reading = lens). No leaning.\n\nHAIKU: ${JSON.stringify(haikuSurvey)}\n\nSONNET: ${JSON.stringify(sonnetSurvey)}\n\nOPUS: ${JSON.stringify(opusSurvey)}\n\nTRIANGULATION: ${JSON.stringify(triangulation)}`,
  { label: 'merge-verify', phase: 'Merge-verify', model: 'opus', schema: MERGE_SCHEMA })

return { surveys: { haiku: haikuSurvey, sonnet: sonnetSurvey, opus: opusSurvey }, triangulation, merged_result: merged }
