# Evidence-backed efficacy protocol

## Purpose

The capability-scaling harness measures candidate generation, parser behavior, recurrence mechanics, Gate behavior, and review-ready research artifacts. Its normal live arm intentionally injects no external evidence, so zero positive authority is the expected safety invariant rather than an efficacy result.

The evidence-efficacy runner adds the missing paired research question:

> When a predeclared candidate receives provenance-bearing external support through the shipped `evidence_backed` Gate, does that authorized candidate improve a later answer when it actually surfaces?

This is a research protocol, not a second product runtime. It uses the canonical `ShadowChatSession`, `SSLManager`, Validation Gate, contradiction state, and `AgentSafetyContract`.

## Three distinct research views

Keep these arms separate in analysis.

1. **Live no-evidence negative control.** The ordinary live policy is `evidence_backed`; generated recurrence cannot grant authority. Any unexplained positive authority event is a harness/runtime failure.
2. **Exploratory recurrence counterfactual.** The capability-scaling evaluation arm may use `exploratory` to study recurrence-driven authority under an explicit non-production policy.
3. **Evidence-backed paired efficacy.** The new runner uses baseline-isolated evaluation mechanics with the `evidence_backed` policy. It can submit only predeclared, operator-attested external support through `ShadowChatSession.submit_evidence`. A blind A/B item exists only if the resulting authorized seed later passes point-of-use checks and surfaces.

The third arm does **not** change the product Gate policy. Baseline isolation is used only so the comparison answer does not contaminate later history.

## Canonical preregistration

Use:

```text
src/shadowseed/data/evidence_efficacy_preregistration_v1.json
```

Copy it into every result bundle before execution. If the scientific contract changes, create a versioned amendment before inspecting the new results. Do not overwrite the prior preregistration.

The preregistration requires:

- `gate_policy_id = evidence_backed`;
- generated model output is never evidence;
- external support is operator/researcher attested;
- stable `source_ref` values;
- only `ssot`, `human_feedback`, or `retrieval` evidence kinds;
- blind answer preference review;
- no A/B denominator inflation on turns where no authorized seed surfaced.

## Suite contract

A suite uses schema `ssl-evidence-efficacy-suite-v1` and English conversations. Each conversation needs at least two turns and at least one predeclared evidence event.

Example:

```json
{
  "schema": "ssl-evidence-efficacy-suite-v1",
  "version": "study-1",
  "language": "en",
  "conversations": [
    {
      "id": "CONV_001",
      "domain": "example domain",
      "turns": [
        {"question": "Initial question"},
        {"question": "Later question where the supported direction could matter"}
      ],
      "evidence_plan": [
        {
          "evidence_id": "source-001",
          "after_turn": 0,
          "selector": {"text_contains": "predeclared candidate phrase"},
          "kind": "ssot",
          "source_ref": "study://source/001",
          "strength": 1.0,
          "independent": true,
          "reason": "Predeclared source supports this candidate"
        }
      ]
    }
  ]
}
```

### Candidate selectors

A plan item must use exactly one selector form:

- `seed_id`: deterministic replay when the exact seed identity is already part of a frozen fixture;
- `text_contains`: a predeclared textual target; ambiguity or no match is recorded as failure to create an opportunity;
- `born_turn` + `seed_index`: deterministic mechanical tests and tightly controlled fixtures.

Do not inspect a failed run and replace an unmatched selector to manufacture a successful opportunity. For real-model efficacy studies, prefer a predeclared semantic/textual target derived from the study design or use a separate pilot plus a new held-out preregistered run.

## Evidence is an external attestation

The runner cannot prove that a source is true. It can prove that the software received a typed signal with a stable source identity and that the canonical Gate handled that signal.

The researcher/operator is responsible for the external statement:

> this source actually supports this candidate.

The runner therefore refuses recurrence, probe output, task outcome, model output, and other internal channels as efficacy evidence. `verified=True` is never inferred from model fluency.

## Opportunity audit

Every planned evidence event writes an item to `opportunity_audit.json` with this stage order:

```text
candidate observed
-> evidence submitted
-> Gate authority granted
-> selected on a later turn
-> point-of-use allowed
-> surfaced
-> blinded A/B generated
```

A stopped path is a result. Typical terminal reasons include:

- candidate selector did not match;
- Gate did not grant authority;
- selected but blocked at point of use;
- no later relevant surfacing opportunity;
- A/B generated.

This prevents `0 A/B items` from being collapsed into the vague statement that SSL had no effect.

## Running the fixture smoke

Fixture runs prove mechanics only:

```bash
python -m shadowseed.benchmark.evidence_efficacy run \
  --backend fixture \
  --model-id fixture \
  --embedding-backend lexical \
  --suite path/to/evidence-efficacy-suite.json \
  --preregistration src/shadowseed/data/evidence_efficacy_preregistration_v1.json \
  --output-dir results/evidence-efficacy/fixture
```

Verify the moved bundle:

```bash
python -m shadowseed.benchmark.evidence_efficacy verify \
  results/evidence-efficacy/fixture
```

For real-model runs, pin the same provenance fields used by capability scaling: model revision/digest, embedding revision, exact suite, preregistration, Git SHA, environment, and output hashes.

## Blind review

The bundle contains the same answer packet/key shape used by capability scaling:

```text
review/answer_review_packet.json
review/answer_review_key.json
```

Only surfaced turns enter the packet. Reviewers see A/B in blind order and choose `A`, `B`, or `tie`. The runner intentionally leaves reviewer fields blank. It never invents independent human judgments.

The bundle also includes empty candidate packet/key files so the existing `capability_scaling summarize-reviews` command can summarize its answer review without a parallel review implementation.

## Interpretation

A completed run can support statements such as:

> Under this pinned model, suite, evidence plan, source attestation, embedding setup, runtime revision, and review sample, N predeclared evidence opportunities reached surfacing and reviewers preferred the SSL answer in X of Y non-tie comparisons.

It cannot support:

- the candidate is universally true;
- SSL generally improves answers;
- every promoted seed helps;
- recurrence is evidence;
- larger models deserve more authority;
- the system is production-ready.

Report unmatched selectors, blocked Gate events, point-of-use denials, and no-opportunity conversations alongside successful A/B items. Negative and null results are part of the protocol rather than errors to hide.
