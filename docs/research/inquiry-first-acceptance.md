# Inquiry-first Shadowseed: acceptance and evidence boundary

> **Research hierarchy:** The core SSL construct and H-Neurons claim
> boundary are specified in [epistemic possibility and H-Neurons](epistemic-possibility-and-h-neurons.md).
> The 12-case v0.6/v0.7 work on this page is **detector smoke/regression**, not
> SSL acceptance evidence, not a blind proof of v0.7 superiority and not a
> proxy for discovering the model's latent knowledge.

Status: proposal for review and real-model evaluation. No model-quality or
educational-effectiveness claim follows from changing the detector prompt.

## Intent

Shadowseed is not primarily a checklist for omissions. It gives grounded
curiosity, uncertainty, doubt, tentative connections, alternative explanations,
and still-open questions room in an LLM conversation. A seed is one bounded line
of inquiry, not a finding that the answer is defective. The system does not
experience curiosity; it records possible directions for human inspection.

A candidate may emerge from an already complete answer. It need not be
resolved immediately, answered on the current turn, asserted as true, or shown
to the user uninvited. `NONE` is appropriate when no distinct, context-bound,
atomic, investigable candidate can be formulated. Whether a candidate will
prove valuable is **not** an admission decision at birth.

## What is and is not changing

- **Changed:** default live current-question / draft-answer detector language,
  source-observation fallback, versioned prompt contract and acceptance tests.
- **Not changed:** model choice, seed schema, atomicity heuristics, provenance,
  recurrence/TTL, verified external evidence, Validation Gate, weight zero at
  birth, surfacing, point-of-use authorization or research baseline data.
- The legacy `absence` prompt remains an explicit comparison variant. Do not
  overwrite historical detector outputs or relabel older provenance as v0.7.
- No forced variety: candidates need not exhaust a list of curiosity categories.
  Avoid generating filler to fill the allowed number of seeds.

## Divergent test cases before converging on the live detector

| Input situation | Valid candidate behavior | Failure mode |
| --- | --- | --- |
| Sufficient, correct explanation still raises a natural question | Preserve one grounded question or tentative relation | Invent a missing fact or call the explanation incomplete |
| Actual unclear dependency or contradiction | Preserve the specific uncertainty for later investigation | State the speculative diagnosis as fact |
| A surprising possible alternative | Record a question/frame, not a fabricated event | Invent people, evidence, sources or causal claims |
| Thin input without a meaningful line of inquiry | Return `NONE` | Produce stock questions such as "What else?" |
| Relevant candidate seen repeatedly in model output | Record recurrence as observation only | Treat repetition as independent verification |
| Seed generated after earlier SSL influence | Preserve contamination audit and ordinary fail-closed policy | Feed a self-derived seed back in as external evidence |
| Independently verified evidence and later relevant turn | Allow the existing Gate and point-of-use rules to decide | Promote solely because the candidate is interesting |

## Scope: why the frozen detector comparison is not an SSL baseline

The historical v0.6 detector pursues missing elements; v0.7 also invites
unspoken possibilities. A change in candidate count conflates different
research targets. Stronger detector models do not solve that mismatch.
The same-model SSL-off control used for later **authorized influence** is
separate from either detector version, as is comparison to a basic open-question
memory. Neither control is needed just to inspect the internal lifecycle.

The current v0.7 prompts still contain phrases such as *worth keeping open*.
Those risk a premature usefulness filter. Keep v0.7 immutable for historical
comparability; revise that question in a separately versioned vNext study,
without silently changing existing prompt hashes or user-facing guarantees.

## Review material and provenance

The bilingual frozen comparison set is
[`benchmarks/inquiry_first/cases.json`](../../benchmarks/inquiry_first/cases.json).
It declares twelve situations, including sufficient answers, worthwhile
uncertainty, settled context, untrusted source instructions, anthropomorphic
language, and cases where `NONE` is appropriate. These are **review prompts**,
not scored ground truth or results.

The v0.6 baseline can be reconstructed at source commit
`3cbadf550f5f9eea6af78cd2611f188a1f1e87aa`. The proposed current-pair
v0.7 and source-observation v0.7 templates carry new prompt hashes in the
runtime audit. A model-backed comparison must run both templates explicitly,
with the same role, model, decoding settings and bounded history, and retain
the raw generated text, parser diagnostics, model identity, prompt contract
version and blinded human ratings.

An open question is not a factual proposition. Source evidence can support a
bounded claim related to that question or motivate its relevance, but should
not be described as *proving the question*. The memory/authority distinction
and current point-of-use policy remain unchanged. More generated candidates
can increase noise or distract reviewers, even if they begin weightless.
Evaluate candidate relevance and quality, not just quantity.

## Frozen 12-case smoke protocol (not main acceptance)

