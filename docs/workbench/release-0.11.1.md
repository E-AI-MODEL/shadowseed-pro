# Shadowseed Workbench 0.11.1

Shadowseed Workbench 0.11.1 is a focused compatibility hotfix for the Ollama-first semantic embedding path introduced in 0.11.0.

## Ollama / EmbeddingGemma compatibility diagnostic

0.11.0 made `embeddinggemma` the default local semantic embedding model for Ollama Workbench sessions. EmbeddingGemma itself requires Ollama v0.11.10 or later.

On an older local Ollama server, the Workbench could therefore fail on `POST /api/embed` with a generic HTTP 404 and then report the misleading suggestion that Ollama might not be running or that the model had not been pulled.

0.11.1 corrects that diagnostic boundary:

- HTTP status/body details are preserved for Ollama compatibility decisions;
- when `embeddinggemma` receives a route-level 404, the client checks the local Ollama server version;
- versions older than 0.11.10, or servers that cannot report a compatible version, now produce an explicit update-required message;
- a true “model not found” 404 still keeps the existing `ollama pull embeddinggemma` guidance;
- the vNext Workbench setup text now states that EmbeddingGemma requires Ollama v0.11.10 or later.

The current `/api/embed` endpoint remains the normal path. This hotfix does not silently switch EmbeddingGemma to a legacy embedding endpoint, because the model itself has a minimum Ollama version requirement.

## User action

If 0.11.0 shows an HTTP 404 for `/api/embed` with `embeddinggemma`, update Ollama to v0.11.10 or later, restart the Ollama app/server, and retry:

```bash
ollama --version
ollama pull embeddinggemma
```

## Claim boundary

0.11.1 changes compatibility diagnostics only. It does not change Gate, authority, lifecycle, recurrence, behavior epochs, SSL orchestration, embedding vectors, model-selection policy or the `production-ready/local` claim.
