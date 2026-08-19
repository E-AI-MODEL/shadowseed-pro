# ADR-003: SSL-Influenced Output Is an Observation, Not Independent Recurrence

- Status: Accepted; minimum fail-closed boundary implemented
- Date: 2026-08-18
- Refines: ADR-001 and ADR-002

## Context

The live runtime can surface a previously promoted Shadow Seed into the model prompt. The answer produced on that turn is therefore causally exposed to SSL context. A detector may then find a candidate in that answer.

That candidate can be valuable. It can also be a paraphrase, consequence, or reframing caused by the surfaced seed. Semantic distance is not proof of causal independence. Counting such a candidate as fresh recurrence would let SSL reinforce itself.

The implementation fails closed: when any seed influenced a live turn, every detected candidate from that answer is deferred from seed intake and listed in `suppressed_self_attributed_candidates`. This is safe against self-credit, but the historical field name "suppressed" can be misread as "discarded". The contract interprets these records as deferred contaminated observations.

## Decision

An SSL-exposed detector result is a **contaminated observation**.

Canonical rule:

> Observe it, preserve its provenance, but do not count it as independent recurrence and do not let it create or raise authority until an independent observation or external validation establishes a clean basis.

The minimum live behavior is:

1. record the raw candidate and the turn that produced it;
2. record which surfaced seed ids made the turn SSL-exposed;
3. do not increment an existing seed's occurrence count from that observation;
4. do not create an authority-bearing recurrence signal from it;
5. do not treat semantic dissimilarity as proof that it is independent;
6. permit a later clean observation to create or reinforce the corresponding seed normally;
7. preserve the contaminated observation in the audit/session record so it can be inspected and measured.

The current `suppressed_self_attributed_candidates` field satisfies the minimal audit-preservation requirement because turn reports are persisted. New code and documentation should describe these entries as **deferred contaminated observations**, not as evidence that the candidates were invalid.

## Why not ingest every contaminated candidate as a normal seed?

Weightlessness prevents immediate steering, but normal seed intake also participates in deduplication, occurrence counting, clustering, lifecycle state, and later Gate inputs. Ingesting a contaminated candidate into those same paths without an explicit taint model would blur observation and independent recurrence.

A future implementation may introduce a separate immutable `CandidateObservation` ledger or a taint-aware seed observation model. If it does, contaminated observations may be attached to candidate identity while remaining recurrence-ineligible. Until that model is implemented, deferral from normal seed intake is the safer interpretation.

## Why not discard the whole detector result?

Because SSL is about remembering uncertainty without trusting it. A potentially useful gap discovered after influence still carries research and diagnostic value. The information must remain auditable even when it cannot count toward authority.

This creates a deliberate distinction:

```text
clean detector observation
    -> atomicity check
    -> seed intake / recurrence eligibility

SSL-exposed detector observation
    -> record with provenance
    -> no recurrence credit
    -> later clean observation or external evidence required
```

## Relationship to the Qwen 7B deferral measurement

The Qwen 7B stress artifact recorded complete same-turn deferral for candidates detected on influenced turns. Those counts are opportunity-cost measurements of this conservative attribution boundary. They do not prove that the deferred candidates were useful, true, permanently lost, or incorrectly blocked.

Future high-end-model experiments should retain this measurement and add a qualitative review of deferred observations. Model capability does not remove the need for causal provenance.

## Consequences

### Positive

- prevents self-reinforcing recurrence loops;
- keeps detector observations available for audit and research;
- avoids pretending cosine distance proves causal independence;
- preserves the separation between observation, recurrence, evidence, and authority;
- makes the live fail-closed behavior explicit rather than accidental.

### Costs

- useful same-turn candidates cannot automatically become recurrence-bearing seeds;
- continuous surfacing can reduce clean observation opportunities;
- a richer observation ledger may eventually be needed for long sessions and cross-session analysis;
- deferral must be measured so the safety boundary does not hide excessive opportunity cost.

## Required invariants

1. An SSL-exposed observation never earns independent recurrence credit on the same turn.
2. A contaminated observation never becomes external evidence by relabeling.
3. The raw observation and its surfaced-seed provenance remain auditable.
4. A later clean observation may enter normal seed intake.
5. External verified evidence may still validate the underlying epistemic candidate through the Gate if it is independently sourced.
6. Point-of-use influence remains governed by ADR-001.

## Verification targets

Tests and measurements cover or should continue to cover:

- direct paraphrase after surfacing receives no recurrence credit;
- semantically distinct consequence after surfacing also receives no recurrence credit;
- the candidate remains present in the persisted turn report;
- later clean recurrence is accepted normally;
- deferral metrics distinguish observable recovery from unobservable recovery;
- stress measurements never label deferred candidates as false or useless.