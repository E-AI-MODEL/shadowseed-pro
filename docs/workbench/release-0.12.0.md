# Shadowseed Workbench 0.12.0

Shadowseed Workbench 0.12.0 adds a packaged local web product on top of the
canonical Shadowseed runtime. It keeps the existing Gate, evidence, lifecycle,
recurrence, contradiction and point-of-use semantics in Python and exposes them
through a new browser client without creating a second authority implementation.

`v0.11.1` remains the latest published Research Preview until the exact-SHA
Release Workbench publishes `v0.12.0`.

## Web product foundation

The new web client provides the normal Shadowseed chat experience through a
loopback-only Python API and renders persisted canonical state rather than
reimplementing SSL semantics in TypeScript.

The first web slice includes:

- persisted session listing, opening and creation;
- fixture and local Ollama chat through canonical application services;
- Controlled, Assisted/Evidence-backed and Exploratory product behavior choices;
- canonical chat history, seed summaries and human/SSL orchestration state;
- responsive session and Shadow inspectors;
- stable request IDs so a lost HTTP response cannot silently duplicate a turn.

## Seed detail, evidence and contradictions

A seed can now be opened from the Shadow inspector. The detail surface renders
the canonical seed timeline assembled by the Python inspection layer, including
validation, Gate, contradiction and influence records.

The browser can also invoke existing authority-bearing application paths for:

- operator-attested verified evidence;
- contradiction submission;
- contradiction resolution through the canonical Gate flow.

These mutations use persistent request IDs and the existing production ledger,
so retries after response loss are idempotent. Credential, evidence and
contradiction semantics remain server-side.

## Explicit OpenAI provider setup

The local web product can expose OpenAI when the explicit `openai` provider
extra is installed.

A key entered in the browser is sent only to the loopback Python API and held in
process memory. It is not written to workspace state, SQLite, exports, browser
storage or API responses. The existing `OPENAI_API_KEY` environment path
remains supported for non-interactive setup.

Credential setup and data-egress permission are separate:

- an OpenAI session cannot be created without explicit external-processing
  confirmation;
- each OpenAI turn requires fresh external-processing confirmation;
- existing OpenAI sessions remain inspectable when the provider is not ready,
  but provider-backed generation is disabled.

The thin frozen standalone still does not bundle the OpenAI SDK.

## One-process packaged launcher

`shadowseed-web` is now the normal packaged web launcher.

It:

- serves the static Next export and `/api/v1` from one Python process and one
  loopback origin;
- opens the browser automatically;
- falls back to another loopback port if 8765 is already occupied;
- requires no Node runtime in the packaged product;
- rejects static path traversal;
- verifies packaged web assets against a SHA-256 manifest before startup.

The existing Gradio Workbench remains available. Frozen `Shadowseed` bundles
also accept `--web`, allowing Windows, macOS and Linux standalone packages to
exercise the same packaged web client without replacing the legacy surface.

## Packaging and release assurance

The 0.12.0 release contract now verifies the web product at every distribution
boundary:

- Web Client CI builds the static export and checks the browser/API contract;
- normal CI builds and syncs web assets before wheel/sdist creation;
- a clean installed wheel must pass `shadowseed-web --self-test` outside the
  source tree;
- PyInstaller bundles include the web assets and execute a frozen web self-test
  on Windows, macOS and Linux;
- macOS archive round-trip verification includes the packaged web self-test;
- Release Workbench dispatches Web Client CI as exact-SHA release evidence.

## Security and claim boundary

0.12.0 remains a **Research Preview** candidate. It does not establish
`production-ready/local`, hostile-network safety, multi-user service security,
universal missing-information detection, factual truth of seeds, or general
answer-quality improvement.

The web surface does not weaken the core doctrine:

```text
observation ≠ authority
recurrence ≠ evidence
promotion ≠ relevance
relevance ≠ permission
permission ≠ use
use ≠ new evidence
```

Publication is a separate fact. The version is released only after the explicit
exact-SHA Release Workbench succeeds and publishes the immutable `v0.12.0` tag
and verified release assets.