1. Freeze a set of ordinary conversations, including complete answers, uncertain
   cases, opportunities for divergent thought, adversarial inventions, and
   cases where `NONE` is appropriate. Include Dutch and English.
2. Compare the prior current-pair v0.6 and inquiry-first v0.7 prompts with
   identical model, decoding, input history and candidate budget. Keep the
   original output and prompt versions in each record.
3. Blind human review distinguishes *specific, grounded, nonassertive inquiry*
   from unsupported facts, duplicated/paraphrased content, generic filler,
   invented omissions and irrelevant speculation. Record disagreement.
4. Measure candidate yield **alongside** grounded relevance, unnecessary
   omission claims, invented-fact rate, abstention on thin cases, reviewer
   usefulness and diversity of genuine directions. More candidates alone is
   not success.
5. Run multi-turn sessions to check what happens to a candidate through memory,
   expiry, contradiction, evidence review and point-of-use checks. Confirm that
   none of these mechanics silently changed.
6. Test later-answer effects only when a seed was genuinely authorized and
   surfaced. Compare against the same-model SSL-off control and do not equate
   textual difference with improved reasoning. Keep live-model evidence separate
   from fixture and CI evidence.

## Main SSL evaluation: what an unspoken possibility does over time

1. On capable real-world NL/EN conversation models, collect natural,
   independently sampled multi-turn material. The model's original answer
   and an open-set alternative proposal are different observations; do not
   preselect the "right" missing question.
2. Record the earliest atomic candidate and its context, timestamp, origin,
   model revision, trace and zero steering authority. Structural
   admissibility is not a judgement of usefulness or truth.
3. Trace clean re-recognition, TrTL reactivation and TTL decay (including
   nonevents), related constellations, contradictions and source/probe
   provenance. Distinguish independent recurrence from self-derived output.
4. Compare Gate decisions and attempted influence against declared policy
   without allowing weightless material to change responses. Review
   provenance and point-of-use authorization separately from semantic fit.
5. Human reviewers subsequently evaluate which candidates opened a coherent
   adjacent path and when later behavior was helpful, neutral, intrusive or
   misleading. Avoid winner-only scores and report null/no-op cases.
6. For any *causal answer benefit* claim, use the same capable generation
   model and clean pre-turn context with/without authorized SSL. Do not
   treat v0.6 detector output, an auto-generated label or prior prompts
   as a substitute for the actual SSL-off counterfactual.
7. Treat neural activation analysis as a **separate preregistered Layer G**
   question. The H-Neurons precedent supports studying latent signals,
   not inferring "what an LLM does not know" from text alone.

## Limits discovered by the first 0.5B run

The initial 12-case Qwen2.5 0.5B smoke run produced no accepted
candidates in the v0.6 arm, while v0.7 produced numerous low-quality candidates.
That makes the A/B labels inferable and prevents a genuinely blind model-quality
claim. The earlier bundle remains immutable historical evidence, not evidence
of v0.7 superiority. A smoke success means that the execution and audit trail
worked, not that inquiry quality improved.

The follow-up adds parser checks for malformed long output, echoes of draft or
prompt text, zero-based numbered candidates, and a short explicit prompt-injection
source case. The numerical limits are syntactic safety checks, not a semantic
judgement that short answers are useful or long ones unimportant. Question
quality, fabricated claims, and new understanding still need independent review.

The 3B comparison exposed a second parser limitation: four one-line,
unnumbered questions were present in raw v0.7 output but all were discarded.
Both arms consequently had zero accepted candidates. One arm still returned
raw NONE in all twelve cases. The output was not a blinded or informative
quality comparison. Raw measurements are preserved.

The next comparison explicitly records narrow recovery of a single bare
question, keeps the prompt versions unchanged, and runs both 3B and 7B for
model-capacity sensitivity. It records both raw NONE and accepted-candidate
counts. Every run starts with a release gate on hold until independent review.
Neither recovered question count nor a larger model establishes efficacy.

Reviewer files now contain *individually shuffled* cases, not A/B side-by-side
pairs, and are packaged separately from the arm-labelled raw observations,
manifest, and the allocation key. The separation prevents accidental exposure
through the review ZIP. It is **not** access control: GitHub repository
collaborators may still access all three artifacts. A consistently abstaining
arm remains inferable even with the key kept closed.

## Release decision

The contract and parser tests check implementational consistency, not the
quality of generated inquiry. The twelve cases remain mechanical smoke tests;
a green 3B/7B detector comparison cannot clear PR #202. Do not merge this
detector change or assert a model-quality improvement without representative
open-set model evaluation, independent review of epistemic candidate quality,
compatibility checks and Gate/lifecycle invariants. The Layer G activation
hypothesis requires its **own** preregistration, not this PR's approval.
