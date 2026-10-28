# Shadowseed Pro

Shadowseed Pro is a model-independent memory and validation engine for language-model applications. It includes a reusable Python engine, a local Workbench, lifecycle and audit mechanisms, and research tooling.

This repository contains several kinds of material: source code, recorded model conversations, detector outputs, runtime events, benchmark results, research notes, proposals, and historical decisions. They are not interchangeable. Read each record in its own context before drawing conclusions from it.

## Start with the observations

The research data is the starting point. Begin with the original outputs and event records, then follow their source, sequence, and transformations. Do not let a label from an earlier pipeline decide what a record means.

- [Chronological fixed22 A/B HTML](https://github.com/E-AI-MODEL/shadowseed-pro) — use the local owner-held `fixed22_A_en_B_volledig_naast_elkaar.html` artifact when available. It places the complete A and B answers side by side, by model, conversation, and turn, with the detector candidates recorded for each turn.
- [Raw-stage trajectory reconstruction](docs/research/possibility-space/raw-stage-trajectory-reconstruction-2026-10-28.md) — reconstruction of an existing derived register, retaining source keys and mismatches.
- [Possibility-space research index](docs/research/possibility-space/README.md) — links to source records, experiment material, technical documents, and earlier interpretations.
- [Original research question](docs/research/possibility-space-thesis.md) — the full Dutch formulation, preserved as written.
- [Benchmark results](benchmarks/results/) and [historical source results](archive/source-results/) — inspect each artifact's origin and configuration before comparing it with another record.

### How to read a record

Keep the following separate:

- **Original output:** the answer or text that was recorded.
- **Recorded event:** what a specific software component logged, such as a detector candidate, intake decision, seed lifecycle event, or surfacing event.
- **Source attribution:** the model, conversation, turn, artifact, configuration, and source hash that can be established from the record.
- **Researcher interpretation:** a reading added after the event. Preserve who made it and when.
- **Open question:** something the existing records do not yet resolve.

Labels such as `accepted`, `rejected`, `born`, `surfaced`, `promoted`, `failed`, and `not_atomic` are values emitted or assigned in particular historical workflows. Preserve them as recorded values. Do not treat them, by themselves, as judgements about the meaning, quality, originality, truth, or future significance of the underlying text.

A text difference is a text difference. A candidate record is a candidate record. A software transition is a software transition. Any interpretation beyond those observations should be stated separately and remain traceable to its source.

The repository contains overlapping datasets and different experiment designs. Counts from different sources should not be combined unless their relationship has been checked. A missing join is not, by itself, evidence that a record was lost. Repeated, absent, or differently worded text should remain visible rather than being silently normalized into a preferred account.

## The research question

The foundational question is preserved in full in [the thesis document](docs/research/possibility-space-thesis.md):

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

Keep this question intact while examining the material. The repository contains multiple attempts to describe, instrument, and investigate parts of it. Those attempts are historical records and working proposals, not substitutes for the original question.

## The software

The reusable `ShadowseedEngine` pipeline does not call a language model itself. A host application owns the model call and conversation history. The engine prepares a turn, observes the returned answer, records candidate and lifecycle events, and applies the configured authority checks.

The runtime separates memory from authority:

- `trace` records remembered presence and lifecycle behaviour.
- `weight` represents authority under the configured policy.
- The Validation Gate and point-of-use checks govern whether a candidate may influence a later answer.

These are software concepts and contracts. They do not, on their own, characterize the meaning of a recorded candidate or settle the broader research question. See the [manual](docs/manual/README.md), [engine integration guide](docs/engine/README.md), and [architecture decisions](docs/architecture/).

## Run from source

Requires Python 3.10 or later.

```bash
git clone https://github.com/E-AI-MODEL/shadowseed-pro.git
cd shadowseed-pro
python -m pip install --upgrade pip
pip install -e ".[test,workbench]"
python -m pytest -q
python -m ruff check .
shadowseed --help
shadowseed-web
```

For research tooling, install the separate research package:

```bash
pip install --no-deps -e ./research
shadowseed run-dialectic-falsification --help
```

See the [manual](docs/manual/README.md) for model configuration, the local Workbench, exports, privacy, and development.

## Source, results, and history

- `src/shadowseed/` — runtime, chat, memory, lifecycle, Gate, export and collection code.
- `src/shadowseed_agent/` — point-of-use authorization and influence audit.
- `research/` — research and evaluation tools.
- `benchmarks/` — benchmark suites, schemas, and result artifacts.
- `experiments/` and `results/` — experiment code and generated records.
- `docs/research/` — research questions, source records, protocols, and interpretations.
- `docs/architecture/` — architecture documents and ADRs.
- `paper/` — manuscript, sources, and bibliography.
- `archive/` — historical material.

Use the exact commit, model/backend, configuration, protocol, and source artifact when reproducing or comparing a result. Keep raw records intact; put derived summaries alongside them and document each transformation.

## Release and rights

The source tree and published release are different artifacts. Check the exact tag, release assets, and checksums for the version being used. See the [release notes](docs/workbench/release-0.12.4.md).

Repository states and releases that include `LICENSE` are available under the PolyForm Noncommercial License 1.0.0. Read [LICENSE](LICENSE) for the terms. Historical artifacts and third-party material may have different terms.
