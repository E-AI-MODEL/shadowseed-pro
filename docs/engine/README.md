# Shadowseed Engine integration

`ShadowseedEngine` is the model-independent public boundary for the live Shadow
Seed Learning pipeline. It does not select a provider, keep provider
credentials, call a language model, or own the host application's conversation
history.

The host owns generation. The engine owns:

- shadow-memory intake and lifecycle;
- recurrence observations;
- the evidence-backed Validation Gate;
- contextual seed selection;
- recorded point-of-use authorization;
- post-generation candidate detection;
- contradiction records and influence audit.

## Integration flow

```text
host message
    -> engine.prepare_turn
    -> host model call with optional bounded candidate context
    -> engine.observe_turn with the visible answer
    -> updated shadow and audit state
```

One engine instance represents one ordered conversation or task stream. A host
must finish `observe_turn` before preparing another message.

## Minimal integration

```python
from shadowseed import ShadowseedEngine

engine = ShadowseedEngine()

prepared = engine.prepare_turn("What should this decision account for?")

# This function belongs to the host application. Shadowseed does not call it.
visible_answer = host_model.generate(
    message=prepared.question,
    additional_context=prepared.model_context,
)

turn_report = engine.observe_turn(prepared, visible_answer)
```

`prepared.model_context` is empty when no seed is authorized and relevant. When
present, it contains a bounded block with explicit untrusted-data delimiters.
`prepared.surfaced_seed_ids` and `prepared.influence_decisions` let the host
retain precise provenance without parsing the text block.

The host may use another prompt format or structured model input. It should
preserve the candidate-data boundary and must not treat every surfaced seed as
mandatory guidance.

## Supplying real detector and embedding adapters

The default fixture path demonstrates mechanics only. A real integration can
pass existing `DetectorBackend` and embedding implementations without giving
the engine a generation backend:

```python
engine = ShadowseedEngine(
    detector_backend=my_detector,
    embedding_fn=my_embedding_function,
)
```

A detached real detector with the built-in lexical embedder is rejected by
default. `allow_toy_embedder=True` exists only for explicit non-production
experiments.

A detector must implement:

```python
def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]: ...
```

An embedding function accepts text and returns a one-dimensional NumPy array.
Candidate output remains hypothetical and starts with weight zero regardless of
which detector produced it.

## Verified support

Support is an external host attestation. The engine validates the signal shape
and stable source identity; it cannot determine whether the source itself is
true.

```python
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
)

result = engine.submit_evidence(
    seed_id,
    ValidationSignal(
        kind=SignalKind.HUMAN_FEEDBACK,
        direction=SignalDirection.SUPPORT,
        verified=True,
        independent=True,
        source_ref="reviewer:stable-id",
        reason="Checked outside the model output",
    ),
)
```

Submitting evidence does not force promotion. The configured Gate policy owns
that decision.

## Contradictions

```python
result = engine.submit_contradiction(
    seed_id,
    reason="The referenced policy has been withdrawn",
    source_ref="policy-register:withdrawal-7",
)
```

The reason and source reference are required. An open contradiction blocks
later influence while preserving the audit history.

## Inspection, audit, and state

```python
shadow = engine.inspect()
checked_records = engine.audit()
state = engine.export_state()

restored = ShadowseedEngine.from_state(
    state,
    detector_backend=my_detector,
    embedding_fn=my_embedding_function,
)
```

State export is rejected while a prepared turn is awaiting observation. The
host should persist state only after `observe_turn` completes.

## Current boundary

This is an in-process Python API. It is not a hosted service, network security
boundary, authentication system, or tenant store. A host remains responsible
for user authorization, provider credentials, retention, deletion, and safe
handling of message content.

The local Workbench remains the packaged reference client. Its chat flow uses
the same `prepare_turn` and `observe_turn` methods around the selected model
adapter.
