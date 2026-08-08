# Shadowseed Workbench 0.4.0 Tester Preview

Shadowseed 0.4.0 adds a practical local tester environment over the existing
Shadow Seed Learning runtime. This prerelease is intended for guided and
self-directed testing, feedback collection and auditable session review.

## Highlights

- local Gradio Workbench launched with `shadowseed workbench`;
- versioned SQLite tester workspace with backup and restore;
- resumable sessions and imported scenarios;
- Demo, Balanced, Conservative and Exploratory profiles;
- fixture, Ollama, Hugging Face Transformers and OpenAI backend flows;
- seed inspection with plain-language explanations and audit timeline;
- record-only tester feedback;
- side-by-side and blind baseline-vs-Shadowseed comparison;
- full session report ZIPs with standalone HTML/JSON/CSV content;
- privacy-minimized support bundles;
- SHA-256 manifest verification and defensive ZIP validation;
- clean-wheel, headless UI and cross-platform installation smokes;
- optional Docker packaging.

## Install

```bash
python -m pip install "shadowseed[workbench]"
shadowseed doctor
shadowseed init
shadowseed workbench
```

See `docs/workbench/README.md` for the tester workflow and
`docs/workbench/limitations.md` before sharing data or changing the default
network binding.

## Safety and claim boundary

The Workbench does not add a direct authority editor or a second Validation
Gate. Tester feedback remains record-only by default. Full reports can contain
sensitive session content; support bundles are minimized but not anonymous in a
formal privacy sense.

This is a **tester preview**: local-first, single-user and research-ready, but
not production-ready. A successful Workbench run or tester comparison is not by
itself scientific evidence of model benefit.
