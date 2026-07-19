# Contributing

1. Install with `pip install -e ".[test]"`.
2. Run `ruff check .` and `pytest -q` before opening a change.
3. Keep trace and weight separate.
4. Never allow a seed to influence output without a logged gate decision and point-of-use contract check.
5. Put reusable behavior in runtime modules. Tests and benchmarks must import it rather than carry independent copies.
6. Label fixture evidence, real-model evidence, exploratory results, and replicated results separately.
7. Write active code, documentation, CLI text, and errors in English. Multilingual input fixtures are welcome when their purpose is documented.
