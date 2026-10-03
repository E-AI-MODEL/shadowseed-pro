# Shadowseed Web

Product-facing web client for the canonical Shadowseed engine.

This client deliberately does not reimplement Gate, recurrence, evidence,
lifecycle, authority or point-of-use semantics in TypeScript. Those remain in
the Python runtime/application layer.

## Local development

From the repository root:

    python -m pip install -e ".[test]"
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

## First vertical slice

- list/open persisted sessions;
- create fixture or local Ollama sessions;
- choose Controlled, Evidence-backed/Assisted or Exploratory product behavior;
- send a real turn through the canonical Shadowseed application layer;
- render canonical chat history;
- render canonical seed authority, recurrence and evidence snapshots;
- render human/SSL orchestration state.

Evidence and contradiction endpoints already exist in the local API for the
next UI slice.
