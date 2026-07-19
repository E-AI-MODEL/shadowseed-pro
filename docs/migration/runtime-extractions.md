# Runtime code extracted from benchmark modules

The audit found production behavior imported from `shadowseed.benchmark`, especially by the live chat. The reusable parts now have runtime-owned modules. Compatibility wrappers keep older imports working.

| Runtime concern | New owner | Former location or duplicate |
|---|---|---|
| Surfacing thresholds, early-turn margin, resurface damping, selection | `shadowseed.surfacing` | duplicated in `chat.py` and `benchmark/ssl_session_suite.py` |
| Recurrence cluster representative refresh | `shadowseed.recurrence` | benchmark session helper |
| Model generation backends | `shadowseed.adapters.models` | benchmark model adapter module |
| OpenAI and Ollama clients | `shadowseed.adapters.openai_client`, `shadowseed.adapters.ollama_client` | benchmark adapter helpers |
| Embedding backends | `shadowseed.adapters.embedding` | benchmark embedding helpers |
| Model-backed gap detector | `shadowseed.detection.model_detector` | `benchmark/open_set_model_detector.py` |
| Recurrence clustering | `shadowseed.recurrence_clustering` | benchmark recurrence module |
| Retrieval probes | `shadowseed.retrieval_probe` | benchmark retrieval helper |
| Text similarity | `shadowseed.text_similarity` | benchmark-local lexical helpers |

The live chat and benchmark session suite now use the same surfacing functions. Contract-blocked candidates are not recorded as surfaced.
