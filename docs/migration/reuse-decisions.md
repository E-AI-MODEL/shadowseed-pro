# Reuse Decisions

| Source area | Decision | Reason |
|---|---|---|
| `manager.py`, SSOT, vector store, agent contract | Keep as active runtime | Core SSL implementation |
| Benchmark surfacing code | Extract to `shadowseed.surfacing` | Prevent chat and benchmark drift |
| Model and embedding backends | Extract to `shadowseed.adapters` | Used by applications and benchmarks |
| Retrieval probe | Extract to `shadowseed.retrieval_probe` | Runtime behavior, not benchmark-only code |
| Recurrence clustering | Extract to runtime modules | Shared algorithmic behavior |
| Text tokenization and lexical embeddings | Extract to `shadowseed.text_similarity` | Shared deterministic utility |
| Old benchmark import locations | Keep as thin wrappers | Preserve compatibility with older imports |
| Historical open-review rounds | Keep under `benchmarks/open_review/rounds` | Tests use them as regression fixtures |
| Original documentation | Move to `archive/source-docs` | Preserve provenance without presenting it as current guidance |
| Original workflows | Move to `archive/source-workflows` | Preserve research routes; replace active CI with one audited workflow |
| Original result artifacts | Move to `archive/source-results` | Preserve evidence while keeping generated output out of active source paths |
| Dutch benchmark inputs | Keep as fixtures | Preserve multilingual coverage and historical comparability |
| Dutch active prose, CLI help, prompts, and errors | Translate to English | New repository language policy |
