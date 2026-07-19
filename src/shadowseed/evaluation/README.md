# Evaluation ownership

The existing regression and small-benchmark code remains under `shadowseed.benchmark` for compatibility. This package records which evidence layer owns each type of evaluation and provides a safe migration path.

| Package | Purpose | Status |
|---|---|---|
| `regression/` | mechanics, smoke tests, and fixed small suites | active ownership marker |
| `behavioral/` | usefulness after promotion and downstream action | active ownership marker |
| `adversarial/` | gate, contradiction, and abuse resistance | active ownership marker |
| `open_review/` | open-set candidate quality and human review | active ownership marker |
| `transfer/` | transfer across topics, datasets, and models | planned ownership marker |

New evaluation code should declare one evidence layer. Existing imports may remain in `shadowseed.benchmark` until a tested migration is available.
