# Contributing

1. Install the scope you are changing. For core tests use `pip install -e ".[test]"`; for Workbench changes use `pip install -e ".[test,workbench]"`.
2. Run `python -m ruff check .` and `python -m pytest -q` before opening a change. Workbench and packaging changes must also pass their focused CI and portability/standalone gates.
3. Keep trace and weight separate. A remembered candidate is not evidence and is not authority.
4. Never allow a seed to influence output without a current logged Gate authorization and a point-of-use contract check.
5. Keep recurrence, semantic similarity, retrieval, and external evidence distinct. Reusing the same underlying external `source_ref` through another signal channel must not create additional authority credit.
6. Preserve the chat-first product contract: ordinary new sessions are live/evidence-backed; a same-message SSL-off control is generated automatically and must not mutate detector, recurrence, Gate, seed, or conversation-history state.
7. Put reusable behavior in runtime modules. Tests and benchmarks must import canonical behavior rather than carry independent copies.
8. Label fixture evidence, real-model evidence, exploratory results, reviewed results, and replicated results separately. Packaging or tester usability is not efficacy evidence.
9. Write active code, documentation, CLI text, and errors in English. Multilingual product input is supported; benchmark fixtures may retain a documented research language.
10. Keep historical and research-only material explicitly labelled. Do not make archived baselines, scenario JSON, or evaluation harnesses prerequisites for the ordinary tester flow.
