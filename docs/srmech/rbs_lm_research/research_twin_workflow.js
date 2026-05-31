/**
 * research-twin — STANDING research workflow (user direction 2026-05-31; rationale F248).
 *
 * Every research dive runs the SAME task through BOTH an opus agent and a sonnet agent
 * (identical prompt; model is the ONLY variable), then adversarially compares + merges.
 * We never trust one model's research. F248 proved why: the twin caught two hallucinated
 * citations a single sonnet run would have shipped silently, and showed the F242b honesty-
 * gradient is TASK-RELATIVE (sonnet most honest on RENDERING, opus most honest/uncentered on
 * RESEARCH) — so NO model is the privileged "honest one". Holding both perspectives at once is
 * the citation-integrity + uncentered-coverage safeguard, and is itself the no-privileged-
 * perspective discipline applied to our own renderers.
 *
 * INVOKE:
 *   Workflow({ name: "research-twin", args: { task: "<the full research prompt>" } })
 *   Workflow({ name: "research-twin", args: "<the full research prompt>" })       // string ok
 *   Workflow({ scriptPath: "docs/srmech/rbs_lm_research/research_twin_workflow.js", args: {...} })
 *
 * The CANONICAL committed copy is this file (docs/); a working copy lives in the gitignored
 * .claude/workflows/research-twin.js so the Workflow tool resolves it by name. Keep them in sync.
 */
export const meta = {
  name: 'research-twin',
  description: 'Standing twin-research: run a research task identically through an opus agent and a sonnet agent, adversarially compare (F242b lens), then merge/verify — no privileged model',
  phases: [
    { title: 'Survey-AB', detail: 'same prompt, 1 opus agent + 1 sonnet agent (model is the only variable)' },
    { title: 'Compare', detail: 'adversarial diff per the F242b structure-touch / centering / citation lens' },
    { title: 'Merge-verify', detail: 'union findings (no privileged model), spot-verify load-bearing citations, attested result + flagged residue' },
  ],
}

const TASK = (typeof args === 'string') ? args : (args && args.task)
if (!TASK) {
  throw new Error('research-twin requires args.task (the research prompt) or a string arg')
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

const COMPARE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    opus_finding_count: { type: 'integer' }, sonnet_finding_count: { type: 'integer' },
    who_held_more_perspectives: { type: 'string', enum: ['opus', 'sonnet', 'tie'] },
    who_centered_less: { type: 'string', enum: ['opus', 'sonnet', 'tie'] },
    structural_touch_difference: { type: 'string' },
    overclaim_difference: { type: 'string' },
    citation_discipline_difference: { type: 'string' },
    false_attributions_caught: { type: 'array', items: { type: 'string' } },
    consistent_with_F242b_gradient: { type: 'boolean' },
    verdict: { type: 'string' },
  }, required: ['opus_finding_count', 'sonnet_finding_count', 'who_centered_less',
    'structural_touch_difference', 'citation_discipline_difference', 'false_attributions_caught',
    'consistent_with_F242b_gradient', 'verdict'],
}

const MERGE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    merged_findings: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { item: { type: 'string' }, claim: { type: 'string' }, best_citation: { type: 'string' },
        verification_status: { type: 'string', enum: ['verified', 'flagged', 'unverifiable'] } },
      required: ['item', 'claim', 'best_citation', 'verification_status'] } },
    cross_cutting: { type: 'string' },
    flagged_citations: { type: 'array', items: { type: 'string' } },
    honest_tier: { type: 'string' },
  }, required: ['merged_findings', 'cross_cutting', 'flagged_citations', 'honest_tier'],
}

phase('Survey-AB')
const [opusSurvey, sonnetSurvey] = await parallel([
  () => agent(`${DISC}\n\n=== RESEARCH TASK ===\n${TASK}`, { label: 'survey:opus', phase: 'Survey-AB', model: 'opus', schema: RESEARCH_SCHEMA }),
  () => agent(`${DISC}\n\n=== RESEARCH TASK ===\n${TASK}`, { label: 'survey:sonnet', phase: 'Survey-AB', model: 'sonnet', schema: RESEARCH_SCHEMA }),
])

phase('Compare')
const comparison = await agent(
  `Two independent surveys produced from the IDENTICAL prompt — the only variable is the model (one OPUS, one SONNET). Deliberate A/B per F242b (the SONNET renderer touches/over-supplies the STRUCTURE of knowledge LESS on a RENDER task; F248 found this INVERTS on a RESEARCH task — opus was more uncentered + cleaner-cited, sonnet over-claimed + carried unflagged false attributions; the 0/0/0 structural-invention floor held on both). Assess WITHOUT leaning: (a) COVERAGE; (b) CENTERING — did either privilege/collapse the landscape? who held more perspectives?; (c) STRUCTURAL-TOUCH — who imposed more structure / asserted a lens as established?; (d) CITATION DISCIPLINE — verified-vs-flagged, and CATCH any hallucinated/false attribution (list each); (e) is it consistent with the F242b directional gradient or does it invert again? OPUS: ${JSON.stringify(opusSurvey)}\n\nSONNET: ${JSON.stringify(sonnetSurvey)}`,
  { label: 'compare', phase: 'Compare', model: 'opus', schema: COMPARE_SCHEMA })

phase('Merge-verify')
const merged = await agent(
  `Merge the two surveys into ONE attested result, NO model privileged. (1) UNION the findings (an item from EITHER survey is kept). (2) best-attested claim + citation per item. (3) SPOT-VERIFY (web) the most load-bearing citations; mark verified/flagged/unverifiable; reject paywalled-only DOIs for OA; carry every false attribution the comparison caught into flagged_citations. (4) cross-cutting synthesis (mark any framework lens as LENS, not asserted). (5) honest tier (domain facts = literature's; framework reading = lens). No leaning; keep weak/flagged items IN but marked. OPUS: ${JSON.stringify(opusSurvey)}\n\nSONNET: ${JSON.stringify(sonnetSurvey)}\n\nCOMPARISON: ${JSON.stringify(comparison)}`,
  { label: 'merge-verify', phase: 'Merge-verify', model: 'opus', schema: MERGE_SCHEMA })

return { opus_survey: opusSurvey, sonnet_survey: sonnetSurvey, ab_comparison: comparison, merged_result: merged }
