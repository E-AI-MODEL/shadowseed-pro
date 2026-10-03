# Shadowseed Web

Product-facing web client for the canonical Shadowseed engine.

This client deliberately does not reimplement Gate, recurrence, evidence,
lifecycle, authority or point-of-use semantics in TypeScript. Those remain in
the Python runtime/application layer.

## Local development

From the repository root:

    python -m pip install -e ".[test]"

For hosted OpenAI support, install the explicit provider extra instead:

    python -m pip install -e ".[test,openai]"
    python -m shadowseed_webapi --port 8765

In a second terminal:

    cd apps/web
    npm install
    npm run dev

Open http://127.0.0.1:3000.

The web v1 transport is deliberately loopback-only. The Python API cannot bind
to a remote interface, and `NEXT_PUBLIC_SHADOWSEED_API_URL` may only point to
`127.0.0.1` or `localhost`. Ollama generation, revision and embedding routes
are likewise rejected when `OLLAMA_HOST` is not loopback.

OpenAI is opt-in. A key entered in the web client is sent only to the loopback
Python API and kept in process memory; it is not written to the workspace,
session state, browser storage, exports, or logs. An existing `OPENAI_API_KEY`
environment variable remains supported. Credential setup does not grant data
egress permission: creating an OpenAI session and sending each OpenAI turn both
require explicit external-processing confirmation.

## Current product slice

- list/open persisted sessions;
- create fixture, local Ollama, or explicitly configured OpenAI sessions;
- choose Controlled, Evidence-backed/Assisted or Exploratory product behavior;
- send a real turn through the canonical Shadowseed application layer;
- render canonical chat history;
- render canonical seed authority, recurrence and evidence snapshots;
- render human/SSL orchestration state;
- inspect canonical seed timelines;
- submit verified evidence and contradictions through canonical services;
- configure OpenAI without persisting credentials and confirm external egress
  separately from credential setup.
