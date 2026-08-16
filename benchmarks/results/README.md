# Benchmark result examples

This directory contains the active JSON schema and small example outputs. Generated local results should normally be written outside version control or to a clearly named experiment directory.

A result must not claim `live_benchmark` unless the complete benchmark route was executed.

The reviewed real-model live-runtime run is recorded under
[`live_runtime/`](live_runtime/). Its default and stress artifacts are kept
separate so non-production thresholds cannot be mistaken for shipped behavior.
