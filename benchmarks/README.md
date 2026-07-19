# Benchmarks

This directory contains active benchmark definitions, review fixtures, schemas, and generated examples.

The benchmark lane separates three states:

- `benchmark_scan`: source and runner discovery only
- `benchmark_preparation`: an executable route is being prepared or verified
- `live_benchmark`: an end-to-end run was actually executed

A visible upstream repository is not proof of a live run. Every result records its run type, execution status, host status, runner status, limitations, and whether an execution gap remains.

Historical open-review rounds under `open_review/rounds/` are retained as regression fixtures. Their original language and machine tokens are preserved where tests or published artifacts depend on them.
