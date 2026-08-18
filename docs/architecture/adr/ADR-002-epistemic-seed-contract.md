# ADR-002: Shadow Seeds Are Atomic Epistemic Candidates

- Status: Accepted; implementation alignment in progress
- Date: 2026-08-18
- Supersedes: no earlier ADR
- Refines: ADR-001

## Context

Shadow Seed Learning (SSL) exists to retain useful uncertainty without silently turning model speculation into truth or steering authority. Earlier SSL 4.5 and 4.6 material, the current runtime, and the August 2026 alignment audit all converge on the same core idea but do not always separate doctrine from historical heuristics.

The repository currently contains several mechanisms that can look like doctrine because they are concrete: an 18-word atomicity limit, Dutch separator rules, TTL values, cosine thresholds, recurrence thresholds, fixed weight increments, and surfacing caps. Those values are useful implementation parameters. They are not the definition of SSL.

At the same time, merely making arbitrary model output weightless is not enough. A Shadow Seed is not any uncertain note. It must represent one small epistemic candidate that can be investigated independently.

## Decision

A Shadow Seed is **one atomic epistemic candidate** tied to a specific context.

Canonical rule:

> A seed may represent one gap, doubt, missing relation, boundary, dependency, unstated assumption, alternative hypothesis, contradiction to investigate, or relevant what-if direction. It is a candidate for investigation, not a fact, instruction, evidence item, conclusion, or authority grant.

The minimum semantic contract is:

1. **Atomic.** One seed represents one epistemic uncertainty or missing relation.
2. **Context-bound.** The candidate is connected to the source question, answer, document, or task that produced it.
3. **Investigable.** It is possible in principle to seek recurrence, evidence, falsification, or another bounded test of that same candidate.
4. **Non-assertive at birth.** A generated possibility is not accepted as true merely because the detector produced plausible prose.
5. **Weightless at birth.** New authority is exactly zero.
6. **Identity-preserving.** Downstream modules must not silently change what the seed claims or asks.

## Gap, doubt, and what-if are all valid SSL territory

SSL is not limited to grammatically explicit omission statements such as "X is missing".

The following can all be valid atomic seeds when they satisfy the semantic contract:

- **Gap:** a relevant relation, boundary, factor, owner, dependency, or condition is absent.
- **Doubt:** the current framing leaves a specific uncertainty unresolved.
- **What-if / alternative direction:** one relevant explanatory frame or relation could change the interpretation and is worth testing.

A what-if must still name a direction to investigate rather than assert an invented fact. This is why the current generative detector can be doctrine-compatible: it asks for one angle, frame, relation, or dimension and explicitly forbids treating that direction as established truth.

Existing `CandidateType` values are useful audit metadata for this epistemic origin. Candidate type does not itself change trace, weight, evidence, promotion, or Gate policy.

## Detection establishes candidacy, not authority

The pipeline responsibilities are intentionally separate:

```text
DETECT       -> proposes one atomic epistemic candidate
REMEMBER     -> records the candidate with trace > 0 and weight = 0
TEST         -> gathers recurrence, evidence, falsification, or bounded probe results
GATE         -> may change authority under an explicit policy
POINT OF USE -> decides whether current authority may affect this action
INFLUENCE    -> optional, bounded, and audited
```

Short form:

> Detection establishes candidacy. Trace establishes persistence. Validation establishes authority. Point-of-use authorization permits influence.

## Atomicity is doctrine; the current heuristic is not

Semantic atomicity is a hard invariant. Specific parser and prescreen rules are calibration aids.

The following are **not** canonical definitions of atomicity:

- a fixed maximum of 18 words;
- the presence or absence of a comma;
- Dutch tokens such as `en`, `of`, or `ontbreekt`;
- a particular embedding threshold;
- a particular model family or parameter count.

These rules may remain as tested heuristics, especially for historical corpora, but code and documentation must label them as heuristics. A semantically atomic candidate must not be declared non-SSL merely because a historical surface-form heuristic rejects it. Conversely, a short candidate is not automatically atomic.

The runtime must reject empty or whitespace-only candidates. A candidate that cannot yet be shown to be atomic should be normalized, reviewed, or rejected before it can participate in recurrence or authority decisions.

## Model capability is not part of the trust model

