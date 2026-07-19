# Benchmark pipeline

1. Define the SSL behavior under test.
2. Record the trusted code, data, and rule sources.
3. Verify the dataset host, paper source, and runner repository.
4. Classify the run as `benchmark_scan`, `benchmark_preparation`, or `live_benchmark`.
5. Record the exact command, model, provider, configuration, and output mapping.
6. Write a result that separates measured scores from readiness claims.
7. Keep `execution_gap=true` until the complete route has been executed and checked.
