# Contributing

Shadowseed Pro is source-available under the license shipped with the repository state you are using. Read `LICENSE` before copying, modifying, or redistributing code. Commercial use is not granted by the PolyForm Noncommercial License 1.0.0.

External contributions are welcome for review, but contributor relicensing/assignment is not currently formalized. Before investing in a substantial code contribution, open an issue to agree scope and rights expectations. Submitting a patch does not silently transfer copyright or create commercial relicensing rights for the maintainer.

1. Install the scope you are changing. For core tests use `pip install -e ".[test]"`; for Workbench changes use `pip install -e ".[test,workbench]"`.
2. Run `python -m ruff check .` and `python -m pytest -q` before opening a change. Workbench and packaging changes must also pass their focused CI and portability/standalone gates.
3. Keep trace and weight separate. A remembered candidate is not evidence and is not authority.
4. Never allow a seed to influence output without a current logged Gate authorization and a point-of-use contract check.
5. Keep recurrence, semantic similarity, retrieval, and external evidence distinct. Reusing the same underlying external `source_ref` through another signal channel must not create additional authority credit.
6. Preserve the chat-first product contract: ordinary new sessions are live/evidence-backed; a same-message SSL-off control is generated automatically and must not mutate detector, recurrence, Gate, seed, or conversation-history state.
7. Put reusable behavior in runtime modules. Tests and benchmarks must import canonical behavior rather than carry independent copies.
8. Label fixture evidence, real-model evidence, exploratory results, evidence-backed research results, reviewed results, and replicated results separately. Packaging, licensing, or tester usability is not efficacy evidence.
9. Never create a benchmark-only authority bypass. Research evidence must use the same typed signal and Gate boundaries as the runtime, with policy differences explicitly declared.
10. Never fill independent human-review fields automatically. Missing review remains pending evidence, not a value to infer from model output.
11. Write active code, documentation, CLI text, and errors in English. Multilingual product input is supported; benchmark fixtures may retain a documented research language.
12. Keep historical and research-only material explicitly labelled. Do not make archived baselines, scenario JSON, or evaluation harnesses prerequisites for the ordinary tester flow.