SSL must remain valid if the detector changes from a small local model to a frontier model.

A stronger model may:

- identify subtler gaps;
- produce better atomic doubts;
- propose more useful alternative frames;
- reduce malformed detector output.

It may not receive additional authority merely because it is stronger. The same birth and Gate invariants apply:

```text
trace > 0  means remembered
weight = 0 means no steering authority
```

The Qwen 7B runs in this repository are reference measurements of the largest practical GitHub-hosted route used at that time. They are not an architectural model ceiling. Future high-end-model tests are capability-scaling experiments, not changes to the authority contract.

## Recurrence and external evidence

Recurrence is an observation that the same epistemic candidate appeared again. It is not truth and is never external evidence.

The production-oriented `evidence_backed` policy is allowed to validate verified external support without first requiring model recurrence. Requiring recurrence as a universal prerequisite would make repeated model behavior part of the trust anchor, which conflicts with remembering without trusting.

This does not mean that one source should be able to manufacture repeated authority increments. Evidence identity and independence are defined separately in ADR-004.

The compatibility-only `legacy_evidence_required` policy may continue to reproduce historical 4.5 accumulation semantics for replay and compatibility. That policy is not the canonical definition of SSL.

## Validation search and influence retrieval are different operations

A weightless atomic seed may be used as a **read-only validation query** against a trusted evidence layer when the result cannot steer the user-facing answer or downstream action directly. This is evidence gathering, not influence.

By contrast, retrieval whose result is injected into an answer, action, warning, tool call, or decision is influence-bearing and must remain behind promotion plus point-of-use authorization.

Therefore:

```text
weightless seed -> bounded validation search -> evidence offered to Gate
promoted seed   -> point-of-use check -> optional influence retrieval
```

SSOT validation of open weightless seeds is an existing example of the first pattern.

## Lifecycle parameters are calibration

TTL, TrTL thresholds, dormancy duration, recurrence thresholds, similarity thresholds, fixed increments, promotion thresholds, top-k values, and resurface damping are policy or calibration parameters unless a later ADR explicitly promotes one of them to a doctrine invariant.

A calibration value must be:

- validated for type and range;
- observable in reports where it affects an experiment;
- changeable without redefining what SSL is;
- tested for boundary behavior.

## Identity preservation across modules

Every module must preserve the seed's epistemic identity.

A module must not silently:

- turn a gap into a factual conclusion;
- turn a what-if into a claim of truth;
- merge unrelated uncertainties and then count them as one recurring seed;
- convert recurrence into external evidence;
- convert semantic similarity into source trust;
- convert retrieval presence into confirmation;
- convert promotion into mandatory inclusion;
- convert surfaced candidate data into instructions.

## Consequences

### Positive

- restores atomicity as a first-class SSL invariant;
- keeps gaps, doubts, and relevant what-ifs inside the original SSL idea;
- allows detector capability to scale independently of authority;
- prevents historical thresholds from becoming accidental doctrine;
- makes module-by-module review possible with one stable semantic contract;
- preserves the strict authority and point-of-use boundaries from ADR-001.

### Costs

- some historical atomicity filters need better language-neutral coverage;
- tests must distinguish semantic contracts from corpus-specific heuristics;
- longer or unusual but valid candidates may need review rather than binary rejection;
- evidence and contaminated-observation semantics require explicit follow-up contracts.

## Required invariants

1. One accepted seed represents one epistemic candidate.
2. Empty or whitespace-only seeds are invalid.
3. Every newly created seed starts with zero authority.
4. Trace and recurrence cannot grant authority unless the active Gate policy explicitly permits them.
5. Generated detector output cannot become verified evidence by relabeling.
6. Candidate type is provenance, not authority.
7. Detector model size or reputation never bypasses the Gate.
8. Calibration parameters are not doctrine unless explicitly promoted by an ADR.
9. User-facing influence still requires current point-of-use authorization under ADR-001.

## Verification targets

Implementation alignment should include tests for:

- empty/whitespace rejection;
- English and Dutch atomic candidates;
- compound candidate rejection or normalization;
- model-detector output not being rewritten by historical human-input normalization;
- all new seeds being weightless;
- candidate type having no authority effect;
- config values failing fast outside valid ranges;
- high-end-model evaluation preserving the same Gate invariants.
