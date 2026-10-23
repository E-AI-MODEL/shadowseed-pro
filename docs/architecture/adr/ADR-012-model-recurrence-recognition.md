# ADR-012: The Session Model Recognizes a Returning Gap

- Status: Accepted
- Date: 2026-10-23
- Refines: recurrence clustering (`RecurrenceClusterer`), ADR-004 (recurrence is observation)

## Context

Recurrence is how SSL remembers: a gap that returns keeps its trace. Cluster
membership decided whether a new candidate repeated an earlier one, using
embedding similarity against a fixed threshold (0.60).

The calibration in `docs/research/seed-calibration.md` labelled 56 cross-turn
candidate pairs from GPT-5 and GPT-6.1-sol. Same-gap pairs scored 0.59 to 0.75
and different-gap pairs up to 0.72. At 0.60 the threshold recognized 7 of 8
same-gap pairs and wrongly merged 10 of 44 different pairs. No threshold
separates them. Qwen 2.5 7B, asked whether two candidates name the same open
question, recognized 7 of 8 and wrongly merged 1 of 44.

## Decision

When a turn produces new seeds and the conversation already has clusters, the
session asks its own model one question:

> Open questions noted earlier: 1..K. New notes: a..n. For each new note, which
> earlier open question does it repeat, or NONE?

- Only clusters whose centroid is at least 0.3 similar to a new seed are
  offered (at most 12). A claimed repeat below 0.3 is refused and logged.
- A failed call or an unreadable answer falls back to the embedding threshold
  and is logged.
- Every decision is recorded as a `recurrence_recognized` event with the
  cluster, representative seed and similarity.
- `recurrence_recognizer` is `auto` by default: the model is used for real
  backends and embedding for the fixture backend. Sessions saved before this
  change restore with `embedding`, so an existing conversation does not change
  behavior mid-way.

## Revision after the live probe (prompt v2)

A live probe (`scripts/recurrence_live_probe.py`, #214) ran the twelve
eight-turn study conversations through live sessions with Qwen 2.5 7B and the
product embedding model `embeddinggemma`. No seed gained weight and no
recognition call failed (median 22 s per call on a CPU runner, against about
2.5 minutes per turn). However, notes from one turn were still grouped by the
0.60 embedding threshold, and with `embeddinggemma` that merged up to eleven
different gaps sharing the "The draft does not ..." template into one cluster.

The question now also covers notes from the same turn: each new note may repeat
an earlier open question (a number), an earlier note in the same list (a
letter), or neither (NONE). The first detection of a conversation with several
notes is also judged by the model. Embedding similarity stays a floor for both
kinds of repeat.

## Unchanged

- Recurrence is observation. It affects cluster membership, the recurrence count
  and trace. It is never evidence. Under `evidence_backed` (Controlled and
  Assisted) it never adds weight. Under `exploratory` (Autonomous) the existing
  recurrence step applies as before.
- Observation scoping: one recurrence credit per cluster per turn or source.
- The detector prompt and its contract (v0.6).

## Consequences

- One extra short model call per turn when new seeds meet existing clusters.
- Recognition quality depends on the session model; the fallback keeps the old
  behavior when the model cannot answer.
- The calibration set is small (8 same-gap pairs) and its labels are a model's
  judgment. The pair sample and judge script stay in the repository so the
  decision can be re-measured with other models or human labels.
